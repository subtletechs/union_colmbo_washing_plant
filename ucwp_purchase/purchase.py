from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    chemical_purchase = fields.Boolean(string="Chemical Purchase", default=False)
