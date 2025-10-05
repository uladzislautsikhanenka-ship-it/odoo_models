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

    @api.onchange('product_id')
    def _onchange_product_id_check_and_update_domain(self):
        """Check for duplicate products and update domain when product changes - INSTANT REMOVAL"""
        if self.product_id and self.order_id:
            # Check if this product is already in other order lines
            existing_lines = self.order_id.order_line.filtered(
                lambda line: line.product_id == self.product_id and line != self
            )
            if existing_lines:
                # Clear product field silently - no warning
                self.product_id = False
                return
        
        if self.order_id:
            # Get already selected product IDs excluding current line
            selected_product_ids = self.order_id.order_line.filtered(
                lambda line: line.product_id and line != self
            ).mapped('product_id.id')
            
            # Force update domains for ALL lines in the order
            for line in self.order_id.order_line:
                if line != self:  # Skip current line to avoid recursion
                    # Trigger domain update for other lines
                    line._force_update_product_domain()
            
            # Return domain to exclude already selected products
            domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
            return {
                'domain': {
                    'product_id': domain
                }
            }

    def _force_update_product_domain(self):
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

    def action_remove_product_from_available_list(self):
        """Action to remove selected product from available list"""
        if self.product_id and self.order_id:
            # Get all selected product IDs excluding current line
            selected_product_ids = self.order_id.order_line.filtered(
                lambda line: line.product_id and line != self
            ).mapped('product_id.id')
            
            # Return domain to exclude already selected products
            domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'domain': domain
                }
            }

    def action_get_available_products(self):
        """Action to get list of available products"""
        if self.order_id:
            available_products = self._get_available_products_list(self.order_id.id)
            selected_products = self._get_selected_products_list(self.order_id.id)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Available Products'),
                    'message': _('Available: %s, Selected: %s') % (len(available_products), len(selected_products)),
                    'type': 'info',
                }
            }

    def action_force_update_all_domains(self):
        if self.order_id:
            selected_product_ids = self.order_id.order_line.filtered('product_id').mapped('product_id.id')
            for line in self.order_id.order_line:
                if hasattr(line, '_onchange_product_id_check_and_update_domain'):
                    line._onchange_product_id_check_and_update_domain()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'domain': [('id', 'not in', selected_product_ids)] if selected_product_ids else []
                }
            }

    @api.onchange('order_line')
    def _onchange_order_line_update_all_domains(self):
        if self.order_id:
            selected_template_ids = self.order_id.order_line.filtered(
                lambda line: line.product_template_id
            ).mapped('product_template_id.id')
            for line in self.order_id.order_line:
                line._force_update_product_domain()
            
            domain = [('id', 'not in', selected_template_ids)] if selected_template_ids else []
            return {
                'domain': {
                    'product_template_id': domain
                }
            }

    @api.onchange('order_id', 'product_template_id')
    def _onchange_update_product_domain(self):
        """Update product template domain when order or product template changes - INSTANT REMOVAL"""
        if self.order_id:
            # Force update domains for ALL lines immediately
            for line in self.order_id.order_line:
                line._force_update_product_domain()
            
            # Get already selected product template IDs excluding current line
            selected_template_ids = self.order_id.order_line.filtered(
                lambda line: line.product_template_id and line != self
            ).mapped('product_template_id.id')
            
            # Return domain to exclude already selected product templates
            domain = [('id', 'not in', selected_template_ids)] if selected_template_ids else []
            return {
                'domain': {
                    'product_template_id': domain
                }
            }

    @api.model
    def default_get(self, fields_list):
        """Set default domain when creating new line"""
        res = super().default_get(fields_list)
        
        # If we're creating a line for an existing order, set up the domain
        if 'order_id' in res and res['order_id']:
            order = self.env['sale.order'].browse(res['order_id'])
            if order.exists():
                selected_template_ids = order.order_line.filtered('product_template_id').mapped('product_template_id.id')
                if selected_template_ids:
                    # Store domain in context for the field
                    self = self.with_context(
                        default_product_template_domain=[('id', 'not in', selected_template_ids)]
                    )
        
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set up domain for new lines - INSTANT REMOVAL"""
        lines = super().create(vals_list)
        
        # Force domain update for all lines in the same order IMMEDIATELY
        for line in lines:
            if line.order_id:
                # Trigger onchange for all lines in the order
                for order_line in line.order_id.order_line:
                    if hasattr(order_line, '_onchange_product_id_check_and_update_domain'):
                        order_line._onchange_product_id_check_and_update_domain()
                    if hasattr(order_line, '_force_update_product_domain'):
                        order_line._force_update_product_domain()
        
        return lines

    @api.onchange('sequence')
    def _onchange_sequence_update_domain(self):
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

    @api.onchange('product_uom_qty', 'price_unit', 'discount')
    def _onchange_any_field_update_domain(self):
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

    @api.onchange('name', 'product_uom', 'tax_id')
    def _onchange_additional_fields_update_domain(self):
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

    @api.onchange('display_type', 'product_template_id')
    def _onchange_display_type_update_domain(self):
        """Update domain when display type or product template changes"""
        if self.order_id:
            # Get already selected product template IDs excluding current line
            selected_template_ids = self.order_id.order_line.filtered(
                lambda line: line.product_template_id and line != self
            ).mapped('product_template_id.id')
            
            # Return domain to exclude already selected product templates
            domain = [('id', 'not in', selected_template_ids)] if selected_template_ids else []
            return {
                'domain': {
                    'product_template_id': domain
                }
            }

    @api.model
    def _search_product_id(self, args, offset=0, limit=None, order=None):
        """Override search for product_id to exclude already selected products"""
        # Get the current order line from context
        line_id = self.env.context.get('active_id')
        if not line_id:
            return super()._search_product_id(args, offset, limit, order)
        
        # Get the order line
        line = self.browse(line_id)
        if not line.exists() or not line.order_id:
            return super()._search_product_id(args, offset, limit, order)
        
        # Get already selected product IDs excluding current line
        selected_product_ids = line.order_id.order_line.filtered(
            lambda l: l.product_id and l.id != line_id
        ).mapped('product_id.id')
        
        # Add exclusion domain to args
        if selected_product_ids:
            args.append(('id', 'not in', selected_product_ids))
        
        return super()._search_product_id(args, offset, limit, order)

    def _name_search_product_id(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """Override name_search for product_id to exclude already selected products"""
        if args is None:
            args = []
        
        # Get the current order line from context
        line_id = self.env.context.get('active_id')
        if line_id:
            # Get the order line
            line = self.browse(line_id)
            if line.exists() and line.order_id:
                # Get already selected product IDs excluding current line
                selected_product_ids = line.order_id.order_line.filtered(
                    lambda l: l.product_id and l.id != line_id
                ).mapped('product_id.id')
                
                # Add exclusion domain to args
                if selected_product_ids:
                    args.append(('id', 'not in', selected_product_ids))
        
        # Call the product model's name_search
        return self.env['product.product'].name_search(name, args, operator, limit, name_get_uid)

    @api.model
    def _search_product_id(self, args, offset=0, limit=None, order=None):
        """Override search for product_id to exclude already selected products - DIRECT APPROACH"""
        # Get the current order line from context
        line_id = self.env.context.get('active_id')
        if not line_id:
            return super()._search_product_id(args, offset, limit, order)
        
        # Get the order line
        line = self.browse(line_id)
        if not line.exists() or not line.order_id:
            return super()._search_product_id(args, offset, limit, order)
        
        # Get already selected product IDs excluding current line
        selected_product_ids = line.order_id.order_line.filtered(
            lambda l: l.product_id and l.id != line_id
        ).mapped('product_id.id')
        
        # Add exclusion domain to args
        if selected_product_ids:
            args.append(('id', 'not in', selected_product_ids))
        
        return super()._search_product_id(args, offset, limit, order)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        """Override search to exclude already selected products when searching for products"""
        # Check if we're searching for products in sale order line context
        if self.env.context.get('active_model') == 'sale.order.line':
            active_id = self.env.context.get('active_id') or self.env.context.get('line_id')
            if active_id:
                # Get the order line
                line = self.browse(active_id)
                if line.exists() and line.order_id:
                    # Get already selected product IDs excluding current line
                    selected_product_ids = line.order_id.order_line.filtered(
                        lambda l: l.product_id and l.id != active_id
                    ).mapped('product_id.id')
                    
                    # Add exclusion domain to args
                    if selected_product_ids:
                        args.append(('id', 'not in', selected_product_ids))
        
        return super()._search(args, offset, limit, order)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to exclude already selected products when searching for products"""
        if args is None:
            args = []
        
        # Check if we're searching for products in sale order line context
        if self.env.context.get('active_model') == 'sale.order.line':
            active_id = self.env.context.get('active_id') or self.env.context.get('line_id')
            if active_id:
                # Get the order line
                line = self.browse(active_id)
                if line.exists() and line.order_id:
                    # Get already selected product IDs excluding current line
                    selected_product_ids = line.order_id.order_line.filtered(
                        lambda l: l.product_id and l.id != active_id
                    ).mapped('product_id.id')
                    
                    # Add exclusion domain to args
                    if selected_product_ids:
                        args.append(('id', 'not in', selected_product_ids))
        
        return super().name_search(name, args, operator, limit)

    def action_update_product_domain(self):
        if self.order_id:
            pass
            selected_product_ids = self.order_id.order_line.filtered('product_id').mapped('product_id.id')
            domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    @api.model
    def _get_domain_for_product_selection(self, order_id, current_line_id=None):
        if not order_id:
            return []
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return []

        selected_product_ids = order.order_line.filtered(
            lambda line: line.product_id and line.id != current_line_id
        ).mapped('product_id.id')
        return [('id', 'not in', selected_product_ids)] if selected_product_ids else []

    @api.constrains('product_id')
    def _check_product_uniqueness(self):
        for line in self:
            if line.product_id and line.order_id:
                existing_lines = line.order_id.order_line.filtered(
                    lambda l: l.product_id == line.product_id and l != line
                )
                if existing_lines:
                    line.product_id = False
                    return

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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        """Override search to exclude already selected products in sale order lines"""
        # Check if we're in sale order line context
        if self.env.context.get('active_model') == 'sale.order.line':
            active_id = self.env.context.get('active_id') or self.env.context.get('line_id')
            if active_id:
                # Get the order line
                line = self.env['sale.order.line'].browse(active_id)
                if line.exists() and line.order_id:
                    # Get already selected product IDs excluding current line
                    selected_product_ids = line.order_id.order_line.filtered(
                        lambda l: l.product_id and l.id != active_id
                    ).mapped('product_id.id')
                    
                    # Add exclusion domain to args
                    if selected_product_ids:
                        args.append(('id', 'not in', selected_product_ids))
                        
                        # Debug log
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.info(f"Product search: excluding {selected_product_ids} from search")
        
        return super()._search(args, offset, limit, order)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to exclude already selected products in sale order lines"""
        if args is None:
            args = []
        
        # Check if we're in sale order line context
        if self.env.context.get('active_model') == 'sale.order.line':
            active_id = self.env.context.get('active_id') or self.env.context.get('line_id')
            if active_id:
                # Get the order line
                line = self.env['sale.order.line'].browse(active_id)
                if line.exists() and line.order_id:
                    # Get already selected product IDs excluding current line
                    selected_product_ids = line.order_id.order_line.filtered(
                        lambda l: l.product_id and l.id != active_id
                    ).mapped('product_id.id')
                    
                    # Add exclusion domain to args
                    if selected_product_ids:
                        args.append(('id', 'not in', selected_product_ids))
                        
                        # Debug log
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.info(f"Product name_search: excluding {selected_product_ids} from search")
        
        return super().name_search(name, args, operator, limit)

    def action_get_selected_products_info(self):
        if self.order_id:
            selected_products = []
            for line in self.order_id.order_line:
                if line.product_id and line.id != self.id:
                    selected_products.append({
                        'id': line.product_id.id,
                        'name': line.product_id.name,
                        'default_code': line.product_id.default_code,
                    })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Selected Products'),
                    'message': _('Already selected: %s') % ', '.join([p['name'] for p in selected_products]),
                    'type': 'info',
                }
            }
        
        return {'type': 'ir.actions.act_window_close'}
