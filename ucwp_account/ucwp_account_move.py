from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    delivery_order = fields.Many2one(comodel_name="stock.picking", string="Delivery order")

    # [UC-18]
    balance_in_days = fields.Integer(string="Balance in Days", readonly=True, track_visibility='always')

    def action_special_payments(self):
        special_payment_form_view = self.env.ref('union_colmbo_washing_plant.special_payment_details_form_view')

        return {
            'res_model': 'account.move.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': special_payment_form_view.id,
            'target': 'new',
        }


class AccountMove(models.TransientModel):
    _name = "account.move.wizard"

    balance_in_days = fields.Integer(string="Balance in Days")

    # TODO call register payment method
    def action_register_payment(self):
        pass


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
