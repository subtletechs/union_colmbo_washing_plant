import datetime

from odoo import api, fields, models, _

from odoo.exceptions import UserError, ValidationError

from collections import defaultdict


class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_type = fields.Selection([('invoice', 'Invoiceable'), ('not_invoiceable', 'Non-Invoiceable')],
                                    string='Invoice Type')
    wash_type = fields.Selection([('wash', 'Wash'), ('rewash', 'Re-wash')], string="Wash Type")
    approval = fields.Selection([('approved', 'Approved'), ('rejected', 'Rejected')], string="Approved/Rejected")
    comment = fields.Text(string="Comment")
    done_qty = fields.Float(string="Total Done")  # , compute="_compute_done")
    # [UC-12]
    op_type = fields.Many2one('stock.picking.type', 'Operation Type', related="picking_id.picking_type_id", store=True)
    op_name = fields.Char(string="Name")
    # Add Fault Type
    fault_type = fields.Selection([('customer_fault', "Customer Fault"), ('uc_fault', 'UC Fault')],
                                  string="Fault")

    # GRN Operation Type
    is_garment = fields.Boolean(string="Is Garment")

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

    @api.onchange('product_id')
    def product_domain(self):
        """ Filter Products in GRN"""
        if self.picking_id.garment_receipt:
            if 'sale_id' in self.env.context:
                sale_id = self.env.context.get('sale_id')
                if sale_id:
                    records = self.env['sale.order.line'].search([('order_id', '=', sale_id)])
                    if records:
                        product_ids = records.mapped('product_id').ids
                        return {
                            'domain': {'product_id': [('id', 'in', product_ids)]}
                        }
                else:
                    if self.picking_id.garment_select == 'sample':
                        sample_products = self.env['product.product'].search([('is_sample', '=', True)])
                        sample_products_ids = sample_products.ids
                        return {
                            'domain': {'product_id': [('id', 'in', sample_products_ids)]}
                        }
                    elif self.picking_id.garment_select == 'bulk':
                        bulk_products = self.env['product.product'].search([('is_bulk', '=', True)])
                        return {
                            'domain': {'product_id': [('id', 'in', bulk_products.ids)]}
                        }
                    else:
                        raise UserError(_("Select Bulk/Sample Before Select Products"))
        else:
            pass

    # Override split icon method
    def action_show_details(self):
        """ Returns an action that will open a form view (in a popup) allowing to work on all the
        move lines of a particular move. This form view is used when "show operations" is not
        checked on the picking type.
        """
        self.ensure_one()

        # If "show suggestions" is not checked on the picking type, we have to filter out the
        # reserved move lines. We do this by displaying `move_line_nosuggest_ids`. We use
        # different views to display one field or another so that the webclient doesn't have to
        # fetch both.
        if self.picking_type_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        elif self.is_garment:
            view = self.env.ref('union_colmbo_washing_plant.view_stock_move_nosuggest_operations_garment_receipt')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')

        if self.product_id.tracking == "serial" and self.state == "assigned":
            self.next_serial = self.env['stock.production.lot']._get_next_serial(self.company_id, self.product_id)

        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_owner=self.picking_type_id.code != 'incoming',
                show_lots_m2o=self.has_tracking != 'none' and (
                        self.picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),
                # able to create lots, whatever the value of ` use_create_lots`.
                show_lots_text=self.has_tracking != 'none' and self.picking_type_id.use_create_lots and not self.picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                show_source_location=self.picking_type_id.code != 'incoming',
                show_destination_location=self.picking_type_id.code != 'outgoing',
                show_package=not self.location_id.usage == 'supplier',
                show_reserved_quantity=self.state != 'done' and not self.picking_id.immediate_transfer and self.picking_type_id.code != 'incoming'
            ),
        }


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    barcode = fields.Char(string="Barcode", readonly=True)
    washing_options = fields.Many2one(comodel_name="washing.options", string="Washing Options")
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample',
                                      related="product_id.garment_select", store=True)

    # GRN Operation Type
    is_garment = fields.Boolean(string="Is Garment", related="move_id.is_garment", store=True)

    @api.model
    def create(self, vals):
        if 'picking_id' in vals:
            picking_obj = self.env['stock.picking'].browse(vals.get('picking_id'))
            if picking_obj.picking_type_id.garment_receipt:
                stock_move = self.env['stock.move'].browse(vals.get('move_id'))
                sequence = self.env['ir.sequence'].next_by_code('stock.move.line') or _('New')
                lot_id = self.env['stock.production.lot'].create({
                    'name': sequence,
                    'product_id': stock_move.product_id.id,
                    'barcode': sequence,
                    'product_type': 'material'
                })
                if lot_id:
                    vals['lot_id'] = lot_id.id
                    vals['barcode'] = lot_id.name
        return super(StockMoveLine, self).create(vals)

    def print_barcode(self):
        data = {
            'barcode': self.barcode,
        }
        return self.env.ref('union_colmbo_washing_plant.stock_move_line_barcode_action').report_action(self, data=data)


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    barcode = fields.Char(string="Barcode", readonly=True, compute="_compute_barcode")
    product_type = fields.Selection([('material', 'Material'), ('finish', 'Finish Product')], string='Product Type')

    def _compute_barcode(self):
        self.barcode = self.name


