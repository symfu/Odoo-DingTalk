odoo.define('dingtalk.hrm.list.tree', function (require) {
    "use strict";

    let core = require('web.core');
    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let qweb = core.qweb;

    let DingTalkHrmListController = ListController.extend({
        buttons_template: 'HrmListView.hrm_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_dingtalk_hrm_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk.get.hrm.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingTalkHrmListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkHrmListController,
        }),
    });

    viewRegistry.add('dingtalk_hrm_list_tree', GetDingTalkHrmListView);
});
