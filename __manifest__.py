# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Union Colombo Washing Plant',
    'version': '1',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'stock',
        'sale',
        'mrp',
        'quality',
        'quality_control',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'ucwp_stock/product_template.xml',
        'ucwp_stock/stock_move.xml',
        'ucwp_stock/ucwp_fabric_type.xml',
        'ucwp_stock/ucwp_wash_type.xml',
        'ucwp_stock/ucwp_garment_type.xml',
        'ucwp_sale/sale_order.xml',
        'ucwp_mrp/mrp_bom_views.xml',
        'ucwp_quality/quality_views.xml',
        'ucwp_quality/ucwp_defects.xml',
        'ucwp_mrp/mrp_production_view.xml',
        'ucwp_mrp/job_card.xml',
    ],

    'installable': True,
    'application': True,
}
