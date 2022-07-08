from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    payment_method = fields.Selection([('cod', 'Cash On Delivery'), ('credit', 'Credit')], string='Payment Type')
    geo_location = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string='Customer From')
    credit_limit_available = fields.Boolean(string="Credit Limit Available", default=False)
    credit_limit = fields.Monetary(string="Credit Limit")
    currency_id = fields.Many2one(default=lambda self: self.env.company.currency_id, string="Currency")
    available_credit_limit = fields.Monetary(currency_field='currency_id', string="Available Credit Limit")
    total_pending_payments = fields.Monetary(currency_field='currency_id', string="Total Pending Payments")
    # total_due = fields.Monetary(compute='_compute_total_due')

    # # @api.depends_context('company', 'allowed_company_ids')
    # def _compute_total_due(self):
    #     """
    #     Compute the fields 'total_due'
    #     """
    #     today = fields.Date.context_today(self)
    #     for record in self:
    #         total_due = 0
    #         total_overdue = 0
    #         for aml in record.unreconciled_aml_ids:
    #             if aml.company_id == self.env.company and not aml.blocked:
    #                 amount = aml.amount_residual
    #                 total_due += amount
    #                 is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
    #                 if is_overdue:
    #                     total_overdue += amount
    #         record.total_due = total_due

    # def compute_total_pending(self):
    #     for record in self:
    #         if record.credit_limit_available:
    #             record.total_pending_payments = record.total_due
    #
    # def compute_available_credit_limit(self):
    #     for record in self:
    #         if record.credit_limit_available:
    #             record.available_credit_limit = record.credit_limit - record.total_due


