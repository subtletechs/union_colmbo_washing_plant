from odoo import api, fields, models, _


class WashType(models.Model):
    _name = 'wash.type'
    _description = 'Wash Type'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
