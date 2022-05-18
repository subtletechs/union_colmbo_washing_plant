from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = 'create_date desc'

    is_garment = fields.Boolean(string="Is Garment Product ?", default=True)

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer")
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type")
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type")
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type")
    customer = fields.Many2one(comodel_name="res.partner", string="Customer")
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')
    samples = fields.Many2one(comodel_name="garment.sample", string="Samples")

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('product.uc.number') or _('New')
        values['default_code'] = sequence
        return super(ProductTemplate, self).create(values)


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_garment = fields.Boolean(string="Is Garment Product ?", related='product_tmpl_id.is_garment', store=True)

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_tmpl_id.buyer',
                            store=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product_tmpl_id.fabric_type', store=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related='product_tmpl_id.wash_type', store=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type",
                                   related='product_tmpl_id.garment_type', store=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", related='product_tmpl_id.customer', store=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample',
                                      related='product_tmpl_id.garment_select', store=True)
    samples = fields.Many2one(comodel_name="garment.sample", string="Samples", related='product_tmpl_id.samples', store=True)