class Picking(models.Model):
    _inherit = "stock.picking"

    # @api.model
    # def default_get(self, fields):
    #     res = super(Picking, self).default_get(fields)
    #     active_id = self.env.context.get('active_id')
    #     active_model = self.env.context.get('active_model')
    #     return res

    variant_id = fields.Many2one(string="Variant", related="move_ids_without_package.product_id", store=True)
    garment_select = fields.Selection([('bulk', 'Bulk'), ('sample', 'Sample')], string='Bulk/Sample')
    samples = fields.Many2one(comodel_name="product.product", string="Samples")

    # UC-05
    receive_logistic = fields.Datetime(string="Received to Logistics", readonly=True)
    receive_sample_room = fields.Datetime(string='Received to Sample Room', readonly=True)

    # TODO add filters to stock.picking
    receipts = fields.Many2one(comodel_name="stock.picking", string="Receipts")
    manufacture_order = fields.Many2one(comodel_name="mrp.production", string="Manufacture Order")

    # To capture garment receipts
    garment_receipt = fields.Boolean(string="Garment Receipt", compute="_garment_receipt")
    chemical_receipt = fields.Boolean(string="Chemical Receipt", compute="_chemical_receipt")

    # [UC-11] - To calculate stock moves
    quality_check_count = fields.Integer(string="Quality Check", compute="_get_quality_checks")
    quality_check_id = fields.Many2one(comodel_name='ucwp.quality.check', compute='_get_quality_checks', copy=False)

    # [UC-07]
    bulk_production_count = fields.Integer(string="Parent Manufacturing Order Count", compute="_get_bulk_production")

    is_receipt_return = fields.Boolean(string='Stock Receipt return', default=False)

    # [UC-17]
    invoice_count = fields.Integer(string="Invoice Count", compute="_get_invoice")
    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice ID", compute="_get_invoice")

    # [UC-30]
    po_availability = fields.Selection([('po', 'PO'), ('temp_po', 'TEMP PO'), ('no_po', 'No PO')],
                                       string='PO Availability')
    customer_ref = fields.Char(string='Customer Ref')

    # To Map the sale order
    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order')

    # Gate pass number
    customer_gate_pass_no = fields.Char(string="Customer Gate Pass")
    customer_manual_ref = fields.Char(string="Manual Ref")

    # To bypass the Before QC
    bypass_qc = fields.Boolean(string="Bypass Quality Check?", default=False)
    bypass_comment = fields.Text(string="Comment")
    bypassed_by = fields.Many2one(comodel_name='res.users', string="Bypassed By", readonly=True)

    @api.onchange('bypass_qc')
    def set_bypass_user(self):
        """When user click to bypass the before QC, map the user who did the change"""
        if self.bypass_qc:
            self.bypassed_by = self.env.user

    def receive_logistic_update_datetime(self):
        """Update logistic order received date and time"""
        self.write({'receive_logistic': datetime.datetime.now()})

    def receive_sample_update_datetime(self):
        """Update Sample room order received date time and trasnfer stock from Logistic to Sample room"""
        if self.move_ids_without_package:

            picking_id = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('barcode', '=', 'WH-INTERNAL')])
            source = self.env['stock.location'].search([('locations_category', '=', 'logistic')])
            destination = self.env['stock.location'].search([('locations_category', '=', 'sample')])
            transfer = self.env['stock.picking'].create({
                'picking_type_id': picking_id.id,
                'location_id': source.id,
                'location_dest_id': destination.id,
                'move_ids_without_package': False
            })

            move_list = []
            for move in self.move_ids_without_package:
                product_id = move.product_id
                if move.move_line_nosuggest_ids:
                    split_lines = []
                    for move_line in move.move_line_nosuggest_ids:
                        done_qty = move_line.qty_done
                        lot_id = move_line.lot_id
                        # TODO get available qty for qty_done
                        split_lines.append(
                            (0, 0, {'product_id': product_id.id,
                                    'location_id': source.id,
                                    'location_dest_id': destination.id,
                                    'lot_id': lot_id.id,
                                    'qty_done': done_qty,
                                    'product_uom_id': move_line.product_uom_id.id,
                                    'picking_id': transfer.id
                                    }))
                move_list.append(
                    (0, 0, {'product_id': product_id.id,
                            'name': product_id.display_name,
                            'product_uom': product_id.uom_id.id,
                            'location_id': source.id,
                            'location_dest_id': destination.id,
                            'move_line_ids': split_lines,
                            }))
            # picking_id = self.env['stock.picking.type'].search(
            #     [('code', '=', 'internal'), ('barcode', '=', 'WH-INTERNAL')])
            # transfer = self.env['stock.picking'].create({
            #     'picking_type_id': picking_id.id,
            #     'location_id': source.id,
            #     'location_dest_id': destination.id,
            #     'move_ids_without_package': move_list
            # })
            transfer.write({'move_ids_without_package': move_list})
            transfer.button_validate()

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
            else:
                record.garment_receipt = False

    @api.depends('picking_type_id')
    def _chemical_receipt(self):
        """Check the Operation Type for Chemical Receipt"""
        for record in self:
            if record.picking_type_id:
                if record.picking_type_id.chemical_receipt:
                    record.chemical_receipt = True
                else:
                    record.chemical_receipt = False

    # quality check button
    def before_quality_check(self):
        """Create Quality Check record"""
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
        """Calculate Parent Manufacturing Order count for GRN and IDS"""
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
                'name': _('Parent Manufacture Orders'),
                'res_model': 'bulk.production',
                'type': 'ir.actions.act_window',
                'view_mode': 'list,form',
                'views': [[tree_view.id, 'list'], [form_view.id, 'form']],
                'target': 'current',
                'domain': [('id', 'in', bulk_production_records.ids)],
            }

    def generate_mo(self):
        if self.move_ids_without_package:
            for stock_move in self.move_ids_without_package:
                bulk_record = self.env['bulk.production'].create({
                    'garment_receipt': self.id,
                    'product': stock_move.product_id.id,
                    'garment_select': stock_move.product_id.garment_select,
                    'quantity_done': stock_move.quantity_done,
                })
                if stock_move.move_line_nosuggest_ids and self.garment_select == 'sample':
                    split_lines = stock_move.move_line_nosuggest_ids
                    for split_line in split_lines:
                        self.env['mrp.production'].create({
                            'product_id': split_line.product_id.id,
                            'product_qty': split_line.qty_done,
                            'bulk_id': bulk_record.id,
                            'product_uom_id': split_line.product_uom_id.id
                        })

    def _get_invoice(self):
        invoices = self.env['account.move'].search([('delivery_order', '=', self.id)], limit=1)
        if invoices:
            self.invoice_count = 1
            self.invoice_id = invoices.id
        else:
            self.invoice_count = 0
            self.invoice_id = None

    def action_view_invoice_count(self):
        invoice_form_view = self.env.ref('account.view_move_form')
        record = self.env['account.move'].search([('delivery_order', '=', self.id)], limit=1)

        return {
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': invoice_form_view.id,
            'res_id': record.id,
            'target': 'current',
        }

    # [UC-17]
    def create_invoice(self):
        do_stock_moves = self.move_ids_without_package
        grn_stock_moves = self.receipts.move_ids_without_package
        invoiced_list = []
        for do_stock_move in do_stock_moves:
            records = grn_stock_moves.filtered(
                lambda move_lines: move_lines.product_id.id == do_stock_move.product_id.id)
            for record in records:
                if record.invoice_type == 'invoice':
                    invoiced_list.append(
                        (0, 0, {'product_id': do_stock_move.product_id.id, 'name': do_stock_move.product_id.name,
                                'quantity': do_stock_move.quantity_done, 'product_uom_id': do_stock_move.product_uom.id,
                                'tax_ids': [(6, 0, do_stock_move.product_id.taxes_id.ids)],
                                'price_unit': do_stock_move.product_id.list_price,
                                }))

        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'receipts': self.receipts.id,
            'delivery_order': self.id,
            'partner_id': self.receipts.partner_id.id,
            'invoice_line_ids': invoiced_list
        })

    def write(self, vals):
        if 'bypass_qc' in vals:
            if vals['bypass_qc']:
                vals['bypassed_by'] = self.env.user
        return super(Picking, self).write(vals)

    def button_validate(self):
        sale_id = self.sale_id.id
        for move in self.move_ids_without_package:
            done_qty = move.quantity_done
            if sale_id and self.move_ids_without_package:
                available_qty_records = self.env['actually.received.product.quantity'].search(
                    [('sale_order_id', '=', sale_id), ('product_id', '=', move.product_id.id)])
                if available_qty_records:
                    actually_received = available_qty_records.actually_received
                    if self.garment_receipt:
                        actually_received += done_qty
                    if self.is_receipt_return:
                        actually_received -= done_qty
                    available_qty_records.write({
                        'actually_received': actually_received,
                    })
                    # Get sale order line qty for current product
                    sale_order_qty = 0
                    for line in self.sale_id.order_line:
                        if line:
                            if line.product_id.id == move.product_id.id:
                                sale_order_qty += line.product_uom_qty
                    if actually_received > sale_order_qty:
                        # TODO: Need to be checked correct email template
                        template_id = self.env['ir.model.data']._xmlid_to_res_id(
                            'union_colmbo_washing_plant.extra_qty_email_template.xml',
                            raise_if_not_found=False)
                        lang = self.env.context.get('lang')
                        template = self.env['mail.template'].browse(template_id)
                        if template.lang:
                            lang = template._render_lang(self.ids)[self.id]
                        ctx = {
                            'default_model': 'stock.picking',
                            # 'default_res_id': self.ids[0],
                            'default_use_template': bool(template_id),
                            'default_template_id': template_id,
                            'default_composition_mode': 'comment',
                            'mark_so_as_sent': True,
                            # 'custom_layout': "mail.mail_notification_paynow",
                            'proforma': self.env.context.get('proforma', False),
                            'force_email': True,
                            # 'model_description': self.with_context(lang=lang).type_name,
                        }

                        return {
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'mail.compose.message',
                            'views': [(False, 'form')],
                            'view_id': False,
                            'target': 'new',
                            # 'context': ctx,
                        }

        return super(Picking, self).button_validate()


class WashingOptions(models.Model):
    _name = "washing.options"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    """To Capture Garment Receipt Operation Type"""
    garment_receipt = fields.Boolean(string="Garment Receipt", default=False)

    # To Capture Chemical Receipt Operation Type
    chemical_receipt = fields.Boolean(string="Chemical Receipt", default=False)


class Location(models.Model):
    _inherit = "stock.location"

    # [UC-46] - Update Inventory Locations for Sample room receive
    locations_category = fields.Selection(
        [('logistic', 'Logistic'), ('sample', 'Sample Room'), ('qc', 'Quality Check')], string="Locations Category")
