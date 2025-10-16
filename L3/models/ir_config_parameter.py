# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'
    
    @api.model
    def get_date_panel_settings(self):
        """Получить настройки панели даты"""
        return {
            'enabled': self.sudo().get_param('l3.date_panel.enabled', 'True') == 'True',
            'format': self.sudo().get_param('l3.date_panel.format', 'short'),
            'timezone': self.sudo().get_param('l3.date_panel.timezone', 'Europe/Moscow'),
            'link_url': self.sudo().get_param('l3.date_panel.link_url', 'https://www.timeanddate.com/worldclock/russia/moscow'),
        }
    
    @api.model
    def set_date_panel_enabled(self, enabled):
        """Включить/выключить панель даты"""
        self.sudo().set_param('l3.date_panel.enabled', str(enabled))
    
    @api.model
    def set_date_panel_format(self, format_type):
        """Установить формат отображения даты"""
        self.sudo().set_param('l3.date_panel.format', format_type)
    
    @api.model
    def set_date_panel_timezone(self, timezone):
        """Установить часовой пояс"""
        self.sudo().set_param('l3.date_panel.timezone', timezone)
    
    @api.model
    def set_date_panel_link_url(self, url):
        """Установить URL для ссылки при клике"""
        self.sudo().set_param('l3.date_panel.link_url', url)

