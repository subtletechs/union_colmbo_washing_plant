from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class InspectionQuantity(models.Model):
    _name = "inspection.quantity"

    quantity = fields.Char(string="Quantity")
    pass_Quantity = fields.Char(string="Pass Quantity")
    fail_Quantity = fields.Char(string="Fail Quantity")
    quality_id = fields.Many2one(comodel_name="quality.check")
