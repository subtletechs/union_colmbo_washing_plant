from odoo import api, fields, models, _


class BulkProduction(models.Model):
    """ Bulk Manufacturing Orders """
    _name = 'bulk.production'

    name = fields.Char(string="Bulk Production", default="New")
    product = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    manufacture_orders = fields.One2many(comodel_name='mrp.production', inverse_name='bulk_id',
                                         string='Manufacture Orders')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bulk_id = fields.Many2one(comodel_name="bulk.production", string="Bulk Production")
