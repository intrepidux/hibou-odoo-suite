{
    'name': 'Timesheet Grid Description',
    'description': 'bridge',
    'version': '15.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'timesheet_description',
        'timesheet_grid',
    ],
    'data': [
        'views/timesheet_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
