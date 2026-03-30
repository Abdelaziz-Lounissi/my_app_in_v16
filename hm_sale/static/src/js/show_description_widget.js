/** @odoo-module **/


import { formatDateTime } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";

const { Component, EventBus, onWillRender } = owl;
export class CustomPopover extends Component {
    setup() {
        this.actionService = useService("action");
    }
}

CustomPopover.template = 'hm_sale.CustomPopoverTemplate';

export class CustomWidget extends Component {
    setup() {
        this.bus = new EventBus();
        this.popover = usePopover();
        this.closePopover = null;
        this.orm = useService("orm");
        this.productDescription = null;
    }

    getProductDescription(){
        return this.props.record.data.name;
    }

    async showPopup(ev) {
        this.productDescription = await this.getProductDescription();
        this.closePopover = this.popover.add(
            ev.currentTarget,
            this.constructor.components.Popover,
            {productDescription: this.productDescription,bus: this.bus, record: this.props.record},
            {
                position: 'top',
            }
            );
        this.bus.addEventListener('close-popover', this.closePopover);
    }

    closePopup(ev){
        this.closePopover();
    }
}

CustomWidget.components = { Popover: CustomPopover };
CustomWidget.template = 'hm_sale.ShowDescriptioninSOLWidgetTemplate';
registry.category("view_widgets").add("show_description_in_sol_widget", CustomWidget);
