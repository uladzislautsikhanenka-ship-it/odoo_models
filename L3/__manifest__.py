# -*- coding: utf-8 -*-
{
    'name': 'L3',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add primary contact functionality, improve sale order product selection, express delivery, split order lines, activity salesperson enhancement, and date panel in top bar',
    'description': """
        Custom Partner Contacts and Sale Order Enhancements
        ==================================================
        
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
        
        4. Sale Order Lines Split Functionality:
           - Dynamic splitting of sale order lines
           - Custom quantity distribution for split lines
           - Wizard interface for easy line splitting
           - Validation of split quantities
        
        5. Activity Salesperson Enhancement:
           - Add salesperson field to mail.activity model
           - Automatically populate salesperson from sale order when creating activities
           - Enhanced activity forms and views with salesperson information
           - Visual highlighting of read-only fields in sale order lines
        
        6. Date Panel in Top Bar:
           - Add interactive date panel next to clock icon in top navigation
           - Display current date and time in Russian locale
           - Click to open external time reference link
           - Auto-update every minute with smooth animations
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
        'security/ir.model.access.xml',
        'data/email_templates.xml',
        'wizard/split_order_lines_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/o2m_single_line_widget.xml',  # Виджет для ограничения пустых строк в o2m полях
        # 'views/mail_activity_views.xml',  # Временно отключено для исправления ошибки
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
            'L3/static/src/css/partner_no_highlight.css',  # CSS для убирания красной подсветки поля Partner
            'L3/static/src/css/order_line_single.css',  # CSS для ограничения пустых строк в order_line
            'L3/static/src/css/o2m_single_line.css',  # Универсальный CSS для o2m полей
            'L3/static/src/css/date_panel.css',  # CSS для панели даты
            'L3/static/src/js/date_panel_final.js',  # JavaScript для панели даты
            'L3/static/src/js/activity_popup_salesperson.js',  # JavaScript для добавления salesperson во всплывающие окна активностей
            'L3/static/src/js/order_line_single_row.js',  # JavaScript для ограничения количества пустых строк в order_line
            'L3/static/src/js/order_line_single_widget.js',  # Кастомный виджет для order_line
            'L3/static/src/js/order_line_force_single.js',  # Принудительное удаление лишних пустых строк
            'L3/static/src/js/order_line_remove_empty.js',  # Удаление пустых строк из DOM
            'L3/static/src/js/o2m_single_line_widget.js',  # Универсальный виджет для o2m полей
            'L3/static/src/js/single_line_widget.js',  # Основной виджет single_line
            # 'L3/static/src/js/activity_salesperson.js',  # Временно отключено для исправления ошибки
            # 'L3/static/src/css/date_panel.css',  # CSS для панели даты - ОТКЛЮЧЕНО
            # 'L3/static/src/js/date_panel_final.js',  # JavaScript для панели даты - ОТКЛЮЧЕНО
            # 'L3/static/src/css/sale_order_line_readonly_minimal.css',  # Временно отключено
            # 'L3/static/src/js/activity_salesperson_simple.js',  # Временно отключено
            # 'L3/static/src/css/sale_order_line_readonly.css',  # Отключена
            # 'L3/static/src/js/sale_order_line_readonly.js',  # Временно отключен
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
