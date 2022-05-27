from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    style_expire = fields.Boolean(string="Style Expire Timer")
    days = fields.Integer(string="Days")
