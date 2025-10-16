/** @odoo-module **/

import { registry } from "@web/core/registry";

// Безопасный сервис для подсветки read-only полей
registry.category("services").add("readonly_highlighter", {
    start() {
        return {
            highlightReadonlyFields: () => {
                try {
                    // Проверяем, что DOM готов
                    if (!document.body) {
                        return;
                    }
                    
                    // Применяем стили к полям с классом o_field_readonly_highlight
                    const highlightedFields = document.querySelectorAll('.o_field_readonly_highlight');
                    highlightedFields.forEach(field => {
                        if (field && field.classList) {
                            field.classList.add('o_readonly_highlighted');
                            
                            // Добавляем иконку замка
                            if (!field.querySelector('.o_readonly_icon')) {
                                const icon = document.createElement('span');
                                icon.className = 'o_readonly_icon';
                                icon.innerHTML = '🔒';
                                icon.style.cssText = `
                                    position: absolute;
                                    left: 5px;
                                    top: 50%;
                                    transform: translateY(-50%);
                                    font-size: 12px;
                                    opacity: 0.7;
                                    pointer-events: none;
                                `;
                                field.style.position = 'relative';
                                field.appendChild(icon);
                            }
                        }
                    });
                } catch (error) {
                    console.warn('Error highlighting readonly fields:', error);
                }
            }
        };
    }
});

// Безопасное применение стилей
function safeHighlightReadonlyFields() {
    try {
        const service = registry.category("services").get("readonly_highlighter");
        if (service) {
            service.start().highlightReadonlyFields();
        }
    } catch (error) {
        console.warn('Error in readonly highlighter service:', error);
    }
}

// Применяем стили при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', safeHighlightReadonlyFields);
} else {
    safeHighlightReadonlyFields();
}

// Применяем стили при изменении DOM с задержкой
let timeoutId;
const observer = new MutationObserver((mutations) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
        safeHighlightReadonlyFields();
    }, 100);
});

// Начинаем наблюдение только когда DOM готов
if (document.body) {
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
} else {
    document.addEventListener('DOMContentLoaded', () => {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}