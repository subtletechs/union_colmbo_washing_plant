from odoo import fields, models
from datetime import date, timedelta


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    style_expire = fields.Boolean(string="Style Expire Timer",
                                  config_parameter='union_colmbo_washing_plant.style_expire')
    days = fields.Integer(string="Days",
                          config_parameter='union_colmbo_washing_plant.days')
