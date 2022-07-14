{
    'name': 'Sale Payment Web',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Sales',
    'version': '14.0.1.0.0',
    'description':
        """
Sale Payment Web
================

Allow sales people to register payments for sale orders.

Electronic payments will create transactions and automatically reconcile on the invoice.

        """,
    'depends': [
        'payment',
        'sale',
    ],
    'auto_install': False,
    'data': [
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'views/sale_views.xml',
    ],
}
