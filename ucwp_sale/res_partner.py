from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    payment_method = fields.Selection([('cod', 'Cash On Delivery'), ('credit', 'Credit')], string='Payment Type')
    geo_location = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string='Customer From')
    credit_limit_available = fields.Boolean(string="Credit Limit Available", default=False)
    credit_limit = fields.Monetary(string="Credit Limit")
    currency_id = fields.Many2one(default=lambda self: self.env.company.currency_id, string="Currency")
    # available_credit_limit = fields.Monetary(currency_field='currency_id', string="Available Credit Limit",
    #                                          compute='compute_available_credit_limit')
    # total_pending_payments = fields.Monetary(currency_field='currency_id', string="Total Pending Payments",
    #                                          compute='compute_total_pending')
    #
    # def compute_total_pending(self):
    #     self.total_pending_payments = self.total_due
    #
    # def compute_available_credit_limit(self):
    #     self.available_credit_limit = self.credit_limit - self.total_due
