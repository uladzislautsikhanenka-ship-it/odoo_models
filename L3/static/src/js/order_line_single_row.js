/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { One2ManyListRenderer } from "@web/views/one2many_list/one2many_list_renderer";
import { patch } from "@web/core/utils/patch";

// Патч для обычного ListRenderer
patch(ListRenderer.prototype, {
    /**
     * Переопределяем метод для ограничения количества пустых строк в order_line
     */
    async _onAddRecord(ev) {
        // Проверяем, что мы работаем с order_line
        if (this.props.list.resModel === 'sale.order.line') {
            // Получаем текущее количество строк
            const currentRows = this.state.records.length;
            
            // Если уже есть пустые строки, не добавляем новые
            if (currentRows > 0) {
                // Проверяем, есть ли уже пустые строки (без product_id)
                const emptyRows = this.state.records.filter(record => 
                    !record.data.product_id || record.data.product_id === false
                );
                
                if (emptyRows.length >= 1) {
                    // Не добавляем новую строку, если уже есть одна пустая
                    return;
                }
            }
        }
        
        // Вызываем оригинальный метод
        return super._onAddRecord(ev);
    }
});

// Патч для One2ManyListRenderer
patch(One2ManyListRenderer.prototype, {
    /**
     * Переопределяем метод добавления записи для order_line
     */
    async _onAddRecord(ev) {
        if (this.props.list.resModel === 'sale.order.line') {
            // Считаем пустые строки
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length >= 1) {
                // Не добавляем, если уже есть одна пустая строка
                return;
            }
        }
        
        return super._onAddRecord(ev);
    },

    /**
     * Переопределяем создание записей для ограничения количества пустых строк
     */
    async _createRecord() {
        if (this.props.list.resModel === 'sale.order.line') {
            // Проверяем количество пустых строк
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length >= 1) {
                // Не создаем новую запись, если уже есть одна пустая
                return;
            }
        }
        
        return super._createRecord();
    }
});
