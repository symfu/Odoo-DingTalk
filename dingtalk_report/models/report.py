# -*- coding: utf-8 -*-
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingtalkReportTemplate(models.Model):
    _name = 'dingtalk.report.template'
    _description = "日志模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    report_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_template(self):
        """获取日志模板"""
        logging.info(">>>获取日志模板...")
        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_template_listbyuserid')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'offset': 0,
            'size': 100,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=20)
            result = json.loads(result.text)
            # logging.info(">>>获取日志模板返回结果{}".format(result))
            if result.get('errcode') == 0:
                d_res = result.get('result')
                for report in d_res.get('template_list'):
                    data = {
                        'name': report.get('name'),
                        'icon_url': report.get('icon_url'),
                        'report_code': report.get('report_code'),
                        'url': report.get('url'),
                    }
                    template = self.env['dingtalk.report.template'].search(
                        [('report_code', '=', report.get('report_code'))])
                    if template:
                        template.write(data)
                    else:
                        self.env['dingtalk.report.template'].create(data)
            else:
                raise UserError('获取日志模板失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取日志模板结束...")

    @api.model
    def get_get_template_number_by_user(self):
        """
        根据当前用户获取该用户的未读日志数量
        :return:
        """
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
        if len(emp) > 1:
            return {'state': False, 'number': 0, 'msg': '登录用户关联了多个员工'}
        if emp and emp.din_id:
            url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_unreadcount')]).value
            token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'userid': emp.din_id,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    return {'state': True, 'number': result.get('count')}
                else:
                    return {'state': False, 'number': 0, 'msg': result.get('errmsg')}
            except ReadTimeout:
                return {'state': False, 'number': 0, 'msg': '网络连接超时'}
            except Exception:
                return {'state': False, 'number': 0, 'msg': "网络连接失败"}
        else:
            return {'state': False, 'number': 0, 'msg': 'None'}

class DingtalkReportList(models.Model):
    _name = 'dingtalk.report.list'
    _description = "日志列表"
    _rec_name = 'name'

    name = fields.Char(string='日志名', required=True)
    remark = fields.Char(string='备注')
    dept_name = fields.Char(string='部门')
    image_url = fields.Char(string='图片链接')
    image2_url = fields.Char(string='图片2')
    creator_name = fields.Char(string='日志创建人')
    create_time = fields.Char(string='日志创时间')
    report_id = fields.Char(string='日志ID')
    template_id = fields.Many2one(comodel_name='dingtalk.report.template', string=u'日志模板', required=True)
    
    
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)            
            


class DownloadDingtalkList(models.TransientModel):
    _name = 'dingtalk.report.list.download'
    _description = "下载钉钉日志列表"
 
    date_from = fields.Datetime('开始日期')
    date_to = fields.Datetime('结束日期')


    @api.multi
    def get_report_list(self):
        """
        获取日志列表
        :param pid:
        :param pcode:
        :return:
        """
        
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
        if len(emp) > 1:
            return {'state': False, 'number': 0, 'msg': '登录用户关联了多个员工'}
        if emp and emp.din_id:
            url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_list')]).value
            token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
            templates = self.env['dingtalk.report.template'].browse(self._context.get('active_ids',[]))
            for temp in templates:
                if temp:
                    data = {
                        'start_time': int(time.mktime(self.date_from.timetuple())*1000),
                        'end_time': int(time.mktime(self.date_to.timetuple())*1000),
                        'template_name': temp.name,
                        'userid': emp.din_id,
                        'cursor': 0,
                        'size': 20,
                    }
                    headers = {'Content-Type': 'application/json'}
                    try:
                        result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                        result = json.loads(result.text)
                        # logging.info(">>>获取日志列表返回结果{}".format(result))
                        if result.get('errcode') == 0:
                            d_res = result.get('result')
                            #获取日志列表
                            for report in d_res.get('data_list'):
                                data = {
                                    'template_id': temp.id,
                                    'name': report.get('template_name'),
                                    'remark': report.get('remark'),
                                    'dept_name': report.get('dept_name'),
                                    'report_id': report.get('report_id'),
                                    'creator_name': report.get('creator_name'),
                                    'create_time': self.get_time_stamp(report.get('create_time')),
                                    'image_url': report.get('images') if report.get('images') else '',
                                    # 'image2_url': report.get('images')[1]['image'] if len(report.get('images')) > 1 else '',
                                }
                                report_list = self.env['dingtalk.report.list'].search(
                                    [('report_id', '=', report.get('report_id'))])
                                if report_list:
                                    report_list.write(data)
                                else:
                                    self.env['dingtalk.report.list'].create(data)
                                
                                #获取日志内容
                                report_list = self.env['dingtalk.report.list'].search(
                                    [('report_id', '=', report.get('report_id'))])
                                for content in report['contents']:
                                    data = {
                                    'name': report.get('template_name'),
                                    'report_id': report_list.id,
                                    'report_sort': content.get('sort'),
                                    'report_type': content.get('type'),
                                    'report_key': content.get('key'),
                                    'report_value': content.get('value'),
                                    }
                                    report_content = self.env['dingtalk.report.list.contents'].search(
                                        [('report_id', '=', report_list.id), ('report_sort', '=', content.get('sort'))])
                                    if report_content:
                                        report_content.write(data)
                                    else:
                                        self.env['dingtalk.report.list.contents'].create(data)

                        else:
                            raise UserError('获取日志列表失败，详情为:{}'.format(result.get('errmsg')))
                    except ReadTimeout:
                        raise UserError("网络连接超时！")
            logging.info(">>>获取日志列表结束...")              

    @api.model
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间
        :param timeNum:
        :return:
        """
        if timeNum:
            timestamp = float(timeNum / 1000)
            timearray = time.localtime(timestamp)
            otherstyletime = time.strftime("%Y-%m-%d %H:%M:%S", timearray)
            return otherstyletime

class DingtalkReportListContents(models.Model):
    _name = 'dingtalk.report.list.contents'
    _description = "日志内容"
    _rec_name = 'name'

    name = fields.Char(string='日志名', required=True)
    report_sort = fields.Char(string='排序')
    report_type = fields.Char(string='类型')
    report_key = fields.Char(string='日志字段')
    report_value = fields.Char(string='填写内容')
    report_id = fields.Many2one(comodel_name='dingtalk.report.list', string=u'日志ID', required=True)


           