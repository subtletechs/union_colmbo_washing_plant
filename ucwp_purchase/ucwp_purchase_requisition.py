from odoo import api, fields, models, _
from datetime import date


class PurchaseRequisition(models.Model):
    _name = "ucwp.purchase.requisition"
    _description = "Purchase Requisition"

    name = fields.Char(string="Purchase Requisition", default="New")
    # TODO :  groups should need to be added according to the credentials
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate'), ('authorized', 'Authorized')],
                             string="Status", default="draft")
    requested_date = fields.Date(string="Requested Date", default=date.today(), required=True)
    expected_date = fields.Date(string="Expected Date", default=date.today(), required=True)
    requested_by = fields.Many2one(comodel_name="res.users", string="Requested By", default=lambda self: self.env.user)
    requisition_line = fields.One2many(comodel_name="ucwp.purchase.requisition.line",
                                       inverse_name="purchase_requisition_id", string="Purchase Requisition Lines")

    @api.model
    # Generate sequence for Purchase Requisition
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('purchase.requisition') or _('New')
        values['name'] = sequence
        return super(PurchaseRequisition, self).create(values)

    def action_validate(self):
        self.write({'state': 'validate'})

    def action_authorized(self):
        self.write({'state': 'authorized'})

    def set_to_draft(self):
        self.write({'state': 'draft'})


class PurchaseRequisitionLine(models.Model):
    _name = "ucwp.purchase.requisition.line"
    _description = "Purchase Requisition Lines"

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    product_uom = fields.Many2one(comodel_name="uom.uom", string="UoM", related="product_id.uom_id", store=True)
    purchase_requisition_id = fields.Many2one(comodel_name="ucwp.purchase.requisition",
                                              string="Purchase Requisition ID")
