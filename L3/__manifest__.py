# -*- coding: utf-8 -*-
{
    'name': 'L3',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add primary contact functionality, improve sale order product selection, and express delivery',
    'description': """
        Custom Partner Contacts
        =======================
        
        This module adds the following features:
        
        1. Primary Contact Management:
           - Add is_primary field to res.partner model
           - Only one primary contact per company
           - Prevent deletion of primary contacts
           - Visual indicators in the interface
        
        2. Sale Order Product Selection:
           - Exclude already selected products from sale order lines
           - Prevent duplicate product selection
        
        3. Express Delivery:
           - Add express_delivery field to sale.order.line
           - Create separate deliveries for standard and express items
           - Automatic delivery separation on order confirmation
    """,
    'author': 'Custom Development',
    'website': '',
    'depends': [
        'base',
        'contacts',
        'sale',
        'sale_stock',
        'stock',
        'mail',
        'sale_pdf_quote_builder',
    ],
    'data': [
        'reports/invoice_payment_report.xml',
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'test': [
        'tests/test_res_partner.py',
        'tests/test_sale_order.py',
    ],
    'assets': {
        'web.assets_backend': [
            'L3/static/src/css/partner_kanban.css',
            'L3/static/src/css/partner_kanban_simple.css',
            'L3/static/src/css/product_selector.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
