# -*- coding: utf-8 -*-
import base64
import json
import logging
import time
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class IndexController(http.Controller):

    def send_request(self, method, request_url, data, retry=True, retry_count=0, retry_interval=3):
        """
        发送HTTP请求
        """
        headers = {
            'Content-Type': 'application/json;charset=utf-8'
        }
        if method == 'GET':
            res = requests.get(request_url, params=data, headers=headers, verify=False)
        if method == 'POST':
            res = requests.post(request_url, data=json.dumps(data), headers=headers, verify=False)
        result = res.json()
        if result.get('errcode') != 0:
            if retry:
                if retry_count <= 5:
                    # 接口访问出错时重试
                    time.sleep(retry_interval)
                    return self.send_request(method, request_url, data, retry_count=retry_count + 1)
                else:
                    raise Exception('（钉钉接口错误）' + result.get('errmsg') + ' | （接口地址）' + request_url)
            else:
                raise Exception('（钉钉接口错误）' + result.get('errmsg') + ' | （接口地址）' + request_url)
        else:
            return result

    def get_user_info_by_auth_code(self, auth_code):
        """
        通过AuthCode获取用户基本信息
        """
        method = 'GET'
        url = request.env['ali.dingtalk.system.conf'].sudo().search([('key', '=', 'get_userid')]).value
        token = request.env['ali.dingtalk.system.conf'].sudo().search([('key', '=', 'token')]).value
        params = {
            'access_token': token,
            'code': auth_code
        }
        result = self.send_request(method, url, params)
        return result

    @http.route('/dingtalk/sign/in', type='http', auth='none')
    def sign_in(self, **kw):
        """
        钉钉免登入口
        """
        data = {
            'corp_id': request.env['ir.config_parameter'].sudo().get_param('ali_dingtalk.din_corpId')
        }
        return request.render('dingtalk_auth.sign_in', data)

    @http.route('/dingtalk/auth', type='http', auth='none')
    def auth(self, **kw):
        """
        钉钉免登认证
        """
        authCode = kw.get('authCode')
        if authCode:
            user_info = self.get_user_info_by_auth_code(authCode)
            logging.info(">>>获取的user_info为：{}".format(user_info))
            employee = request.env['hr.employee'].sudo().search([('din_id', '=', user_info.get('userid'))])
            if employee:
                    if employee.user_id:
                        user = employee.user_id
                        if user:
                            # 解密钉钉登录密码
                            logging.info(u'>>>:解密钉钉登录密码')
                            password = base64.b64decode(user.din_password)
                            password = password.decode(encoding='utf-8', errors='strict')
                            request.session.authenticate(request.session.db, user.login, password)
                            return http.local_redirect('/web')
                        return http.local_redirect('/web/login')
                    return http.local_redirect('/web/login')
            return http.local_redirect('/web/login')
