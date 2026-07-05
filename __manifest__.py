{
    'name': 'Custom OTP Login with Kaveh Negar',
    'version': '19.0.1.0.0',
    'category': 'Authentication',
    'summary': 'Login with OTP via Kaveh Negar SMS',
    'description': """
Login system using One-Time Password (OTP) via the Kaveh Negar service.
    """,
    'author': 'Fadoo,Kalantarzadeh',
    'website': 'https://yourwebsite.com',
    'depends': ['base', 'web', 'mail','website'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/login_templates.xml',
        'views/standard_login_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_otp_login/static/src/css/otp_style.css',
            'custom_otp_login/static/src/js/otp_login.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}