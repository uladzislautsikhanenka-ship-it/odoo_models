# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
                excluded_ids = line.order_id._get_excluded_product_template_ids(line.order_id.id, line.id)
                if line.product_template_id.id in excluded_ids:
                    raise models.ValidationError(
                        'Product Template "%s" is already selected in another line of this order.' % 
                        line.product_template_id.name
                    )
        return lines

    def write(self, vals):
        if 'product_template_id' in vals and vals['product_template_id']:
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
