# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Переопределяем поле partner_id для изменения строкового представления
    partner_id = fields.Many2one(
        'res.partner', 
        string='Partner',
        required=False,  # Убираем required=True чтобы не было красной подсветки
        change_default=True, 
        index=True, 
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Автоматически заполняем адреса при выборе партнера"""
        if self.partner_id:
            # Автоматически заполняем адреса
            self.partner_invoice_id = self.partner_id
            self.partner_shipping_id = self.partner_id
        else:
            # Очищаем адреса если партнер не выбран
            self.partner_invoice_id = False
            self.partner_shipping_id = False
        return super()._onchange_partner_id() if hasattr(super(), '_onchange_partner_id') else {}

    @api.model
    def _get_excluded_product_template_ids(self, order_id=None, exclude_line_id=None):
        if not order_id:
            return []
        
        order = self.browse(order_id)
        if not order.exists():
            return []
        
       
        domain = [
            ('order_id', '=', order_id),
            ('product_template_id', '!=', False),
            ('display_type', '=', False)
        ]
        if exclude_line_id:
            domain.append(('id', '!=', exclude_line_id))
        
        excluded_lines = self.env['sale.order.line'].search(domain)
        excluded_ids = excluded_lines.mapped('product_template_id.id')
        
        return excluded_ids

    def get_available_products_domain(self, exclude_line_id=None):
        excluded_ids = self._get_excluded_product_template_ids(self.id, exclude_line_id)
        domain = [('sale_ok', '=', True)]
        if excluded_ids:
            domain.append(('id', 'not in', excluded_ids))
        return domain

    def action_split_order_lines(self):
        """Открывает wizard для разделения выбранных линий заказа"""
        self.ensure_one()
        
        import logging
        _logger = logging.getLogger(__name__)
        
        # Принудительно сохраняем изменения в базе данных
        self.env.flush_all()
        
        # Получаем все линии заказа и логируем их состояние
        all_lines = self.order_line
        _logger.info(f"Order {self.name}: total lines = {len(all_lines)}")
        
        for line in all_lines:
            _logger.info(f"Line {line.id}: product={line.product_template_id.name if line.product_template_id else 'No product'}, split_line={line.split_line}")
        
        # Получаем линии, отмеченные для разделения
        lines_to_split = self.order_line.filtered('split_line')
        _logger.info(f"Order {self.name}: found {len(lines_to_split)} lines with split_line=True")
        
        if not lines_to_split:
            raise ValidationError(_('Не выбраны линии для разделения. Отметьте линии флажком Split.'))
        
        # Создаем wizard напрямую с выбранными линиями
        wizard_vals = {
            'sale_order_id': self.id,
        }
        
        wizard = self.env['split.order.lines.wizard'].create(wizard_vals)
        
        # Создаем линии wizard
        for line in lines_to_split:
            line_vals = {
                'wizard_id': wizard.id,
                'order_line_id': line.id,
            }
            self.env['split.order.lines.wizard.line'].create(line_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Разделить линии заказа'),
            'res_model': 'split.order.lines.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }
    
    def action_split_selected_lines(self):
        """Алиас для action_split_order_lines (для совместимости со старыми представлениями)"""
        return self.action_split_order_lines()
    
    def action_clear_split_flags(self):
        """Очищает все флажки Split в линиях заказа"""
        self.ensure_one()
        self.order_line.write({'split_line': False})
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def action_debug_split_flags(self):
        """Отладочный метод для проверки флажков Split"""
        self.ensure_one()
        split_lines = self.order_line.filtered('split_line')
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Debug: Order {self.name} has {len(split_lines)} lines with split_line=True")
        for line in split_lines:
            _logger.info(f"Debug: Line {line.id} - {line.product_template_id.name if line.product_template_id else 'No product'} - split_line={line.split_line}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug Split Flags',
                'message': f'Found {len(split_lines)} lines with split_line=True',
                'type': 'info',
            }
        }

    @api.model
    def default_get(self, fields_list):
        """Переопределяем default_get для полного отключения пустых строк"""
        result = super().default_get(fields_list)
        
        # Полностью отключаем создание пустых строк в order_line
        if 'order_line' in fields_list:
            result['order_line'] = []
        
        return result

    @api.model
    def _get_default_order_line(self):
        """Переопределяем метод для полного отключения пустых строк"""
        # Не создаем никаких пустых строк
        return []

    @api.onchange('order_line')
    def _onchange_order_line_limit(self):
        """Ограничиваем количество пустых строк в order_line до одной"""
        if self.order_line:
            # Считаем пустые строки (без product_id)
            empty_lines = self.order_line.filtered(lambda l: not l.product_id)
            
            if len(empty_lines) > 1:
                # Оставляем только первую пустую строку
                lines_to_remove = empty_lines[1:]
                for line in lines_to_remove:
                    self.order_line = [(2, line.id, 0)]
                
                return {
                    'warning': {
                        'title': 'Ограничение строк',
                        'message': 'Можно создать только одну пустую строку в Order Lines. Лишние строки были удалены.',
                    }
                }

    @api.model
    def _get_default_order_line(self):
        """Переопределяем метод для полного отключения пустых строк"""
        # Не создаем никаких пустых строк
        return []

    @api.model
    def create(self, vals):
        """Переопределяем create для валидации обязательных полей"""
        # Проверяем partner_id перед созданием
        if not vals.get('partner_id'):
            raise ValidationError(_('Поле Partner обязательно для заполнения. Пожалуйста, выберите партнера.'))
        
        # Автоматически заполняем адреса если не указаны
        if vals.get('partner_id') and not vals.get('partner_invoice_id'):
            vals['partner_invoice_id'] = vals['partner_id']
        if vals.get('partner_id') and not vals.get('partner_shipping_id'):
            vals['partner_shipping_id'] = vals['partner_id']
        
        # Ограничиваем количество пустых строк в order_line
        if 'order_line' in vals and not self.env.context.get('skip_empty_line_limit'):
            order_lines = vals.get('order_line', [])
            if order_lines:
                # Фильтруем пустые строки (без product_id)
                empty_lines = [line for line in order_lines if isinstance(line, (list, tuple)) and len(line) >= 2 and line[0] == 0 and not line[2].get('product_id')]
                filled_lines = [line for line in order_lines if isinstance(line, (list, tuple)) and len(line) >= 2 and line[0] == 0 and line[2].get('product_id')]
                
                # Оставляем только одну пустую строку
                if len(empty_lines) > 1:
                    vals['order_line'] = [empty_lines[0]] + filled_lines
                elif len(empty_lines) == 1:
                    vals['order_line'] = empty_lines + filled_lines
            
        return super().create(vals)

    @api.model
    def _get_default_order_line(self):
        """Переопределяем метод для полного отключения пустых строк"""
        # Не создаем никаких пустых строк
        return []

    def write(self, vals):
        """Переопределяем write для валидации обязательных полей"""
        # Проверяем partner_id только если он изменяется и становится пустым
        if 'partner_id' in vals and not vals['partner_id']:
            raise ValidationError(_('Поле Partner обязательно для заполнения. Пожалуйста, выберите партнера.'))
        
        # Автоматически заполняем адреса при изменении партнера
        if vals.get('partner_id'):
            if not vals.get('partner_invoice_id'):
                vals['partner_invoice_id'] = vals['partner_id']
            if not vals.get('partner_shipping_id'):
                vals['partner_shipping_id'] = vals['partner_id']
        
        return super().write(vals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_template_id')
    def _onchange_product_template_id_exclude_selected(self):
        if not self.product_template_id or not self.order_id:
            return
        
        excluded_ids = self.order_id._get_excluded_product_template_ids(
            self.order_id.id, 
            self.id if self.id else None
        )
        
        if self.product_template_id.id in excluded_ids:
            self.product_template_id = False
            return {
                'warning': {
                    'title': 'Product Template Already Selected',
                    'message': 'This product template is already selected in another line of this order.'
                }
            }




    @api.model
    def _get_product_template_domain(self):
        domain = super()._get_product_domain() if hasattr(super(), '_get_product_domain') else []
        
        order_id = self._context.get('default_order_id') or (self.order_id.id if self.order_id else None)
        line_id = self._context.get('default_id') or (self.id if self.id else None)
        
        if order_id:
            excluded_ids = self.env['sale.order']._get_excluded_product_template_ids(order_id, line_id)
            if excluded_ids:
                domain.append(('id', 'not in', excluded_ids))
        
        return domain

    @api.model_create_multi
    def create(self, vals_list):
        # Ограничиваем количество пустых строк до одной
        if not self.env.context.get('skip_empty_line_limit'):
            # Проверяем, создаются ли пустые строки (без product_id)
            empty_lines = [vals for vals in vals_list if not vals.get('product_id') and not vals.get('product_template_id')]
            
            if empty_lines:
                # Получаем order_id из контекста или из vals
                order_id = self.env.context.get('default_order_id')
                if not order_id and vals_list:
                    order_id = vals_list[0].get('order_id')
                
                if order_id:
                    # Считаем существующие пустые строки в заказе
                    order = self.env['sale.order'].browse(order_id)
                    existing_empty_lines = order.order_line.filtered(
                        lambda l: not l.product_id and not l.product_template_id
                    )
                    
                    # Если уже есть пустые строки, не создаем новые
                    if existing_empty_lines:
                        return self.env['sale.order.line']
                    
                    # Ограничиваем до одной пустой строки
                    if len(empty_lines) > 1:
                        vals_list = [empty_lines[0]] + [vals for vals in vals_list if vals.get('product_id') or vals.get('product_template_id')]
        
        lines = super().create(vals_list)
        for line in lines:
            if line.product_template_id and line.order_id:
                # Проверяем, не создается ли линия в процессе разделения
                is_split_operation = self.env.context.get('split_operation', False)
                if not is_split_operation:
                    excluded_ids = line.order_id._get_excluded_product_template_ids(line.order_id.id, line.id)
                    if line.product_template_id.id in excluded_ids:
                        raise models.ValidationError(
                            'Product Template "%s" is already selected in another line of this order.' % 
                            line.product_template_id.name
                        )
        return lines

    def write(self, vals):
        if 'product_template_id' in vals and vals['product_template_id']:
            # Проверяем, не выполняется ли операция разделения
            is_split_operation = self.env.context.get('split_operation', False)
            if not is_split_operation:
                for line in self:
                    if line.order_id:
                        excluded_ids = line.order_id._get_excluded_product_template_ids(line.order_id.id, line.id)
                        if vals['product_template_id'] in excluded_ids:
                            product_template = self.env['product.template'].browse(vals['product_template_id'])
                            raise models.ValidationError(
                                'Product Template "%s" is already selected in another line of this order.' % 
                                product_template.name
                            )
        return super().write(vals)
