# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    website_id = fields.Many2one(
        'website', 
        string='Website',
        help='Website where this order has been placed, for eCommerce orders.',
        store=False,  
        readonly=True,
        compute='_compute_website_id_safe'
    )

    is_express_delivery = fields.Boolean(
        string='Express Delivery',
        compute='_compute_is_express_delivery',
        store=True,
        help='Indicates if this is an express delivery'
    )

    @api.depends('group_id')
    def _compute_website_id_safe(self):
        for picking in self:
            if picking.group_id and hasattr(picking.group_id, 'sale_id'):
                if picking.group_id.sale_id and hasattr(picking.group_id.sale_id, 'website_id'):
                    picking.website_id = picking.group_id.sale_id.website_id
                else:
                    picking.website_id = False
            else:
                picking.website_id = False

    @api.depends('move_ids.sale_line_id.express_delivery')
    def _compute_is_express_delivery(self):
        for picking in self:
            picking.is_express_delivery = any(
                move.sale_line_id.express_delivery for move in picking.move_ids
                if move.sale_line_id
            )
             

    def _get_display_name(self):
        result = super()._get_display_name()
        if self.is_express_delivery:
            result = f"🚀 {result} (Express)"
        return result
