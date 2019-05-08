# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = 'res.users'

 
    def create_user_by_employee(self, employee_id, password, active=True):
        """
        通过员工创建Odoo用户
        """
        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)])

        # 获取不重复的邮箱
        email = employee.work_email
        if email:
            email_str_array = email.split('@')
            email_name = email_str_array[0]
            email_host = email_str_array[1]
            if email_host != 'ongood.cn':
                # 返回True是因为免登的时候会判断是否注册失败，如果为True则注册失败，重定向到Odoo登陆页面
                return True
            email_count = len(self.search([('login', 'like', email_name)]).sudo())
            if email_count > 0:
                email = email_name + str(email_count + 1) + '@' + email_host
        else:
            return True

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
            'email': email,
            'groups_id': request.env.ref('base.group_user')
  
        }
        user = self.sudo().create(values)

        # 关联员工与用户
        values = {
            'user_id': user.id
        }
        employee.write(values)
