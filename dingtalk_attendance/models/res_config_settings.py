# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    din_attendance = fields.Boolean(string="自动获取钉钉考勤")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            din_attendance=self.env['ir.config_parameter'].sudo().get_param('dingtalk_attendance.din_attendance'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_attendance.din_attendance', self.din_attendance)
        data = {
            'name': '钉钉-定时更新考勤',
            'active': True,
            'model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.attendance.tran')]).id,
            'state': 'code',
            'user_id': self.env.user.id,
            'numbercall': -1,
            'interval_number': 60,
            'interval_type': 'minutes',
            'code': "env['hr.attendance.tran'].get_attendance_list_sync()",
        }
        if self.din_attendance:
            cron = self.env['ir.cron'].sudo().search([('name', '=', "钉钉-定时更新考勤")])
            if len(cron) >= 1:
                cron.sudo().write(data)
            else:
                self.env['ir.cron'].sudo().create(data)
        else:
            cron = self.env['ir.cron'].sudo().search(
                [('code', '=', "env['hr.attendance.tran'].get_attendance_list_sync()")])
            if len(cron) >= 1:
                cron.sudo().unlink()
