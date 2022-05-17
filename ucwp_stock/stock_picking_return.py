from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking_id, pick_type_id = super(ReturnPicking, self)._create_returns()
        new_picking = self.env['stock.picking'].browse([new_picking_id])
        if self.is_receipt_return:
            new_picking.write({'is_receipt_return':True})
        return new_picking_id, pick_type_id

    is_receipt_return = fields.Boolean(string='Stock Receipt return', default=False)
