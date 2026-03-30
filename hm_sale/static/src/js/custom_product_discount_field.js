/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FloatField } from "@web/views/fields/float/float_field";
import { _lt } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

class CustomProductDiscountField extends FloatField {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }

    onChange(ev) {
        if (!("order_line" in this.props.record.model.root.data)) {
            return;
        }
        const x2mList = this.props.record.model.root.data.order_line;
        const orderLines = x2mList.records.filter(line => !line.data.display_type);

        if (orderLines.length < 3) {
            return;
        }

        const isFirstOrderLine = this.props.record.data.id === orderLines[0].data.id;
        if (isFirstOrderLine && sameValue(orderLines)) {
            // Supprimer l'appel au service de dialogue ici
            const commands = orderLines.slice(1).map((line) => {
                return {
                    operation: "UPDATE",
                    record: line,
                    data: {["discount"]: this.props.value},
                };
            });

            x2mList.applyCommands('order_line', commands);
        }
    }
}

function sameValue(orderLines) {
    const compareValue = orderLines[1].data.discount;
    return orderLines.slice(1).every(line => line.data.discount === compareValue);
}

CustomProductDiscountField.template = "sale.ProductDiscountField";
CustomProductDiscountField.displayName = _lt("Disc.%");

// Utiliser add avec un drapeau pour écraser l'existant
registry.category("fields").add("sol_discount", CustomProductDiscountField, { force: true });
