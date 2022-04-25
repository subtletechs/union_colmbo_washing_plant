from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrder(models.Model):
    _inherit = "sale.order"

    garment_type = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample', required=True)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer")
    style_no = fields.Char(string="Style No")
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type")
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type")
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type")
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')

    @api.onchange('product_id')
    def _onchange_details(self):
        self.buyer = self.product_id.buyer
        self.style_no = self.product_id.style_no
        self.fabric_type = self.product_id.fabric_type
        self.wash_type = self.product_id.wash_type
        self.garment_type = self.product_id.garment_type
        self.garment_select = self.product_id.garment_select

