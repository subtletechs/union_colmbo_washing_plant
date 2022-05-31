from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class BulkProduction(models.Model):
    """ Bulk Manufacturing Orders """
    _name = 'bulk.production'

    name = fields.Char(string="Parent Manufacturing Order", default="New")
    product = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    manufacture_orders = fields.One2many(comodel_name='mrp.production', inverse_name='bulk_id',
                                         string='Manufacture Orders')
    garment_receipt = fields.Many2one(comodel_name="stock.picking", string="Garment Receipt")
    manufacture_operation_stages = fields.One2many(comodel_name="manufacture.operation.stages",
                                                   string="Manufacture Stages",
                                                   inverse_name="bulk_production_id")
    is_clicked = fields.Boolean(string="Clicked", default=False)

    # TODO uncomment if lot information available
    def calculate_job_quantity(self):
        pass
        # self.lot_information = [(5)]
        # jobs = int(self.quantity / self.lot_size) + 2
        # quantity = self.quantity
        # for job_no in range(1, jobs):
        #     if quantity > self.lot_size:
        #         self.lot_information = [(0, 0, {'job_no': job_no, 'job_qty': self.lot_size})]
        #         quantity -= self.lot_size
        #     else:
        #         self.lot_information = [(0, 0, {'job_no': job_no, 'job_qty': quantity})]

    def generate_mo(self):
        self.is_clicked = True
        bulk_id = self.id
        for manufacture_operation_stage in self.manufacture_operation_stages:
            for operation_line in manufacture_operation_stage.operation_lines:
                mo_record = self.env['mrp.production'].create({
                    'product_id': self.product.id,
                    'product_uom_id': self.product.uom_id.id,
                    'bom_id': manufacture_operation_stage.bom.id,
                    'job_no': operation_line.job_no,
                    'product_qty': operation_line.job_qty,
                    'machine_no': operation_line.machine_no.id,
                    'operator_name': operation_line.operator_name.id,
                    'mo_barcode': operation_line.barcode.id,
                    'bulk_id': bulk_id
                })


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bulk_id = fields.Many2one(comodel_name="bulk.production", string="Parent Manufacturing Order")
    # TODO set mo_barcode, job_no, machine_no, operator_name readonly=True after MO auto generate process
    # [UC-08]
    # TODO : if mo_barcode not required remove when deploy
    mo_barcode = fields.Many2one(comodel_name="operation.lines", string="Barcode", readonly=False)
    job_no = fields.Integer(string="Job No", readonly=False)
    machine_no = fields.Many2one(comodel_name="mo.machines", string="Machine No", readonly=False)
    operator_name = fields.Many2one(comodel_name="hr.employee", string="Operator Name", readonly=False)
    # TODO add filters to stock.picking
    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    # [UC-11]
    quality_check_count = fields.Integer(string='Quality Check Count', compute='_get_quality_checks')
    quality_check_id = fields.Many2one(comodel_name='ucwp.quality.check', string="Quality Check ID",
                                       compute='_get_quality_checks', copy=False)

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
        """Print Job Card for MO"""
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
        """Popup quality check view"""
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

    # [UC-10]
    def action_confirm(self):
        if self.bom_id.state == 'draft':
            raise ValidationError(_('BoM should need to be validated first'))
        return super(MrpProduction, self).action_confirm()


# [UC-07]
class ManufactureOperationStages(models.Model):
    _name = "manufacture.operation.stages"

    bom = fields.Many2one(comodel_name="mrp.bom", string="Bill of Material", required=True)
    lot_size = fields.Integer(string="Lot size", related="bom.lot_size", store=True, readonly=True)
    operation_lines = fields.One2many(comodel_name="operation.lines", inverse_name="manufacture_operation_stages_id",
                                      string="Operation Lines")
    bulk_production_id = fields.Many2one(comodel_name="bulk.production", string="Bulk ID")


class OperationLines(models.Model):
    _name = "operation.lines"
    _rec_name = "barcode"

    job_no = fields.Integer(string="Job No")
    job_qty = fields.Integer(string="Job Quantity")
    machine_no = fields.Many2one(comodel_name="mo.machines", string="Machine No")
    operator_name = fields.Many2one(comodel_name="hr.employee", string="Operator Name")
    barcode = fields.Many2one(comodel_name="stock.production.lot", string="Barcode")
    manufacture_operation_stages_id = fields.Many2one(comodel_name="manufacture.operation.stages",
                                                      string="MO stages ID", invisible=True)
    bulk_production = fields.Many2one(comodel_name="bulk.production", string="Parent Manufacturing Order",
                                      related="manufacture_operation_stages_id.bulk_production_id")
