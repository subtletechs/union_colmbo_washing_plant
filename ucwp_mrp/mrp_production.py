from odoo import api, fields, models, _


class BulkProduction(models.Model):
    """ Bulk Manufacturing Orders """
    _name = 'bulk.production'

    name = fields.Char(string="Bulk Production", default="New")
    product = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    manufacture_orders = fields.One2many(comodel_name='mrp.production', inverse_name='bulk_id',
                                         string='Manufacture Orders')
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product.buyer',
                            store=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product.fabric_type', store=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type",
                                related='product.wash_type', store=True)
    bom = fields.Many2one(comodel_name="mrp.bom", string="Bill of Material")
    lot_size = fields.Integer(string="Lot Size", related="bom.lot_size")
    quantity = fields.Integer(string="Bulk size")
    lot_information = fields.One2many(comodel_name="mo.lot.information.lines", inverse_name="bulk_production_id",
                                      string="Lot Information")

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


class LotInformationLines(models.Model):
    _name = "mo.lot.information.lines"

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
