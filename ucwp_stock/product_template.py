from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = 'create_date desc'

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", required=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type", required=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", required=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type", required=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", required=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')
    samples = fields.Many2one(comodel_name="garment.sample", string="Samples")

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('product_uc_number') or _('New')
        values['default_code'] = sequence
        return super(ProductTemplate, self).create(values)


class ProductProduct(models.Model):
    _inherit = "product.product"

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_tmpl_id.buyer', required=True,
                            store=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product_tmpl_id.fabric_type', required=True, store=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", related='product_tmpl_id.wash_type',
                                required=True, store=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type",
                                   related='product_tmpl_id.garment_type', required=True, store=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", related='product_tmpl_id.customer',
                               required=True, store=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample',
                                      related='product_tmpl_id.garment_select', store=True)
    samples = fields.Many2one(comodel_name="garment.sample", string="Samples", related='product_tmpl_id.samples', store=True)
