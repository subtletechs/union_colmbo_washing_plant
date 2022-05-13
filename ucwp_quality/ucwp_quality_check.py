from odoo import api, fields, models, _


class UCWPQualityCheck(models.Model):
    _name = "ucwp.quality.check"
    _description = 'Quality Check'

    quantity = fields.Integer(string="Quantity")
    fail_quantity = fields.Integer(string="Fail Quantity")
    pass_quantity = fields.Integer(string="Pass Quantity")
    # [UC-11]
    grn = fields.Many2one(comodel_name="stock.picking", string="GRN")
    quality_check_lines = fields.One2many(comodel_name="quality.check.lines", inverse_name="ucwp_quality_check_id",
                                          string="Quality Lines")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    manufacture_order = fields.Many2one(comodel_name="mrp.production", string="Manufacture Orders")


# [UC-11]
class QualityCheckLines(models.Model):
    _name = "quality.check.lines"
    _description = "Quality Check Lines"

    product = fields.Many2one(comodel_name="product.product", string="Product")
    lot_no = fields.Many2one(comodel_name="stock.production.lot", string="Lot No", required=True)
    pass_fail = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Pass/Fail", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    defects = fields.Many2one(comodel_name="defects", string="Defects")
    image = fields.Binary(string="Image")
    ucwp_quality_check_id = fields.Many2one(comodel_name="ucwp.quality.check", string="Quality Check")
    comment = fields.Char(string="Comment")
    state = fields.Selection([('processed', 'Processed'), ('rejected', 'Rejected')], string="State",
                             compute="calculate_state", store=True)

    def calculate_state(self):
        if self.pass_fail == 'pass':
            self.state = 'processed'

    def process(self):
        self.write({'state': 'processed'})

    # TODO functionality should need to be updated
    def cancel_process(self):
        self.write({'state': 'rejected'})
        fail_qty = self.quantity
