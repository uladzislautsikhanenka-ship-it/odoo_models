/** @odoo-module **/

import { One2ManyListRenderer } from "@web/views/one2many_list/one2many_list_renderer";
import { patch } from "@web/core/utils/patch";

// Патч для One2ManyListRenderer
patch(One2ManyListRenderer.prototype, {
    /**
     * Переопределяем метод создания записей для order_line
     */
    async _createRecord() {
        if (this.props.list.resModel === 'sale.order.line') {
            // Считаем пустые строки
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length >= 1) {
                // Не создаем новую запись, если уже есть одна пустая
                return;
            }
        }
        
        return super._createRecord();
    },

    /**
     * Переопределяем метод добавления записи
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
     * Переопределяем метод инициализации для ограничения количества пустых строк
     */
    async setup() {
        await super.setup();
        
        if (this.props.list.resModel === 'sale.order.line') {
            // Ограничиваем количество пустых строк при инициализации
            this._limitEmptyRows();
        }
    },

    /**
     * Метод для ограничения количества пустых строк
     */
    _limitEmptyRows() {
        if (this.state.records) {
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length > 1) {
                // Удаляем лишние пустые строки, оставляя только первую
                const rowsToRemove = emptyRows.slice(1);
                for (const row of rowsToRemove) {
                    this.state.records = this.state.records.filter(r => r.id !== row.id);
                }
            }
        }
    },

    /**
     * Переопределяем метод рендеринга для удаления лишних пустых строк
     */
    render() {
        if (this.props.list.resModel === 'sale.order.line') {
            // Удаляем лишние пустые строки перед рендерингом
            this._removeExtraEmptyRows();
        }
        return super.render();
    },

    /**
     * Метод для удаления лишних пустых строк
     */
    _removeExtraEmptyRows() {
        if (this.state.records) {
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length > 1) {
                // Удаляем все пустые строки кроме первой
                const rowsToKeep = this.state.records.filter(record => 
                    record.data.product_id && record.data.product_id !== false
                );
                
                // Добавляем только первую пустую строку
                if (emptyRows.length > 0) {
                    rowsToKeep.push(emptyRows[0]);
                }
                
                this.state.records = rowsToKeep;
            }
        }
    }
});