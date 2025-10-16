/** @odoo-module **/

console.log('Ultra simple date panel loaded');

// Очень простая функция для создания панели даты
function createDatePanel() {
    // Проверяем, не создана ли уже панель
    if (document.getElementById('custom-date-panel')) {
        return;
    }
    
    console.log('Creating ultra simple date panel...');
    
    // Создаем панель даты
    var datePanel = document.createElement('div');
    datePanel.id = 'custom-date-panel';
    datePanel.style.cssText = 'display: inline-block; padding: 8px 12px; margin: 0 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.2); text-align: center; min-width: 140px; position: relative; overflow: hidden;';
    
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
        
        console.log('Date panel clicked - opened:', dateUrl);
    });
    
    // Добавляем эффект при наведении
    datePanel.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-1px)';
        this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
    });
    
    datePanel.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    });
    
    // Ищем место для вставки в верхней панели
    var topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar) {
        // Ищем системный трей (где обычно иконки)
        var systray = document.querySelector('.o_mail_systray, .o_systray, .o_main_navbar_header .o_navbar_right, .o_navbar_right');
        if (systray) {
            // Вставляем перед первым элементом в системном трее
            systray.insertBefore(datePanel, systray.firstChild);
            console.log('Ultra simple date panel added to systray');
        } else {
            // Если системный трей не найден, добавляем в конец верхней панели
            topBar.appendChild(datePanel);
            console.log('Ultra simple date panel added to top bar');
        }
    } else {
        console.warn('Top bar not found');
    }
}

// Функция для поиска и вставки панели
function tryCreatePanel() {
    // Ищем верхнюю панель
    var topBar = document.querySelector('.o_main_navbar, .navbar, .o_main_navbar_header');
    if (topBar && !document.getElementById('custom-date-panel')) {
        console.log('Found top bar, creating ultra simple panel...');
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

console.log('Ultra simple date panel module initialized');

