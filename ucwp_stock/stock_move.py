import datetime

from odoo import api, fields, models, _

from odoo.exceptions import UserError, ValidationError

from collections import defaultdict


class StockMove(models.Model):
    _inherit = "stock.move"
    # _order = "create_date asc, sequence, id"

    invoice_type = fields.Selection([('invoice', 'Invoiceable'), ('not_invoiceable', 'Non-Invoiceable')],
                                    string='Invoice Type')
    wash_type = fields.Selection([('wash', 'Wash'), ('rewash', 'Re-wash')], string="Wash Type")
    approval = fields.Selection([('approved', 'Approved'), ('rejected', 'Rejected')], string="Approved/Rejected")
    comment = fields.Text(string="Comment")
    done_qty = fields.Float(string="Total Done")  # , compute="_compute_done")
    # [UC-12]
    op_type = fields.Many2one('stock.picking.type', 'Operation Type', related="picking_id.picking_type_id", store=True)
    op_name = fields.Char(string="Name")

    @api.onchange('op_type')
    def set_operator_name(self):
        self.op_name = self.op_type.name

    # TODO calculate done qty
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
    washing_options = fields.Many2one(comodel_name="washing.options", string="Washing Options")
    route_operation = fields.Many2one(comodel="mrp.bom", string="Route/Operation")
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample',
                                      related="product_id.garment_select", store=True)

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('stock.move.line') or _('New')
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
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')
    samples = fields.Many2one(comodel_name="product.product", string="Samples")

    # UC-05
    receive_logistic = fields.Datetime(string='Receive to Log', readonly=True)
    receive_sample_room = fields.Datetime(string='Receive to Sample Room', readonly=True)

    # TODO add filters to stock.picking
    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    manufacture_order = fields.Many2one(comodel_name="mrp.production", string="Manufacture Order")

    # To capture garment receipts
    garment_receipt = fields.Boolean(string="Garment Receipt", compute="_garment_receipt")

    # [UC-11] - To calculate stock moves
    quality_check_count = fields.Integer(string="Quality Count", compute="_get_quality_checks")
    quality_check_id = fields.Many2one(comodel_name='ucwp.quality.check', compute='_get_quality_checks', copy=False)

    # [UC-07]
    bulk_production_count = fields.Integer(string="Bulk Production Count", compute="_get_bulk_production")

    is_receipt_return = fields.Boolean(string='Stock Receipt return', default=False)

    # [UC-17]
    invoice_count = fields.Integer(string="Invoice Count", compute="_get_invoice")

    def receive_logistic_update_datetime(self):
        """Update logistic order received date and time"""
        self.write({'receive_logistic': datetime.datetime.now()})

    def receive_sample_update_datetime(self):
        """Update Sample room order received date and time"""
        self.write({'receive_sample_room': datetime.datetime.now()})

    @api.depends("picking_type_id")
    def _garment_receipt(self):
        """Check the Operation Type for Garment Receipt"""
        for record in self:
            if record.picking_type_id:
                if record.picking_type_id.garment_receipt:
                    # record.update({'garment_receipt': True})
                    record.garment_receipt = True
                else:
                    record.garment_receipt = False

    # quality check button
    def before_quality_check(self):
        view = self.env.ref('union_colmbo_washing_plant.ucwp_quality_check_form_view')

        return {
            'res_model': 'ucwp.quality.check',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_grn': self.id,
                'default_quality_point': 'before_wash',
            },
        }

    # [UC-11]
    def _get_quality_checks(self):
        """Calculate the number of quality checks available for the GRN and those IDs"""
        quality_checks = self.env['ucwp.quality.check'].search([('grn', '=', self.id)], limit=1)
        if quality_checks:
            self.quality_check_count = 1
            self.quality_check_id = quality_checks.id
        else:
            self.quality_check_count = 0
            self.quality_check_id = None

    def action_view_quality_count(self):
        view = self.env.ref('union_colmbo_washing_plant.ucwp_quality_check_form_view')
        record = self.env['ucwp.quality.check'].search([('grn', '=', self.id)], limit=1)

        return {
            'res_model': 'ucwp.quality.check',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'res_id': record.id,
            'target': 'current',
        }

    # [UC-07]
    def _get_bulk_production(self):
        """Calculate Bulk Production count for GRN and IDS"""
        bulk_production_records = self.env['bulk.production'].search([('garment_receipt', '=', self.id)])
        if bulk_production_records:
            self.bulk_production_count = len(bulk_production_records.ids)
        else:
            self.bulk_production_count = 0

    def action_view_bulk_production_count(self):
        bulk_production_records = self.env['bulk.production'].search([('garment_receipt', '=', self.id)])
        form_view = self.env.ref('union_colmbo_washing_plant.bulk_production_form_view')

        if self.bulk_production_count == 1:
            return {
                'res_model': 'bulk.production',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': form_view.id,
                'res_id': bulk_production_records.id,
                'target': 'current',
            }
        else:
            tree_view = self.env.ref('union_colmbo_washing_plant.bulk_production_tree_view')
            return {
                'name': _(self.name),
                'res_model': 'bulk.production',
                'type': 'ir.actions.act_window',
                'view_mode': 'list,form',
                'views': [[tree_view.id, 'list'], [form_view.id, 'form']],
                'target': 'current',
                'domain': [('id', 'in', bulk_production_records.ids)],
            }

    def generate_mo(self):
        for stock_move in self.move_ids_without_package:
            bulk_record = self.env['bulk.production'].create({
                'garment_receipt': self.id,
                'product': stock_move.product_id.id,
            })
            split_lines = stock_move.move_line_nosuggest_ids
            for split_line in split_lines:
                self.env['mrp.production'].create({
                    'product_id': split_line.product_id.id,
                    'product_qty': split_line.qty_done,
                    'bulk_id': bulk_record.id,
                    'product_uom_id': split_line.product_uom_id.id
                })

    # [UC-17]
    def create_invoice(self):
        invoice_form_view = self.env.ref('account.view_move_form')
        do_stock_moves = self.move_ids_without_package
        grn_stock_moves = self.receipts.move_ids_without_package
        invoiced_list = []
        for do_stock_move in do_stock_moves:
            # product_id = stock_move_record.product_id.id
            records = grn_stock_moves.filtered(
                lambda move_lines: move_lines.product_id.id == do_stock_move.product_id.id)
            for record in records:
                if record.invoice_type == 'invoice':
                    invoiced_list.append(record.id)

        return {
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': invoice_form_view.id,
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'default_receipts': self.receipts.id,
                'default_delivery_order': self.id,
                'default_partner_id': self.receipts.partner_id.id,
                'default_invoice_line_ids': [(6, 0, invoiced_list)],
            }
        }

    def _get_invoice(self):
        invoices = self.env['account.move'].search([('delivery_order', '=', self.id)])
        if invoices:
            self.invoice_count = len(invoices.ids)
        else:
            self.invoice_count = 0

    def action_view_invoice_count(self):
        pass


class WashingOptions(models.Model):
    _name = "washing.options"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    """To Capture Garment Receipt Operation Type"""
    garment_receipt = fields.Boolean(string="Garment Receipt", default=False)
