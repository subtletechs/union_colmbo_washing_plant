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

    need_to_approve = fields.Boolean(string="Need Pre Cost Approval", default=False, compute="_compute_need_to_approve")
    is_approved = fields.Boolean(string="Approved", default=False)

    def action_confirm(self):
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
        # TODO : complete the code
        if self.pre_costing:
            for record in self.pre_costing:
                for sale_order_line in self.order_line:
                    if record.product_id == sale_order_line.product_id:
                        if record.total_line_costs > sale_order_line.price_subtotal:
                            self.need_to_approve = True
                            break


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
