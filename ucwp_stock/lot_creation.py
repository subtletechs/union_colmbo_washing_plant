from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError


class RewashLotCreation(models.Model):
    _name = "rewash.lot.creation"
    _description = "Create Re-wash lots"

    name = fields.Char(string="Re-wash Lot Number", default="New", required=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    location_src_id = fields.Many2one(comodel_name="stock.location", string="From", required=True)
    location_dest_id = fields.Many2one(comodel_name="stock.location", string="To", required=True)
    quantity = fields.Float(string="Quantity", readonly=True, compute="_calculate_quantity")
    fail_lot_quantity_lines = fields.One2many(comodel_name="fail.lot.quantity.lines", inverse_name="rewash_lot_id",
                                              string="Fail Lots")
    is_approved = fields.Boolean(string="Approved")

    # Create sequence for main lot
    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('rewash.lot.creation') or _('New')
        values['name'] = sequence
        return super(RewashLotCreation, self).create(values)

    @api.depends('fail_lot_quantity_lines.allocate_qty')
    def _calculate_quantity(self):
        for record in self:
            if record.fail_lot_quantity_lines:
                quantity = 0
                for line in record.fail_lot_quantity_lines:
                    quantity += line.allocate_qty
                record.quantity = quantity
            else:
                record.quantity = 0

    def action_confirm(self):
        if self.fail_lot_quantity_lines:
            new_lot = self.env['stock.production.lot'].create({
                'name': self.name,
                'product_id': self.product_id.id,
                'company_id': self.env.company.id,
                'barcode': self.name,
            })
            self.env['stock.quant'].create({
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': self.location_dest_id.id,
                'lot_id': new_lot.id,
                'inventory_quantity': self.quantity,
            }).action_apply_inventory()

            for line in self.fail_lot_quantity_lines:
                rewash_location_id = self.location_src_id.id
                if line.available_qty - line.allocate_qty < 0:
                    raise ValueError(_("Allocated quantity cannot be more than Available Quantity!"))
                else:
                    quant_obj = self.env['stock.quant'].search(
                        [('product_id', '=', line.product_id.id),
                         ('location_id', '=', rewash_location_id),
                         ('lot_id', '=', line.lot_id.id)])
                    quant_obj.write({
                        'quantity': line.available_qty - line.allocate_qty,
                    })
            self.is_approved = True


class FailLotQuantityLines(models.Model):
    _name = "fail.lot.quantity.lines"

    product_id = fields.Many2one(comodel_name="product.product", string="Product", related="rewash_lot_id.product_id",
                                 store=True)
    location_src_id = fields.Many2one(comodel_name="stock.location", string="From",
                                      related="rewash_lot_id.location_src_id")
    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot", required=True)
    available_qty = fields.Float(string="Available Quantity", readonly=True, compute="_calculate_available_qty")
    allocate_qty = fields.Float(string="Allocate Quantity")
    rewash_lot_id = fields.Many2one(comodel_name="rewash.lot.creation", string="Re-wash lot ID")

    @api.onchange('lot_id')
    def _lot_id_domain(self):
        """ Filter failed lots """
        rewash_location_id = self.env.ref('union_colmbo_washing_plant.stock_location_re_wash').id
        if not self.lot_id:
            rewash_records = self.env['stock.quant'].search(
                [('product_id', '=', self.product_id.id), ('location_id', '=', rewash_location_id)])
            lot_ids = []
            for rewash_record in rewash_records:
                lot_ids.append(rewash_record.lot_id.id)
            return {
                'domain': {'lot_id': [('id', 'in', lot_ids)]}
            }

    @api.depends('lot_id', 'allocate_qty')
    def _calculate_available_qty(self):
        for record in self:
            rewash_location_id = self.location_src_id.id
            if record.lot_id and record.allocate_qty is not True:
                quantity_availability_records = self.env['stock.quant'].search(
                    [('product_id', '=', record.product_id.id),
                     ('location_id', '=', rewash_location_id),
                     ('lot_id', '=', record.lot_id.id)])
                if quantity_availability_records:
                    total_available = 0
                    for quantity_availability_record in quantity_availability_records:
                        total_available += quantity_availability_record.quantity
                    record.available_qty = total_available
                else:
                    record.available_qty = 0
            else:
                record.available_qty = 0
