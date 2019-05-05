odoo.define('dingtalk.attendance.listrecord.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let pull_list = function () {
        let self = this;
        let startDate = self.$el.find('#startDate').val();
        let endDate = self.$el.find('#endDate').val();
        let username = self.$el.find('#username').val();
        let def = rpc.query({
            model: 'dingtalk.attendance.list.record',
            method: 'get_attendance_listrecord',
            args: [startDate, endDate, username],
        }).then(function (result) {
            if (result) {
                new Dialog.confirm(this, result.msg, {
                        'title': '结果提示',
                    });
                location.reload();
            }
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.attendance.list.record') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dingtalk.attendance.list.record'\" class=\"btn btn-primary o_pull_dingtalk_simple_groups\">获取打卡详情</button>";
                let button2 = $(but).click(this.proxy('open_attendance_listrecord_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_attendance_listrecord_action: function () {
            new Dialog(this, {
                title: "获取打卡详情",
                size: 'medium',
                buttons: [
                    {
                        text: "确定",
                        classes: 'btn-primary',
                        close: true,
                        click: pull_list
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('PullDingtalkAttendanceList', {widget: this, data: []}))
            }).open();
        },
    });
});
