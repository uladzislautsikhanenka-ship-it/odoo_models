/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ActivityFormController } from "@mail/views/activity/activity_form_controller";

// Патчим контроллер формы активности для автоматического заполнения salesperson
patch(ActivityFormController.prototype, {
    setup() {
        super.setup();
        this._setupSalespersonAutoFill();
    },

    _setupSalespersonAutoFill() {
        // Автоматически заполняем salesperson при создании активности
        this.env.bus.addEventListener('activity_created', (event) => {
            this._autoFillSalesperson();
        });
    },

    _autoFillSalesperson() {
        // Получаем контекст активности
        const context = this.env.services.user.context;
        const activeModel = context.active_model;
        const activeId = context.active_id;

        if (activeModel && activeId && activeModel === 'sale.order') {
            // Получаем заказ
            this.env.services.orm.read(activeModel, [activeId], ['user_id'])
                .then((orders) => {
                    if (orders.length > 0 && orders[0].user_id) {
                        // Заполняем поле salesperson
                        this.model.root.update({
                            salesperson_id: orders[0].user_id[0] // [id, name] format
                        });
                    }
                });
        } else if (activeModel && activeId && activeModel === 'sale.order.line') {
            // Получаем линию заказа и связанный заказ
            this.env.services.orm.read(activeModel, [activeId], ['order_id'])
                .then((lines) => {
                    if (lines.length > 0 && lines[0].order_id) {
                        const orderId = lines[0].order_id[0];
                        return this.env.services.orm.read('sale.order', [orderId], ['user_id']);
                    }
                    return [];
                })
                .then((orders) => {
                    if (orders.length > 0 && orders[0].user_id) {
                        // Заполняем поле salesperson
                        this.model.root.update({
                            salesperson_id: orders[0].user_id[0] // [id, name] format
                        });
                    }
                });
        }
    }
});

// Дополнительный патч для обработки создания активности из чатов
registry.category("services").add("activity_salesperson_enhancer", {
    start(env) {
        return {
            enhanceActivityCreation: (activityData, context) => {
                // Автоматически добавляем salesperson при создании активности
                if (context.active_model === 'sale.order' && context.active_id) {
                    return env.services.orm.read('sale.order', [context.active_id], ['user_id'])
                        .then((orders) => {
                            if (orders.length > 0 && orders[0].user_id) {
                                activityData.salesperson_id = orders[0].user_id[0];
                            }
                            return activityData;
                        });
                } else if (context.active_model === 'sale.order.line' && context.active_id) {
                    return env.services.orm.read('sale.order.line', [context.active_id], ['order_id'])
                        .then((lines) => {
                            if (lines.length > 0 && lines[0].order_id) {
                                const orderId = lines[0].order_id[0];
                                return env.services.orm.read('sale.order', [orderId], ['user_id']);
                            }
                            return [];
                        })
                        .then((orders) => {
                            if (orders.length > 0 && orders[0].user_id) {
                                activityData.salesperson_id = orders[0].user_id[0];
                            }
                            return activityData;
                        });
                }
                return Promise.resolve(activityData);
            }
        };
    }
});



