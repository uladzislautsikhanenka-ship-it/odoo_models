/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { One2ManyListRenderer } from "@web/views/one2many_list/one2many_list_renderer";

// Патч для One2ManyListRenderer
patch(One2ManyListRenderer.prototype, {
    /**
     * Переопределяем метод рендеринга для принудительного удаления пустых строк
     */
    render() {
        const result = super.render();
        
        if (this.props.list.resModel === 'sale.order.line') {
            // Принудительно удаляем пустые строки после рендеринга
            setTimeout(() => {
                this._removeEmptyRows();
            }, 50);
        }
        
        return result;
    },

    /**
     * Принудительно удаляем пустые строки из DOM
     */
    _removeEmptyRows() {
        const listElement = document.querySelector('.o_field_x2many_list[name="order_line"]');
        if (listElement) {
            // Находим все строки с пустыми td[colspan="13"]
            const emptyRows = listElement.querySelectorAll('tbody tr:has(> td[colspan="13"])');
            
            // Удаляем все найденные пустые строки
            emptyRows.forEach(row => {
                if (row.parentNode) {
                    row.parentNode.removeChild(row);
                }
            });
        }
    },

    /**
     * Переопределяем метод инициализации
     */
    async setup() {
        await super.setup();
        
        if (this.props.list.resModel === 'sale.order.line') {
            // Удаляем пустые строки при инициализации
            setTimeout(() => {
                this._removeEmptyRows();
            }, 100);
        }
    }
});
