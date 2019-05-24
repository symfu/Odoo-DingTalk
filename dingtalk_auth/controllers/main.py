# -*- coding: utf-8 -*-
import base64
import json
import logging
import time, random
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class AutoLoginController(http.Controller):

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
            get_result = self.get_user_info_by_auth_code(authCode)
            if not get_result.get('state'):
                return self._post_error_message(get_result.get('msg'))
            userid = get_result.get('userid')
            logging.info(">>>获取的user_id为：{}".format(userid))
            if userid:
                employee = request.env['hr.employee'].sudo().search([('din_id', '=', userid)])
                if employee:
                    user = employee.user_id
                    if user:
                        # 解密钉钉登录密码
                        logging.info(u'>>>:解密钉钉登录密码')
                        password = base64.b64decode(user.din_password)
                        password = password.decode(encoding='utf-8', errors='strict')
                        request.session.authenticate(request.session.db, user.login, password)
                        return http.local_redirect('/web')
                    else:
                        # 自动注册
                        password = str(random.randint(100000, 999999))
                        fail = request.env['res.users'].sudo().create_user_by_employee(employee.id, password)
                        if not fail:
                            return http.local_redirect('/dingtalk/sign/in')
                    return http.local_redirect('/web/login')
                return http.local_redirect('/web/login')

        else:
            return self._post_error_message("获取临时授权码失败,请检查钉钉开发者后台设置!")


    def get_user_info_by_auth_code(self, auth_code):
        """
        根据返回的临时授权码获取用户信息
        :param auth_code:
        :return:
        """
        url = request.env['ali.dingtalk.system.conf'].sudo().search([('key', '=', 'get_userid')]).value
        token = request.env['ali.dingtalk.system.conf'].sudo().search([('key', '=', 'token')]).value
        url = "{}?access_token={}&code={}".format(url, token, auth_code)
        try:
            result = requests.get(url=url, timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') != 0:
                return {'state': False, 'msg': "钉钉接口错误:{}".format(result.get('errmsg'))}
            else:
                return {'state': True, 'userid': result.get('userid')}
        except ReadTimeout:
            return {'state': False, 'msg': "免登超时,请重试!"}
        except Exception as e:
            return {'state': False, 'msg': "登录失败,异常信息:{}".format(str(e))}


    def _post_error_message(self, message):
        """
        返回错误消息
        :param message:
        :return:
        """
        data = {'message': message}
        return request.render('dingtalk_auth.dingtalk_auto_login_message', data)