from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pre_costing = fields.Many2many(comodel_name="pre.costing", string="Pre Costing")

    need_to_approve = fields.Boolean(string="Need Pre Cost Approval", default=True, required=True,
                                     compute="_compute_need_to_approve")
    is_approved = fields.Boolean(string="Approved", default=False)

    # UC-30
    po_availability = fields.Selection([('po', 'PO'), ('temp_po', 'TEMP PO'), ('no_po', 'No PO')],
                                       string='PO Availability', required=True)

    # garment receipt info
    garment_receipt_count = fields.Integer(string='Invoice Count', compute='_get_garment_receipts')
    garment_receipt_ids = fields.Many2many("stock.picking", string='Garment Receipt', compute="_get_garment_receipts", copy=False,)

    def _get_garment_receipts(self):
        """To Get the related Garment Receipts count and IDs"""
        for record in self:
            stock_picking = self.env['stock.picking'].search([('sale_id', '=', record.id)])
            if stock_picking:
                picking_ids = stock_picking.ids
                record.garment_receipt_ids = picking_ids
                record.garment_receipt_count = len(picking_ids)
            else:
                record.garment_receipt_count = 0

    def preview_garment_receipt(self):
        """Preview Garment Receipts"""
        garment_receipts = self.mapped('garment_receipt_ids')
        if len(garment_receipts) > 1:
            tree_view = self.env.ref('stock.vpicktree').id
            return {
                'name': 'Garment Receipts',
                'res_model' : 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree',
                'view_id': tree_view,
                'target': 'current',
                'domain': [('id', 'in', garment_receipts.ids)],

            }
        elif len(garment_receipts) ==1:
            form_view = self.env.ref('stock.view_picking_form').id
            return {
                'res_model' : 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': form_view,
                'res_id': garment_receipts.id,
                'target': 'current',
            }

    def action_confirm(self):
        """Popup Pre Costing Approval wizard and  send quotation id"""
        if self.need_to_approve is True and self.is_approved is False:
            view = self.env.ref('union_colmbo_washing_plant.pre_costing_approval_wizard_form_view')
            return {
                'res_model': 'pre.costing.approval.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'new',
                'context': {
                    'default_quotation': self.id
                }
            }
        return super(SaleOrder, self).action_confirm()

    def _compute_need_to_approve(self):
        """Compute need_to_approve value"""
        if self.pre_costing:
            for record in self.pre_costing:
                for sale_order_line in self.order_line:
                    if record.product_id == sale_order_line.product_id:
                        if record.total_line_costs > sale_order_line.price_subtotal:
                            self.need_to_approve = True
                        else:
                            self.need_to_approve = False
                    break
        else:
            self.need_to_approve = False

    def generate_garment_receipt(self):
        """Generate the Garment Receipt from Sale Order"""
        # TODO : Complete the code
        garment_inventory_operation = self.env['stock.picking.type'].search([('garment_receipt', '=', True)], limit=1)
        if not garment_inventory_operation:
            pass
        view = self.env.ref('stock.view_picking_form')
        return {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_picking_type_id': garment_inventory_operation.id,
                'default_partner_id': self.partner_id.id,
                'default_sale_id': self.id,
                'default_origin': self.name,
                'default_po_availability': self.po_availability,
                'default_customer_ref': self.client_order_ref

            }
        }


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
