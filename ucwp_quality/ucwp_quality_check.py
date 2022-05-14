from odoo import api, fields, models, _


class UCWPQualityCheck(models.Model):
    _name = "ucwp.quality.check"
    _description = 'Quality Check'

    quantity = fields.Integer(string="Quantity")
    fail_quantity = fields.Integer(string="Fail Quantity")
    pass_quantity = fields.Integer(string="Pass Quantity")
    # [UC-11]
    grn = fields.Many2one(comodel_name="stock.picking", string="GRN")
    quality_check_lines = fields.One2many(comodel_name="quality.check.lines", inverse_name="ucwp_quality_check_id",
                                          string="Quality Lines")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    manufacture_order = fields.Many2one(comodel_name="mrp.production", string="Manufacture Orders")


# [UC-11]
class QualityCheckLines(models.Model):
    _name = "quality.check.lines"
    _description = "Quality Check Lines"

    product = fields.Many2one(comodel_name="product.product", string="Product")
    lot_no = fields.Many2one(comodel_name="stock.production.lot", string="Lot No", required=True)
    pass_fail = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Pass/Fail", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    defects = fields.Many2one(comodel_name="defects", string="Defects")
    image = fields.Binary(string="Image")
    ucwp_quality_check_id = fields.Many2one(comodel_name="ucwp.quality.check", string="Quality Check")
    comment = fields.Char(string="Comment")
    state = fields.Selection([('processed', 'Processed'), ('disposed', 'Disposed'), ('returned', 'Returned'),
                              ('rewashed', 'Rewashed')], string="State")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    display_process_button = fields.Boolean(compute="_display_button")
    display_return_button = fields.Boolean(compute="_display_button")
    display_rewash_button = fields.Boolean(compute="_display_button")
    display_dispose_button = fields.Boolean(compute="_display_button")

    def process_garment(self):
        if self.quality_point == 'before_wash' and self.pass_fail == 'fail':
            self.write({'state': 'processed'})
        if self.quality_point == 'after_wash' and self.pass_fail == 'pass':
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

    def rewash_garment(self):
        self.write({'state': 'rewashed'})

    def dispose_garment(self):
        self.write({'state': 'disposed'})

    @api.depends('quality_point', 'pass_fail')
    def _display_button(self):
        # Process Button visibility
        if self.quality_point == 'before_wash' and self.pass_fail == 'fail':
            self.display_process_button = True
        elif self.quality_point == 'after_wash' and self.pass_fail == 'pass':
            self.display_process_button = True
        else:
            self.display_process_button = False

        # Dispose Button visibility
        if self.pass_fail == 'fail':
            self.display_dispose_button = True
        else:
            self.display_dispose_button = False

        # Rewash Button visibility
        if self.quality_point == 'after_wash' and self.pass_fail == 'fail':
            self.display_rewash_button = True
        else:
            self.display_rewash_button = False

        # Return Button visibility
        if self.quality_point == 'before_wash' and self.pass_fail == 'fail':
            self.display_return_button = True
        else:
            self.display_return_button =False
