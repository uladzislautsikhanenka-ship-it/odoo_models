/** @odoo-module **/

// Безопасная версия JavaScript для активности
// Этот файл содержит только базовую функциональность без сложных операций

console.log('Safe activity salesperson module loaded');

// Простая функция для логирования
function logActivityInfo() {
    console.log('Activity salesperson module is working');
}

// Экспортируем функцию
export { logActivityInfo };

// Применяем функцию при загрузке
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', logActivityInfo);
} else {
    logActivityInfo();
}



