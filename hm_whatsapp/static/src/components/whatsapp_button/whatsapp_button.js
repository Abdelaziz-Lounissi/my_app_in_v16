/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import { SendSMSButton } from '@sms/components/sms_button/sms_button';
const { Component , status } = owl;

patch(SendSMSButton.prototype, 'hm_whatsapp', {

    setup() {
        this.action = useService("action");
        this.user = useService("user");
        this.title = this.env._t("Send Text Message");
    },

    get whatsAppHref() {
        return "https://wa.me/" + this.props.value.replace(/\s+/g, "");
    },

    async onClickWhatsApp(event) {
        const href = event.currentTarget.getAttribute("href");
        window.open(href, "_blank");
    }

});