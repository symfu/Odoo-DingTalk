# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import requests
import json
from requests import ReadTimeout
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.iap.models import iap

_logger = logging.getLogger(__name__)


class ChangeMobile(models.TransientModel):
    _name = 'change.mobile'
    _description = 'Change Mobile'

    name = fields.Char('员工姓名', required=True, readonly= True)
    din_id = fields.Char('钉钉ID', required=True, readonly= True)
    dep_din_id = fields.Char('所属部门ID列表', required=True, readonly= True)
    old_mobile = fields.Char('原手机号', readonly= True)
    new_mobile = fields.Char('新手机号', required=True)



    def _sanitization(self, record, field_name):
        value = record[field_name]
        if value:
            return value

    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        return records

    @api.model
    def default_get(self, fields):
        result = super(ChangeMobile, self).default_get(fields)

        active_model = self.env.context.get('active_model')
        model = self.env[active_model]
        records = self._get_records(model)
        userid = []
        name = []
        old_mobile = []
        department = []
        for record in records:
            din_id = self._sanitization(record,'din_id')
            if din_id:
                userid.append(din_id)
            emp = self._sanitization(record,'name')
            if emp:
                name.append(emp)
            dep = self._sanitization(record,'department_id').din_id
            if dep:
                department.append(dep)
            mobile = self._sanitization(record,'mobile_phone')
            if mobile:
                old_mobile.append(mobile)
        result['din_id'] = ', '.join(userid)
        result['name'] = ', '.join(name)
        result['dep_din_id'] = ', '.join(department)
        result['old_mobile'] = ', '.join(old_mobile)
        return result

   
    # 员工钉钉换手机号
    def change_mobile_action(self):
        """强制更换手机号
           -如果手机号未激活，通过更新手机字段实现
           -如果手机号已经激活，则通过先删除该钉钉号，再重新创建钉钉号实现，新建的钉钉号使用老的userid
           -如果该员工有使用钉钉人脸考勤，需要重新录人脸，否则无法继续考勤
        """

        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'user_update')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
        headers = {'Content-Type': 'application/json'}
        data = {
            'userid': self.din_id,  # userid
            'name': self.name,  # 姓名
            'department': [self.dep_din_id],
            'mobile': self.new_mobile,  # 手机
        }
        old_data = data
        #直接更新
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(result)
            if result.get('errcode') == 0:
                # self.message_post(body=u"新的信息已同步更新至钉钉", message_type='notification')
                pass
            elif result.get('errcode') in ['60103','60104','40019']:
                pass
            elif result.get('errcode') != 0:
                #先删除钉钉号
                url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'user_delete')]).value
                token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
                data = {
                    'userid': self.din_id,  # userid
                }
                try:
                    result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
                    result = json.loads(result.text)
                    logging.info("user_delete:{}".format(result))
                    if result.get('errcode') != 0:
                        raise UserError('删除钉钉用户时发生错误，详情为:{}'.format(result.get('errmsg')))
                except ReadTimeout:
                    raise UserError("上传员工至钉钉超时！")
                
                #重新创建钉钉号
                try:
                    url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'user_create')]).value
                    token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
                    result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(old_data), timeout=10)
                    result = json.loads(result.text)
                    logging.info(result)
                    if result.get('errcode') == 0:
                        employee = self.env['hr.employee'].search([('din_id', '=', self.din_id)])
                        if employee:
                            employee.sudo().write({'mobile_phone': self.new_mobile})
                        # self.message_post(body=u"钉钉消息：员工信息已上传至钉钉", message_type='notification')
                    else:
                        raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
                except ReadTimeout:
                    raise UserError("上传员工至钉钉超时！")
        except ReadTimeout:
                    raise UserError("上传员工至钉钉超时！")