# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Union Colombo Washing Plant',
    'version': '1',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'ucwp_stock/product_template.xml',
        'ucwp_stock/ucwp_fabric_type.xml',
        'ucwp_stock/ucwp_wash_type.xml',
        'ucwp_stock/ucwp_garment_type.xml',
    ],

    'installable': True,
    'application': True,
}
