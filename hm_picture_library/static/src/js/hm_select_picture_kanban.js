odoo.define('hm_picture_library.hm_select_picture_kanban', function(require) {
    "use strict";
    var Dialog = require('web.Dialog');
    var config = require('web.config');
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');


    // QuickSelectView
    var QuickSelectView = {

        init: function(viewInfo, params) {
            var show_selectable = params.context.show_selectable;
            var lead_id_select = params.context.lead_id_select;
            var selected_sale_id = params.context.selected_sale_id;
            var hide_create_button = false;


            if (viewInfo.model === 'hm.picture.library' && show_selectable) {
                var crm_picture_select_kanban = true;
            } else {
                var crm_picture_select_kanban = false;
            }

            if (viewInfo.model === 'hm.picture.library' ) {
                var wizard_picture_button = true;
            } else {
                var wizard_picture_button = false;
            }
            if (params.context.hide_create_button) {
                hide_create_button = true;
                wizard_picture_button = false;
            }
            this.controllerParams.crm_picture_select_kanban = crm_picture_select_kanban && !config.device.isMobile;
            this.controllerParams.hide_create_button = hide_create_button && !config.device.isMobile;
            this.controllerParams.lead_id_select = lead_id_select;
            this.controllerParams.selected_sale_id = selected_sale_id;
            this.controllerParams.wizard_picture_button = wizard_picture_button;

        },
    };

    KanbanView.include({
        init: function() {
            this._super.apply(this, arguments);
            QuickSelectView.init.apply(this, arguments);
        },
    });

    //QuickSelectController
    var QuickSelectController = {

        init: function(parent, model, renderer, params) {
            if (params.hide_create_button) {
                this.importEnabled = false;
            }
            this.crm_picture_select_kanban = params.crm_picture_select_kanban;
            this.wizard_picture_button = params.wizard_picture_button;
            this.hide_create_button = params.hide_create_button;
            this.lead_id_select = params.lead_id_select;
            this.selected_sale_id = params.selected_sale_id;
        },

        _quickSelect: function() {
            if (!this.$buttons) {
                return;
            }
            var self = this;
            var lead_id_select = this.lead_id_select;
            var selected_sale_id = this.selected_sale_id;
            this.$buttons.on('click', '.o_button_wizard_picture_button', function() {
                self.do_action({
                    context: {
                        default_hm_lead_id: lead_id_select,
                        default_hm_so_id: selected_sale_id,
                    },
                    type: 'ir.actions.act_window',
                    views: [
                        [false, 'form']
                    ],
                    res_model: 'hm.picture.library.wizard',
                    target: 'new',
                });

            });
            this.$buttons.on('click', '.o_button_crm_picture_select_kanban', function() {
                var domain = [
                    ['lead_ids', 'not in', [lead_id_select]]
                ]
                var unrelated_photos_so = 0;
                var unrelated_photos_lead = 1;
                if (selected_sale_id) {
                    unrelated_photos_so = 1;
                    unrelated_photos_lead = 0;
                    domain = [
                        ['sale_order_ids', 'not in', [selected_sale_id]]
                    ]
                }

                self.do_action({
                    context: {
                        hide_create_button: true,
                        lead_id_select: lead_id_select,
                        selected_sale_id: selected_sale_id,
                        search_default_unrelated_photos_so: unrelated_photos_so,
                        search_default_unrelated_photos_lead: unrelated_photos_lead,

                    },
                    type: 'ir.actions.act_window',
                    views: [
                        [false, 'kanban']
                    ],
                    res_model: 'hm.picture.library',
                    target: 'new',
                    domain: domain,
                });

            });
            this.$buttons.on('click', '.o_button_crm_picture_hide_create_button', function() {
                var selectedRecords = self._getSelectedIds(self.selectedRecords);
                var lead_id_select = self.lead_id_select;
                var selected_sale_id = self.selected_sale_id;
                if (selected_sale_id) {
                    if (selectedRecords.length > 0) {
                        self._rpc({
                            model: 'hm.picture.library',
                            method: 'attach_so_picture',
                            args: [selectedRecords],
                            context: {
                                sale_id: selected_sale_id
                            },
                        }).then(function(res_id) {
                            if (res_id) {
                                self.do_action({
                                    type: 'ir.actions.act_window',
                                    res_model: 'sale.order',
                                    view_mode: 'form',
                                    view_type: 'form',
                                    res_id: res_id,
                                    target: 'current',
                                    views: [
                                        [false, 'form']
                                    ],
                                });
                            }
                        });;
                    } else {
                        var message = "Veuillez sélectionner au moins une image.";
                        Dialog.alert(self, '', {
                            title: "Erreur",
                            $content: $('<div/>').html(
                                message +
                                '<br/>'
                            )
                        });

                    }

                } else {

                    if (selectedRecords.length > 0) {
                        self._rpc({
                            model: 'hm.picture.library',
                            method: 'attach_picture_for_lead',
                            args: [selectedRecords],
                            context: {
                                lead_id: lead_id_select
                            },
                        }).then(function(res_id) {
                            if (res_id) {
                                self.do_action({
                                    type: 'ir.actions.act_window',
                                    res_model: 'crm.lead',
                                    view_mode: 'form',
                                    view_type: 'form',
                                    res_id: res_id,
                                    target: 'current',
                                    views: [
                                        [false, 'form']
                                    ],
                                });
                            }
                        });;
                    } else {
                        var message = "Veuillez sélectionner au moins une image.";
                        Dialog.alert(self, '', {
                            title: "Erreur",
                            $content: $('<div/>').html(
                                message +
                                '<br/>'
                            )
                        });

                    }

                }


            });
        }
    };

    KanbanController.include({
        init: function() {
            this._super.apply(this, arguments);
            QuickSelectController.init.apply(this, arguments);
        },

        _getSelectedRecords: function(records) {
            var self = this;
            return _.map(records, function(db_id) {
                return self.model.get(db_id, {
                    raw: true
                });
            });
        },
        _getSelectedIds: function(records) {
            return _.map(this._getSelectedRecords(records), function(record) {
                return record.res_id;
            });
        },
        renderButtons: function() {
            this._super.apply(this, arguments);
            QuickSelectController._quickSelect.call(this);
        }
    });

});