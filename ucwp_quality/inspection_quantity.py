from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class InspectionQuantity(models.Model):
    _name = "inspection.quantity"

    quantity = fields.Float(string="Quantity")
    pass_quantity = fields.Float(string="Pass Quantity")
    fail_quantity = fields.Float(string="Fail Quantity", compute="calculate_fail_quantity")
    quality_id = fields.Many2one(comodel_name="quality.check")

    @api.depends('pass_quantity')
    def calculate_fail_quantity(self):
        self.fail_quantity = self.quantity - self.pass_quantity
