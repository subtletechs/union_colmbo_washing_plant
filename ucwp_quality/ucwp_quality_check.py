from odoo import api, fields, models, _


class UCWPQualityCheck(models.Model):
    _name = "ucwp.quality.check"
    _description = 'Quality Check'
    _rec_name = "name"

    # [UC-11]
    name = fields.Char(string="Quality Check Number", default="New")
    grn = fields.Many2one(comodel_name="stock.picking", string="GRN")
    quality_check_lines = fields.One2many(comodel_name="quality.check.lines", inverse_name="ucwp_quality_check_id",
                                          string="Quality Lines")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    manufacture_order = fields.Many2one(comodel_name="mrp.production", string="Manufacture Orders")

    # Generate a Sequence for Quality Check
    @api.model
    def create(self, values):
        qc_sequence = self.env['ir.sequence'].next_by_code('quality.check.number') or _('New')
        values['name'] = qc_sequence
        return super(UCWPQualityCheck, self).create(values)


# [UC-11]
class QualityCheckLines(models.Model):
    _name = "quality.check.lines"
    _description = "Quality Check Lines"

    product = fields.Many2one(comodel_name="product.product", string="Product")
    lot_no = fields.Many2one(comodel_name="stock.production.lot", string="Lot No", required=True)
    pass_fail = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Pass/Fail", required=True)
    quantity = fields.Float(string="Pass/Fail Quantity", required=True)
    defects = fields.Many2one(comodel_name="defects", string="Defects")
    image = fields.Binary(string="Image")
    ucwp_quality_check_id = fields.Many2one(comodel_name="ucwp.quality.check", string="Quality Check")
    comment = fields.Char(string="Comment")
    state = fields.Selection([('processed', 'Process'), ('disposed', 'Dispose'), ('returned', 'Returned'),
                              ('rewashed', 'Rewash')], string="State", readonly=True)
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    # Functional Testing 15.
    inspected_qty = fields.Float(string="Inspected Quantity")

    display_process_button = fields.Boolean(compute="_display_button")
    display_return_button = fields.Boolean(compute="_display_button")
    display_rewash_button = fields.Boolean(compute="_display_button")
    display_dispose_button = fields.Boolean(compute="_display_button")

    def process_garment(self):
        if self.quality_point == 'before_wash' and self.pass_fail == 'fail':
            self.write({'state': 'processed'})
        if self.quality_point == 'after_wash' and self.pass_fail == 'pass':
            self.write({'state': 'processed'})
            view = self.env.ref('stock.view_picking_form')
            internal_transfer_operation = self.env['stock.picking.type'].search([('code', '=', 'internal')])
            return {
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'context': {
                    'default_picking_type_id': internal_transfer_operation.id,
                },
            }

    # TODO functionality should need to be updated
    def return_garment(self):
        self.write({'state': 'returned'})
        view = self.env.ref('stock.view_stock_return_picking_form')
        return {
            'res_model': 'stock.return.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': {'active_id': self.ucwp_quality_check_id.grn.id,
                        'active_model': 'stock.picking', 'default_is_receipt_return': True},
        }

    def rewash_garment(self):
        self.write({'state': 'rewashed'})
        if self.pass_fail == 'fail' and self.ucwp_quality_check_id.quality_point == 'after_wash':
            view = self.env.ref('stock.view_picking_form')
            internal_transfer_operation = self.env['stock.picking.type'].search([('code', '=', 'internal')])
            return {
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'context': {
                    'default_picking_type_id': internal_transfer_operation.id,
                },
            }

    def dispose_garment(self):
        self.write({'state': 'disposed'})
        view = self.env.ref('stock.view_picking_form')
        # TODO limit internal transfer operation to one operation
        internal_transfer_operation = self.env['stock.picking.type'].search([('code', '=', 'internal')])
        return {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_picking_type_id': internal_transfer_operation.id,
            },
        }

    @api.depends('quality_point', 'pass_fail')
    def _display_button(self):
        # Process Button visibility
        for record in self:
            if record.quality_point == 'before_wash' and record.pass_fail == 'fail':
                record.display_process_button = True
            elif record.quality_point == 'after_wash' and record.pass_fail == 'pass':
                record.display_process_button = True
            else:
                record.display_process_button = False

            # Dispose Button visibility
            if record.pass_fail == 'fail':
                record.display_dispose_button = True
            else:
                record.display_dispose_button = False

            # Rewash Button visibility
            if record.quality_point == 'after_wash' and record.pass_fail == 'fail':
                record.display_rewash_button = True
            else:
                record.display_rewash_button = False

            # Return Button visibility
            if record.quality_point == 'before_wash' and record.pass_fail == 'fail':
                record.display_return_button = True
            else:
                record.display_return_button = False

    @api.onchange('product', 'lot_no')
    def update_domain(self):
        """Set demain to filter product and Lot No"""
        product_ids = self.ucwp_quality_check_id.grn.move_ids_without_package.product_id.ids
        split_lines = self.ucwp_quality_check_id.grn.move_ids_without_package.move_line_nosuggest_ids
        lot_name_list = []
        for split_line in split_lines:
            if split_line.product_id.id == self.product.id:
                lot_name_list.append(split_line.barcode)
        lot_ids = self.env['stock.production.lot'].search([('name', 'in', lot_name_list)])
        if lot_ids:
            return {
                'domain': {'lot_no': [('id', 'in', lot_ids.ids)]}
            }
        if product_ids:
            return {
                'domain': {'product': [('id', 'in', product_ids)]}
            }

