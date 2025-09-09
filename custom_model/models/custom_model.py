from odoo import models, fields, api
from datetime import datetime, date, timedelta


class CustomModel(models.Model):
    _name = 'custom.model'
    _description = 'Custom Model with All Field Types'
    _rec_name = 'text'

    # Basic Fields
    text = fields.Text(string='Text Field', required=True)
    char_field = fields.Char(string='Char Field', size=100)
    html_field = fields.Html(string='HTML Field')
    
    # Numeric Fields
    integer_field = fields.Integer(string='Integer Field')
    float_field = fields.Float(string='Float Field', digits=(10, 2))
    monetary_field = fields.Monetary(string='Monetary Field', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')
    
    # Boolean Fields
    check1 = fields.Boolean(string='Test 1')
    check2 = fields.Boolean(string='Test 2')
    check_all = fields.Boolean(string='Select all')
    is_company = fields.Boolean(string='Is Company')
    boolean1 = fields.Boolean(string='1')
    boolean2 = fields.Boolean(string='2')
    boolean3 = fields.Boolean(string='3')
    boolean4 = fields.Boolean(string='4')
    boolean5 = fields.Boolean(string='5')
    boolean6 = fields.Boolean(string='6')
    boolean7 = fields.Boolean(string='7')
    boolean8 = fields.Boolean(string='8')
    boolean9 = fields.Boolean(string='9')
    
    # Selection Fields
    select1 = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
    ], string='Select 1')
    
    select2 = fields.Selection([
        ('4', '4'),
        ('5', '5'),
        ('6', '6')
    ], string='Select 2')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')
    
    # Date and Time Fields
    date_field = fields.Date(string='Date Field', default=fields.Date.today)
    datetime_field = fields.Datetime(string='DateTime Field', default=fields.Datetime.now)
    time_field = fields.Float(string='Time Field')
    
    # Binary Fields
    binary_field = fields.Binary(string='Binary Field')
    image_field = fields.Binary(string='Image Field', attachment=True)
    
    # Relational Fields
    many2one_field = fields.Many2one('res.partner', string='Partner')
    many2many_field = fields.Many2many('res.partner', string='Partners')
    one2many_field = fields.One2many('custom.model.line', 'parent_id', string='Lines')
    
    # Order-like relationship (similar to sale.order -> sale.order.line)
    order_lines = fields.One2many(
        comodel_name='custom.model.line',
        inverse_name='order_id',
        string='Order Lines',
        copy=True,
        auto_join=True
    )
    
    # Computed Fields
    computed_field = fields.Char(string='Computed Field', compute='_compute_computed_field', store=True)
    computed_boolean = fields.Boolean(string='Computed Boolean', compute='_compute_computed_boolean')
    
    # Related Fields
    partner_name = fields.Char(string='Partner Name', related='many2one_field.name', readonly=True)
    partner_email = fields.Char(string='Partner Email', related='many2one_field.email', readonly=True)
    
    # Domain Fields
    domain_field = fields.Many2one('res.partner', string='Domain Partner', 
                                  domain=[('is_company', '=', True)])
    
    # Context Fields
    context_field = fields.Many2one('res.partner', string='Context Partner',
                                   context={'default_is_company': True})
    
    # Groups Fields
    groups_field = fields.Char(string='Groups Field', groups='base.group_user')
    
    # Depends Fields
    depends_field = fields.Char(string='Depends Field', compute='_compute_depends_field')
    
    # Default Fields
    default_field = fields.Char(string='Default Field', default='Default Value')
    
    # Required Fields
    required_field = fields.Char(string='Required Field', required=True)
    
    # Readonly Fields
    readonly_field = fields.Char(string='Readonly Field', readonly=True, default='Readonly Value')
    
    # Help Fields
    help_field = fields.Char(string='Help Field', help='This is a help text for the field')
    
    # Placeholder Fields
    placeholder_field = fields.Char(string='Placeholder Field', placeholder='Enter text here...')
    
    # Widget Fields
    widget_text_field = fields.Text(string='Widget Text')
    widget_html_field = fields.Html(string='Widget HTML')
    widget_url_field = fields.Char(string='Widget URL')
    widget_email_field = fields.Char(string='Widget Email')
    widget_phone_field = fields.Char(string='Widget Phone')
    widget_password_field = fields.Char(string='Widget Password')
    
    # Special Fields
    color_field = fields.Integer(string='Color Field')
    progress_field = fields.Float(string='Progress Field')
    gauge_field = fields.Float(string='Gauge Field')
    sparkline_field = fields.Float(string='Sparkline Field')
    
    @api.onchange('check_all')
    def _onchange_check_all(self):
        """Handle select all functionality"""
        if self.check_all:
            self.check1 = True
            self.check2 = True
        else:
            self.check1 = False
            self.check2 = False
        # Обновляем текст после изменения чекбоксов
        self._update_text_with_checkboxes()
    
    @api.onchange('check1', 'check2')
    def _onchange_check_individual(self):
        """Handle individual checkbox changes"""
        # Если сняли check1 или check2, а check_all был установлен - снимаем check_all
        if self.check_all and (not self.check1 or not self.check2):
            self.check_all = False
        
        # Если установили и check1 и check2 - устанавливаем check_all
        if self.check1 and self.check2:
            self.check_all = True
    
    def _update_text_with_checkboxes(self):
        """Update text field based on checkbox states"""
        import re
        
        # Получаем базовый текст без меток чекбоксов
        base_text = self.text or ""
        base_text = re.sub(r'\s*\[Test 1\]\s*', ' ', base_text)
        base_text = re.sub(r'\s*\[Test 2\]\s*', ' ', base_text)
        base_text = base_text.strip()
        
        # Собираем метки в правильном порядке
        labels = []
        if self.check1:
            labels.append("[Test 1]")
        if self.check2:
            labels.append("[Test 2]")
        
        # Формируем итоговый текст
        if base_text and labels:
            self.text = base_text + " " + " ".join(labels)
        elif labels:
            self.text = " ".join(labels)
        else:
            self.text = base_text
    
    @api.onchange('check1')
    def _onchange_check1_text(self):
        """Handle check1 text changes"""
        self._update_text_with_checkboxes()
    
    @api.onchange('check2')
    def _onchange_check2_text(self):
        """Handle check2 text changes"""
        self._update_text_with_checkboxes()
    
    @api.depends('text', 'char_field')
    def _compute_computed_field(self):
        """Compute computed field based on text and char_field"""
        for record in self:
            if record.text and record.char_field:
                record.computed_field = f"{record.text} - {record.char_field}"
            else:
                record.computed_field = "No data"
    
    @api.depends('integer_field', 'float_field')
    def _compute_computed_boolean(self):
        """Compute computed boolean field"""
        for record in self:
            record.computed_boolean = (record.integer_field or 0) > 0 and (record.float_field or 0) > 0
    
    @api.depends('many2one_field')
    def _compute_depends_field(self):
        """Compute depends field"""
        for record in self:
            if record.many2one_field:
                record.depends_field = f"Selected: {record.many2one_field.name}"
            else:
                record.depends_field = "No partner selected"
    
    def action_show_all_fields(self):
        """Action to show all fields - this will refresh the view"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_create_person(self):
        """Create a new person contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Person',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.text or '',
                'default_is_company': False,
            }
        }
    
    def action_create_company(self):
        """Create a new company contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Company',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.text or '',
                'default_is_company': True,
            }
        }
    
    def action_create_partner_wizard(self):
        """Open create partner wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Partner',
            'res_model': 'create.partner.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.text or '',
                'default_is_company': self.is_company,
            }
        }
    
    def _compute_discount(self):
        """Вычисляемое значение discount"""
        for record in self:
            if record.state == 'confirmed':
                # В confirmed используем сохраненное значение
                record.total_discount_percent = record._origin.total_discount_percent
            else:
                # В draft используем обычную логику
                record.total_discount_percent = record._calculate_draft_discount()
    
    
    def _inverse_discount(self):
        """Обратное вычисление - сохраняем значение"""
        for record in self:
            if record.state == 'confirmed':
                # В confirmed просто сохраняем значение
                record._origin.total_discount_percent = record.total_discount_percent
    
    # Status field
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Summary calculation fields - editable in draft, computed in confirmed
    total_offer_value = fields.Monetary(
        string="Total offer value, €",
        currency_field='currency_id'
    )
    max_delivery_days = fields.Integer(
        string="Max Delivery, bd"
    )
    avg_expected_coefficient = fields.Float(
        string="Avg. expected coefficient in SO",
        digits=(16, 2)
    )
    avg_min_coefficient = fields.Float(
        string="Avg. min coefficient",
        digits=(16, 2)
    )
    total_discount_percent = fields.Float(
        string="Discount, %",
        digits=(16, 2),compute='_compute_discount', inverse='_inverse_discount', store=True
    )
    avg_client_discount = fields.Float(
        string="Avg. Client disc., %",
        digits=(16, 2)
    )
    actual_agent_commission = fields.Monetary(
        string="Act. agent commission, €",
        currency_field='currency_id'
    )
    actual_agent_commission_percent = fields.Float(
        string="Act. agent commission, %",
        digits=(16, 2)
    )
    total_purchasing = fields.Monetary(
        string="Total Purchasing, €",
        currency_field='currency_id'
    )
    
    @api.onchange('total_offer_value', 'max_delivery_days', 'avg_expected_coefficient', 
                  'avg_min_coefficient', 'total_discount_percent', 'avg_client_discount',
                  'actual_agent_commission', 'actual_agent_commission_percent', 'total_purchasing')
    def _onchange_summary_fields(self):
        """Auto-calculate related summary fields when one is changed.
        - In draft: validate negatives and recalc.
        - In confirmed: allow interactive recalculation when Discount changes (or other fields),
          preserving user-entered values otherwise.
        """
        # Валидация только в черновике
        if self.state == 'draft':
            if self.total_offer_value and self.total_offer_value < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Total offer value'}}
            if self.max_delivery_days and self.max_delivery_days < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Max Delivery'}}
            if self.avg_expected_coefficient and self.avg_expected_coefficient < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Avg. expected coefficient'}}
            if self.avg_min_coefficient and self.avg_min_coefficient < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Avg. min coefficient'}}
            if self.total_discount_percent and self.total_discount_percent < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Discount'}}
            if self.avg_client_discount and self.avg_client_discount < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Avg. Client disc.'}}
            if self.actual_agent_commission and self.actual_agent_commission < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Act. agent commission'}}
            if self.actual_agent_commission_percent and self.actual_agent_commission_percent < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Act. agent commission %'}}
            if self.total_purchasing and self.total_purchasing < 0:
                return {'warning': {'title': 'Ошибка валидации', 'message': 'Введите положительное число для Total Purchasing'}}

        # Пересчеты (и в draft, и в confirmed по требованию пользователя)
        if (self.total_offer_value or 0) > 0:
            # Комиссия берется из процента, если он задан, иначе 3%
            percent = self.actual_agent_commission_percent if (self.actual_agent_commission_percent or 0) > 0 else 3.0
            self.actual_agent_commission_percent = percent
            self.actual_agent_commission = self.total_offer_value * (percent / 100.0)

            # Закупка = сумма - скидка - комиссия
            disc = (self.total_discount_percent or 0)
            self.total_purchasing = self.total_offer_value - (disc / 100.0 * self.total_offer_value) - (self.actual_agent_commission or 0)

            # Доставка из коэффициента
            if (self.avg_expected_coefficient or 0) > 0:
                self.max_delivery_days = min(int(self.avg_expected_coefficient * 10), 30)

        # Мин. коэффициент всегда поддерживаем как 80% expected
        if (self.avg_expected_coefficient or 0) > 0:
            self.avg_min_coefficient = self.avg_expected_coefficient * 0.8

        # Клиентская скидка влияет на общий дисконт
        if (self.avg_client_discount or 0) > 0:
            self.total_discount_percent = self.avg_client_discount * 1.2
    
    def action_confirm(self):
        """Confirm the record without recomputing user-entered SUMMARY values.
        Values set in draft are preserved as-is in confirmed.
        """
        self.write({'state': 'confirmed'})
        return True
    
    def _auto_calculate_summary(self):
        """Auto-calculate summary fields based on order lines and other data"""
        # Total offer value - сумма всех строк заказа
        self.total_offer_value = sum(line.price_total for line in self.order_lines)
        
        # Max delivery days - на основе integer_field
        self.max_delivery_days = min(self.integer_field or 0, 30)
        
        # Average expected coefficient - на основе float_field
        self.avg_expected_coefficient = (self.float_field or 0) * 1.2
        
        # Average min coefficient - на основе float_field с минимальным значением
        self.avg_min_coefficient = max((self.float_field or 0) * 0.8, 0.5)
        
        # Total discount percent - средняя скидка по строкам
        if self.order_lines:
            self.total_discount_percent = sum(line.discount for line in self.order_lines) / len(self.order_lines)
        else:
            self.total_discount_percent = 0.0
        
        # Average client discount - на основе priority
        priority_discount = {1: 5.0, 2: 3.0, 3: 1.0, 4: 0.5, 5: 0.0}
        self.avg_client_discount = priority_discount.get(self.priority, 0.0)
        
        # Actual agent commission - 5% от общей суммы
        self.actual_agent_commission = self.total_offer_value * 0.05
        
        # Actual agent commission percent
        self.actual_agent_commission_percent = 5.0
        
        # Total purchasing - сумма без налогов и комиссий
        self.total_purchasing = self.total_offer_value * 0.85
    
    def action_draft(self):
        """Set record to draft"""
        self.write({'state': 'draft'})
        return True



