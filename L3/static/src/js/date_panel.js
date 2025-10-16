/** @odoo-module **/

console.log('Date panel module loaded');

// Получаем настройки панели даты
var datePanelSettings = {
    enabled: true,
    format: 'short',
    timezone: 'Europe/Moscow',
    linkUrl: 'https://www.timeanddate.com/worldclock/russia/moscow'
};

// Функция для получения настроек с сервера
function loadDatePanelSettings() {
    try {
        // Используем jQuery для совместимости с Odoo
        if (typeof $ !== 'undefined') {
            $.ajax({
                url: '/web/dataset/call_kw',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    model: 'ir.config_parameter',
                    method: 'get_date_panel_settings',
                    args: [],
                    kwargs: {}
                }),
                success: function(result) {
                    if (result.result) {
                        datePanelSettings = result.result;
                    }
                },
                error: function() {
                    console.warn('Could not load date panel settings, using defaults');
                }
            });
        }
    } catch (error) {
        console.warn('Could not load date panel settings, using defaults:', error);
    }
}

// Функция для создания панели даты
function createDatePanel() {
    // Проверяем, включена ли панель даты
    if (!datePanelSettings.enabled) {
        console.log('Date panel is disabled in settings');
        return;
    }
    // Ищем иконку часов в верхней панели
    const clockIcon = document.querySelector('.o_mail_activity, .o_mail_systray_item, [data-menu-xmlid*="mail"], .fa-clock-o, .fa-clock');
    
    if (!clockIcon) {
        console.log('Clock icon not found, trying alternative selectors...');
        // Альтернативные селекторы для поиска иконки часов
        const alternativeSelectors = [
            '.o_mail_systray_item',
            '.o_mail_activity',
            '.o_mail_systray',
            '[title*="activity"]',
            '[title*="mail"]',
            '.fa-clock',
            '.fa-clock-o'
        ];
        
        for (const selector of alternativeSelectors) {
            const element = document.querySelector(selector);
            if (element) {
                console.log('Found element with selector:', selector);
                break;
            }
        }
    }
    
    // Создаем панель даты
    const datePanel = document.createElement('div');
    datePanel.id = 'custom-date-panel';
    datePanel.className = 'custom-date-panel';
    
    // Функция для обновления даты
    function updateDate() {
        const now = new Date();
        
        // Настройки формата в зависимости от параметра
        let options;
        switch (datePanelSettings.format) {
            case 'full':
                options = {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    weekday: 'long'
                };
                break;
            case 'medium':
                options = {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                };
                break;
            default: // 'short'
                options = {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                };
        }
        
        const dateString = now.toLocaleDateString('ru-RU', options);
        datePanel.textContent = dateString;
        datePanel.title = `Текущая дата и время: ${now.toLocaleString('ru-RU')}`;
    }
    
    // Обновляем дату каждую минуту
    updateDate();
    setInterval(updateDate, 60000);
    
    // Добавляем обработчик клика
    datePanel.addEventListener('click', function() {
        const now = new Date();
        
        // Создаем ссылку с датой и временем используя настройки
        let dateUrl = datePanelSettings.linkUrl;
        if (dateUrl.includes('timeanddate.com')) {
            dateUrl = `${dateUrl}?iso=${now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', 'T')}`;
        }
        
        // Открываем ссылку в новой вкладке
        window.open(dateUrl, '_blank');
        
        // Показываем уведомление
        showNotification('Открыта ссылка с текущей датой и временем', 'info');
    });
    
    // Добавляем панель в верхнюю панель
    const topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar) {
        // Ищем место для вставки (справа от иконки часов)
        const systray = document.querySelector('.o_mail_systray, .o_systray, .o_main_navbar_header .o_navbar_right');
        if (systray) {
            systray.insertBefore(datePanel, systray.firstChild);
        } else {
            topBar.appendChild(datePanel);
        }
        console.log('Date panel added to top bar');
    } else {
        console.warn('Top bar not found');
    }
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `custom-notification custom-notification-${type}`;
    notification.textContent = message;
    
    // Добавляем стили
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'info' ? '#007bff' : '#28a745'};
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 9999;
        font-size: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-out;
    `;
    
    // Добавляем анимацию
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Убираем уведомление через 3 секунды
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Применяем создание панели даты при загрузке страницы
function initializeDatePanel() {
    loadDatePanelSettings();
    // Небольшая задержка для загрузки настроек
    setTimeout(createDatePanel, 100);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDatePanel);
} else {
    initializeDatePanel();
}

// Также применяем при изменении DOM (для SPA навигации)
const observer = new MutationObserver((mutations) => {
    let shouldCreate = false;
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && (
                    node.classList?.contains('o_main_navbar') ||
                    node.querySelector?.('.o_main_navbar') ||
                    node.classList?.contains('navbar') ||
                    node.querySelector?.('.o_mail_systray')
                )) {
                    shouldCreate = true;
                }
            });
        }
    });
    
    if (shouldCreate && !document.getElementById('custom-date-panel')) {
        setTimeout(createDatePanel, 100);
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Экспортируем функции для использования в других модулях
export { createDatePanel, showNotification };
