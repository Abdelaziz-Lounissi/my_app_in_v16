odoo.define('hm_property.save_popup', function (require) {
"use strict";

var BasicController = require('web.FormController');
var FormController = BasicController.include({
    _onSave: function (ev) {

        ev.stopPropagation(); // Prevent x2m lines to be auto-saved
        var self = this;
        this._disableButtons();
        var modelname = this.modelName;
        if (this.modelName === 'hm.property'){
        $('#tenantShow').delay(1000).hide(0);
        $('#LandlordShow').delay(1000).hide(0);
        var res = this.saveRecord().then(
        function(result){
        for(var i= 0; i < result.length; i++)
        {

            if ((result[i] == 'street') || (result[i] == 'street2') || (result[i] == 'city')){
             var landlord_id = false ;
             var tenant_id = false ;
             var property_id = self.renderer.state.data.id ;

             var for_rent = self.renderer.state.data.for_rent;
                   if(self.renderer.state.data.tenant_id != false){
                   var tenant_id = self.renderer.state.data.tenant_id.data.id;
                   }
                  if(self.renderer.state.data.landlord_id != false){

                   var landlord_id = self.renderer.state.data.landlord_id.data.id;
                                      }
                        if(for_rent == true  ){
                            if((tenant_id != false) || (landlord_id != false) ){
                         self._rpc({
                                model: 'ir.model.data',
                                method: 'xmlid_to_res_id',
                                kwargs: {xmlid: 'hm_property.hm_property_popup_wizard'},
                            }).then(function (res_id) {
                               self.do_action({
                                type: 'ir.actions.act_window',
                                res_model: 'hm.property.popup',
                                view_mode: 'form',
                                view_type: 'form',
                                target: 'new',
                                context: {default_property_id: property_id, default_landlord: landlord_id, default_tanent: tenant_id},
                                views: [[res_id || false, 'form']],
                                });
                         });
                        }}
            }
        }

        }).then(this._enableButtons.bind(this)).guardedCatch(this._enableButtons.bind(this));
            }
        else {
        this.saveRecord().then(this._enableButtons.bind(this)).guardedCatch(this._enableButtons.bind(this));


        }



    },
});

return FormController;
});
