# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
from odoo import tools
import base64
_logger = logging.getLogger(__name__)


class DingDingData(models.Model):
    _name = 'dingding.data'
    _description = "钉钉文件存储"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'


    name = fields.Char(string='文件名称', required=True)
    chat_id = fields.Char(string='群会话Id')
    media_id = fields.Char(string='群头像mediaId')
    media_type = fields.Selection(string=u'文件类型', selection=[('image', '图片'), ('voice', '语音'), ('file', '一般文件')], default='image')
    
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
  
    @api.model
    def create(self, values):
        tools.image_resize_images(values)
        return super(DingDingChat, self).create(values)

    @api.multi
    def write(self, values):
        tools.image_resize_images(values)
        return super(DingDingChat, self).write(values)

    @api.multi
    def create_dingding_chat(self):
        """
        创建群会话
        :return:
        """
        for res in self:
            user_list = self.check_employee_din_id(res)
            logging.info(">>>开始钉钉创建群会话")
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_create')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'name': res.name,
                'owner': res.employee_id.din_id,
                'showHistoryType': res.show_history_type,
                'searchable': res.searchable,
                'validationType': res.validation_type,
                'mentionAllAuthority': res.mention_all_authority,
                'chatBannedType': res.chat_banned_type,
                'managementType': res.management_ype,
                'useridlist': user_list,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    res.write({'chat_id': result.get('chatid'), 'state': 'normal'})
                    res.message_post(body=u"群会话已创建!群会话的ID:{}".format(result.get('chatid')), message_type='notification')
                else:
                    raise UserError('创建失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")

    @api.multi
    def write_dingding_chat(self):
        """
        修改群会话
        :return:
        """
        for res in self:
            self.check_employee_din_id(res)
            logging.info(">>>开始钉钉修改群会话")
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'chatid': res.chat_id,
                'name': res.name,
                'owner': res.employee_id.din_id,
                'showHistoryType': res.show_history_type,
                'searchable': res.searchable,
                'validationType': res.validation_type,
                'mentionAllAuthority': res.mention_all_authority,
                'chatBannedType': res.chat_banned_type,
                'managementType': res.management_ype,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    res.message_post(body=u"群会话已修改!", message_type='notification')
                else:
                    raise UserError('修改失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")

    @api.model
    def check_employee_din_id(self, res):
        if not res.employee_id.din_id:
            raise UserError("员工（群主）在钉钉中不存在，请选择其他人员!")
        user_list = list()
        for emp in res.useridlist:
            if not emp.din_id:
                raise UserError("员工{}:在钉钉中不存在，请选择其他人员!".format(emp.name))
            user_list.append(emp.din_id)
        return user_list

    @api.model
    def process_dingding_chat_onchange(self, msg):
        """
        处理回调
        :param msg: msg
        :return:
        """
        print(msg)
        chat = self.env['dingding.chat'].sudo().search([('chat_id', '=', msg.get('ChatId'))])
        # 群会话更换群主
        if msg.get('EventType') == 'chat_update_owner':
            if chat:
                employee = self.env['hr.employee'].sudo().search([('din_id', '=', msg.get('Owner'))])
                if employee:
                    chat.sudo().write({'employee_id': employee[0].id})
        # 群会话更换群名称
        elif msg.get('EventType') == 'chat_update_title':
            if chat:
                chat.sudo().write({'name': msg.get('Title')})
        # 群会话添加人员
        elif msg.get('EventType') == 'chat_add_member':
            new_users = list()
            for user in chat.useridlist:
                new_users.append(user.id)
            for user in msg.get('UserId'):
                employee = self.env['hr.employee'].sudo().search([('din_id', '=', user)])
                if employee:
                    new_users.append(employee[0].id)
            chat.sudo().write({'useridlist': [(6, 0, new_users)]})
        # 群会话删除人员
        elif msg.get('EventType') == 'chat_remove_member':
            for user in msg.get('UserId'):
                employee = self.env['hr.employee'].sudo().search([('din_id', '=', user)])
                if employee:
                    chat.sudo().write({'useridlist': [(3, employee[0].id)]})
        # 群会话用户主动退群
        elif msg.get('EventType') == 'chat_quit':
            employee = self.env['hr.employee'].sudo().search([('din_id', '=', msg.get('Operator'))])
            if employee:
                chat.sudo().write({'useridlist': [(3, employee[0].id)]})
        # 群会话解散群
        elif msg.get('EventType') == 'chat_disband':
            if chat:
                emp = self.env['hr.employee'].sudo().search([('din_id', '=', msg.get('Operator'))])
                chat.sudo().write({'state': 'close'})
                if emp:
                    chat.sudo().message_post(body=u"群会话已被解散，操作人: {}!".format(emp[0].name), message_type='notification')
        return True


class DingDingChatUserModelAdd(models.TransientModel):
    _name = 'dingding.chat.user.model.add'
    _description = "群会话添加成员"

    on_user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_chat_on_user_add_and_hr_employee_rel',
                                   column1='model_id', column2='emp_id', string=u'已有成员')
    user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_chat_user_add_and_hr_employee_rel',
                                column1='model_id', column2='emp_id', string=u'新群成员', required=True)

    @api.model
    def default_get(self, fields):
        res = super(DingDingChatUserModelAdd, self).default_get(fields)
        chat_id = self.env.context.get('active_id', False)
        ding_chat = self.env['dingding.chat'].browse(chat_id)
        if 'on_user_ids' in fields:
            res.update({'on_user_ids': [(6, 0, ding_chat.useridlist.ids)]})
        return res

    @api.multi
    def add_chat_users(self):
        """
        添加群成员
        :return:
        """
        for res in self:
            chat_id = self.env.context.get('active_id', False)
            ding_chat = self.env['dingding.chat'].browse(chat_id)
            user_list = list()
            for emp in res.user_ids:
                if not emp.din_id:
                    raise UserError("员工{}:在钉钉中不存在，请选择其他人员!".format(emp.name))
                user_list.append(emp.din_id)
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'chatid': ding_chat.chat_id,
                'add_useridlist': user_list,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    new_user_list = list()
                    for user in res.on_user_ids:
                        new_user_list.append(user.id)
                    for user in res.user_ids:
                        new_user_list.append(user.id)
                    ding_chat.write({'useridlist': [(6, 0, new_user_list)]})
                    ding_chat.message_post(body=u"群成员已增加!", message_type='notification')
                else:
                    raise UserError('群成员更新失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")


class DingDingChatUserModelDel(models.TransientModel):
    _name = 'dingding.chat.user.model.del'
    _description = "群会话删除成员"

    user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_chat_user_del_and_hr_employee_rel',
                                column1='model_id', column2='emp_id', string=u'删除群成员', required=True)
    old_user_ids = fields.Many2many(comodel_name='hr.employee',
                                    relation='dingding_chat_old_user_del_and_hr_employee_rel',
                                    column1='model_id', column2='emp_id', string=u'群成员', required=True)

    @api.model
    def default_get(self, fields):
        res = super(DingDingChatUserModelDel, self).default_get(fields)
        chat_id = self.env.context.get('active_id', False)
        ding_chat = self.env['dingding.chat'].browse(chat_id)
        if 'old_user_ids' in fields:
            res.update({'old_user_ids': [(6, 0, ding_chat.useridlist.ids)]})
        return res

    @api.multi
    def del_chat_users(self):
        """
        删除群成员
        :return:
        """
        for res in self:
            chat_id = self.env.context.get('active_id', False)
            ding_chat = self.env['dingding.chat'].browse(chat_id)
            user_list = list()
            for emp in res.user_ids:
                if not emp.din_id:
                    raise UserError("员工{}:在钉钉中不存在，请选择其他人员!".format(emp.name))
                user_list.append(emp.din_id)
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'chatid': ding_chat.chat_id,
                'del_useridlist': user_list,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    for user in res.user_ids:
                        ding_chat.write({'useridlist': [(3, user.id)]})
                    ding_chat.message_post(body=u"群成员已删除!", message_type='notification')
                else:
                    raise UserError('群成员更新失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")


class DingDingSendChatMessage(models.TransientModel):
    _name = 'dingding.send.chat.message'
    _description = "发送群消息"

    message = fields.Text(string=u'消息内容', required=True)

    @api.multi
    def send_dingding_message(self):
        """
        发送群会话消息
        :return:
        """
        chat_id = self.env.context.get('active_id', False)
        ding_chat = self.env['dingding.chat'].browse(chat_id)
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_send')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'chatid': ding_chat.chat_id,
            'msg': {
                "msgtype": "text",
                "text": {
                    "content": self.message
                }
            },
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            logging.info(">>>返回结果{}".format(result))
            if result.get('errcode') == 0:
                ding_chat.message_post(body=u"消息已成功发送!".format(self.message), message_type='notification')
            else:
                raise UserError('操作失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")

    @api.model
    def send_message(self, ding_chat, body):
        """
        发送群会话消息
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_send')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'chatid': ding_chat.chat_id,
            'msg': {
                "msgtype": "markdown",
                "markdown": {
                    "title": "来自ERP的备注消息",
                    "text": body
                }
            },
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
            result = json.loads(result.text)
            logging.info(">>>返回结果{}".format(result))
        except ReadTimeout:
            logging.info("发送群会话:'{}'时，网络连接超时！".format(ding_chat.name))


class DingDingChatList(models.TransientModel):
    _name = 'get.dingding.chat.list'
    _description = "获取群已存在的会话"

    chat_id = fields.Char(string='群会话Id', required=True)

    @api.multi
    def get_chat_info(self):
        """
        获取群会话
        :return:
        """
        for res in self:
            logging.info(">>>开始获取群会话...")
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_get')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'chatid': res.chat_id,
            }
            try:
                result = requests.get(url="{}{}".format(url, token), params=data, timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    chat_info = result.get('chat_info')
                    employee = self.env['hr.employee'].sudo().search([('din_id', '=', chat_info.get('owner'))])
                    if not employee:
                        raise UserError("返回的群管理员在Odoo系统中不存在!")
                    user_list = list()
                    for userlist in chat_info.get('useridlist'):
                        user = self.env['hr.employee'].sudo().search([('din_id', '=', userlist)])
                        if user:
                            user_list.append(user[0].id)
                    data = {
                        'chat_id': chat_info.get('chatid'),
                        'chat_icon': chat_info.get('icon'),
                        'name': chat_info.get('name'),
                        'employee_id': employee[0].id,
                        'show_history_type': chat_info.get('showHistoryType'),
                        'searchable': chat_info.get('searchable'),
                        'validation_type': chat_info.get('validationType'),
                        'mention_all_authority': chat_info.get('mentionAllAuthority'),
                        'management_ype': chat_info.get('managementType'),
                        'useridlist': [(6, 0, user_list)],
                        'state': 'normal'
                    }
                    chat = self.env['dingding.chat'].sudo().search([('chat_id', '=', res.chat_id)])
                    if chat:
                        chat.write(data)
                    else:
                        self.env['dingding.chat'].sudo().create(data)
                else:
                    raise UserError('操作失败:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")
