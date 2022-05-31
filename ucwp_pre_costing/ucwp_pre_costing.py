from odoo import api, fields, models, _, tools


class PreCosting(models.Model):
    _name = "pre.costing"
    _description = "Pre Costing"

    name = fields.Char(string="Name", default="New")
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    total_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price", readonly=True, store=True,
                                       compute="_calculate_total_line_costs")
    res_currency = fields.Many2one(comodel_name='res.currency', default=lambda self: self.env.company.currency_id)
    gsn = fields.Float(string="GSN")
    fabric_composition = fields.Text(string="Fabric Composition")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="States", default="draft")
    pre_costing_lines = fields.One2many(comodel_name="pre.costing.lines", inverse_name="pre_costing_id",
                                        string="Pre Costing Name", store=True)
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related="product_id.buyer", store=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", related="product_id.customer", store=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type", related="product_id.fabric_type",
                                  store=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related="product_id.wash_type",
                                store=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type",
                                   related="product_id.garment_type", store=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample', readonly=True)

    def action_confirm(self):
        """Set sequence and change state to Confirm"""
        sequence = self.env['ir.sequence'].next_by_code('pre.costing') or _('New')
        self.write({'state': 'confirm', 'name': sequence})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.depends('pre_costing_lines.price')
    def _calculate_total_line_costs(self):
        """Calculate Total for each Pre costing line"""
        total_line_costs = 0
        for pre_costing_line in self.pre_costing_lines:
            total_line_costs = total_line_costs + pre_costing_line.price
        self.total_line_costs = total_line_costs

    @api.onchange('product_id')
    def _get_garment_select(self):
        self.garment_select = self.product_id.garment_select


class PreCostingLines(models.Model):
    _name = "pre.costing.lines"
    _description = "Pre Costing Lines"

    process_type = fields.Selection([('wet', 'Wet Process'), ('dry', 'Dry Process')], string="Process Type")
    operation = fields.Many2one(comodel_name="mrp.routing.workcenter", string="Operation", required=True,
                                domain="[('process_type', '=', process_type)]")
    res_currency = fields.Many2one(comodel_name='res.currency', default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(currency_field='res_currency', string="Cost", required=True)
    margin = fields.Float(string="Margin(%)", required=True)
    pieces_for_hour_actual = fields.Integer(string="Actual No of Pieces for Hour")
    pieces_for_hour_target = fields.Integer(string="Target No of Pieces for Hour")
    price = fields.Monetary(currency_field='res_currency', string="Price", required=True, store=True,
                            compute="_calculate_cost")
    pre_costing_id = fields.Many2one(comodel_name="pre.costing", string="Pre Costing ID")

    @api.depends('cost', 'margin')
    def _calculate_cost(self):
        """Calculate total per line"""
        for record in self:
            record.price = record.cost * ((100 + record.margin) / 100)
