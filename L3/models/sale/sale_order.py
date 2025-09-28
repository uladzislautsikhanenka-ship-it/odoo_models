# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Keep default confirmation flow from `sale`/`sale_stock`.

    delivery_count = fields.Integer(string='Delivery Count', compute='_compute_delivery_count')
    
    # Computed field to get used product template IDs
    used_product_template_ids = fields.Many2many(
        'product.template',
        string='Used Product Templates',
        compute='_compute_used_product_template_ids',
        help='Product templates already selected in this order'
    )

    @api.model
    def _get_available_products_domain(self):
        """Return domain to exclude already selected products from dropdown"""
        # Get current order from context
        order_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if not order_id:
            return []
        
        # Get the order
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return []
        
        # Get all already selected product IDs in this order
        selected_product_ids = order.order_line.mapped('product_id.id')
        
        # Exclude already selected products from dropdown
        if selected_product_ids:
            return [('id', 'not in', selected_product_ids)]
        return []

    @api.depends('order_line.product_template_id')
    def _compute_used_product_template_ids(self):
        """Compute used product template IDs from order lines"""
        for order in self:
            used_templates = order.order_line.filtered('product_template_id').mapped('product_template_id')
            order.used_product_template_ids = used_templates

    def _compute_delivery_count(self):
        for order in self:
            order.delivery_count = self.env['stock.picking'].search_count([
                ('sale_id', '=', order.id),
                ('state', 'not in', ('cancel',))
            ])

    def action_view_delivery_custom(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('sale_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.partner_shipping_id.id or self.partner_id.id,
            'search_default_sale_id': self.id,
        }
        return action

    def _action_confirm(self):
        """After order confirmation, immediately confirm created deliveries.

        - Call standard super to create movements and pickings
        - Confirm all unfinished/uncancelled deliveries
        - Try to reserve goods (action_assign) so that the Delivery button
          immediately shows readiness
        """
        result = super()._action_confirm()
        for order in self:
            # Force creation of movements/pickings according to warehouse rules
            try:
                order.order_line._action_launch_stock_rule()
            except Exception:
                pass
            pickings = order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            # If for some reason deliveries haven't been created (non-standard configuration),
            # create them manually and put the corresponding lines.
            if not pickings:
                regular_lines = order.order_line.filtered(lambda l: not l.display_type and l.product_id and not l.express_delivery)
                express_lines = order.order_line.filtered(lambda l: not l.display_type and l.product_id and l.express_delivery)

                regular_picking = express_picking = False
                if regular_lines:
                    regular_picking = order._create_regular_picking()
                    for line in regular_lines:
                        order._create_move_for_line(line, regular_picking)
                if express_lines:
                    express_picking = order._create_express_picking()
                    for line in express_lines:
                        order._create_move_for_line(line, express_picking)

                pickings = self.env['stock.picking'].browse([p.id for p in [regular_picking, express_picking] if p])
            if pickings:
                # Transfer from draft/waiting to confirmed/ready
                pickings.action_confirm()
                # Try to reserve (if sufficient stock)
                try:
                    pickings.action_assign()
                except Exception:
                    # Reservation may not work due to lack of stock - this is not critical
                    pass

            # Additionally group deliveries: one for express, one for regular
            # This is needed in case standard rules distributed goods across different movements/deliveries
            regroup_pickings = order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel') and p.picking_type_code == 'outgoing')
            if regroup_pickings:
                # Find/create target deliveries
                regular_target = regroup_pickings.filtered(lambda p: (p.note or '').lower().strip() == _('Regular Delivery').lower().strip())[:1]
                express_target = regroup_pickings.filtered(lambda p: (p.note or '').lower().strip() == _('Express Delivery').lower().strip())[:1]

                if not regular_target:
                    # Create empty regular delivery if needed
                    regular_lines_exist = any(l for l in order.order_line.filtered(lambda l: not l.display_type and l.product_id and not l.express_delivery))
                    if regular_lines_exist:
                        regular_target = order._create_regular_picking()
                if not express_target:
                    # Create empty express delivery if needed
                    express_lines_exist = any(l for l in order.order_line.filtered(lambda l: not l.display_type and l.product_id and l.express_delivery))
                    if express_lines_exist:
                        express_target = order._create_express_picking()

                # Move movements to corresponding target deliveries
                for picking in regroup_pickings:
                    for move in picking.move_ids:
                        is_express = bool(getattr(move.sale_line_id, 'express_delivery', False))
                        target_picking = express_target if is_express else regular_target
                        if target_picking and move.picking_id.id != (target_picking.id if hasattr(target_picking, 'id') else target_picking):
                            move.write({'picking_id': target_picking.id})

                # Cancel empty deliveries so they don't count in delivery count
                for picking in regroup_pickings:
                    if not picking.move_ids:
                        try:
                            if picking.state not in ('done', 'cancel'):
                                picking.action_cancel()
                        except Exception:
                            # If can't cancel - hide from count through state
                            pass
            # Update computed fields and references so Delivery button appears immediately
            try:
                order.invalidate_recordset()
                order.flush(['picking_ids', 'state'])
            except Exception:
                pass
        return result

    # --- Helper methods for forced creation of deliveries ---
    def _get_outgoing_picking_type(self):
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', self.warehouse_id.id)
        ], limit=1)
        if not picking_type:
            raise UserError(_('No outgoing picking type found for this warehouse'))
        return picking_type

    def _create_regular_picking(self):
        self.ensure_one()
        picking_type = self._get_outgoing_picking_type()
        vals = {
            'partner_id': self.partner_shipping_id.id or self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': self.name,
            'sale_id': self.id,
            'note': _('Regular Delivery'),
        }
        return self.env['stock.picking'].create(vals)

    def _create_express_picking(self):
        self.ensure_one()
        picking_type = self._get_outgoing_picking_type()
        vals = {
            'partner_id': self.partner_shipping_id.id or self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': self.name,
            'sale_id': self.id,
            'note': _('Express Delivery'),
        }
        return self.env['stock.picking'].create(vals)

    def _create_move_for_line(self, line, picking):
        self.ensure_one()
        if not picking:
            return False
        move_vals = {
            'name': line.name,
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'sale_line_id': line.id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'description_picking': line.name,
        }
        return self.env['stock.move'].create(move_vals)

    @api.model
    def _update_product_domain_on_line_change(self):
        """Update product domain when order lines change"""
        # This method can be called to refresh the product domain
        # when order lines are added or removed
        return True

    @api.onchange('order_line')
    def _onchange_order_line_update_domain(self):
        """Update product domain when order lines change - INSTANT REMOVAL"""
        # Get all selected product IDs
        selected_product_ids = self.order_line.filtered('product_id').mapped('product_id.id')
        
        # Force onchange for all order lines to update their domains IMMEDIATELY
        for line in self.order_line:
            if hasattr(line, '_onchange_product_id_check_and_update_domain'):
                line._onchange_product_id_check_and_update_domain()
            if hasattr(line, '_force_update_product_domain'):
                line._force_update_product_domain()
        
        # Return domain to exclude already selected products for all lines
        domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
        
        return {
            'domain': {
                'order_line': {
                    'product_id': domain
                }
            }
        }

    @api.onchange('partner_id', 'partner_invoice_id', 'partner_shipping_id')
    def _onchange_partner_update_domain(self):
        """Update product domain when partner changes - INSTANT REMOVAL"""
        # Get all selected product IDs
        selected_product_ids = self.order_line.filtered('product_id').mapped('product_id.id')
        
        # Force onchange for all order lines to update their domains IMMEDIATELY
        for line in self.order_line:
            if hasattr(line, '_onchange_product_id_check_and_update_domain'):
                line._onchange_product_id_check_and_update_domain()
            if hasattr(line, '_force_update_product_domain'):
                line._force_update_product_domain()
        
        # Return domain to exclude already selected products for all lines
        domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
        
        return {
            'domain': {
                'order_line': {
                    'product_id': domain
                }
            }
        }

    @api.onchange('company_id', 'warehouse_id', 'pricelist_id')
    def _onchange_company_warehouse_update_domain(self):
        """Update product domain when company or warehouse changes - INSTANT REMOVAL"""
        # Get all selected product IDs
        selected_product_ids = self.order_line.filtered('product_id').mapped('product_id.id')
        
        # Force onchange for all order lines to update their domains IMMEDIATELY
        for line in self.order_line:
            if hasattr(line, '_onchange_product_id_check_and_update_domain'):
                line._onchange_product_id_check_and_update_domain()
            if hasattr(line, '_force_update_product_domain'):
                line._force_update_product_domain()
        
        # Return domain to exclude already selected products for all lines
        domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
        
        return {
            'domain': {
                'order_line': {
                    'product_id': domain
                }
            }
        }

    @api.onchange('state', 'date_order', 'validity_date')
    def _onchange_state_date_update_domain(self):
        """Update product domain when state or date changes - INSTANT REMOVAL"""
        # Get all selected product IDs
        selected_product_ids = self.order_line.filtered('product_id').mapped('product_id.id')
        
        # Force onchange for all order lines to update their domains IMMEDIATELY
        for line in self.order_line:
            if hasattr(line, '_onchange_product_id_check_and_update_domain'):
                line._onchange_product_id_check_and_update_domain()
            if hasattr(line, '_force_update_product_domain'):
                line._force_update_product_domain()
        
        # Return domain to exclude already selected products for all lines
        domain = [('id', 'not in', selected_product_ids)] if selected_product_ids else []
        
        return {
            'domain': {
                'order_line': {
                    'product_id': domain
                }
            }
        }
    
    def _get_selected_product_ids(self):
        """Get all selected product IDs in this order"""
        return self.order_line.filtered('product_id').mapped('product_id.id')
    
    def _update_all_product_domains(self):
        """Update product domains for all order lines"""
        for line in self.order_line:
            if hasattr(line, '_onchange_order_id_update_domain'):
                line._onchange_order_id_update_domain()

    def action_get_products_status(self):
        """Action to get status of selected and available products"""
        selected_products = self._get_selected_products_list()
        available_products = self._get_available_products_list()
        
        message = _('Selected: %s products\nAvailable: %s products') % (
            len(selected_products), len(available_products)
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Products Status'),
                'message': message,
                'type': 'info',
            }
        }

    def action_test_highlight(self):
        """Action to test product highlighting"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Highlight'),
                'message': _('Check browser console for highlighting logs. Use F12 to open console.'),
                'type': 'info',
                'sticky': False,
                'buttons': [
                    {
                        'text': 'Debug Selected Products',
                        'primary': False,
                        'click': 'window.debugSelectedProducts();'
                    },
                    {
                        'text': 'Force Test Highlight',
                        'primary': True,
                        'click': 'window.testHighlightAll();'
                    }
                ]
            }
        }

    def _get_selected_products_list(self):
        """Get list of selected products with their details"""
        selected_products = []
        for line in self.order_line:
            if line.product_id:
                selected_products.append({
                    'id': line.product_id.id,
                    'name': line.product_id.name,
                    'default_code': line.product_id.default_code,
                    'list_price': line.product_id.list_price,
                    'qty_available': line.product_id.qty_available,
                })
        return selected_products

    def _get_available_products_list(self):
        """Get list of available products (excluding already selected)"""
        # Get selected product IDs
        selected_product_ids = self.order_line.filtered('product_id').mapped('product_id.id')
        
        # Get available products (excluding selected ones)
        available_products = self.env['product.product'].search([
            ('id', 'not in', selected_product_ids)
        ])
        
        return [{'id': p.id, 'name': p.name, 'default_code': p.default_code, 
                'list_price': p.list_price, 'qty_available': p.qty_available} for p in available_products]

    def action_force_update_product_domains(self):
        """Force update domains for all product fields"""
        # Get all selected product IDs
        selected_product_ids = self.order_line.filtered('product_id').mapped('product_id.id')
        
        # Force onchange for all order lines to update their domains
        for line in self.order_line:
            if hasattr(line, '_onchange_product_id_check_and_update_domain'):
                line._onchange_product_id_check_and_update_domain()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'domain': [('id', 'not in', selected_product_ids)] if selected_product_ids else []
            }
        }
