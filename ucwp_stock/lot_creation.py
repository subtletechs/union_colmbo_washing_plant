from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError


class RewashLotCreation(models.Model):
    _name = "rewash.lot.creation"
    _description = "Create Re-wash lots"

    name = fields.Char(string="Re-wash Lot Number", default="New", required=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    location_src_id = fields.Many2one(comodel_name="stock.location", string="From")
    location_dest_id = fields.Many2one(comodel_name="stock.location", string="To")
    quantity = fields.Float(string="Quantity", readonly=True)
    fail_lot_quantity_lines = fields.One2many(comodel_name="fail.lot.quantity.lines", inverse_name="rewash_lot_id",
                                              string="Fail Lots")


class FailLotQuantityLines(models.Model):
    _name = "fail.lot.quantity.lines"

    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot", required=True)
    available_qty = fields.Float(string="Available Quantity", readonly=True)
    allocate_qty = fields.Float(string="Allocate Quantity")
    rewash_lot_id = fields.Many2one(comodel_name="rewash.lot.creation", string="Re-wash lot ID")
