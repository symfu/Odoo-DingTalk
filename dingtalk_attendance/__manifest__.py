# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-考勤排班详情",
    'summary': """钉钉办公-考勤排班详情""",
    'description': """ 钉钉办公-考勤排班详情 """,
    'author': "OnGood, SuXueFeng",
    'website': "https://www.ongood.cn",
    'category': 'dingtalk',
    'version': '1.0',
    'depends': ['base', 'ali_dingtalk', 'mail', 'hr_attendance'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'views/asset.xml',
        'views/simplegroups.xml',
        'views/attendance_list.xml',
        'views/attendance_listrecord.xml',
        'views/res_config_settings_views.xml',
        'views/hr_attendance.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
