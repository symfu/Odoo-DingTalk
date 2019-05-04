odoo.define('dingtalk.blackboard.info', function (require) {
    "use strict";

    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');
    let AbstractAction = require('web.AbstractAction');


    let DingtalkDashboard = AbstractAction.extend({
        template: 'DingtalkDashboardInfo',
        setBlackboardData: function (data) {
            let self = this;
            self.$el.find('#blackboard_list').html(QWeb.render("DingtalkDashboardInfoLine", {
                widget: self,
                data: data,
            }));
        },
        setBlackboardFalseData: function (data) {
            let self = this;
            self.$el.find('#blackboard_list').html(QWeb.render("DingtalkDashboardInfoLineFalse", {
                widget: self,
                data: data,
            }));
        },
        setBlackboardDataNull: function () {
            let self = this;
            self.$el.find('#blackboard_list').html(QWeb.render("DingtalkDashboardInfoLineNull", {
                widget: self,
                data: [],
            }));
        },
        setWorkRecordNumber: function (result) {
            this.$('.my-val1').html(result);
        },
        getUserApprovalNumber: function (result) {
            if (result.state) {
                this.$('.my-val3').html(result.number);
            } else {
                this.$('.my-val3').html(result.msg);
            }
        },

        start: function () {
            let self = this;
            //获取我的待办
            rpc.query({
                model: 'dingtalk.work.record',
                method: 'get_record_number',
                args: [],
            }).then(function (result) {
                self.setWorkRecordNumber(result);
            });
            //获取待审批数
            rpc.query({
                model: 'dingtalk.approval.template',
                method: 'get_get_template_number_by_user',
                args: [],
            }).then(function (result) {
                self.getUserApprovalNumber(result);
            });

            let def = rpc.query({
                model: 'dingtalk.blackboard',
                method: 'get_blackboard_by_user',
                args: [],
            }).then(function (result) {
                if (result.state) {
                    if (result.data.length == 0) {
                        self.setBlackboardDataNull();
                    } else {
                        self.setBlackboardData(result.data);
                        self.$('.my-val2').html(result.number);
                    }
                } else {
                    self.setBlackboardFalseData(result);
                }
            });
        },
    });

    core.action_registry.add('dingtalk_dashboard', DingtalkDashboard);
    return DingtalkDashboard;
});