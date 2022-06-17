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
        else:
            company_id = self.env.company.id
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'),
                 ('warehouse_id.company_id', '=', company_id),
                 ('chemical_receipt', '!=', True),
                 ('garment_receipt', '!=', True),
                 ('return_picking_type_id', '!=', False)])
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming'),
                     ('warehouse_id', '=', False),
                     ('chemical_receipt', '!=', True),
                     ('garment_receipt', '!=', True)
                     ])
            self.picking_type_id = picking_type.id

