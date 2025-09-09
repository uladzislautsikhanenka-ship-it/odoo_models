from odoo import models, fields, api


class CustomModelLine(models.Model):
    _name = 'custom.model.line'
    _description = 'Custom Model Line'
    _rec_names_search = ['name', 'order_id.text']
    _order = 'order_id, sequence, id'
    
    # Main relationship (similar to sale.order.line -> sale.order)
    order_id = fields.Many2one(
        comodel_name='custom.model',
        string="Order Reference",
        required=True, 
        ondelete='cascade', 
        index=True, 
        copy=False
    )
    
    # Legacy relationship (keeping for backward compatibility)
    parent_id = fields.Many2one('custom.model', string='Parent')
    
    # Basic fields
    name = fields.Char(string='Description', required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    
    # Numeric fields (similar to sale.order.line)
    quantity = fields.Float(
        string="Quantity",
        digits='Product Unit of Measure', 
        default=1.0,
        required=True
    )
    price_unit = fields.Float(
        string="Unit Price",
        digits='Product Price',
        required=True
    )
    discount = fields.Float(
        string="Discount (%)",
        digits='Discount',
        default=0.0
    )
    tax_amount = fields.Float(
        string="Tax Amount",
        digits='Account',
        default=0.0
    )
    
    # Computed fields
    price_subtotal = fields.Float(
        string="Subtotal",
        compute='_compute_price_subtotal',
        digits='Account',
        store=True
    )
    price_total = fields.Float(
        string="Total",
        compute='_compute_price_total',
        digits='Account',
        store=True
    )
    
    # Legacy field for backward compatibility
    total = fields.Float(
        string="Total (Legacy)",
        compute='_compute_total',
        digits='Account',
        store=True
    )
    
    # Related fields (similar to sale.order.line)
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        depends=['order_id.currency_id'],
        store=True, 
        precompute=True
    )
    state = fields.Selection(
        related='order_id.state',
        string="Order Status",
        copy=False, 
        store=True, 
        precompute=True
    )
    
    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_price_subtotal(self):
        """Compute subtotal before tax"""
        for record in self:
            subtotal = record.quantity * record.price_unit
            if record.discount:
                subtotal = subtotal * (1 - record.discount / 100.0)
            record.price_subtotal = subtotal
    
    @api.depends('price_subtotal', 'tax_amount')
    def _compute_price_total(self):
        """Compute total including tax"""
        for record in self:
            record.price_total = record.price_subtotal + record.tax_amount
    
    # Legacy method (keeping for backward compatibility)
    @api.depends('quantity', 'price_unit')
    def _compute_total(self):
        for record in self:
            record.total = record.quantity * record.price_unit









