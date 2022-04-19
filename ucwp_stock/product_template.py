from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", required=True)
    style_no = fields.Char(string="Style No", required=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type", required=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type", required=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type", required=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", required=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], default='bulk', string='Bulk/Sample')
    samples = fields.Many2one(comodel_name="garment.sample", string="Samples")

