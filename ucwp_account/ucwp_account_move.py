from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    delivery_order = fields.Many2one(comodel_name="stock.picking", string="Delivery order")

    # [UC-18]
    balance_in_days = fields.Integer(string="Balance in Days", readonly=True, track_visibility='always')

    def action_special_payments(self):
        """Action for Special payment in Invoice"""
        special_payment_form_view = self.env.ref('union_colmbo_washing_plant.special_payment_details_form_view')

        return {
            'res_model': 'account.move.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': special_payment_form_view.id,
            'target': 'new',
            'context': {
                'default_invoice_number': self.id
            }
        }


class AccountMoveWizard(models.TransientModel):
    _name = "account.move.wizard"

    balance_in_days = fields.Integer(string="Balance in Days")
    invoice_number = fields.Many2one(comodel_name="account.move", string="Invoice Number")

    def action_register_payment(self):
        """Popup Register payment view"""
        invoice_record = self.env['account.move'].search([('id', '=', self.invoice_number.id)], limit=1)
        invoice_record.balance_in_days = self.balance_in_days
        return {
            'name': _('Special Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': invoice_record.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

