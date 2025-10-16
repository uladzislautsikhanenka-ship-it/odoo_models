/** @odoo-module **/

import { One2ManyListRenderer } from "@web/views/one2many_list/one2many_list_renderer";
import { patch } from "@web/core/utils/patch";

// Создаем кастомный виджет single_line
export class SingleLineWidget extends One2ManyListRenderer {
    /**
     * Переопределяем метод рендеринга для ограничения пустых строк до одной
     */
    render() {
        const result = super.render();
        
        // Ограничиваем пустые строки для всех o2m полей
        setTimeout(() => {
            this._limitEmptyRows();
        }, 50);
        
        return result;
    }

    /**
     * Ограничиваем количество пустых строк до одной
     */
    _limitEmptyRows() {
        if (this.state.records) {
            // Считаем пустые строки (без основных данных)
            const emptyRows = this.state.records.filter(record => 
                this._isEmptyRecord(record)
            );
            
            if (emptyRows.length > 1) {
                // Оставляем только первую пустую строку
                const filledRows = this.state.records.filter(record => 
                    !this._isEmptyRecord(record)
                );
                
                // Добавляем только первую пустую строку
                if (emptyRows.length > 0) {
                    this.state.records = [...filledRows, emptyRows[0]];
                } else {
                    this.state.records = filledRows;
                }
                
                // Принудительно обновляем рендеринг
                this.render();
            }
        }
    }

    /**
     * Проверяем, является ли запись пустой
     */
    _isEmptyRecord(record) {
        if (!record || !record.data) {
            return true;
        }
        
        // Проверяем основные поля, которые указывают на заполненность записи
        const hasData = Object.keys(record.data).some(key => {
            const value = record.data[key];
            return value && value !== false && value !== 0 && value !== '';
        });
        
        return !hasData;
    }

    /**
     * Переопределяем метод создания записей
     */
    async _createRecord() {
        // Проверяем количество пустых строк перед созданием новой
        const emptyRows = this.state.records.filter(record => 
            this._isEmptyRecord(record)
        );
        
        if (emptyRows.length >= 1) {
            // Не создаем новую запись, если уже есть одна пустая
            return;
        }
        
        return super._createRecord();
    }

    /**
     * Переопределяем метод добавления записи
     */
    async _onAddRecord(ev) {
        // Проверяем количество пустых строк перед добавлением
        const emptyRows = this.state.records.filter(record => 
            this._isEmptyRecord(record)
        );
        
        if (emptyRows.length >= 1) {
            // Не добавляем, если уже есть одна пустая строка
            return;
        }
        
        return super._onAddRecord(ev);
    }

    /**
     * Переопределяем метод инициализации
     */
    async setup() {
        await super.setup();
        
        // Ограничиваем пустые строки при инициализации
        setTimeout(() => {
            this._limitEmptyRows();
        }, 100);
    }
}

// Регистрируем виджет
import { registry } from "@web/core/registry";

registry.category("view_widgets").add("single_line", SingleLineWidget);
