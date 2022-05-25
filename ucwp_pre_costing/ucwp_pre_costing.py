from odoo import api, fields, models, _, tools


class PreCosting(models.Model):
    _name = "pre.costing"
    _description = "Pre Costing"

    name = fields.Char(string="Name")
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    total_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price", readonly=True)
    res_currency = fields.Many2one(comodel_name='res.currency', default=lambda self: self.env.company.currency_id)
    # currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')
    # total_line_costs = fields.Monetary(string='Retail Price', currency_field='currency_id')
    gsn = fields.Text(string="GSN")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="States")
    pre_costing_lines = fields.One2many(comodel_name="pre.costing.lines", inverse_name="pre_costing_id",
                                        string="Pre Costing Name")
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related="product_id.buyer")
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", related="product_id.customer")
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type", related="product_id.fabric_type")
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related="product_id.wash_type")
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type", related="product_id.garment_type")

    def action_confirm(self):
        sequence = self.env['ir.sequence'].next_by_code('pre.costing') or _('New')
        self.write({'state': 'confirm', 'name': sequence})

    def action_draft(self):
        self.write({'state': 'draft'})
    # TODO pre costing must be added to sales menu


class PreCostingLines(models.Model):
    _name = "pre.costing.lines"
    _description = "Pre Costing Lines"

    process_type = fields.Selection([('wet', 'Wet Process'), ('dry', 'Dry Process')], string="Process Type")
    operation = fields.Many2one(comodel_name="mrp.routing.workcenter", string="Operation", required=True)
    cost = fields.Float(string="Cost", required=True)
    margin = fields.Float(string="Margin", required=True)
    pieces_for_hour_actual = fields.Integer(string="Actual No of Pieces for Hour")
    pieces_for_hour_target = fields.Integer(string="Target No of Pieces for Hour")
    price = fields.Float(string="Price", required=True)
    pre_costing_id = fields.Many2one(comodel_name="pre.costing", string="Pre Costing ID")
