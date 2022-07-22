from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import datetime


class InternalLabTests(models.Model):
    _name = "internal.lab.tests"
    _inherit = ['mail.thread']
    _description = "Internal Lab Test record"

    name = fields.Char(string="Report No", default="New", tracking=True, readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="Status", default="draft")
    date_in = fields.Datetime(string="Date In", tracking=True)
    date_out = fields.Datetime(string="Date Out", tracking=True, readonly=True)
    is_pass = fields.Boolean(string="Pass")
    is_fail = fields.Boolean(string="Fail")
    is_data = fields.Boolean(string="Data")
    product_id = fields.Many2one(comodel_name="product.product", string="Style", domain="[('is_garment', '=', True)]",
                                 tracking=True)
    style_no = fields.Char(string="Style No", related="product_id.default_code", store=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Factory", related="product_id.customer", store=True)
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related="product_id.buyer", store=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Item", related="product_id.garment_type",
                                   store=True)
    tested_property = fields.Many2one(comodel_name="tested.property", string="Tested Property")
    testing_method = fields.Many2one(comodel_name="testing.method", string="Testing Method")
    requirement = fields.Text(string="Requirement")
    samples = fields.Many2one(comodel_name="garment.sample", string="Sample Type", related="product_id.samples",
                              store=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related="product_id.wash_type",
                                store=True)
    season = fields.Many2one(comodel_name="season", string="Season")
    country = fields.Many2one(comodel_name="res.country", string="Country")
    ph_is_pass = fields.Boolean(string="Ph Pass")
    ph_is_fail = fields.Boolean(string="Ph Fail")
    ph_result = fields.Text(string="Ph Result")
    ph_requirement = fields.Text(string="Ph Requirement")
    dry_is_pass = fields.Boolean(string="Dry Pass")
    dry_is_fail = fields.Boolean(string="Dry Fail")
    dry_result = fields.Text(string="Dry Result")
    dry_requirement = fields.Text(string="Dry Requirement")
    wet_is_pass = fields.Boolean(string="Wet Pass")
    wet_is_fail = fields.Boolean(string="Wet Fail")
    wet_result = fields.Text(string="Wet Result")
    wet_requirement = fields.Text(string="Wet Requirement")
    image = fields.Binary(string="Image")

    @api.onchange('is_pass')
    def update_is_pass(self):
        if self.is_pass:
            self.is_fail = False

    @api.onchange('is_fail')
    def update_is_fail(self):
        if self.is_fail:
            self.is_pass = False

    @api.onchange('ph_is_pass', 'dry_is_pass', 'wet_is_pass')
    def update_test_result_pass(self):
        if self.ph_is_pass:
            self.ph_is_fail = False
        if self.dry_is_pass:
            self.dry_is_fail = False
        if self.wet_is_pass:
            self.wet_is_fail = False

    @api.onchange('ph_is_fail', 'dry_is_fail', 'wet_is_fail')
    def update_test_result_fail(self):
        if self.ph_is_fail:
            self.ph_is_pass = False
        if self.dry_is_fail:
            self.dry_is_pass = False
        if self.wet_is_fail:
            self.wet_is_pass = False

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('internal.lab.tests') or _('New')
        vals['name'] = sequence
        vals['date_in'] = datetime.now()
        return super(InternalLabTests, self).create(vals)

    def action_confirm(self):
        """ Confirm internal lab test record """
        self.write({
            'state': 'confirm',
            'date_out': datetime.now()
        })

    def set_to_draft(self):
        """ Set to draft """
        self.write({
            'state': 'draft'
        })


class TestedProperty(models.Model):
    _name = "tested.property"

    name = fields.Text(string="Tested Property")


class TestingMethod(models.Model):
    _name = "testing.method"

    name = fields.Text(string="Testing Method")


class Season(models.Model):
    _name = "season"

    name = fields.Text(string="Season")
