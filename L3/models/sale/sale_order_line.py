# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    express_delivery = fields.Boolean(
        string='Express Delivery',
        default=False,
        help='Mark this line for express delivery (separate picking)'
    )
    
    express_picking_name = fields.Char(
        string='Express Picking',
        compute='_compute_express_picking_name',
        store=True,
        help='Name of the created express delivery'
    )
    
    split_line = fields.Boolean(string='Split', default=False, help='Отметить для разделения этой линии')
    
    @api.depends('move_ids.picking_id', 'move_ids.picking_id.note', 'move_ids.picking_id.name', 
                 'express_delivery', 'order_id.picking_ids', 'order_id.picking_ids.note')
    def _compute_express_picking_name(self):
        """Compute the name of express picking related to this line"""
        import logging
        _logger = logging.getLogger(__name__)
        
        for line in self:
            if not line.express_delivery:
                line.express_picking_name = ''
                continue
                
            express_picking = False
            
            # Способ 1: Поиск через move_ids текущей линии
            if line.move_ids:
                _logger.info(f"Line {line.id}: Found {len(line.move_ids)} moves")
                for move in line.move_ids:
                    if move.picking_id:
                        note = (move.picking_id.note or '').lower()
                        _logger.info(f"  Move {move.id}: picking {move.picking_id.name}, note: '{note}'")
                        if 'express' in note or 'экспресс' in note:
                            express_picking = move.picking_id
                            _logger.info(f"  -> Found express picking: {express_picking.name}")
                            break
            
            # Способ 2: Поиск через все доставки заказа
            if not express_picking and line.order_id and line.order_id.picking_ids:
                _logger.info(f"Line {line.id}: Searching through order pickings")
                for picking in line.order_id.picking_ids:
                    if picking.state == 'cancel':
                        continue
                    note = (picking.note or '').lower()
                    _logger.info(f"  Picking {picking.name}, note: '{note}'")
                    if 'express' in note or 'экспресс' in note:
                        # Проверяем, есть ли линия в этой доставке
                        sale_line_ids = picking.move_ids.mapped('sale_line_id')
                        _logger.info(f"    Sale lines in picking: {sale_line_ids.ids}")
                        if line in sale_line_ids:
                            express_picking = picking
                            _logger.info(f"  -> Found express picking: {express_picking.name}")
                            break
            
            if express_picking:
                line.express_picking_name = express_picking.name
                _logger.info(f"Line {line.id}: Set express_picking_name = {express_picking.name}")
            else:
                line.express_picking_name = ''
                _logger.info(f"Line {line.id}: No express picking found")
    
    available_product_domain = fields.Char(compute='_compute_available_product_domain', store=False)

    @api.depends('order_id', 'order_id.order_line', 'order_id.order_line.product_template_id')
    def _compute_available_product_domain(self):
        for line in self:
            if line.order_id:
                selected_template_ids = line.order_id.order_line.filtered(
                    lambda l: l.product_template_id and l.id != line.id
                ).mapped('product_template_id.id')
                
                if selected_template_ids:
                    domain_str = f"[('id', 'not in', {selected_template_ids})]"
                    line.available_product_domain = domain_str
                else:
                    line.available_product_domain = "[]"
            else:
                line.available_product_domain = "[]"

    @api.model
    def _get_available_products_domain(self):
        order_id = self.env.context.get('default_order_id')
        if not order_id:
            return []

        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return []

        selected_product_ids = order.order_line.mapped('product_id.id')

        if selected_product_ids:
            return [('id', 'not in', selected_product_ids)]
        return []

    @api.model
    def _get_selected_products_list(self, order_id=None):
        if not order_id:
            order_id = self.env.context.get('default_order_id')
        
        if not order_id:
            return []
        
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return []
        
        selected_products = []
        for line in order.order_line:
            if line.product_id:
                selected_products.append({
                    'id': line.product_id.id,
                    'name': line.product_id.name,
                    'default_code': line.product_id.default_code,
                    'list_price': line.product_id.list_price,
                    'qty_available': line.product_id.qty_available,
                })
        
        return selected_products

    @api.model
    def _get_available_products_list(self, order_id=None):
        if not order_id:
            order_id = self.env.context.get('default_order_id')
        
        if not order_id:
            products = self.env['product.product'].search([])
            return [{'id': p.id, 'name': p.name, 'default_code': p.default_code, 
                    'list_price': p.list_price, 'qty_available': p.qty_available} for p in products]
        
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return []
        
        selected_product_ids = order.order_line.filtered('product_id').mapped('product_id.id')
        available_products = self.env['product.product'].search([
            ('id', 'not in', selected_product_ids)
        ])
        
        return [{'id': p.id, 'name': p.name, 'default_code': p.default_code, 
                'list_price': p.list_price, 'qty_available': p.qty_available} for p in available_products]

    @api.model
    def _get_product_domain(self):
        order_id = self.env.context.get('default_order_id') or self.env.context.get('order_id')
        if not order_id:
            return []
        
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return []

        selected_product_ids = order.order_line.mapped('product_id.id')
        if selected_product_ids:
            return [('id', 'not in', selected_product_ids)]
        return []

    @api.onchange('order_id')
    def _onchange_order_id_update_domain(self):
        if self.order_id:
            selected_product_ids = self.order_id.order_line.filtered(
                lambda line: line.product_id and line != self
            ).mapped('product_id.id')
            domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
            return {
                'domain': {
                    'product_id': domain
                }
            }

    def _get_procurement_group(self):
        self.ensure_one()
        base_group = super()._get_procurement_group()
        if not self.express_delivery:
            return base_group

        if self.order_id.procurement_group_id:
            express_group = self.env['procurement.group'].search([
                ('sale_id', '=', self.order_id.id),
                ('name', '=', f"{self.order_id.name} - Express")
            ], limit=1)
        else:
            express_group = False

        if not express_group:
            express_group = self.env['procurement.group'].create({
                'name': f"{self.order_id.name} - Express",
                'move_type': self.order_id.picking_policy,
                'sale_id': self.order_id.id,
                'partner_id': self.order_id.partner_shipping_id.id,
            })
        return express_group