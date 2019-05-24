odoo.define('dingtalk.chat.list.tree', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let DingTalkChatListController = ListController.extend({
        buttons_template: 'DingTalkChatListView.dingtalk_chat_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_dingtalk_chat_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'get.dingtalk.chat.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingTalkChatListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkChatListController,
        }),
    });

    viewRegistry.add('dingtalk_chat_list_tree', GetDingTalkChatListView);
});
