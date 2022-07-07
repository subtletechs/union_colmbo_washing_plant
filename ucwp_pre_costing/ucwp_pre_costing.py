from odoo import api, fields, models, _, tools


class PreCosting(models.Model):
    _name = "pre.costing"
    _description = "Pre Costing"

    name = fields.Char(string="Name", default="New")
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    res_currency = fields.Many2one(comodel_name='res.currency', string="Currency Type", required=True)
    total_wet_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price(Wet)", readonly=True,
                                           store=True,
                                           compute="_calculate_total_line_costs")
    total_dry_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price(Dry)", readonly=True,
                                           store=True,
                                           compute="_calculate_total_dry_line_costs")
    total_cost_of_wet_and_dry = fields.Monetary(currency_field='res_currency', string="Total Price", readonly=True,
                                                store=True,
                                                compute="_calculate_total_line_costs")
    gsn = fields.Float(string="GSN")
    fabric_composition = fields.Text(string="Fabric Composition")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="States", default="draft")
    # For wet process
    pre_costing_wet_process_lines = fields.One2many(comodel_name="pre.costing.lines", inverse_name="pre_costing_id",
                                                    string="Wet Process Lines")
    # For dry process
    pre_costing_dry_process_lines = fields.One2many(comodel_name="pre.costing.lines", inverse_name="pre_costing_dry_id",
                                                    string="Dry Process Lines")
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

    @api.depends('pre_costing_wet_process_lines.price')
    def _calculate_total_line_costs(self):
        """Calculate Total for Wet process, Dry process and Total cost of wet & dry processes"""
        for record in self:
            # Total cost for wet process
            total_wet_line_costs = 0
            for pre_costing_wet_process_line in self.pre_costing_wet_process_lines:
                total_wet_line_costs += pre_costing_wet_process_line.price
            record.total_wet_line_costs = total_wet_line_costs
            # Total cost for dry process
            total_dry_line_cost = 0
            for pre_costing_dry_process_line in self.pre_costing_dry_process_lines:
                total_dry_line_cost += pre_costing_dry_process_line.price
            record.total_dry_line_costs = total_dry_line_cost
            # Total cost for wet and dry processes
            record.total_cost_of_wet_and_dry = record.total_wet_line_costs + record.total_dry_line_costs

    @api.onchange('product_id')
    def _get_garment_select(self):
        self.garment_select = self.product_id.garment_select

    @api.onchange('pre_costing_wet_process_lines', 'pre_costing_dry_process_lines', 'res_currency')
    def set_currency_type(self):
        """Set currency type for wet process & dry process tabs"""
        self.pre_costing_wet_process_lines.res_currency = self.res_currency
        self.pre_costing_dry_process_lines.res_currency = self.res_currency


class PreCostingLines(models.Model):
    _name = "pre.costing.lines"
    _description = "Pre Costing Lines"

    # Wet process
    pre_costing_id = fields.Many2one(comodel_name="pre.costing", string="Wet Pre Costing ID")
    # Dry process
    pre_costing_dry_id = fields.Many2one(comodel_name="pre.costing", string="Dry Pre Costing ID")
    process_type = fields.Selection([('wet', 'Wet Process'), ('dry', 'Dry Process')], string="Process Type")
    operation = fields.Many2one(comodel_name="mrp.routing.workcenter", string="Operation", required=True,
                                domain="[('process_type', '=', process_type)]")
    res_currency = fields.Many2one(comodel_name='res.currency')
    cost = fields.Monetary(currency_field='res_currency', string="Cost", required=True)
    margin = fields.Float(string="Margin(%)", required=True)
    pieces_for_hour_actual = fields.Integer(string="Actual No of Pieces for Hour")
    pieces_for_hour_target = fields.Integer(string="Target No of Pieces for Hour")
    price = fields.Monetary(currency_field='res_currency', string="Price", store=True,
                            compute="_calculate_cost")

    @api.depends('cost', 'margin')
    def _calculate_cost(self):
        """Calculate total per line"""
        for record in self:
            record.price = record.cost * ((100 + record.margin) / 100)
