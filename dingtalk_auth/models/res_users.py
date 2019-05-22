# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import AccessDenied
import pypinyin
from pypinyin import Style

class ResUsers(models.Model):
    _inherit = 'res.users'

 
    def create_user_by_employee(self, employee_id, password, active=True):
        """
        通过员工创建Odoo用户
        """
        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)])
        if employee:
            # 账号生成改为格式：姓名首字母+手机号末四位@企业邮箱域名
            # 安装 pypinyin:  pip install pypinyin
            # email_name1 = pypinyin.slug(employee.name, separator='') #全拼
            email_name1 = pypinyin.slug(employee.name, style=Style.FIRST_LETTER, separator='') #首字母
            email_name2 = employee.mobile_phone[7:] #取手机号末四位
            email_name = email_name1 + email_name2
            url = request.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')
            if url:
                email_host = url
            else:
                email_host = 'dingtalk.com'
            email_count = len(self.search([('login', 'like', email_name)]).sudo())
            if email_count > 0:
                user = request.env['res.users'].sudo().search([('login', '=', email_name + '@' + email_host)])
                values = {
                'user_id': user.id
                }
                employee.sudo().write(values)
            else:
                email = email_name + '@' + email_host

                # 获取不重复的姓名
                name = employee.name
                name_count = len(self.search([('name', 'like', name)]).sudo())
                if name_count > 0:
                    name = name + str(name_count + 1)

                # 创建Odoo用户
                values = {
                    'active': active,
                    "login": email,
                    "password": password,
                    "name": name,
                    'email': employee.work_email,
                    'groups_id': request.env.ref('base.group_user')
        
                }
                user = self.sudo().create(values)

                # 关联员工与用户
                values = {
                    'user_id': user.id
                }
                employee.sudo().write(values)
