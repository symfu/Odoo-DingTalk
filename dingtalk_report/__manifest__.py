# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-日志",
    'summary': """钉钉办公-日志""",
    'description': """ 钉钉办公-日志 """,
    'author': "OnGood",
    'website': "https://www.ongood.cn",
    'category': 'dingtalk',
    'version': '1.0',
    "sequence": 0,
    'depends': ['base', 'ali_dingtalk'],
    'installable': True,
    'application': True,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'data/mail_channel.xml',
        'views/asset.xml',
        'views/report_template.xml',
        'views/report_list.xml',
        'views/download_report.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
    'price': '50',
    'currency': 'EUR',
    'images':  ['static/description/app1.png', 'static/description/app2.png']
}
