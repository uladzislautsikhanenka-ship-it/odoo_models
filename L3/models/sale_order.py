# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Переопределяем поле partner_id для изменения строкового представления
    partner_id = fields.Many2one(
        'res.partner', 
        string='Partner',
        required=True, 
        change_default=True, 
        index=True, 
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

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
