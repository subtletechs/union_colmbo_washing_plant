from odoo import api, fields, models, _


class GarmentType(models.Model):
    _name = 'garment.type'
    _description = 'Garment Type'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
