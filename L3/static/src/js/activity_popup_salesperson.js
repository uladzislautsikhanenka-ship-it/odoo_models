/** @odoo-module **/

console.log('Activity popup salesperson module loaded');

// Функция для добавления информации о salesperson во всплывающее окно
function addSalespersonToPopup() {
    // Ищем всплывающие окна активностей с различными селекторами
    const popupSelectors = [
        '.o_popover:not([style*="display: none"])',
        '.popover:not([style*="display: none"])',
        '.o_activity_popup:not([style*="display: none"])',
        '.tooltip:not([style*="display: none"])',
        '.dropdown-menu:not([style*="display: none"])',
        '.o_dropdown_menu:not([style*="display: none"])'
    ];
    
    popupSelectors.forEach(selector => {
        const popups = document.querySelectorAll(selector);
        
        popups.forEach(popup => {
            // Проверяем, что это всплывающее окно активности
            if (isActivityPopup(popup)) {
                // Проверяем, не добавлена ли уже информация о salesperson
                if (!popup.querySelector('.salesperson-info')) {
                    addSalespersonInfo(popup);
                }
            }
        });
    });
}

// Функция для определения, является ли всплывающее окно окном активности
function isActivityPopup(popup) {
    const text = popup.textContent.toLowerCase();
    const hasActivityText = text.includes('schedule activities') || 
                           text.includes('schedule an activity') ||
                           text.includes('activity') ||
                           text.includes('запланировать') ||
                           text.includes('активность');
    
    const hasActivityButton = popup.querySelector('button[title*="activity"], .btn[title*="activity"], [data-action*="activity"]');
    const hasActivityClass = popup.classList.contains('o_activity_popup') ||
                            popup.classList.contains('activity-popup');
    
    return hasActivityText || hasActivityButton || hasActivityClass;
}

