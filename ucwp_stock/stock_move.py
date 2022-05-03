from odoo import api, fields, models

from odoo.exceptions import UserError, ValidationError

from collections import defaultdict


class StockMove(models.Model):
    _inherit = "stock.move"
    # _order = "create_date asc, sequence, id"

    invoice_type = fields.Selection([('invoice', 'Invoiceable'), ('not_invoiceable', 'Not-Invoiceable')],
                                    string='Invoice Type')
    wash_type = fields.Selection([('wash', 'Wash'), ('rewash', 'Re-wash')], sting="Wash Type")
    approval = fields.Selection([('approved', 'Approved'), ('rejected', 'Rejected')], string="Approved/Rejected")
    comment = fields.Text(string="Comment")
    done_qty = fields.Float(string="Total Done")  # , compute="_compute_done")

    # def write(self, vals):
    #     record_id = self.id
    #     stock_move = self.browse(record_id)
    #     move_lines = stock_move.move_line_nosuggest_ids
    #     if move_lines:
    #         existing_done_qty = sum(line.qty_done for line in move_lines)
    #     val_qty = self.quantity_done
    #     # if self.product_uom_qty != self.quantity_done:
    #     #     raise UserError('Quantity mismatched!')
    #     return super(StockMove, self).write(vals)

    @api.depends('move_line_nosuggest_ids.qty_done')
    def _compute_done(self):
        if not any(self._ids):
            # onchange
            for move in self:
                quantity_done = 0
                for move_line in move._get_move_lines():
                    quantity_done += move_line.product_uom_id._compute_quantity(
                        move_line.qty_done, move.product_uom, round=False)
                move.quantity_done = quantity_done
                # print(quantity_done)
        else:
            # compute
            move_lines_ids = set()
            for move in self:
                move_lines_ids |= set(move._get_move_lines().ids)

            data = self.env['stock.move.line'].read_group(
                [('id', 'in', list(move_lines_ids))],
                ['move_id', 'product_uom_id', 'qty_done'], ['move_id', 'product_uom_id'],
                lazy=False
            )
            # print(data[0]['qty_done'])

            # if data[0]['qty_done'] != self.product_uom_qty:
            #     raise UserError("Quantity mismatched!")


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    barcode = fields.Char(string="Barcode", readonly=True)
    route_operation = fields.Many2one(comodel="mrp.bom", string="Route/Operation")

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('stock_move_line') or _('New')
        vals['lot_name'] = sequence
        vals['barcode'] = sequence
        return super(StockMoveLine, self).create(vals)


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    barcode = fields.Char(string="Barcode", readonly=True, compute="_compute_barcode")

    def _compute_barcode(self):
        self.barcode = self.name


class Picking(models.Model):
    _inherit = "stock.picking"

    variant_id = fields.Many2one(string="Variant", related="move_ids_without_package.product_id", store=True)


    def variant_ids(self):
        pass
        # ids = self.env['stock.picking'].search([('')])
