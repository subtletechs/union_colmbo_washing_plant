from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pre_costing = fields.Many2many(comodel_name="pre.costing", string="Pre Costing",
                                   domain="[('state', '=', 'confirm')]")

    need_to_approve = fields.Boolean(string="Need Pre Cost Approval", default=True, required=True,
                                     compute="_compute_need_to_approve")
    is_approved = fields.Boolean(string="Approved", default=False)

    # UC-30
    po_availability = fields.Selection([('po', 'PO'), ('temp_po', 'TEMP PO'), ('no_po', 'No PO')],
                                       string='PO Availability', required=True)

    # garment receipt info
    garment_receipt_count = fields.Integer(string='Invoice Count', compute='_get_garment_receipts')
    garment_receipt_ids = fields.Many2many("stock.picking", string='Garment Receipt', compute="_get_garment_receipts",
                                           copy=False)

    # Actually received product quantity
    actually_received_product_qty = fields.One2many(comodel_name="actually.received.product.quantity",
                                                    inverse_name="sale_order_id",
                                                    string="Actually Received Product Quantity")

    # [UC-47]
    garment_sales = fields.Boolean(string="Garment Sales", default=True)

    # Sale order type
    local_export = fields.Selection([('local', 'Local'), ('export', 'Export')], string="Local/Export")

    credit_limit_exceeded = fields.Boolean(string="Credit Limit Exceeded", default=False)
    credit_limit_override = fields.Boolean(string="Credit Limit Override", default=False)

    # UCWP|FUN|-008 - Add Delivery Requirement tab
    delivery_requirement = fields.One2many(comodel_name="delivery.requirement",
                                           inverse_name="delivery_requirement_sale_order_id",
                                           string="Delivery Requirement")

    # @api.depends('partner_id', 'amount_total', 'order_line')
    # def check_credit_block(self):
    #     for order in self:
    #         if order.credit_limit_override == False:
    #             partner = order.partner_id
    #             payment_method = partner.payment_method
    #             credit_limit_available = partner.credit_limit_available
    #             credit_limit = partner.credit_limit
    #             if payment_method == 'credit' and credit_limit_available == True:
    #                 if self.amount_total > partner.available_credit_limit:
    #                     order.credit_limit_exceeded = True
    #                 else:
    #                     order.credit_limit_exceeded = False
    #             else:
    #                 order.credit_limit_exceeded = False
    #         else:
    #             order.credit_limit_exceeded = False

    # def action_credit_override(self):
    #     """Override credit limit"""
    #     return self.write({'credit_limit_override': True, 'credit_limit_exceeded': False})

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
            form_view = self.env.ref('stock.view_picking_form').id
            tree_view = self.env.ref('stock.vpicktree').id
            return {
                'name': 'Garment Receipts',
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'list,form',
                'views': [[tree_view, 'list'], [form_view, 'form']],
                'target': 'current',
                'domain': [('id', 'in', garment_receipts.ids)],

            }
        elif len(garment_receipts) == 1:
            form_view = self.env.ref('stock.view_picking_form').id
            return {
                'res_model': 'stock.picking',
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
        for sale_record in self:
            if sale_record.garment_sales:
                if sale_record.pre_costing:
                    for record in sale_record.pre_costing:
                        for sale_order_line in sale_record.order_line:
                            if record.product_id == sale_order_line.product_id:
                                if record.total_cost_of_wet_and_dry > sale_order_line.price_unit:
                                    sale_record.need_to_approve = True
                                    break
                                else:
                                    sale_record.need_to_approve = False
                            else:
                                sale_record.need_to_approve = False
                else:
                    sale_record.need_to_approve = False
            else:
                sale_record.need_to_approve = False

    def generate_garment_receipt(self):
        """Generate the Garment Receipt from Sale Order"""
        # TODO : Complete the code
        garment_inventory_operation = self.env['stock.picking.type'].search([('garment_receipt', '=', True)], limit=1)
        if not garment_inventory_operation:
            pass
        view = self.env.ref('stock.view_picking_form')
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
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
                'default_customer_ref': self.client_order_ref,
                'default_company_id': self.company_id.id,
            }
        }

    @api.model
    def create(self, vals):
        """"Check the products available in order line and create new records in actual product quantity"""
        res = super(SaleOrder, self).create(vals)
        if vals['garment_sales']:
            if 'order_line' in vals:
                order_lines = vals['order_line']
                for line in order_lines:
                    self.env['actually.received.product.quantity'].create(
                        {'sale_order_id': res.id, 'product_id': line[2].get('product_id')})

        return res

    def write(self, values):
        # TODO : Restrict Product removing from order line while having related records in GRN
        # We are going to check add new product and remove product form order line
        if self.garment_sales:
            order_id = self.id
            if 'order_line' in values:
                lines = values['order_line']
                for line in lines:
                    if line[0] == 0:
                        # check product duplicate
                        duplicate_product_record = self.env['actually.received.product.quantity'].search([
                            ('sale_order_id', '=', order_id),
                            ('product_id', '=', line[2].get('product_id'))
                        ])
                        if not duplicate_product_record:
                            self.env['actually.received.product.quantity'].create({
                                'sale_order_id': order_id,
                                'product_id': line[2].get('product_id')
                            })
                    if line[0] == 2:
                        line_object = self.env['sale.order.line'].browse(line[1])
                        product = line_object.product_id
                        record = self.env['actually.received.product.quantity'].search(
                            [('sale_order_id', '=', order_id),
                             ('product_id', '=', product.id)])
                        if record:
                            record.unlink()
        return super(SaleOrder, self).write(values)


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

    @api.onchange('garment_select')
    def _product_domain(self):
        # Filter Products based on Garment Type
        if self.garment_select:
            if self.garment_select == 'sample':
                sample_products = self.env['product.product'].search([('is_sample', '=', True)])
                sample_products_ids = sample_products.ids
                return {
                    'domain': {'product_id': [('id', 'in', sample_products_ids)]}
                }
            elif self.garment_select == 'bulk':
                bulk_products = self.env['product.product'].search([('is_bulk', '=', True)])
                return {
                    'domain': {'product_id': [('id', 'in', bulk_products.ids)]}
                }
            else:
                pass


class ActuallyReceivedProductQuantity(models.Model):
    _name = "actually.received.product.quantity"
    _description = "Actually Received Product Quantity"

    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    actually_received = fields.Float(string="Actually Received qty")
    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale order ID")


class DeliveryRequirement(models.Model):
    _name = "delivery.requirement"
    _rec_name = "expected_delivery_date"

    # UCWP|FUN|-008 - Add Delivery Requirement tab
    expected_delivery_date = fields.Date(string="Expected Delivery Date")
    expected_quantity = fields.Integer(string="Expected Quantity")
    delivery_requirement_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale order ID")
