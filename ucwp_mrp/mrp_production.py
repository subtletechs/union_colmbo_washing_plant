from odoo import api, fields, models, _
from datetime import datetime


class BulkProduction(models.Model):
    """ Bulk Manufacturing Orders """
    _name = 'bulk.production'

    name = fields.Char(string="Bulk Production", default="New")
    product = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    manufacture_orders = fields.One2many(comodel_name='mrp.production', inverse_name='bulk_id',
                                         string='Manufacture Orders')
    # buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product.buyer',
    #                         store=True)
    # fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
    #                               related='product.fabric_type', store=True)
    # wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type",
    #                             related='product.wash_type', store=True)
    # bom = fields.Many2one(comodel_name="mrp.bom", string="Bill of Material")
    # lot_size = fields.Integer(string="Lot Size", related="bom.lot_size", store=True)
    # quantity = fields.Integer(string="Bulk size")
    # lot_information = fields.One2many(comodel_name="mo.lot.information.lines", inverse_name="bulk_production_id",
    #                                   string="Lot Information")
    garment_receipt = fields.Many2one(comodel_name="stock.picking", string="Garment Receipt")

    def calculate_job_quantity(self):
        self.lot_information = [(5)]
        jobs = int(self.quantity / self.lot_size) + 2
        quantity = self.quantity
        for job_no in range(1, jobs):
            if quantity > self.lot_size:
                self.lot_information = [(0, 0, {'job_no': job_no, 'job_qty': self.lot_size})]
                quantity -= self.lot_size
            else:
                self.lot_information = [(0, 0, {'job_no': job_no, 'job_qty': quantity})]


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bulk_id = fields.Many2one(comodel_name="bulk.production", string="Bulk Production")
    # TODO set mo_barcode, job_no, machine_no, operator_name readonly=True after MO auto generate process
    # [UC-08]
    # TODO : if mo_barcode not required remove when deploy
    mo_barcode = fields.Many2one(comodel_name="mo.lot.information.lines", string="Barcode", readonly=False)
    job_no = fields.Integer(string="Job No", readonly=False)
    machine_no = fields.Many2one(comodel_name="mo.machines", string="Machine No", readonly=False)
    operator_name = fields.Many2one(comodel_name="hr.employee", string="Operator Name", readonly=False)
    # TODO add filters to stock.picking
    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    # [UC-11]
    quality_check_count = fields.Integer(string='Quality Check Count', compute='_get_quality_checks')
    quality_check_id = fields.Many2one(comodel_name='ucwp.quality.check', compute='_get_quality_checks', copy=False)

    def _get_quality_checks(self):
        """Calculate the number of quality checks available for the MO and those IDs"""
        quality_checks = self.env['ucwp.quality.check'].search([('manufacture_order', '=', self.id)], limit=1)
        if quality_checks:
            self.quality_check_count = 1
            self.quality_check_id = quality_checks.id
        else:
            self.quality_check_count = 0
            self.quality_check_id = None

    def action_view_quality_check(self):
        if self.quality_check_count == 1:
            quality_record_id = self.quality_check_id.id
            view = self.env.ref('union_colmbo_washing_plant.ucwp_quality_check_form_view')
            return {
                'res_model': 'ucwp.quality.check',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'res_id': quality_record_id
                }

    def print_job_card(self):
        barcode = self.mo_barcode.barcode
        product = self.product_id.display_name
        buyer = self.product_id.buyer.name
        wash_type = self.product_id.wash_type.display_name
        job_no = self.job_no
        machine_no = self.machine_no.display_name
        operator_name = self.operator_name.display_name

        data = {
            'barcode': barcode,
            'mo_no': self.name,
            'product': product,
            'buyer': buyer,
            'wash_type': wash_type,
            'job_no': job_no,
            'machine_no': machine_no,
            'operator_name': operator_name,
            'date_time': datetime.now(),
            'name': self.name
        }
        return self.env.ref('union_colmbo_washing_plant.job_card_action').report_action(self, data=data)

    def after_quality_check(self):
        view = self.env.ref('union_colmbo_washing_plant.ucwp_quality_check_form_view')

        return {
            'res_model': 'ucwp.quality.check',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_manufacture_order': self.id,
                'default_quality_point': 'after_wash',
            },
        }


class LotInformationLines(models.Model):
    _name = "mo.lot.information.lines"
    _rec_name = "barcode"

    job_no = fields.Integer(string="Job No")
    job_qty = fields.Integer(string="Job Quantity")
    machine_no = fields.Many2one(comodel_name="mo.machines", string="Machine No")
    operator_name = fields.Many2one(comodel_name="hr.employee", string="Operator Name")
    barcode = fields.Char(string="Barcode")
    bulk_production_id = fields.Many2one(comodel_name="bulk.production", string="Bulk Production")

    @api.model
    def create(self, values):
        job_sequence = self.env['ir.sequence'].next_by_code('lot_information_lines') or _('New')
        values['barcode'] = job_sequence
        return super(LotInformationLines, self).create(values)
