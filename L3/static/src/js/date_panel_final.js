/** @odoo-module **/

console.log('Date panel final module loaded');

// Простая функция для создания панели даты
function createDatePanel() {
    // Проверяем, не создана ли уже панель
    if (document.getElementById('custom-date-panel')) {
        return;
    }
    
    console.log('Creating date panel...');
    
    // Создаем панель даты
    var datePanel = document.createElement('div');
    datePanel.id = 'custom-date-panel';
    datePanel.className = 'custom-date-panel';
    
    // Функция для обновления даты
    function updateDate() {
        var now = new Date();
        var options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        var dateString = now.toLocaleDateString('ru-RU', options);
        datePanel.textContent = dateString;
        datePanel.title = 'Текущая дата и время: ' + now.toLocaleString('ru-RU');
    }
    
    // Обновляем дату каждую минуту
    updateDate();
    setInterval(updateDate, 60000);
    
    // Добавляем обработчик клика
    datePanel.addEventListener('click', function() {
        var now = new Date();
        var dateUrl = 'https://www.timeanddate.com/worldclock/russia/moscow?iso=' + 
                     now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', 'T');
        
        // Открываем ссылку в новой вкладке
        window.open(dateUrl, '_blank');
        
        // Показываем уведомление
        showNotification('Открыта ссылка с текущей датой и временем');
    });
    
    // Ищем место для вставки в верхней панели
    var topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar) {
        // Ищем системный трей (где обычно иконки)
        var systray = document.querySelector('.o_mail_systray, .o_systray, .o_main_navbar_header .o_navbar_right, .o_navbar_right');
        if (systray) {
            // Вставляем перед первым элементом в системном трее
            systray.insertBefore(datePanel, systray.firstChild);
            console.log('Date panel added to systray');
        } else {
            // Если системный трей не найден, добавляем в конец верхней панели
            topBar.appendChild(datePanel);
            console.log('Date panel added to top bar');
        }
    } else {
        console.warn('Top bar not found');
    }
}

// Функция для показа уведомлений
function showNotification(message) {
    // Создаем уведомление
    var notification = document.createElement('div');
    notification.className = 'custom-notification';
    notification.textContent = message;
    
    // Добавляем стили
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #007bff; color: white; padding: 12px 20px; border-radius: 4px; z-index: 9999; font-size: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);';
    
    document.body.appendChild(notification);
    
    // Убираем уведомление через 3 секунды
    setTimeout(function() {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Функция для поиска и вставки панели
function tryCreatePanel() {
    // Ищем верхнюю панель
    var topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar && !document.getElementById('custom-date-panel')) {
        console.log('Found top bar, creating panel...');
        createDatePanel();
    }
}

// Применяем создание панели при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(tryCreatePanel, 1000);
    });
} else {
    setTimeout(tryCreatePanel, 1000);
}

// Также пытаемся создать панель при изменении DOM
var observer = new MutationObserver(function(mutations) {
    var shouldTry = false;
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    // Проверяем, добавилась ли верхняя панель
                    if (node.classList && (
                        node.classList.contains('o_main_navbar') ||
                        node.classList.contains('navbar') ||
                        node.classList.contains('o_main_navbar_header')
                    )) {
                        shouldTry = true;
                    }
                    // Проверяем, добавился ли системный трей
                    if (node.querySelector && (
                        node.querySelector('.o_main_navbar') ||
                        node.querySelector('.o_mail_systray') ||
                        node.querySelector('.o_navbar_right')
                    )) {
                        shouldTry = true;
                    }
                }
            });
        }
    });
    
    if (shouldTry && !document.getElementById('custom-date-panel')) {
        setTimeout(tryCreatePanel, 500);
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log('Date panel module initialized');

