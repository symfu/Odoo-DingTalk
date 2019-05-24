# -*- coding: utf-8 -*-
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingTalkReportTemplate(models.Model):
    _name = 'dingtalk.report.template'
    _description = "日志模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    report_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one('res.company',
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

class DingTalkReportList(models.Model):
    _name = 'dingtalk.report.list'
    _description = "日志列表"
    _rec_name = 'name'

    name = fields.Char(string='日志名')
    report_id = fields.Char(string='钉钉日志ID')
    remark = fields.Char(string='备注')
    dept_name = fields.Char(string='部门')
    creator_name = fields.Char(string='日志创建人')
    create_time = fields.Char(string='日志创时间')
    read_num = fields.Char(string='已读数')
    comment_num = fields.Char(string='评论数')
    comment_user_num = fields.Char(string='去重后评论数')
    like_num = fields.Char(string='点赞数')
    content_ids = fields.One2many('dingtalk.report.list.contents', 'rep_id', string='日志内容列表')
    receiver_user_ids = fields.One2many('dingtalk.report.list.receivers', 'rep_id', string='接受日志用户列表')
    follower_user_ids = fields.One2many('dingtalk.report.list.followers', 'rep_id', string='相关用户列表')
    image_url_ids = fields.One2many('dingtalk.report.list.images', 'rep_id', string='照片列表')
    comment_user_ids = fields.One2many('dingtalk.report.list.comments', 'rep_id', string='评论列表')
    template_id = fields.Many2one('dingtalk.report.template', string='日志模板', required=True)
    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.user.company_id.id)            
            

    @api.multi
    def update_report(self):
        """
        获取日志统计数据
        :param pid:
        :param pcode:
        :return:
        """
        self.get_report_statistics()
        self.get_report_receivers()
        self.get_report_followers()
        self.get_report_comments()
 
 
    @api.multi
    def get_report_statistics(self):
        """
        获取日志统计数据
        :param pid:
        :param pcode:
        :return:
        """
        
        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_statistics')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'report_id': self.report_id,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            logging.info(">>>获取日志统计数据返回结果{}".format(result))
            if result.get('errcode') == 0:
                res = result.get('result')
                data = {
                        'read_num': res.get('read_num'),
                        'comment_user_num': res.get('comment_user_num'),
                        'like_num': res.get('like_num'),
                        }
                report_list = self.env['dingtalk.report.list'].search(
                        [('report_id', '=', self.report_id)])
                if report_list:
                    report_list.write(data)
            else:
                raise UserError('获取日志统计数据失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取日志统计数据结束...")  


    @api.multi
    def get_report_receivers(self):
        """
        获取日志接收人列表
        :param pid:
        :param pcode:
        :return:
        """
        
        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_receivers')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value

        data = {
            'report_id': self.report_id,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            logging.info(">>>获取日志统计数据返回结果{}".format(result))
            if result.get('errcode') == 0:
                res = result.get('result')
                userid_list = res.get('userid_list')
                if userid_list:
                    for userid in userid_list:
                        emp = self.env['hr.employee'].sudo().search([('din_id', '=', userid)])
                        if emp:
                            data = {
                                    'emp_id': emp.id,
                                    'rep_id': self.id,
                                    }
                            report_receiver = self.env['dingtalk.report.list.receivers'].search(
                                    [('rep_id', '=', self.id), ('emp_id', '=', emp.id)])
                            if report_receiver:
                                pass
                            else:
                                self.env['dingtalk.report.list.receivers'].create(data)
            else:
                raise UserError('获取日志接收人列表数据失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取日志接收人列表数据结束...")  


    @api.multi
    def get_report_followers(self):
        """
        获取日志相关人员列表
        :param pid:
        :param pcode:
        :return:
        """
        
        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_followers')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
        for ty in ['0','1','2']:
            data = {
                'report_id': self.report_id,
                'type': ty,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>获取日志统计数据返回结果{}".format(result))
                if result.get('errcode') == 0:
                    res = result.get('result')
                    userid_list = res.get('userid_list')
                    if userid_list:
                        for userid in userid_list:
                            emp = self.env['hr.employee'].sudo().search([('din_id', '=', userid)])

                            data = {
                                    'emp_id': emp.id,
                                    'report_follower_type': ty,
                                    'rep_id': self.id,
                                    }
                            report_follower = self.env['dingtalk.report.list.followers'].search(
                                    [('rep_id', '=', self.id), ('emp_id', '=', emp.id)])
                            if report_follower:
                                report_follower.write(data)
                            else:
                                self.env['dingtalk.report.list.followers'].create(data)
                            
                            #更新接受人员状态
                            report_receiver = self.env['dingtalk.report.list.receivers'].search(
                                    [('rep_id', '=', self.id), ('emp_id', '=', emp.id)])
                            if report_receiver:
                                report_receiver.write(data)

                else:
                    raise UserError('获取日志相关人员列表数据失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")
        logging.info(">>>获取日志相关人员列表数据结束...")  

    @api.multi
    def get_report_comments(self):
        """
        获取日志评论
        :param pid:
        :param pcode:
        :return:
        """
        
        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_comments')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
 
        data = {
            'report_id': self.report_id,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            logging.info(">>>获取日志评论数据返回结果{}".format(result))
            if result.get('errcode') == 0:
                res = result.get('result').get('comments')
                if res:
                    for comment in res:
                        if comment:
                            emp = self.env['hr.employee'].sudo().search([('din_id', '=', comment.get('userid'))])
                            data = {
                                    'emp_id': emp.id,
                                    'report_comment': comment.get('content'),
                                    'report_create_time': comment.get('create_time'),
                                    'rep_id': self.id,
                                    }
                            report_comment = self.env['dingtalk.report.list.comments'].search(
                                    [('rep_id', '=', self.id), ('emp_id', '=', emp.id)])
                            if report_comment:
                                report_comment.write(data)
                            else:
                                self.env['dingtalk.report.list.comments'].create(data)
            else:
                raise UserError('获取日志评论数据失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取日志评论数据结束...")  

 
class DownloadDingTalkList(models.TransientModel):
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

        url = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'get_report_list')]).value
        token = self.env['ali.dingtalk.system.conf'].search([('key', '=', 'token')]).value
        templates = self.env['dingtalk.report.template'].browse(self._context.get('active_ids',[]))
        for temp in templates:
            if temp:
                data = {
                    'start_time': int(time.mktime(self.date_from.timetuple())*1000),  #datetime转13位时间戳
                    'end_time': int(time.mktime(self.date_to.timetuple())*1000),
                    'template_name': temp.name,
                    'cursor': 0,
                    'size': 20,
                }
                headers = {'Content-Type': 'application/json'}
                try:
                    result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                    result = json.loads(result.text)
                    logging.info(">>>获取日志列表返回结果{}".format(result))
                    if result.get('errcode') == 0:
                        d_res = result.get('result')
                        #获取日志列表
                        for report in d_res.get('data_list'):
                            data = {
                                'template_id': temp.id,
                                'name': report.get('creator_name') + "的" + report.get('template_name'),
                                'remark': report.get('remark'),
                                'dept_name': report.get('dept_name'),
                                'report_id': report.get('report_id'),
                                'creator_name': report.get('creator_name'),
                                'create_time': self.get_time_stamp(report.get('create_time')),
                            }
                            report_list = self.env['dingtalk.report.list'].search(
                                [('report_id', '=', report.get('report_id'))])
                            if report_list:
                                report_list.write(data)
                            else:
                                self.env['dingtalk.report.list'].create(data)
                            
                            report_list = self.env['dingtalk.report.list'].search(
                                [('report_id', '=', report.get('report_id'))])
                            #获取日志内容
                            content = report.get('contents')
                            for fi in content:
                                data = {
                                'rep_id': report_list.id,
                                'report_field_sort': fi.get('sort'),
                                'report_field_type': fi.get('type'),
                                'report_field_key': fi.get('key'),
                                'report_field_value': fi.get('value'),
                                }
                                report_content = self.env['dingtalk.report.list.contents'].search(
                                    [('rep_id', '=', report_list.id), ('report_field_sort', '=', fi.get('sort'))])
                                if report_content:
                                    report_content.write(data)
                                else:
                                    self.env['dingtalk.report.list.contents'].create(data)

                            #获取日志照片
                            images = report.get('images')
                            sort = 1
                            for img in images:
                                img = json.loads(img)
                                data = {
                                'rep_id': report_list.id,
                                'image_sort': sort,
                                'image_url': img.get('image'),
                                }
                                report_imge = self.env['dingtalk.report.list.images'].search(
                                    [('rep_id', '=', report_list.id), ('image_sort', '=', sort)])
                                if report_imge:
                                    report_content.write(data)
                                else:
                                    self.env['dingtalk.report.list.images'].create(data)
                                sort = sort + 1

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

class DingTalkReportListContents(models.Model):
    _name = 'dingtalk.report.list.contents'
    _description = "日志内容"
    _rec_name = 'rep_id'

    FieldType = [
        ('1', '文本型'),
        ('2', '数字型'),
        ('3', '下拉型'),
        ('4', '日期和时间'),
        ('5', '仅日期'),
        ('6', '仅时间'),
        ('15', '外部联系人'),
    ]

    report_field_sort = fields.Char(string='排序')
    report_field_type = fields.Selection(string='字段类型', selection = FieldType)
    report_field_key = fields.Char(string='日志字段')
    report_field_value = fields.Char(string='填写内容')
    rep_id = fields.Many2one('dingtalk.report.list', string='日志ID', required=True)


class DingTalkReportListReceivers(models.Model):
    _name = 'dingtalk.report.list.receivers'
    _description = "日志接收人员列表"
    _rec_name = 'rep_id'

    FollowerType = [
        ('0', '已读'),
        ('1', '已评论'),
        ('2', '已点赞'),
    ]

    emp_id = fields.Many2one('hr.employee', string='接收人', required=True)
    report_follower_type = fields.Selection(string='状态', selection=FollowerType)
    rep_id = fields.Many2one('dingtalk.report.list', string='日志ID', required=True)

class DingTalkReportListFollowers(models.Model):
    _name = 'dingtalk.report.list.followers'
    _description = "日志相关人员列表"
    _rec_name = 'rep_id'

    FollowerType = [
        ('0', '已读人员'),
        ('1', '评论人员'),
        ('2', '点赞人员'),
    ]

    emp_id = fields.Many2one('hr.employee', string='关注者', required=True)
    report_follower_type = fields.Selection(string='类别', selection=FollowerType)
    rep_id = fields.Many2one('dingtalk.report.list', string='日志ID', required=True)


class DingTalkReportListComments(models.Model):
    _name = 'dingtalk.report.list.comments'
    _description = "日志评论列表"
    _rec_name = 'rep_id'

    # name = fields.Char(string='日志名', required=True)
    emp_id = fields.Many2one('hr.employee', string='评论人', required=True)
    report_comment = fields.Char(string='评论内容')
    report_create_time = fields.Char(string='评论时间')
    rep_id = fields.Many2one('dingtalk.report.list', string='日志ID', required=True)


class DingTalkReportListImages(models.Model):
    _name = 'dingtalk.report.list.images'
    _description = "日志相关图片"
    _rec_name = 'rep_id'

    image_url = fields.Char(string='图片链接')
    image_sort = fields.Char(string='序号')
    rep_id = fields.Many2one('dingtalk.report.list', string='日志ID', required=True)
