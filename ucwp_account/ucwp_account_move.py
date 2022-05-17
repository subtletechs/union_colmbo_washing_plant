from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    delivery_order = fields.Many2one(comodel_name="stock.picking", string="Delivery order")
