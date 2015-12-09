# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              <contact@eficent.com>
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
from openerp.tools.translate import _
from openerp.osv import fields, orm
import time
import decimal_precision as dp


class AnalyticPlanMassCreate(orm.TransientModel):
    _name = "analytic.plan.mass.create"
    _description = "Create multiple analytic plan lines"

    _columns = {
        'item_ids': fields.one2many(
            'analytic.plan.mass.create.item',
            'wiz_id', 'Items'),
        'template_id': fields.many2one('analytic.plan.mass.create.template',
                                       'Template', required=True,
                                       ondelete='cascade'),
    }

    def _prepare_item(self, cr, uid, account, context=None):
        return [{
            'account_id': account.id,
            'company_id': account.company_id.id,
            'date': time.strftime('%Y-%m-%d')
        }]

    def default_get(self, cr, uid, fields, context=None):
        res = super(AnalyticPlanMassCreate, self).default_get(
            cr, uid, fields, context=context)
        analytic_obj = self.pool['account.analytic.account']
        analytic_account_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not analytic_account_ids:
            return res
        assert active_model == 'account.analytic.account', \
            'Bad context propagation'

        items = []
        for account in analytic_obj.browse(cr, uid, analytic_account_ids,
                                           context=context):
                items += self._prepare_item(cr, uid, account, context=context)
        res['item_ids'] = items

        return res

    def _prepare_analytic_line_plan_common(self, cr, uid, wizard, item,
                                           context=None):

        return {
            'account_id': item.account_id.id,
            'name': item.account_id.name,
            'date': item.date,
            'currency_id': wizard.template_id.currency_id.id,
            'user_id': uid,
            'company_id': item.account_id.company_id.id,
            'version_id': wizard.template_id.version_id.id
        }

    def _prepare_analytic_line_plan(self, cr, uid, wizard, item, product,
                                    amount_currency, type, common,
                                    context=None):
        plan_line_obj = self.pool['account.analytic.line.plan']
        am = plan_line_obj.on_change_amount_currency(
            cr, uid, False, amount_currency,
            wizard.template_id.currency_id.id,
            item.account_id.company_id.id, context=context)
        if am and 'value' in am and 'amount' in am['value']:
            amount = am['value']['amount']
        else:
            amount = item.labor_cost

        if type == 'expense':
            general_account_id = product.product_tmpl_id.\
                property_account_expense.id
            if not general_account_id:
                general_account_id = product.categ_id.\
                    property_account_expense_categ.id
        else:
            general_account_id = product.product_tmpl_id.\
                property_account_income.id
            if not general_account_id:
                general_account_id = product.categ_id.\
                    property_account_income_categ.id
        if not general_account_id:
            raise orm.except_orm(_('Error !'),
                                 _('There is no expense or income account '
                                   'defined for this product: "%s" (id:%d)')
                                 % (product.name,
                                    product.id,))
        if type == 'expense':
            journal_id = product.expense_analytic_plan_journal_id \
                and product.expense_analytic_plan_journal_id.id \
                or False
        else:
            journal_id = product.revenue_analytic_plan_journal_id \
                and product.revenue_analytic_plan_journal_id.id \
                or False
        if not journal_id:
            raise orm.except_orm(_('Error !'),
                                 _('There is no planning expense or revenue '
                                   'journals defined for this product: '
                                   '"%s" (id:%d)') % (product.name,
                                                      product.id,))
        if type == 'expense':
            amount_currency *= -1
            amount *= -1

        data = {
            'amount_currency': amount_currency,
            'amount': amount,
            'product_id': product.id,
            'product_uom_id':
                wizard.template_id.labor_cost_product_id.uom_id.id,
            'general_account_id': general_account_id,
            'journal_id': journal_id,
        }
        data.update(common)
        return data

    def create_analytic_plan_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = []
        wizard = self.browse(cr, uid, ids[0], context=context)
        analytic_line_plan_obj = self.pool['account.analytic.line.plan']
        for item in wizard.item_ids:
            if item.delete_existing:
                line_ids = analytic_line_plan_obj.search(cr, uid,
                                        [('account_id', '=',
                                          item.account_id.id),
                                         ('version_id', '=',
                                          wizard.template_id.version_id.id)],
                                        context=context)
                if line_ids:
                    analytic_line_plan_obj.unlink(cr, uid, line_ids,
                                                  context=context)

            common = self._prepare_analytic_line_plan_common(
                cr, uid, wizard, item, context=context)

            # Create Labor costs
            if item.labor_cost:
                plan_line_data_labor = \
                    self._prepare_analytic_line_plan(
                        cr, uid, wizard, item,
                        wizard.template_id.labor_cost_product_id,
                        item.labor_cost, 'expense', common, context=context)
                plan_line_id = analytic_line_plan_obj.create(
                    cr, uid, plan_line_data_labor, context=context)
                res.append(plan_line_id)

            # Create Material costs
            if item.material_cost:
                plan_line_data_material = \
                    self._prepare_analytic_line_plan(
                        cr, uid, wizard, item,
                        wizard.template_id.material_cost_product_id,
                        item.material_cost, 'expense', common,
                        context=context)

                plan_line_id = analytic_line_plan_obj.create(
                    cr, uid, plan_line_data_material, context=context)
                res.append(plan_line_id)

            # Create Revenue
            if item.revenue:
                plan_line_data_revenue = \
                    self._prepare_analytic_line_plan(
                        cr, uid, wizard, item,
                        wizard.template_id.revenue_product_id,
                        item.revenue, 'revenue', common, context=context)
                plan_line_id = analytic_line_plan_obj.create(
                    cr, uid, plan_line_data_revenue, context=context)
                res.append(plan_line_id)

        return {
            'domain': "[('id','in', ["+','.join(map(str, res))+"])]",
            'name': _('Analytic Plan Lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line.plan',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }


class AnalyticPlanMassCreateItem(orm.TransientModel):
    _name = "analytic.plan.mass.create.item"
    _description = "Create multiple analytic plan lines item"

    _columns = {
        'wiz_id': fields.many2one(
            'analytic.plan.mass.create',
            'Wizard', required=True, ondelete='cascade',
            readonly=True),
        'account_id': fields.many2one('account.analytic.account',
                                      'Analytic Account', required=True),
        'date': fields.date('Date', required=True),
        'material_cost': fields.float(
            'Planned material cost', required=True,
            help='Planned material cost, expressed it in positive quantity.',
            digits_compute=dp.get_precision('Account')),
        'labor_cost': fields.float(
            'Planned labor cost', required=True,
            help='Planned labor cost, expressed it in positive quantity.',
            digits_compute=dp.get_precision('Account')),
        'revenue': fields.float(
            'Planned revenue', required=True,
            help='Planned Revenue',
            digits_compute=dp.get_precision('Account')),
        'delete_existing': fields.boolean(
            'Delete existing',
            help='Delete existing planned lines. Will delete all planning '
                 'lines for this analytic account for the version indicated '
                 'in the template, and regardless of the date.'),
    }
