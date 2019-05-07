# -*- coding: utf-8 -*-
{
    'name': "钉钉免登",
    'summary': """提供钉钉集成服务""",
    'description': """
        钉钉内免登第三方网站（odoo）
	""",
    'author': "Ongood",
    'website': "https://ongood.cn",
    'category': 'Connector',
    'version': '1.0',
    'depends': ['ali_dingtalk'],
    'data': [
        'views/dingtalk_auth_templates.xml',
    ]
}
