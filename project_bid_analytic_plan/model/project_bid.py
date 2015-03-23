# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester <jordi.ballester@eficent.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp


class project_bid(orm.Model):
    _inherit = 'project.bid'

    _columns = {
        'plan_lines': fields.many2many(
            'account.analytic.line.plan',
            string='Analytic Plan Lines',
            readonly=True),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'plan_lines': []
        })

    def _prepare_cost_plan_lines(self, cr, uid, line, context=None):
        plan_version_obj = self.pool.get('account.analytic.plan.version')
        res = {}
        res['value'] = {}
        if line.product_id:
            product_id = line.product_id
            uom_id = line.uom_id
        else:
            product_id = line.bid_id.bid_template_id.expense_product_id
            uom_id = product_id.uom_id

        account_id = line.bid_id.project_id.analytic_account_id
        journal_id = product_id.expense_analytic_plan_journal_id \
            and product_id.expense_analytic_plan_journal_id.id \
            or False
        version_id = line.bid_id.bid_template_id.version_id.id or False

        general_account_id = product_id.product_tmpl_id.\
            property_account_expense.id
        if not general_account_id:
            general_account_id = product_id.categ_id.\
                property_account_expense_categ.id
        if not general_account_id:
            raise orm.except_orm(_('Error !'),
                                 _('There is no expense account defined '
                                   'for this product: "%s" (id:%d)')
                                 % (product_id.name,
                                    product_id.id,))
        default_plan_ids = plan_version_obj.search(
            cr, uid, [('default_plan', '=', True)],  context=context)
        if default_plan_ids:
            default_plan = plan_version_obj.browse(cr, uid,
                                                   default_plan_ids[0],
                                                   context=context)
        else:
            default_plan = False

        if account_id.active_analytic_planning_version != default_plan:
            raise orm.except_orm(_('Error !'),
                                 _('The active planning version of the '
                                   'analytic account must be %s. '
                                   '')
                                 % (default_plan.name,))

        return [{
            'account_id': account_id.id,
            'name': line.name,
            'date': time.strftime('%Y-%m-%d'),
            'product_id': product_id.id,
            'product_uom_id': uom_id.id,
            'unit_amount': line.quantity,
            'amount': -1*line.unit_cost *
            line.quantity,
            'general_account_id': general_account_id,
            'journal_id': journal_id,
            'version_id': version_id,
            'currency_id': account_id.company_id.currency_id.id,
            'amount_currency': line.unit_cost *
            line.quantity,
        }]

    def create_cost_plan_lines(self, cr, uid, line, context=None):
        res = []
        line_plan_obj = self.pool.get('account.analytic.line.plan')
        lines_vals = self._prepare_cost_plan_lines(cr, uid, line,
                                                   context=context)
        for line_vals in lines_vals:
            line_id = line_plan_obj.create(cr, uid, line_vals, context=context)
            res.append(line_id)
        return res

    def _prepare_revenue_plan_lines(self, cr, uid, bid, context=None):
        plan_version_obj = self.pool.get('account.analytic.plan.version')
        res = {}
        res['value'] = {}
        account_id = bid.project_id.analytic_account_id
        product_id = bid.bid_template_id.revenue_product_id
        journal_id = \
            product_id.revenue_analytic_plan_journal_id \
            and product_id.revenue_analytic_plan_journal_id.id \
            or False
        version_id = bid.bid_template_id.version_id.id or False

        general_account_id = product_id.product_tmpl_id.\
            property_account_income.id
        if not general_account_id:
            general_account_id = product_id.categ_id.\
                property_account_income_categ.id
        if not general_account_id:
            raise orm.except_orm(_('Error !'),
                                 _('There is no expense account defined '
                                   'for this product: "%s" (id:%d)')
                                 % (product_id.name,
                                    product_id.id,))
        default_plan_ids = plan_version_obj.search(
            cr, uid, [('default_plan', '=', True)],  context=context)
        if default_plan_ids:
            default_plan = plan_version_obj.browse(cr, uid,
                                                   default_plan_ids[0],
                                                   context=context)
        else:
            default_plan = False

        if account_id.active_analytic_planning_version != default_plan:
            raise orm.except_orm(_('Error !'),
                                 _('The active planning version of the '
                                   'analytic account must be %s. '
                                   '')
                                 % (default_plan.name,))

        return [{
            'account_id': account_id.id,
            'name': product_id.name,
            'date': time.strftime('%Y-%m-%d'),
            'product_id': product_id.id,
            'product_uom_id': product_id.uom_id.id,
            'unit_amount': 1,
            'amount': bid.total_income,
            'general_account_id': general_account_id,
            'journal_id': journal_id,
            'version_id': version_id,
            'currency_id': account_id.company_id.currency_id.id,
            'amount_currency': bid.total_income,
        }]

    def create_revenue_plan_lines(self, cr, uid, bid, context=None):
        res = []
        line_plan_obj = self.pool.get('account.analytic.line.plan')
        lines_vals = self._prepare_revenue_plan_lines(cr, uid, bid,
                                                      context=context)
        for line_vals in lines_vals:
            line_id = line_plan_obj.create(cr, uid, line_vals, context=context)
            res.append(line_id)
        return res

    def action_button_confirm(self, cr, uid, ids, form, context=None):
        res = super(project_bid, self).action_button_confirm(
            cr, uid, ids, form, context=context)

        for bid in self.browse(cr, uid, ids, context=context):
            line_ids = []
            for component in bid.components:
                line_ids.extend(self.create_cost_plan_lines(
                    cr, uid, component, context=context))
                for labor in component.labor:
                    line_ids.extend(self.create_cost_plan_lines(
                        cr, uid, labor, context=context))
            for labor in bid.other_labor:
                line_ids.extend(self.create_cost_plan_lines(
                    cr, uid, labor, context=context))
            for expense in bid.other_expenses:
                line_ids.extend(self.create_cost_plan_lines(
                    cr, uid, expense, context=context))
            line_ids.extend(self.create_revenue_plan_lines(
                cr, uid, bid, context=context))
            self.write(cr, uid, bid.id, {'plan_lines': [(6, 0, line_ids)]},
                       context=context)

        return res

    def _delete_analytic_lines(self, cr, uid, ids, context=None):
        line_plan_obj = self.pool.get('account.analytic.line.plan')
        for bid in self.browse(cr, uid, ids, context=context):
            plan_lines = []
            for line in bid.plan_lines:
                plan_lines.append(line.id)
            line_plan_obj.unlink(cr, uid, plan_lines, context=context)
        return True

    def action_button_draft(self, cr, uid, ids, form, context=None):
        res = super(project_bid, self).action_button_draft(
            cr, uid, ids, form, context=context)
        self._delete_analytic_lines(cr, uid, ids, context=context)
        return res

    def action_button_cancel(self, cr, uid, ids, form, context=None):
        res = super(project_bid, self).action_button_cancel(
            cr, uid, ids, form, context=context)
        self._delete_analytic_lines(cr, uid, ids, context=context)
        return res
