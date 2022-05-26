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
    pre_costing = fields.Many2many(comodel_name="pre.costing", string="Pre Costing")

    need_to_approve = fields.Boolean(string="Need Pre Cost Approval", default=False)
    is_approved = fields.Boolean(string="Approved", default=False)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer")
    fabric_type = fields.Many2one(comodel_name="fabric.type", string="Fabric Type")
    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type")
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type")
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')

    @api.onchange('product_id')
    def _onchange_details(self):
        if self.product_id.buyer:
            self.buyer = self.product_id.buyer
        if self.product_id.fabric_type:
            self.fabric_type = self.product_id.fabric_type
        if self.product_id.wash_type:
            self.wash_type = self.product_id.wash_type
        if self.product_id.garment_type:
            self.garment_type = self.product_id.garment_type
        if self.product_id.garment_select:
            self.garment_select = self.product_id.garment_select


class PreCostingApproval(models.Model):
    _name = "pre.costing.approval"
    _description = "Approval For Pre Costing"

    quotation = fields.Many2one(comodel_name="sale.order", string="Quotation", domain="[('state', '=', 'draft')]")
    state = fields.Selection([('waiting', 'Waiting for Approval'), ('approved', 'Approved')], string="State",
                             default='waiting')

    def action_approve(self):
        self.write({'state': 'approved'})
        # TODO set value of SO approved field True

    def action_wait(self):
        self.write({'state': 'waiting'})
