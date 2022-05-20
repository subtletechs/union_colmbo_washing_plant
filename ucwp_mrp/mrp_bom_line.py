from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import AND, NEGATIVE_TERM_OPERATORS
from odoo.tools import float_round

from collections import defaultdict


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample',
                                      related='product_tmpl_id.garment_select')
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_tmpl_id.buyer', required=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product_tmpl_id.fabric_type', required=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related='product_tmpl_id.wash_type',
                                required=True)
    machine_type = fields.Many2one(comodel_name="machine.type", string="Machine Type")
    lot_size = fields.Integer(string="Lot size")
    per_piece_weight = fields.Float(string="Per piece weight")


class MachineType(models.Model):
    _name = "machine.type"

    name = fields.Char(sting="name")
    code = fields.Char(string="code")


class Machines(models.Model):
    _name = "mo.machines"
    _rec_name = "machine_number"

    machine_number = fields.Char(string="Machine Number")
    machine_type = fields.Many2one(comodel_name="machine.type", string="Machine Type")


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    sub_process = fields.One2many(comodel_name='mrp.routing.sub.process', inverse_name='mrp_routing_workcenter_id',
                                  string='Sub Process')


class MrpRoutingSubProcess(models.Model):
    _name = 'mrp.routing.sub.process'

    sub_process = fields.Many2one(comodel_name='routing.sub.process', string='Sub Process', required=True)
    time = fields.Float(sting="Time")
    temperature = fields.Float(string="Temperature")
    ph = fields.Float(string="pH")
    mrp_routing_workcenter_id = fields.Many2one(comodel_name='mrp.routing.workcenter', string="Operation")


class RoutingSubProcess(models.Model):
    _name = 'routing.sub.process'

    name = fields.Char(string='Sub Process', required=True)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    sub_process = fields.Many2one(comodel_name='routing.sub.process', string='Sub Process')

    @api.onchange('operation_id')
    def set_domain_sub_process(self):
        sub_list =[]
        if self.operation_id:
            if self.operation_id.sub_process:
                for records in self.operation_id.sub_process:
                    sub_list.append(records.sub_process)
        return {'domain':{'sub_process':[('id','in',sub_list)]}}



