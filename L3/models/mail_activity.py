# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    # Добавляем поле для связи с продавцом
    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        help='Salesperson associated with this activity'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Переопределяем создание активности для автоматического заполнения salesperson"""
        for vals in vals_list:
            # Если активность создается для sale.order или sale.order.line
            if 'res_model' in vals and vals['res_model'] in ['sale.order', 'sale.order.line']:
                # Получаем запись, для которой создается активность
                res_id = vals.get('res_id')
                if res_id:
                    record = self.env[vals['res_model']].browse(res_id)
                    
                    # Если это sale.order, берем user_id
                    if vals['res_model'] == 'sale.order' and hasattr(record, 'user_id') and record.user_id:
                        vals['salesperson_id'] = record.user_id.id
                    
                    # Если это sale.order.line, берем user_id из order_id
                    elif vals['res_model'] == 'sale.order.line' and hasattr(record, 'order_id') and record.order_id.user_id:
                        vals['salesperson_id'] = record.order_id.user_id.id
        
        return super().create(vals_list)

    @api.model
    def _get_salesperson_from_record(self, res_model, res_id):
        """Получаем продавца из записи"""
        if not res_model or not res_id:
            return False
            
        try:
            record = self.env[res_model].browse(res_id)
            
            # Если это sale.order, берем user_id
            if res_model == 'sale.order' and hasattr(record, 'user_id') and record.user_id:
                return record.user_id.id
            
            # Если это sale.order.line, берем user_id из order_id
            elif res_model == 'sale.order.line' and hasattr(record, 'order_id') and record.order_id.user_id:
                return record.order_id.user_id.id
                
        except Exception:
            # Игнорируем ошибки при получении записи
            pass
            
        return False