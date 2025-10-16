/** @odoo-module **/

console.log('Simple date panel module loaded');

// Простая функция для создания панели даты
function createSimpleDatePanel() {
    // Проверяем, не создана ли уже панель
    if (document.getElementById('custom-date-panel')) {
        return;
    }
    
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
        
        // Показываем простое уведомление
        console.log('Открыта ссылка с текущей датой и временем');
    });
    
    // Ищем место для вставки в верхней панели
    var topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar) {
        var systray = document.querySelector('.o_mail_systray, .o_systray, .o_main_navbar_header .o_navbar_right');
        if (systray) {
            systray.insertBefore(datePanel, systray.firstChild);
        } else {
            topBar.appendChild(datePanel);
        }
        console.log('Simple date panel added to top bar');
    } else {
        console.warn('Top bar not found');
    }
}

// Функция для поиска и вставки панели с задержкой
function tryCreatePanel() {
    // Ищем верхнюю панель
    var topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar && !document.getElementById('custom-date-panel')) {
        createSimpleDatePanel();
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
                if (node.nodeType === 1 && (
                    node.classList && (
                        node.classList.contains('o_main_navbar') ||
                        node.classList.contains('navbar')
                    ) ||
                    node.querySelector && (
                        node.querySelector('.o_main_navbar') ||
                        node.querySelector('.o_mail_systray')
                    )
                )) {
                    shouldTry = true;
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

// Экспортируем функцию для использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createSimpleDatePanel };
}

