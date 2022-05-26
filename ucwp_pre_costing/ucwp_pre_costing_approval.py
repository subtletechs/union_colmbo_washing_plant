from odoo import api, fields, models, _, tools


class PreCostingApproval(models.Model):
    _name = "pre.costing.approval"
    _description = "Approval For Pre Costing"

    quotation = fields.Many2one(comodel_name="sale.order", string="Quotation", domain="[('state', '=', 'draft')]")
    state = fields.Selection([('waiting', 'Waiting for Approval'), ('approved', 'Approved')], string="State",
                             default='waiting')

    def action_approve(self):
        self.write({'state': 'approved'})
        # TODO set value of SO approved field True
        field = self.quotation.is_approved
        self.quotation.is_approved = True

    def action_wait(self):
        self.write({'state': 'waiting'})


class PreCostingApprovalWizard(models.TransientModel):
    _name = "pre.costing.approval.wizard"

    quotation = fields.Many2one(comodel_name="sale.order", string="Quotation", domain="[('state', '=', 'draft')]")
    # warning = fields.Text(string="Warning", compute="_compute_warning")

    def create_approval(self):
        self.env['pre.costing.approval'].create({
            'quotation': self.quotation.id,
            'state': 'waiting',
        })
