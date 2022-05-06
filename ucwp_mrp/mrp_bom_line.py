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


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    time = fields.Float(sting="Time")
    temperature = fields.Float(string="Temperature")
    ph = fields.Float(string="pH")


class MachineType(models.Model):
    _name = "machine.type"

    name = fields.Char(sting="name")
    code = fields.Char(string="code")


class Machines(models.Model):
    _name = "mo.machines"
    _rec_name = "machine_number"

    machine_number = fields.Char(string="Machine Number")
    machine_type = fields.Many2one(comodel_name="machine.type", string="Machine Type")
