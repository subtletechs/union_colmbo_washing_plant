from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    chemical_purchase = fields.Boolean(string="Chemical Purchase", default=False)

    @api.onchange('chemical_purchase')
    def update_picking_type(self):
        """Set Chemical Receipt as Stock Operation Type """
        if self.chemical_purchase:
            picking_type = self.env['stock.picking.type'].search(
                [('chemical_receipt', '=', True)])
            if picking_type:
                self.picking_type_id = picking_type.id
