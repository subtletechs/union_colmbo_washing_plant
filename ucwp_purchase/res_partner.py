from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = "res.partner"

    vendor_certification = fields.One2many(comodel_name="vendor.certifications", inverse_name="vendor_certification_id",
                                           string="Vendor Certifications")


class VendorCertifications(models.Model):
    _name = "vendor.certifications"

    product_id = fields.Many2one(comodel_name="product.template", string="Product", required=True,
                                 domain="[('is_chemical', '=', True)]")
    certifications = fields.One2many(comodel_name="vendor.certification.lines", inverse_name="certification_lines_id",
                                     string="Certifications")
    vendor_certification_id = fields.Many2one(comodel_name="res.partner", string="Vendor Certification ID")


class VendorCertificationLines(models.Model):
    _name = "vendor.certification.lines"

    certification_type = fields.Many2one(comodel_name="chemical.certification.type", string="Certification Type")
    certification = fields.Many2many(comodel_name="ir.attachment", attachment=True, string="Certification")
    certification_lines_id = fields.Many2one(comodel_name="vendor.certifications", string="Certification Line id")


class ChemicalCertificationType(models.Model):
    _name = "chemical.certification.type"

    name = fields.Char(string="Name", required=True)
