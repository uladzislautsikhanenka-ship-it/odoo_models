/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { One2ManyListRenderer } from "@web/views/one2many_list/one2many_list_renderer";

// Патч для One2ManyListRenderer
patch(One2ManyListRenderer.prototype, {
    /**
     * Переопределяем метод рендеринга для принудительного удаления лишних пустых строк
     */
    render() {
        const result = super.render();
        
        if (this.props.list.resModel === 'sale.order.line') {
            // Принудительно удаляем лишние пустые строки после рендеринга
            setTimeout(() => {
                this._forceRemoveExtraEmptyRows();
            }, 100);
        }
        
        return result;
    },

    /**
     * Принудительно удаляем лишние пустые строки
     */
    _forceRemoveExtraEmptyRows() {
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
                this.render();
            }
        }
    },

    /**
     * Переопределяем метод создания записей
     */
    async _createRecord() {
        if (this.props.list.resModel === 'sale.order.line') {
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length >= 1) {
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
            const emptyRows = this.state.records.filter(record => 
                !record.data.product_id || record.data.product_id === false
            );
            
            if (emptyRows.length >= 1) {
                return;
            }
        }
        
        return super._onAddRecord(ev);
    }
});
