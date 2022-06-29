from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


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
    state = fields.Selection([('draft', 'Draft'), ('lock', 'Lock')], string='State', default='draft', readonly=True)

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def set_to_validate(self):
        check_products = self.quality_check_lines.product
        check_lines = self.quality_check_lines
        product_list = []
        product_names = []
        for product in check_products:
            total_inspect = 0
            total_process = 0
            for line in check_lines:
                if line.product.id == product.id:
                    total_inspect += line.inspected_qty
                    total_process += line.quantity
            if total_inspect != total_process:
                product_list.append(product.id)
                product_names.append(product.name)
        if len(product_list) > 0:
            products = ' '.join([str(name) + ',' for name in product_names])
            error = "Product" + " - " + products + " Inspected Quantity and Process Quantity Not matched "
            raise ValidationError(error)
        else:
            self.write({'state': 'lock'})

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
    ucwp_quality_check_id = fields.Many2one(comodel_name="ucwp.quality.check", string="Quality Check")
    # Functional Testing 15.
    inspected_qty = fields.Float(string="Inspected Quantity")

    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")

    # UCWP|IMP|-00048 Quality check process - Re-engineering
    quality_check_line_info = fields.One2many(comodel_name="quality.check.line.info",
                                              inverse_name="quality_check_line_id", string="Quality Check Info")
    rest_qty = fields.Float(string="Rest Inspected qty", compute="_set_rest_inspected_qty")

    # Set initial value to rest qty
    @api.depends('quality_check_line_info.quantity')
    def _set_rest_inspected_qty(self):
        for line in self:
            quantity_done = 0
            for quality_check_info_record in line.quality_check_line_info:
                quantity_done += quality_check_info_record.quantity
            line.rest_qty = quantity_done
            if quantity_done > self.inspected_qty:
                raise ValidationError(_("Total of Pass/Fail quantities cannot exceed inspected quantity"))

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


class QualityCheckLineInfo(models.Model):
    _name = "quality.check.line.info"
    _description = "Quality Check line Information"

    # UCWP|IMP|-00048 Quality check process - Re-engineering
    pass_fail = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Pass/Fail", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    defects = fields.Many2one(comodel_name="defects", string="Defects")
    image = fields.Binary(string="Image")
    comment = fields.Char(string="Comment")
    state = fields.Selection([('processed', 'Process'), ('returned', 'Returned'),
                              ('rewashed', 'Rewash')], string="State", readonly=True)
    quality_check_line_id = fields.Many2one(comodel_name="quality.check.lines", string="Quality Check Line ID")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")

    display_process_button = fields.Boolean(compute="_display_button")
    display_return_button = fields.Boolean(compute="_display_button")
    display_rewash_button = fields.Boolean(compute="_display_button")

    # display_dispose_button = fields.Boolean(compute="_display_button")

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
            # if record.pass_fail == 'fail':
            #     record.display_dispose_button = True
            # else:
            #     record.display_dispose_button = False

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

    def process_garment(self):
        """Process garment"""
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

    # def dispose_garment(self):
    #     self.write({'state': 'disposed'})
    #     view = self.env.ref('stock.view_picking_form')
    #     # TODO limit internal transfer operation to one operation
    #     internal_transfer_operation = self.env['stock.picking.type'].search([('code', '=', 'internal')])
    #     return {
    #         'res_model': 'stock.picking',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'view_id': view.id,
    #         'target': 'current',
    #         'context': {
    #             'default_picking_type_id': internal_transfer_operation.id,
    #         },
    #     }