// Функция для добавления информации о salesperson
function addSalespersonInfo(popup) {
    // Получаем информацию о текущей строке таблицы
    const tableRow = getCurrentTableRow();
    if (!tableRow) return;
    
    // Получаем информацию о salesperson из строки
    const salespersonInfo = getSalespersonFromRow(tableRow);
    if (!salespersonInfo) return;
    
    // Создаем элемент с информацией о salesperson
    const salespersonDiv = document.createElement('div');
    salespersonDiv.className = 'salesperson-info';
    salespersonDiv.style.cssText = `
        margin: 8px 0;
        padding: 8px;
        background-color: #f8f9fa;
        border-radius: 4px;
        border-left: 3px solid #007bff;
        font-size: 13px;
        color: #495057;
    `;
    
    // Создаем HTML для отображения salesperson
    salespersonDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #007bff; 
                        display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">
                ${salespersonInfo.avatar || '👤'}
            </div>
            <div>
                <div style="font-weight: 500; color: #007bff;">Salesperson:</div>
                <div style="font-size: 12px; color: #6c757d;">${salespersonInfo.name}</div>
            </div>
        </div>
    `;
    
    // Добавляем элемент в всплывающее окно
    const content = popup.querySelector('.popover-body, .tooltip-inner, .o_popover_content');
    if (content) {
        // Вставляем перед кнопкой "Schedule an activity"
        const button = content.querySelector('button, .btn, [title*="Schedule"]');
        if (button) {
            button.parentNode.insertBefore(salespersonDiv, button);
        } else {
            content.appendChild(salespersonDiv);
        }
    } else {
        // Если нет специального контейнера, добавляем в начало
        popup.insertBefore(salespersonDiv, popup.firstChild);
    }
}

// Функция для получения текущей строки таблицы
function getCurrentTableRow() {
    // Ищем строку таблицы, над которой находится всплывающее окно
    const popup = document.querySelector('.o_popover:not([style*="display: none"]), .popover:not([style*="display: none"]), .tooltip:not([style*="display: none"])');
    if (!popup) return null;
    
    // Получаем позицию всплывающего окна
    const popupRect = popup.getBoundingClientRect();
    
    // Ищем строки таблицы
    const tableRows = document.querySelectorAll('tr[data-id], .o_data_row');
    
    // Находим строку, которая находится под всплывающим окном
    for (const row of tableRows) {
        const rowRect = row.getBoundingClientRect();
        
        // Проверяем, пересекается ли строка с всплывающим окном
        if (rowRect.top <= popupRect.bottom && rowRect.bottom >= popupRect.top) {
            return row;
        }
    }
    
    return null;
}

// Функция для получения информации о salesperson из строки таблицы
function getSalespersonFromRow(row) {
    // Различные селекторы для поиска колонки с salesperson
    const salespersonSelectors = [
        '[data-name="user_id"]',
        '.o_field_salesperson',
        '.o_salesperson_cell',
        '.o_field_many2one[data-name="user_id"]',
        '.o_data_cell[data-name="user_id"]',
        'td[data-name="user_id"]'
    ];
    
    // Ищем колонку с salesperson
    let salespersonCell = null;
    for (const selector of salespersonSelectors) {
        salespersonCell = row.querySelector(selector);
        if (salespersonCell) break;
    }
    
    if (salespersonCell) {
        // Получаем аватар
        const avatarSelectors = ['img', '.o_avatar', '.avatar', '.o_user_avatar'];
        let avatar = null;
        let avatarSrc = null;
        
        for (const selector of avatarSelectors) {
            avatar = salespersonCell.querySelector(selector);
            if (avatar) {
                avatarSrc = avatar.src || avatar.style.backgroundImage;
                break;
            }
        }
        
        // Получаем имя
        const nameSelectors = ['.o_field_char', '.o_input', '.o_field_text', 'span', 'div', '.o_data_cell'];
        let name = 'Unknown';
        
        for (const selector of nameSelectors) {
            const nameElement = salespersonCell.querySelector(selector);
            if (nameElement && nameElement.textContent.trim()) {
                name = nameElement.textContent.trim();
                break;
            }
        }
        
        return {
            name: name,
            avatar: avatarSrc
        };
    }
    
    // Альтернативный способ - поиск по позиции колонки (обычно salesperson в определенной позиции)
    const cells = row.querySelectorAll('td, .o_data_cell');
    const salespersonPosition = 4; // Примерная позиция колонки salesperson (0-based)
    
    if (cells.length > salespersonPosition) {
        const salespersonCell = cells[salespersonPosition];
        const text = salespersonCell.textContent.trim();
        
        // Проверяем, содержит ли ячейка имя пользователя
        if (text && text.length > 2 && text.length < 50 && 
            !text.match(/^\d+$/) && 
            !text.includes('@') &&
            !text.match(/\d{2}\/\d{2}\/\d{4}/) && 
            !text.match(/^S\d+$/) &&
            !text.match(/^\d{2}:\d{2}/)) {
            
            // Ищем аватар в этой ячейке
            const avatar = salespersonCell.querySelector('img, .o_avatar, .avatar');
            const avatarSrc = avatar ? avatar.src || avatar.style.backgroundImage : null;
            
            return {
                name: text,
                avatar: avatarSrc
            };
        }
    }
    
    return null;
}

// Функция для отслеживания появления всплывающих окон
function observePopups() {
    // Создаем наблюдатель за изменениями DOM
    const observer = new MutationObserver((mutations) => {
        let shouldCheck = false;
        
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && (
                        node.classList?.contains('o_popover') ||
                        node.classList?.contains('popover') ||
                        node.classList?.contains('tooltip') ||
                        node.querySelector?.('.o_popover, .popover, .tooltip')
                    )) {
                        shouldCheck = true;
                    }
                });
            }
        });
        
        if (shouldCheck) {
            // Небольшая задержка для полной загрузки всплывающего окна
            setTimeout(addSalespersonToPopup, 100);
        }
    });
    
    // Начинаем наблюдение
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(observePopups, 1000);
        setTimeout(addSalespersonToPopup, 1500);
    });
} else {
    setTimeout(observePopups, 1000);
    setTimeout(addSalespersonToPopup, 1500);
}

// Также проверяем при изменении размера окна или прокрутке
window.addEventListener('resize', () => {
    setTimeout(addSalespersonToPopup, 100);
});

window.addEventListener('scroll', () => {
    setTimeout(addSalespersonToPopup, 100);
});

console.log('Activity popup salesperson module initialized');
