{
    'name': 'Custom Model',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Custom model with various field types',
    'description': """
        This module provides a comprehensive custom model with ALL Odoo field types:
        - Basic fields (Text, Char, HTML)
        - Numeric fields (Integer, Float, Monetary)
        - Boolean fields and checkboxes
        - Selection fields with states
        - Date and time fields
        - Binary and media fields
        - Relational fields (Many2one, Many2many, One2many)
        - Computed and related fields
        - Widget fields with special displays
        - Security and group fields
        - And much more!
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base'],
    'version': '18.0.1.0.0',
    'data': [
        'security/ir.model.access.csv',
        'views/custom_model_views.xml',
        'wizard/create_partner_wizard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}






