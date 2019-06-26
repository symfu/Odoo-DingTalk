# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import api, models
from .dingtalk_client import get_client
_logger = logging.getLogger(__name__)


class GetAliDinDinToken(models.TransientModel):
    _description = '获取钉钉token值'
    _name = 'ali.dindin.get.token'

    @api.model
    def get_token(self):
        """获取钉钉token值的方法函数
        获取token值需要用户用户唯一凭证（din_appkey）和用户唯一凭证密钥（din_appsecret）
        """
        client = get_client(self)
        result = client.get_access_token()
        logging.info(">>>获取钉钉token结果:{}".format(result))
        if result.get('errcode') == 0:
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')])
            if token:
                token.write({
                    'value': result.get('access_token')
                })
        else:
            logging.info(">>>获取钉钉Token失败！请检查网络是否通畅或检查日志输出")
