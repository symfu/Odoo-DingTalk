odoo.define('dingtalk_approval.pull.dingtalk.approval.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let save_data = function () {
        this.do_notify("请稍后...", "查询完成后需要刷新界面方可查看！!");
        getTemplate();
    };

    let getTemplate = function () {
        let def = rpc.query({
            model: 'dingtalk.approval.template',
            method: 'get_template',
            args: [],
        }).then(function () {
            console.log("查询成功");
            location.reload();
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.approval.template') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dingtalk.approval.template'\" class=\"btn btn-secondary o_pull_dingtalk_approval_template\">" +
                    "拉取审批模板</button>";
                let button2 = $(but).click(this.proxy('open_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_action: function () {
            new Dialog(this, {
                title: "拉取审批模板",
                size: 'medium',
                buttons: [
                    {
                        text: "开始拉取",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('PullDingtalkApprovalTemplate', {widget: this, data: []}))
            }).open();
        },

    });
});
