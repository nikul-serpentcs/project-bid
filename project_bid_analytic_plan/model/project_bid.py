# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from openerp import api, fields, models, _
import time
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError


class ProjectBid(models.Model):
    _inherit = 'project.bid'

    project_id = fields.Many2one(
            'project.project', 'Project', required=False,
            ondelete='set null', select=True,
            readonly=True, states={'draft': [('readonly', False)]})
    plan_lines = fields.Many2many(
            'account.analytic.line.plan',
            string='Analytic Plan Lines',
            readonly=True, copy=False)

    @api.model
    def _prepare_cost_plan_lines(self, line):
        plan_version_obj = self.env['account.analytic.plan.version']
        res = {}
        res['value'] = {}
        if line.name:
            name = line.name
        elif line.product_id:
            name = line.product_id.default_code
        else:
            raise UserError(_("All the material components have to "
                            "include at least a description or a product"))

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
            property_account_expense_id.id
        if not general_account_id:
            general_account_id = product_id.categ_id.\
                property_account_expense_categ_id.id
        if not general_account_id:
            raise UserError(_('There is no expense account defined '
                              'for this product: "%s" (id:%d)') %
                            (product_id.name, product_id.id,))
        default_plan = plan_version_obj.search(
            [('default_plan', '=', True)], limit=1)
        if account_id.active_analytic_planning_version != default_plan:
            raise UserError(_('Error !'),
                            _('The active planning version of the '
                            'analytic account must be %s. ')
                            % (default_plan.name,))

        return [{
            'account_id': account_id.id,
            'name': name,
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

    @api.model
    def create_cost_plan_lines(self, line):
        res = []
        line_plan_obj = self.env['account.analytic.line.plan']
        lines_vals = self._prepare_cost_plan_lines(line)
        for line_vals in lines_vals:
            line_id = line_plan_obj.create(line_vals)
            res.append(line_id.id)
        return res

    @api.multi
    def _prepare_revenue_plan_lines(self):
        for bid in self:
            plan_version_obj = self.env['account.analytic.plan.version']
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
                property_account_income_id.id
            if not general_account_id:
                general_account_id = product_id.categ_id.\
                    property_account_income_categ_id.id
            if not general_account_id:
                raise UserError(_('There is no expense account defined '
                                  'for this product: "%s" (id:%d)')
                                  % (product_id.name, product_id.id,))
            default_plan = plan_version_obj.search(
                [('default_plan', '=', True)], limit=1)

            if account_id.active_analytic_planning_version != default_plan:
                raise UserError(_('The active planning version of the '
                                  'analytic account must be %s.')
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

    @api.multi
    def create_revenue_plan_lines(self):
        self.ensure_one()
        res = []
        line_plan_obj = self.env['account.analytic.line.plan']
        lines_vals = self._prepare_revenue_plan_lines()
        for line_vals in lines_vals:
            line_id = line_plan_obj.create(line_vals)
            res.append(line_id.id)
        return res

    @api.multi
    def action_button_transfer_to_project(self):
        res = {}
        self._delete_analytic_lines()
        for bid in self:
            if not bid.project_id:
                raise UserError(_('The bids must have a project assigned'))
            line_ids = []
            for component in bid.components:
                for material in component.material_ids:
                    line_ids.extend(bid.create_cost_plan_lines(material))
                for labor in component.labor:
                    line_ids.extend(bid.create_cost_plan_lines(labor))
            for labor in bid.other_labor:
                line_ids.extend(bid.create_cost_plan_lines(labor))
            for expense in bid.other_expenses:
                line_ids.extend(bid.create_cost_plan_lines(expense))
            line_ids.extend(bid.create_revenue_plan_lines())
            bid.write({'plan_lines': [(6, 0, line_ids)]})
        return res

    @api.multi
    def _delete_analytic_lines(self):
        for bid in self:
            for line in bid.plan_lines:
                line.unlink()
        return True

    @api.multi
    def action_button_draft(self):
        res = super(ProjectBid, self).action_button_draft()
        self._delete_analytic_lines()
        return res

    @api.multi
    def action_button_cancel(self):
        res = super(ProjectBid, self).action_button_cancel()
        self._delete_analytic_lines()
        return res
