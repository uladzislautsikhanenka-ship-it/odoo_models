# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SplitOrderLinesWizard(models.TransientModel):
    _name = 'split.order.lines.wizard'
    _description = 'Wizard для разделения линий заказа'

    sale_order_id = fields.Many2one('sale.order', string='Заказ на продажу', required=True)
    line_ids = fields.One2many('split.order.lines.wizard.line', 'wizard_id', string='Линии для разделения')

    @api.model
    def default_get(self, fields_list):
        """Получаем контекст для создания wizard"""
        result = super().default_get(fields_list)
        
        # Получаем ID заказа из контекста
        sale_order_id = self.env.context.get('default_sale_order_id') or self.env.context.get('active_id')
        if sale_order_id:
            result['sale_order_id'] = sale_order_id
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Переопределяем create для создания wizard"""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Wizard create: vals_list = {vals_list}")
        
        wizards = super().create(vals_list)
        
        # Логируем созданные wizard
        for wizard in wizards:
            _logger.info(f"Wizard created: {wizard.id}, sale_order_id: {wizard.sale_order_id.id if wizard.sale_order_id else None}")
        
        return wizards

    def action_split_lines(self):
        """Выполняет разделение линий заказа"""
        self.ensure_one()
        
        if not self.line_ids:
            raise ValidationError(_('Нет линий для разделения'))
        
        # Проверяем корректность данных
        for line in self.line_ids:
            line._validate_split_data()
        
        # Подсчитываем общее количество новых линий, которые будут созданы
        total_new_lines = sum(line.number_of_splits for line in self.line_ids)
        original_lines_count = len(self.line_ids)
        
        # Выполняем разделение
        for line in self.line_ids:
            line._split_order_line()
        
        # Очищаем флажки Split в оставшихся линиях заказа
        if self.sale_order_id:
            remaining_lines = self.sale_order_id.order_line.filtered('split_line')
            if remaining_lines:
                remaining_lines.write({'split_line': False})
            
            # Записываем сообщение в чаттер
            self._post_split_message(original_lines_count, total_new_lines)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def _post_split_message(self, original_lines_count, total_new_lines):
        """Записывает сообщение о разделении в чаттер"""
        if not self.sale_order_id:
            return
        
        # Получаем имя текущего пользователя
        current_user = self.env.user
        user_name = current_user.name or current_user.login or 'Система'
        
        # Создаем красивое сообщение
        if original_lines_count == 1:
            lines_text = "линию"
        elif original_lines_count in [2, 3, 4]:
            lines_text = "линии"
        else:
            lines_text = "линий"
            
        if total_new_lines == 1:
            new_lines_text = "линию"
        elif total_new_lines in [2, 3, 4]:
            new_lines_text = "линии"
        else:
            new_lines_text = "линий"
        
        message = f"🔄 Разделено {original_lines_count} {lines_text} на {total_new_lines} {new_lines_text} пользователем {user_name}"
        
        # Записываем в чаттер
        self.sale_order_id.message_post(
            body=message,
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )


class SplitOrderLinesWizardLine(models.TransientModel):
    _name = 'split.order.lines.wizard.line'
    _description = 'Линия wizard для разделения заказа'

    wizard_id = fields.Many2one('split.order.lines.wizard', string='Wizard', required=True, ondelete='cascade')
    order_line_id = fields.Many2one('sale.order.line', string='Исходная линия заказа', required=True)
    product_id = fields.Many2one('product.product', string='Продукт', related='order_line_id.product_id', readonly=True)
    product_template_id = fields.Many2one('product.template', string='Шаблон продукта', related='order_line_id.product_template_id', readonly=True)
    product_name = fields.Char(string='Название продукта', related='order_line_id.product_template_id.name', readonly=True)
    original_quantity = fields.Float(string='Исходное количество', related='order_line_id.product_uom_qty', readonly=True)
    number_of_splits = fields.Integer(string='Количество разделений', default=1, required=True)
    split_quantities = fields.Text(string='Количества для разделения', 
                                   help='Введите количества через запятую (например: 2,3,1)')
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('order_line_id', 'product_template_id')
    def _compute_display_name(self):
        """Вычисляем отображаемое имя для записи"""
        for record in self:
            if record.product_template_id:
                record.display_name = record.product_template_id.name
            elif record.order_line_id:
                record.display_name = f"Line {record.order_line_id.id}"
            else:
                record.display_name = "Unknown"
    
    @api.model_create_multi
    def create(self, vals_list):
        """Переопределяем create для дополнительных проверок"""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"WizardLine create: vals_list = {vals_list}")
        
        # Проверяем каждую запись
        for vals in vals_list:
            if not vals.get('order_line_id'):
                _logger.warning("WizardLine create: order_line_id not provided in vals")
        
        wizard_lines = super().create(vals_list)
        _logger.info(f"WizardLine created: {len(wizard_lines)} lines")
        
        return wizard_lines
    
    @api.onchange('number_of_splits', 'original_quantity')
    def _onchange_number_of_splits(self):
        """Автоматически генерирует количества при изменении количества разделений"""
        if self.number_of_splits > 0 and self.original_quantity > 0:
            # Равномерно распределяем количество
            base_quantity = self.original_quantity / self.number_of_splits
            quantities = []
            total_allocated = 0
            
            for i in range(self.number_of_splits):
                if i == self.number_of_splits - 1:
                    # Последняя часть получает остаток для избежания ошибок округления
                    remaining = self.original_quantity - total_allocated
                    quantities.append(str(round(remaining, 3)))
                else:
                    allocated = round(base_quantity, 3)
                    quantities.append(str(allocated))
                    total_allocated += allocated
            
            self.split_quantities = ','.join(quantities)

    def _validate_split_data(self):
        """Проверяет корректность данных для разделения"""
        if self.number_of_splits <= 0:
            raise ValidationError(_('Количество разделений должно быть больше 0'))
        
        if not self.split_quantities:
            raise ValidationError(_('Не указаны количества для разделения'))
        
        try:
            quantities = [float(q.strip()) for q in self.split_quantities.split(',')]
        except ValueError:
            raise ValidationError(_('Некорректный формат количеств. Используйте числа через запятую'))
        
        if len(quantities) != self.number_of_splits:
            raise ValidationError(_('Количество значений не соответствует количеству разделений'))
        
        if any(q <= 0 for q in quantities):
            raise ValidationError(_('Все количества должны быть больше 0'))
        
        if abs(sum(quantities) - self.original_quantity) > 0.001:
            raise ValidationError(_('Сумма количеств должна равняться исходному количеству (%s)') % self.original_quantity)

    def _split_order_line(self):
        """Выполняет разделение линии заказа"""
        import logging
        _logger = logging.getLogger(__name__)
        
        self._validate_split_data()
        
        quantities = [float(q.strip()) for q in self.split_quantities.split(',')]
        
        # Создаем новые линии на основе исходной
        original_line = self.order_line_id
        new_lines = []
        
        _logger.info(f"Splitting line {original_line.id}: product_id={original_line.product_id.id}, product_template_id={original_line.product_template_id.id}")
        
        for i, quantity in enumerate(quantities):
            line_vals = {
                'order_id': original_line.order_id.id,
                'product_id': original_line.product_id.id,
                'product_template_id': original_line.product_template_id.id,
                'name': original_line.name,
                'product_uom_qty': quantity,
                'product_uom': original_line.product_uom.id,
                'price_unit': original_line.price_unit,
                'tax_id': [(6, 0, original_line.tax_id.ids)],
                'discount': original_line.discount,
                'express_delivery': original_line.express_delivery,
                'split_line': False,  # Новые линии не помечены для разделения
                'sequence': original_line.sequence,  # Сохраняем последовательность
                'display_type': original_line.display_type,  # Сохраняем тип отображения
            }
            
            _logger.info(f"Creating new line {i+1} with vals: {line_vals}")
            
            try:
                # Создаем линию с контекстом разделения, чтобы обойти ограничения дублирования
                new_line = self.env['sale.order.line'].with_context(split_operation=True).create(line_vals)
                new_lines.append(new_line)
                _logger.info(f"Created new line {new_line.id}: product_id={new_line.product_id.id}")
            except Exception as e:
                _logger.error(f"Error creating new line: {e}")
                raise ValidationError(_('Ошибка создания новой линии: %s') % str(e))
        
        # Удаляем исходную линию с контекстом разделения
        _logger.info(f"Deleting original line {original_line.id}")
        original_line.with_context(split_operation=True).unlink()
        
        return new_lines
