import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class QualityPoint(models.Model):
    _inherit = "quality.check"

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_id.product_tmpl_id.buyer',
                            required=True)
    style_no = fields.Char(string="Style No", related='product_id.product_tmpl_id.style_no', required=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product_id.product_tmpl_id.fabric_type', required=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type",
                                related='product_id.product_tmpl_id.wash_type', required=True)
    color_id = fields.Many2one(comodel_name="product.attribute.value", compute="_compute_variant")
    color = fields.Char(string="Color")
    quality_of = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample'), ('finish', 'Finish Good')],
                                  string="Quality of")
    second_wash = fields.Selection([('before', 'Before Wash'), ('after', 'After Wash')], string="Before/After Wash")
    inspection_quantity = fields.One2many(comodel_name="inspection.quantity", inverse_name="quality_id",
                                          string="Inspection Quantity")

    def _compute_variant(self):

        attribute_ids = self.env['product.attribute'].search([('display_type', '=', 'color')])

        for attribute_id in attribute_ids:
            for record in self:
                product = record.product_id
                variant_records = product.product_template_variant_value_ids
                for variant_record in variant_records:
                    if variant_record.attribute_id == attribute_id:
                        record.color_id = variant_record.product_attribute_value_id
                        record.color = record.color_id.name
