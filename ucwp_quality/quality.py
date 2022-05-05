import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class QualityCheck(models.Model):
    _inherit = "quality.check"

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_id.product_tmpl_id.buyer',
                            required=True)
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type",
                                  related='product_id.product_tmpl_id.fabric_type', required=True)
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type",
                                related='product_id.product_tmpl_id.wash_type', required=True)
    color_id = fields.Many2one(comodel_name="product.attribute.value", compute="_compute_variant")
    color = fields.Char(string="Color")
    quality_of = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample'), ('finish', 'Finish Good')],
                                  string="Quality of")
    second_wash = fields.Selection([('before', 'Before Wash'), ('after', 'After Wash')], string="Before/After Wash")
    # Inspection Quantity
    inspection_quantity = fields.One2many(comodel_name="inspection.quantity", inverse_name="quality_id",
                                          string="Inspection Quantity")
    done_quantity = fields.Float(string="Done")

    product = fields.Float(compute="calculate_quantity")
    # Defects
    defects_lines = fields.One2many(comodel_name="defects.lines", inverse_name="quality_check_id", string="Defects")

    @api.depends('product_id')
    def _compute_variant(self):

        attribute_ids = self.env['product.attribute'].search([('display_type', '=', 'color')])

        for attribute_id in attribute_ids:
            for record in self:
                if record.product_id:
                    product = record.product_id
                    if product.product_template_variant_value_ids:
                        variant_records = product.product_template_variant_value_ids
                        for variant_record in variant_records:
                            if variant_record.attribute_id == attribute_id:
                                if variant_record.product_attribute_value_id:
                                    record.color_id = variant_record.product_attribute_value_id
                                    record.color = record.color_id.name
                    else:
                        record.color_id = None
                else:
                    record.color_id = None

    # @api.depends('product_id', 'picking_id')
    # def calculate_quantity(self):
    #     for record in self:
    #         # if record.picking_id:
    #         stock_picking = record.picking_id
    #         # if record.product_id:
    #         product = record.product_id
    #         stock_picking_lines = stock_picking.move_ids_without_package
    #                 # if stock_picking_lines:
    #         for line in stock_picking_lines:
    #             if line.product_id.id == product.id:
    #                 done_qty = line.quantity_done
    #                 record.done_quantity = done_qty
    #                 break
    #             else:
    #                 record.done_quantity = 0
    #                 # else:
    #                 #     record.done_quantity = 0


class DefectsLines(models.Model):
    _name = 'defects.lines'

    defect = fields.Many2one(comodel_name="defects", string="Defect", required=True)
    quantity = fields.Integer(string="Quantity", required=True)
    quality_check_id = fields.Many2one(comodel_name="quality.check", string="Quality Check Id")


class DefectRecordLines(models.Model):
    _name = "defects"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
