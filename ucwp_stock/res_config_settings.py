from odoo import fields, models
from datetime import date, timedelta


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    style_expire = fields.Boolean(string="Style Expire Timer")
    days = fields.Integer(string="Days")

    def action_style_expire(self):
        set_days = self.days
        current_date = date.today()
        from_date = current_date - timedelta(days=set_days)
