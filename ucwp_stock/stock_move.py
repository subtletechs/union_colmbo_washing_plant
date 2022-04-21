from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.move"

    invoice_type = fields.Selection([('invoice', 'Invoiceable'), ('not_invoiceable', 'Not-Invoiceable')],
                                    string='Invoice Type')
