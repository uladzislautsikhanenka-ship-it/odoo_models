/** @odoo-module **/

// Простой модуль для автоматического заполнения поля salesperson в активности
console.log('Activity salesperson module loaded');

// Добавляем стили для поля salesperson
const style = document.createElement('style');
style.textContent = `
    .o_field_salesperson_id {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 8px;
    }
    
    .o_field_salesperson_id .o_field_many2one {
        width: 100%;
    }
`;
document.head.appendChild(style);

// Простая функция для автоматического заполнения
function autoFillSalesperson() {
    // Ищем форму активности
    const activityForm = document.querySelector('.o_activity_form, .o_form_view');
    if (!activityForm) return;
    
    // Ищем поле salesperson
    const salespersonField = activityForm.querySelector('input[name="salesperson_id"], select[name="salesperson_id"]');
    if (!salespersonField || salespersonField.value) return;
    
    // Получаем информацию о текущей записи из URL
    const urlParams = new URLSearchParams(window.location.search);
    const activeModel = urlParams.get('active_model') || urlParams.get('model');
    const activeId = urlParams.get('active_id') || urlParams.get('id');
    
    if (activeModel === 'sale.order' && activeId) {
        // Заполняем поле salesperson для заказа
        fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
            },
            body: JSON.stringify({
                model: 'sale.order',
                method: 'read',
                args: [parseInt(activeId)],
                kwargs: {
                    fields: ['user_id']
                }
            })
        })
        .then(response => response.json())
        .then(result => {
            if (result.result && result.result.length > 0 && result.result[0].user_id) {
                // Заполняем поле
                const userId = result.result[0].user_id[0];
                const userName = result.result[0].user_id[1];
                
                if (salespersonField.tagName === 'INPUT') {
                    salespersonField.value = userName;
                    salespersonField.dispatchEvent(new Event('input', { bubbles: true }));
                } else if (salespersonField.tagName === 'SELECT') {
                    salespersonField.value = userId;
                    salespersonField.dispatchEvent(new Event('change', { bubbles: true }));
                }
                
                console.log('Auto-filled salesperson:', userName);
            }
        })
        .catch(error => {
            console.warn('Error auto-filling salesperson:', error);
        });
    }
}

// Применяем автоматическое заполнение при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoFillSalesperson);
} else {
    autoFillSalesperson();
}

// Также применяем при изменении DOM
const observer = new MutationObserver((mutations) => {
    let shouldCheck = false;
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // Проверяем, добавилась ли форма активности
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && (
                    node.classList?.contains('o_activity_form') ||
                    node.querySelector?.('.o_activity_form') ||
                    node.classList?.contains('o_form_view') ||
                    node.querySelector?.('.o_field_salesperson_id')
                )) {
                    shouldCheck = true;
                }
            });
        }
    });
    
    if (shouldCheck) {
        setTimeout(autoFillSalesperson, 100);
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Экспортируем функцию для использования в других модулях
export { autoFillSalesperson };