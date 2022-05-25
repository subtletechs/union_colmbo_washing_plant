from odoo import api, fields, models, _, tools


class PreCosting(models.Model):
    _name = "pre.costing"

    name = fields.Char(string="Name")
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    total_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price", readonly=True)
    res_currency = fields.Many2one(comodel_name='res.currency', default=lambda self: self.env.company.currency_id)
    # currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')
    # total_line_costs = fields.Monetary(string='Retail Price', currency_field='currency_id')
    gsn = fields.Text(string="GSN")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="States")

    def action_confirm(self):
        sequence = self.env['ir.sequence'].next_by_code('pre.costing') or _('New')
        self.write({'state': 'confirm', 'name': sequence})

    def action_draft(self):
        self.write({'state': 'draft'})
    # TODO pre costing must be added to sales menu
