from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import pytz


class ProductNameChangeLog(models.Model):
    _name = 'product.name.change.log'

    main_product = fields.Many2one(comodel_name='product.template', readonly=True, string='Product')
    product_name = fields.Char(string='Product Name', readonly=True)
    previous_name = fields.Char(string='Previous Name', readonly=True)
    type = fields.Selection([('create', 'Create'), ('update', 'Update')], string='Record Type', readonly=True)
    user = fields.Many2one(comodel_name='res.users', readonly=True, string='User')
    data_time = fields.Datetime(string='Date & Time', readonly=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, values):
        res = super(ProductTemplate, self).create(values)
        if values['name']:
            self.env['product.name.change.log'].create({
                'main_product': res.id,
                'product_name': values.get('name'),
                'type': 'create',
                'user': self.env.user.id,
                'data_time': datetime.now()
            })
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        # get previous logs for the product
        last_record = self.env['product.name.change.log'].search([('main_product', '=', self.id)],
                                                                 order="data_time desc",
                                                                 limit=1)
        if 'name' in vals:
            self.env['product.name.change.log'].create({
                'main_product': self.id,
                'product_name': vals.get('name'),
                'previous_name': last_record.product_name,
                'type': 'update',
                'user': self.env.user.id,
                'data_time': datetime.now()
            })
