/** @odoo-module **/

console.log('Minimal date panel loaded');

// Функция размещения панели рядом с кнопкой Активности с учётом динамического DOM
function placeDatePanelNearActivity(dateString) {
    var activityBtn = document.querySelector('.o_control_panel .o_cp_switch_buttons .o_switch_view.o_activity');
    if (!activityBtn) {
        return false;
    }
    var node = document.getElementById('custom-date-panel-cp');
    if (!node) {
        node = document.createElement('span');
        node.id = 'custom-date-panel-cp';
        node.className = 'custom-date-panel-cp';
        node.addEventListener('click', function() {
            var nowClick = new Date();
            var dateUrl = 'https://www.timeanddate.com/worldclock/russia/moscow?iso=' +
                nowClick.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', 'T');
            window.open(dateUrl, '_blank');
        });
        if (activityBtn.parentNode) {
            activityBtn.parentNode.insertBefore(node, activityBtn.nextSibling);
        }
    }
    node.textContent = dateString;
    return true;
}

// Очень простая функция для обновления даты в CSS панели
function updateDatePanel() {
    try {
        // Получаем текущую дату
        var now = new Date();
        var options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        var dateString = '📅 ' + now.toLocaleDateString('ru-RU', options);
        
        // 1) Пытаемся расположить справа от переключателя вида "Активности"
        if (placeDatePanelNearActivity(dateString)) {
            return; // всё готово
        }

        // 2) Фолбэк: обновляем CSS переменную в верхней навигации (старый способ)
        // Ищем элементы верхней панели для обновления CSS переменной
        var elements = [
            document.querySelector('.o_main_navbar'),
            document.querySelector('.o_mail_systray'),
            document.querySelector('.o_navbar_right')
        ];
        
        elements.forEach(function(element) {
            if (element) {
                // Обновляем CSS переменную
                element.style.setProperty('--date-text', '"' + dateString + '"');
                
                // Добавляем клик если еще не добавлен
                if (!element.hasAttribute('data-click-added')) {
                    element.addEventListener('click', function(e) {
                        // Проверяем, что клик по псевдоэлементу (примерно)
                        var rect = element.getBoundingClientRect();
                        var clickX = e.clientX;
                        var clickY = e.clientY;
                        
                        // Если клик в правой части элемента (где псевдоэлемент)
                        if (clickX > rect.right - 160) {
                            var now = new Date();
                            var dateUrl = 'https://www.timeanddate.com/worldclock/russia/moscow?iso=' + 
                                         now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', 'T');
                            window.open(dateUrl, '_blank');
                            console.log('Date panel clicked - opened:', dateUrl);
                        }
                    });
                    element.setAttribute('data-click-added', 'true');
                }
            }
        });
    } catch (error) {
        console.warn('Error updating date panel:', error);
    }
}

// Обновляем дату при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(updateDatePanel, 1000);
    });
} else {
    setTimeout(updateDatePanel, 1000);
}

// Обновляем дату каждую минуту
setInterval(updateDatePanel, 60000);

// Наблюдаем за изменениями в панели управления, чтобы заново вставлять блок при смене вида
(function observeControlPanel() {
    var root = document.body;
    if (!root || !window.MutationObserver) {
        return;
    }
    var observer = new MutationObserver(function() {
        // Переустановим панель, если кнопка активности появилась или перерисовалась
        try {
            // Обновим сразу текст на текущий момент и вставим рядом с кнопкой
            var now = new Date();
            var options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
            var dateString = '📅 ' + now.toLocaleDateString('ru-RU', options);
            placeDatePanelNearActivity(dateString);
        } catch (e) {
            // тихо игнорируем
        }
    });
    observer.observe(root, { childList: true, subtree: true });
})();

console.log('Minimal date panel initialized');
