from odoo import models, fields, api


class CreatePartnerWizard(models.TransientModel):
    _name = 'create.partner.wizard'
    _description = 'Create Partner Wizard'

    name = fields.Char(string='Name', required=True)
    is_company = fields.Boolean(string='Is Company', required=True)

    def action_create_partner(self):
        """Create partner and return to the created record"""
        # Создаем нового партнера
        partner = self.env['res.partner'].create({
            'name': self.name,
            'is_company': self.is_company,
        })
        
        # Возвращаемся к созданной записи
        return {
            'type': 'ir.actions.act_window',
            'name': 'Partner',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """Cancel wizard"""
        return {'type': 'ir.actions.act_window_close'}




