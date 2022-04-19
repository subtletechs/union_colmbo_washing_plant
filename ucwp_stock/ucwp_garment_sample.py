from odoo import api, fields, models, _


class GarmentSample(models.Model):
    _name = 'garment.sample'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
