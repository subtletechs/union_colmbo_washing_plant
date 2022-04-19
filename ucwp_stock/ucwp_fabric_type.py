from odoo import api, fields, models, _


class FabricType(models.Model):
    _name = 'fabric.type'
    _description = 'Fabric Type'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
