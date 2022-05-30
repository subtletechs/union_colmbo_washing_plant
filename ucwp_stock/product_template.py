from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = 'create_date desc'

    is_garment = fields.Boolean(string="Is Garment Product ?", default=True)
    is_sample = fields.Boolean(string="Is Sample Garment ?", default=False)
    is_bulk = fields.Boolean(string="Is Bulk Garment ?", default=False)
    is_chemical = fields.Boolean(string='Is Chemical ?', default=False)

    # [UC-23]- Add chemical standards to product template
    chemical_standards = fields.One2many(comodel_name="chemical.standards", inverse_name="product_tmpl_id",
                                         string="Chemical Standards")

    # [UC-24]- Add certification to product template and product variant
    available_certification = fields.Boolean(string="Available Certification")
    certification = fields.Text(string="Certification")

    # [UC-25]- Test/Lab Reports tab
    lab_reports = fields.One2many(comodel_name="lab.reports", inverse_name="product_template_id",
                                  string="Test/Lab Reports")

    # [UC-28]- Set Active / Inactive to Product Template
    active = fields.Boolean(string="Active", default=True)

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer")
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type")
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type")
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type")
    customer = fields.Many2one(comodel_name="res.partner", string="Customer")
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')
    samples = fields.Many2one(comodel_name="garment.sample", string="Sample Type")

    # UC-21 chemical MSDS descriptions
    msds_in_english = fields.Text(string='In English')
    msds_in_sinhala = fields.Text(string='In Sinhala')

    @api.onchange('is_sample')
    def update_is_sample(self):
        if self.is_sample:
            self.is_bulk = False

    @api.onchange('is_bulk')
    def update_is_bulk(self):
        if self.is_bulk:
            self.is_sample = False

    @api.onchange('is_garment')
    def update_bulk_sample(self):
        if not self.is_garment:
            self.is_sample = False
            self.is_bulk = False
        if self.is_garment:
            self.is_chemical = False

    @api.onchange('is_chemical')
    def update_is_garment(self):
        if self.is_chemical:
            self.is_garment = False

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('product.uc.number') or _('New')
        values['default_code'] = sequence

        if 'is_sample' or 'is_bulk' in values:
            if values['is_sample']:
                values['garment_select'] = 'sample'
                values['name'] = values['name'] + ' - ' + '(Sample)'
            elif values['is_bulk']:
                values['garment_select'] = 'bulk'
                values['name'] = values['name'] + ' - ' + '(Bulk)'

        if values['is_garment']:
            if values['is_bulk'] is False and values['is_sample'] is False:
                raise UserError('Please select Is Bulk Garment ? or Is Sample Garment ? for a Garment Product')
        return super(ProductTemplate, self).create(values)

    def write(self, vals):
        product_object = self.browse(self.id)
        product_name = product_object.name

        if 'is_bulk' in vals:
            if vals['is_bulk']:
                vals['garment_select'] = 'bulk'
                vals['name'] = product_name.replace('Sample', 'Bulk')
        if 'is_sample' in vals:
            if vals['is_sample']:
                vals['garment_select'] = 'sample'
                vals['name'] = product_name.replace('Bulk', 'Sample')
        return super(ProductTemplate, self).write(vals)


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_garment = fields.Boolean(string="Is Garment Product ?", related='product_tmpl_id.is_garment', store=True)
    is_sample = fields.Boolean(string="Is Sample Garment ?", related='product_tmpl_id.is_sample', store=True)
    is_bulk = fields.Boolean(string="Is Bulk Garment ?", related='product_tmpl_id.is_bulk', store=True)
    is_chemical = fields.Boolean(string='Is Chemical ?', related='product_tmpl_id.is_chemical', store=True)

    # [UC-24]- Add certification to product template and product variant
    available_certification = fields.Boolean(string="Available Certification")
    certification = fields.Text(string="Certification")

    # [UC-28]- Set Active / Inactive to Product Template
    active = fields.Boolean(string="Active", default=True)

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_tmpl_id.buyer',
                            store=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product_tmpl_id.fabric_type', store=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related='product_tmpl_id.wash_type',
                                store=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type",
                                   related='product_tmpl_id.garment_type', store=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", related='product_tmpl_id.customer',
                               store=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample',
                                      related='product_tmpl_id.garment_select', store=True)
    samples = fields.Many2one(comodel_name="garment.sample", string="Samples", related='product_tmpl_id.samples',
                              store=True)

    # [UC-21]- chemical MSDS descriptions
    msds_in_english = fields.Text(string='In English', related='product_tmpl_id.msds_in_english', store=True)
    msds_in_sinhala = fields.Text(string='In Sinhala', related='product_tmpl_id.msds_in_sinhala', store=True)

    @api.model
    def create(self, values):
        product_template = values['product_tmpl_id']
        product_tmpl = self.env['product.template'].browse(product_template)
        values['default_code'] = product_tmpl.default_code

        return super(ProductProduct, self).create(values)

    def action_style_expire(self):
        """Check conditions to set Styles Archive"""
        set_days = self.env['res.config.settings'].search([('style_expire', '=', True)], limit=1)
        if set_days:
            number_of_days = set_days.days
            current_date = datetime.today()
            from_date = current_date - timedelta(days=number_of_days)

            active_product_variants = self.env['product.product'].search(
                [('active', '=', True), ('is_garment', '=', True)])
            if active_product_variants:
                for active_product_variant in active_product_variants:
                    product_qty_available = active_product_variant.qty_available

                    picking_records = self.env['stock.picking'].search(
                        [('scheduled_date', '<', from_date),
                         ('picking_type_id.code', 'in', ['outgoing', 'incoming']),
                         ('state', 'not in', ['draft', 'cancel'])])
                    picking_available = False
                    if picking_records:
                        for picking_record in picking_records:
                            for picking_line in picking_record.move_ids_without_package:
                                if picking_line.product_id.id == active_product_variant.id:
                                    picking_available = True
                    if picking_available is False and product_qty_available > 0:
                        self.env['style.archive.approval'].create({
                            'product_id': active_product_variant.id,
                            'state': 'draft',
                        })
                    elif picking_available is False and product_qty_available <= 0:
                        active_product_variant.write({
                            'active': False
                        })


# [UC-23]
class ChemicalStandards(models.Model):
    _name = "chemical.standards"
    _description = "Chemical Standards"

    name = fields.Char(string="Name")
    document = fields.Binary(string="Document")
    product_tmpl_id = fields.Many2one(comodel_name="product.product", string="Product Template ID")


class LabReports(models.Model):
    _name = "lab.reports"
    _description = "Lab Reports"

    name = fields.Char(string="Report Name")
    document = fields.Binary(string="Report Files")
    product_template_id = fields.Many2one(comodel_name="product.product", string="Product Template ID")


# [UC-28]
class StyleArchiveApproval(models.Model):
    _name = "style.archive.approval"
    _description = "Style Archive Approval"

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string="Status", default='draft')

    def action_approve(self):
        """Approve record and set product inactive"""
        self.write({'state': 'approved'})
        self.product_id.active = False

    def action_set_to_draft(self):
        self.write({'state': 'draft'})
