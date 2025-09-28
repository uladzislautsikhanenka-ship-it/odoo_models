# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_primary = fields.Boolean(
        string='Primary Contact',
        default=False,
        help='Mark this contact as the primary contact for the company'
    )

    primary_contact = fields.Char(
        string='Primary Contact',
        compute='_compute_primary_contact',
        store=False,
        help='Shows if this contact is the primary contact for the company'
    )

    @api.depends('is_primary', 'parent_id')
    def _compute_primary_contact(self):
        for partner in self:
            if partner.is_primary and partner.parent_id:
                partner.primary_contact = f"✓ Основной контакт для {partner.parent_id.name}"
            elif partner.is_primary:
                partner.primary_contact = "✓ Основной контакт"
            else:
                partner.primary_contact = ""

    @api.constrains('is_primary', 'parent_id')
    def _check_primary_contact(self):
        for partner in self:
            if partner.is_primary and partner.parent_id:
                existing_primary = self.search([
                    ('parent_id', '=', partner.parent_id.id),
                    ('is_primary', '=', True),
                    ('id', '!=', partner.id)
                ])
                if existing_primary:
                    raise ValidationError(
                        _('Только один основной контакт разрешен для компании. '
                          'Контакт "%s" уже помечен как основной для "%s".') %
                        (existing_primary[0].name, partner.parent_id.name)
                    )

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            if partner.is_primary and partner.parent_id:
                self._unset_other_primary_contacts(partner.parent_id.id, partner.id)
        return partners

    def write(self, vals):
        for partner in self:
            if 'is_primary' in vals and partner.parent_id:
                if vals['is_primary']:
                    self._unset_other_primary_contacts(partner.parent_id.id, partner.id)
        return super().write(vals)

    def _unset_other_primary_contacts(self, parent_id, exclude_id=None):
        domain = [
            ('parent_id', '=', parent_id),
            ('is_primary', '=', True)
        ]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))

        other_primary_contacts = self.search(domain)
        if other_primary_contacts:
            other_primary_contacts.write({'is_primary': False})

    def unlink(self):
        for partner in self:
            if partner.is_primary:
                raise UserError(
                    _('❌ Нельзя удалить основной контакт "%s"!\n\n'
                      'Чтобы удалить этот контакт:\n'
                      '1. Сначала снимите с него статус основного контакта\n'
                      '2. Или назначьте другой контакт основным\n'
                      '3. Затем удалите этот контакт') %
                    partner.name
                )
        return super().unlink()

    @api.model
    def _get_primary_contact_domain(self, parent_id):
        return [
            ('parent_id', '=', parent_id),
            ('is_primary', '=', True)
        ]

    def get_primary_contact(self):
        self.ensure_one()
        if self.is_company:
            return self.search(self._get_primary_contact_domain(self.id), limit=1)
        elif self.parent_id:
            return self.search(self._get_primary_contact_domain(self.parent_id.id), limit=1)
        return self.env['res.partner']

    def action_save_contact(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window_close'
        }

    def action_remove_contact(self):
        self.ensure_one()
        if self.is_primary:
            raise UserError(_('❌ Нельзя удалить основной контакт "%s"!\n\n'
                              'Чтобы удалить этот контакт:\n'
                              '1. Сначала снимите с него статус основного контакта\n'
                              '2. Или назначьте другой контакт основным\n'
                              '3. Затем удалите этот контакт') % self.name)
        self.unlink()
        return {
            'type': 'ir.actions.act_window_close'
        }

    def action_toggle_primary(self):
        self.ensure_one()
        if not self.parent_id:
            raise UserError(_('Только дочерние контакты могут быть помечены как основные.'))

        if self.is_primary:
            self.is_primary = False
        else:
            self._unset_other_primary_contacts(self.parent_id.id, self.id)
            self.is_primary = True

        return True

    def action_toggle_primary_kanban(self):
        """Toggle primary contact from kanban view"""
        self.ensure_one()
        if not self.parent_id:
            raise UserError(_('Только дочерние контакты могут быть помечены как основные.'))

        if self.is_primary:
            self.is_primary = False
            message = _('Контакт "%s" больше не является основным для "%s"') % (self.name, self.parent_id.name)
        else:
            self._unset_other_primary_contacts(self.parent_id.id, self.id)
            self.is_primary = True
            message = _('Контакт "%s" теперь является основным для "%s"') % (self.name, self.parent_id.name)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Статус обновлен'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
