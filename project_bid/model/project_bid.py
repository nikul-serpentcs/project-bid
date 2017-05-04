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


class project_bid_total_labor(orm.TransientModel):
    _name = 'project.bid.total.labor'
    _description = "Project Bid Labor Totals"

    _columns = {
        'bid_id': fields.many2one('project.bid', string='Bid',
                                  required=True),
        'name': fields.char('Description', size=256),
        'quantity': fields.float('Hours'),
        'cogs': fields.float('COGS'),
        'overhead': fields.float('Overhead cost'),
        'cost': fields.float('Total cost'),
        'profit': fields.float('Profit'),
        'sell': fields.float('Revenue'),
    }


class project_bid_totals(orm.TransientModel):
    _name = 'project.bid.totals'
    _description = "Project Bid Totals"

    _columns = {
        'bid_id': fields.many2one('project.bid', string='Bid', required=True),
        'name': fields.char('Description', size=256),
        'cogs': fields.float('COGS'),
        'overhead': fields.float('Overhead cost'),
        'cost': fields.float('Total cost'),
        'profit': fields.float('Profit'),
        'sell': fields.float('Revenue'),
    }


class project_bid(orm.Model):
    _name = 'project.bid'
    _description = "Project Bid"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _get_child_bids(self, cr, uid, ids, context=None):
        result = {}
        if not ids:
            return result
        for curr_id in ids:
            result[curr_id] = True
        # Now add the children
        cr.execute('''
        WITH RECURSIVE children AS (
        SELECT parent_id, id
        FROM project_bid
        WHERE parent_id IN %s
        UNION ALL
        SELECT a.parent_id, a.id
        FROM project_bid a
        JOIN children b ON(a.parent_id = b.id)
        )
        SELECT * FROM children order by parent_id
        ''', (tuple(ids),))
        res = cr.fetchall()
        for x, y in res:
            result[y] = True
        return result

    def get_child_bids(self, cr, uid, ids, context=None):
        res = self._get_child_bids(cr, uid, ids, context=None)
        return res.keys()

    def _get_totals_labor(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        costs_line_obj = self.pool.get('project.bid.total.labor')
        for bid in self.browse(cr, uid, ids, context=context):
            vals = []
            items = {}
            for component in bid.components:
                for labor in component.labor:
                    if labor.product_id.id not in items:
                        items[labor.product_id.id] = {
                            'name': labor.product_id.name,
                            'quantity': labor.quantity,
                            'cogs': labor.cogs,
                            'overhead': labor.overhead,
                            'cost': labor.cost,
                            'profit': labor.profit,
                            'sell': labor.sell,
                        }
                    else:
                        items[labor.product_id.id]['quantity'] \
                            += labor.quantity
                        items[labor.product_id.id]['cogs'] \
                            += labor.cogs
                        items[labor.product_id.id]['overhead'] \
                            += labor.overhead
                        items[labor.product_id.id]['cost'] \
                            += labor.cost
                        items[labor.product_id.id]['profit'] \
                            += labor.profit
                        items[labor.product_id.id]['sell'] \
                            += labor.sell

            for labor in bid.other_labor:
                if labor.product_id.id not in items:
                    items[labor.product_id.id] = {
                        'name': labor.product_id.name,
                        'quantity': labor.quantity,
                        'cogs': labor.cogs,
                        'overhead': labor.overhead,
                        'cost': labor.cost,
                        'profit': labor.profit,
                        'sell': labor.sell,
                    }
                else:
                    items[labor.product_id.id]['quantity'] \
                        += labor.quantity
                    items[labor.product_id.id]['cogs'] \
                        += labor.cogs
                    items[labor.product_id.id]['overhead'] \
                        += labor.overhead
                    items[labor.product_id.id]['cost'] \
                        += labor.cost
                    items[labor.product_id.id]['profit'] \
                        += labor.profit
                    items[labor.product_id.id]['sell'] \
                        += labor.sell
            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(cr, uid, val,
                                                context=context)
                vals.append(line_id)
            res[bid.id] = vals
        return res

    def _get_wbs_totals_labor(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        costs_line_obj = self.pool.get('project.bid.total.labor')
        for bid in self.browse(cr, uid, ids, context=context):
            bid_ids = self.get_child_bids(cr, uid, [bid.id], context=context)
            vals = []
            items = {}
            for bid_2 in self.browse(cr, uid, bid_ids, context=context):
                for component in bid_2.components:
                    for labor in component.labor:
                        if labor.product_id.id not in items:
                            items[labor.product_id.id] = {
                                'name': labor.product_id.name,
                                'quantity': labor.quantity,
                                'cogs': labor.cogs,
                                'overhead': labor.overhead,
                                'cost': labor.cost,
                                'profit': labor.profit,
                                'sell': labor.sell,
                            }
                        else:
                            items[labor.product_id.id]['quantity'] \
                                += labor.quantity
                            items[labor.product_id.id]['cogs'] \
                                += labor.cogs
                            items[labor.product_id.id]['overhead'] \
                                += labor.overhead
                            items[labor.product_id.id]['cost'] \
                                += labor.cost
                            items[labor.product_id.id]['profit'] \
                                += labor.profit
                            items[labor.product_id.id]['sell'] \
                                += labor.sell

                for labor in bid_2.other_labor:
                    if labor.product_id.id not in items:
                        items[labor.product_id.id] = {
                            'name': labor.product_id.name,
                            'quantity': labor.quantity,
                            'cogs': labor.cogs,
                            'overhead': labor.overhead,
                            'cost': labor.cost,
                            'profit': labor.profit,
                            'sell': labor.sell,
                        }
                    else:
                        items[labor.product_id.id]['quantity'] \
                            += labor.quantity
                        items[labor.product_id.id]['cogs'] \
                            += labor.cogs
                        items[labor.product_id.id]['overhead'] \
                            += labor.overhead
                        items[labor.product_id.id]['cost'] \
                            += labor.cost
                        items[labor.product_id.id]['profit'] \
                            += labor.profit
                        items[labor.product_id.id]['sell'] \
                            += labor.sell
            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(cr, uid, val,
                                                context=context)
                vals.append(line_id)
            res[bid.id] = vals
        return res

    def _get_totals_all(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        costs_line_obj = self.pool.get('project.bid.totals')
        for bid in self.browse(cr, uid, ids, context=context):
            vals = []
            items = {}
            material_cogs = 0.0
            material_overhead = 0.0
            material_cost = 0.0
            material_profit = 0.0
            material_sell = 0.0
            # Total labor
            labor_cogs = 0.0
            labor_overhead = 0.0
            labor_cost = 0.0
            labor_profit = 0.0
            labor_sell = 0.0

            for component in bid.components:
                material_cogs += component.material_cogs
                material_overhead += component.material_overhead
                material_cost += component.material_cost
                material_profit += component.material_profit
                material_sell += component.material_sell

            for labor in bid.totals_non_material:
                labor_cogs += labor.cogs
                labor_overhead += labor.overhead
                labor_cost += labor.cost
                labor_profit += labor.profit
                labor_sell += labor.sell

            # Other expenses
            for expense in bid.other_expenses:
                if expense.product_id.id not in items:
                    items[expense.product_id.id] = {
                        'name': expense.product_id.name,
                        'quantity': expense.quantity,
                        'cogs': expense.cogs,
                        'overhead': expense.overhead,
                        'cost': expense.cost,
                        'profit': expense.profit,
                        'sell': expense.sell
                    }
                else:
                    items[expense.product_id.id]['quantity'] \
                        += expense.quantity
                    items[expense.product_id.id]['cogs'] \
                        += expense.cogs
                    items[expense.product_id.id]['overhead'] \
                        += expense.overhead
                    items[expense.product_id.id]['cost'] \
                        += expense.cost
                    items[expense.product_id.id]['profit'] \
                        += expense.profit
                    items[expense.product_id.id]['sell'] \
                        += expense.sell

            val = {
                'bid_id': bid.id,
                'name': 'Total material',
                'cogs': material_cogs,
                'overhead': material_overhead,
                'cost': material_cost,
                'profit': material_profit,
                'sell': material_sell,
            }
            line_id = costs_line_obj.create(cr, uid, val, context=context)
            vals.append(line_id)

            val = {
                'bid_id': bid.id,
                'name': 'Total labor',
                'cogs': labor_cogs,
                'overhead': labor_overhead,
                'cost': labor_cost,
                'profit': labor_profit,
                'sell': labor_sell,
                }
            line_id = costs_line_obj.create(cr, uid, val, context=context)
            vals.append(line_id)

            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(cr, uid, val, context=context)
                vals.append(line_id)
            res[bid.id] = vals
        return res

    def _get_wbs_totals_all(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        costs_line_obj = self.pool.get('project.bid.totals')
        for bid in self.browse(cr, uid, ids, context=context):
            bid_ids = self.get_child_bids(cr, uid, [bid.id], context=context)
            vals = []
            items = {}
            material_cogs = 0.0
            material_overhead = 0.0
            material_cost = 0.0
            material_profit = 0.0
            material_sell = 0.0
            # Total labor
            labor_cogs = 0.0
            labor_overhead = 0.0
            labor_cost = 0.0
            labor_profit = 0.0
            labor_sell = 0.0
            for bid_2 in self.browse(cr, uid, bid_ids, context=context):
                for component in bid_2.components:
                    material_cogs += component.material_cogs
                    material_overhead += component.material_overhead
                    material_cost += component.material_cost
                    material_profit += component.material_profit
                    material_sell += component.material_sell

                for labor in bid_2.totals_non_material:
                    labor_cogs += labor.cogs
                    labor_overhead += labor.overhead
                    labor_cost += labor.cost
                    labor_profit += labor.profit
                    labor_sell += labor.sell

                # Other expenses
                for expense in bid_2.other_expenses:
                    if expense.product_id.id not in items:
                        items[expense.product_id.id] = {
                            'name': expense.product_id.name,
                            'quantity': expense.quantity,
                            'cogs': expense.cogs,
                            'overhead': expense.overhead,
                            'cost': expense.cost,
                            'profit': expense.profit,
                            'sell': expense.sell
                        }
                    else:
                        items[expense.product_id.id]['quantity'] \
                            += expense.quantity
                        items[expense.product_id.id]['cogs'] \
                            += expense.cogs
                        items[expense.product_id.id]['overhead'] \
                            += expense.overhead
                        items[expense.product_id.id]['cost'] \
                            += expense.cost
                        items[expense.product_id.id]['profit'] \
                            += expense.profit
                        items[expense.product_id.id]['sell'] \
                            += expense.sell

            val = {
                'bid_id': bid.id,
                'name': 'Total material',
                'cogs': material_cogs,
                'overhead': material_overhead,
                'cost': material_cost,
                'profit': material_profit,
                'sell': material_sell,
            }
            line_id = costs_line_obj.create(cr, uid, val, context=context)
            vals.append(line_id)

            val = {
                'bid_id': bid.id,
                'name': 'Total labor',
                'cogs': labor_cogs,
                'overhead': labor_overhead,
                'cost': labor_cost,
                'profit': labor_profit,
                'sell': labor_sell,
                }
            line_id = costs_line_obj.create(cr, uid, val, context=context)
            vals.append(line_id)

            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(cr, uid, val, context=context)
                vals.append(line_id)
            res[bid.id] = vals
        return res

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for bid in self.browse(cr, uid, ids, context=context):
            total_cogs = 0.0
            total_overhead = 0.0
            total_cost = 0.0
            total_profit = 0.0
            total_sell = 0.0
            for total in bid.totals_all:
                total_cogs += total.cogs
                total_overhead += total.overhead
                total_cost += total.cost
                total_profit += total.profit
                total_sell += total.sell

            # Gross profit and gross margin
            total_gp = total_sell - total_cogs
            try:
                total_gm_percent = round((total_gp/total_sell)*100, 2)
            except ZeroDivisionError:
                total_gm_percent = 0.0

            # Profit Margin
            total_npm = total_sell - total_cost
            try:
                total_npm_percent = round((total_npm/total_sell)*100, 2)
            except ZeroDivisionError:
                total_npm_percent = 0.0

            res[bid.id] = {
                'total_income': total_sell,
                'total_cogs': total_cogs,
                'total_gm_percent': total_gm_percent,
                'total_gp': total_gp,
                'total_overhead': total_overhead,
                'total_npm': total_npm,
                'total_npm_percent': total_npm_percent,
            }
        return res

    def _get_wbs_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for bid in self.browse(cr, uid, ids, context=context):
            bid_ids = self.get_child_bids(cr, uid, [bid.id], context=context)
            total_cogs = 0.0
            total_overhead = 0.0
            total_cost = 0.0
            total_profit = 0.0
            total_sell = 0.0
            for bid2 in self.browse(cr, uid, bid_ids, context=context):
                for total in bid2.totals_all:
                    total_cogs += total.cogs
                    total_overhead += total.overhead
                    total_cost += total.cost
                    total_profit += total.profit
                    total_sell += total.sell

            # Gross profit and gross margin
            total_gp = total_sell - total_cogs
            try:
                total_gm_percent = round((total_gp/total_sell)*100, 2)
            except ZeroDivisionError:
                total_gm_percent = 0.0

            # Profit Margin
            total_npm = total_sell - total_cost
            try:
                total_npm_percent = round((total_npm/total_sell)*100, 2)
            except ZeroDivisionError:
                total_npm_percent = 0.0

            res[bid.id] = {
                'wbs_total_income': total_sell,
                'wbs_total_cogs': total_cogs,
                'wbs_total_gm_percent': total_gm_percent,
                'wbs_total_gp': total_gp,
                'wbs_total_overhead': total_overhead,
                'wbs_total_npm': total_npm,
                'wbs_total_npm_percent': total_npm_percent,
            }
        return res

    def _get_gm_percent(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for bid in self.browse(cr, uid, ids, context=context):
            res[bid.id] = 0.0
            if bid.total_cost:
                try:
                    res[bid.id] = \
                        round(((bid.total_sell - bid.total_cost)
                               / bid.total_cost)*100, 2)
                except ZeroDivisionError:
                    res[bid.id] = 0.0
        return res

    def _complete_bid_hierarchy_code_calc(
            self, cr, uid, ids, prop, unknow_none, unknow_dict):
        if not ids:
            return []
        res = []
        for bid in self.browse(cr, uid, ids, context=None):
            data = []
            b = bid
            while b:
                if b.code:
                    data.insert(0, b.code)
                else:
                    data.insert(0, '')

                b = b.parent_id
            data = ' / '.join(data)
            data = '[' + data + '] '

            res.append((bid.id, data))
        return dict(res)

    _track = {
        'state': {
            'project_bid.mt_bid_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'project_bid.mt_bid_approved':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approve',
            'project_bid.mt_bid_draft':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'draft',
            'project_bid.mt_bid_cancel':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'cancel',
        },
    }

    _columns = {
        'state': fields.selection(
            [('draft', 'Draft'),
             ('confirm', 'Awaiting approval'),
             ('approve', 'Approved'),
             ('cancel', 'Cancelled')], 'Status',
            select=True, required=True, readonly=True,
            help=' * The \'Draft\' status is used when a user is encoding '
                 'a new bid. '
                 '\n* The \'Confirmed\' status is used to confirm the '
                 'bid by the user.'
                 '\n* The \'Approved\' status is used to approve the '
                 'bid by an authorized user.'
                 '\n* The \'Cancelled\' status is used to cancel '
                 'the bid.'),
        'bid_template_id': fields.many2one('project.bid.template',
                                           'Bid Template', required=True,
                                           ondelete='cascade', select=True,
                                           readonly=True,
                                           states={
                                               'draft': [('readonly', False)]
                                           }),
        'parent_id': fields.many2one('project.bid', 'Parent Bid',
                                     required=False, ondelete='set null',
                                     readonly=True,
                                     states={
                                         'draft': [('readonly', False)]
                                     }),
        'child_ids': fields.one2many('project.bid', 'parent_id',
                                     'Child bids'),
        'partner_id': fields.many2one('res.partner',
                                      'Customer', required=True, readonly=True,
                                      states={
                                          'draft': [('readonly', False)]
                                      }),
        'code': fields.char('Reference', select=True, required=True),
        'complete_code': fields.function(
            _complete_bid_hierarchy_code_calc, method=True, type='char',
            string='Complete Reference',
            help='Describes the full path of this '
                 'bid hierarchy.',
            store={
                'project.bid': (_get_child_bids, ['name', 'code',
                                                  'parent_id'], 20),
            }),
        'name': fields.char('Name', size=256, required=True,
                            readonly=True,
                            states={'draft': [('readonly', False)]}),
        'created_on': fields.date('Creation date'),
        'created_by': fields.many2one('res.users', 'Created by',
                                      required=True,
                                      readonly=True,
                                      states={
                                          'draft': [('readonly', False)]
                                      }),
        'approved_by': fields.many2one('res.users', 'Approved by',
                                       required=False,
                                       readonly=True),
        'approved_on': fields.date('Approval date', readonly=True),
        'due_by': fields.date('Due by', required=False, readonly=True,
                              states={
                                  'draft': [('readonly', False)]
                              }),
        'components': fields.one2many('project.bid.component', 'bid_id',
                                      'Bid Lines',
                                      readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'notes': fields.text('Notes', readonly=True,
                             states={'draft': [('readonly', False)]}),
        'totals_non_material': fields.function(
            _get_totals_labor, type='one2many',
            obj='project.bid.total.labor', string='Non material costs'),
        'totals_all': fields.function(
            _get_totals_all, type='one2many',
            obj='project.bid.totals', string='Totals'),
        'wbs_totals_non_material': fields.function(
            _get_wbs_totals_labor, type='one2many',
            obj='project.bid.total.labor', string='WBS Non material costs'),
        'wbs_totals_all': fields.function(
            _get_wbs_totals_all, type='one2many',
            obj='project.bid.totals', string='WBS Totals'),
        'other_labor': fields.one2many('project.bid.other.labor', 'bid_id',
                                       'Other labor', readonly=True,
                                       states={'draft': [('readonly',
                                                          False)]}),
        'other_expenses': fields.one2many('project.bid.other.expenses',
                                          'bid_id',
                                          'Other expenses', readonly=True,
                                          states={'draft': [('readonly',
                                                             False)]}),
        'total_income': fields.function(_get_totals, type='float',
                                        multi='totals', string='Revenue'),
        'total_cogs': fields.function(_get_totals, type='float',
                                      multi='totals', string='Cost of Sales'),
        'total_gm_percent': fields.function(_get_totals, type='float',
                                            multi='totals',
                                            string='Gross Margin (%)'),
        'total_gp': fields.function(_get_totals, type='float',
                                    multi='totals', string='Gross Profit'),
        'total_overhead': fields.function(_get_totals, type='float',
                                          multi='totals',
                                          string='Total Overhead'),
        'total_npm': fields.function(_get_totals, type='float',
                                     multi='totals',
                                     string='Net Profit Margin'),
        'total_npm_percent': fields.function(_get_totals, type='float',
                                             multi='totals',
                                             string='Net Profit Margin (%)'),
        'wbs_total_income': fields.function(_get_wbs_totals, type='float',
                                            multi='wbs_totals',
                                            string='WBS Total Revenue'),
        'wbs_total_cogs': fields.function(_get_totals, type='float',
                                          multi='wbs_totals',
                                          string='WBS Cost of Sales'),
        'wbs_total_gm_percent': fields.function(_get_wbs_totals, type='float',
                                                multi='wbs_totals',
                                                string='WBS Gross Margin (%)'),
        'wbs_total_gp': fields.function(_get_wbs_totals, type='float',
                                        multi='wbs_totals',
                                        string='WBS Gross Profit'),
        'wbs_total_overhead': fields.function(_get_wbs_totals, type='float',
                                              multi='wbs_totals',
                                              string='WBS Total Overhead'),
        'wbs_total_npm': fields.function(_get_wbs_totals, type='float',
                                         multi='wbs_totals',
                                         string='WBS Net Profit Margin'),
        'wbs_total_npm_percent': fields.function(
            _get_wbs_totals, type='float', multi='wbs_totals',
            string='WBS Net Profit Margin %)'),
        'overhead_rate': fields.float(
            'Default Overhead %', digits_compute=dp.get_precision('Account')),
        'profit_rate': fields.float(
            'Default Profit (%) over COGS', ditits_compute=dp.get_precision(
                'Account'),
            help="Profit % over COGS"),
    }

    _defaults = {
        'state': 'draft',
        'created_on': lambda *a: time.strftime('%Y-%m-%d'),
        'created_by': lambda obj, cr, uid, ctx=None: uid,

    }

    _order = 'complete_code'

    def on_change_bid_template_id(self, cr, uid, ids, bid_template_id,
                                  context=None):
        values = {}
        if bid_template_id:
            bid_template = self.pool.get('project.bid.template').browse(
                cr, uid, bid_template_id, context=context)
            values = {
                'overhead_rate': bid_template.overhead_rate,
                'profit_rate': bid_template.profit_rate,
            }
        return {'value': values}

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        bid = self.browse(cr, uid, id, context=context)
        default.update({
            'state': 'draft',
            'name': ("%s (copy)") % (bid.name or ''),
        })

        return super(project_bid, self).copy(cr, uid, id, default,
                                             context=context)

    def action_button_confirm(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        return True

    def action_button_approve(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        vals = {
            'state': 'approve',
            'approved_on': time.strftime('%Y-%m-%d'),
            'approved_by': uid,
        }
        self.write(cr, uid, ids, vals, context=context)
        return True

    def action_button_draft(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        vals = {
            'state': 'draft',
            'approved_on': False,
            'approved_by': False,
        }
        self.write(cr, uid, ids, vals, context=context)
        return True

    def action_button_cancel(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def code_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for item in self.browse(cr, uid, ids, context=context):
            data = []
            bid = item
            while bid:
                if bid.code:
                    data.insert(0, bid.code)
                else:
                    data.insert(0, '')
                bid = bid.parent_id
            data = ' / '.join(data)
            res.append((item.id, data))
        return res

    def name_get(self, cr, uid, ids, context=None):

        if not ids:
            return []
        if type(ids) is int:
            ids = [ids]
        new_list = []
        for i in ids:
            if i not in new_list:
                new_list.append(i)
        ids = new_list

        res = []
        for item in self.browse(cr, uid, ids, context=context):
            data = []
            bid = item
            while bid:
                if bid.name:
                    data.insert(0, bid.name)
                else:
                    data.insert(0, '')
                bid = bid.parent_id
            data = ' / '.join(data)
            res2 = self.code_get(cr, uid, [item.id], context=None)
            if res2:
                data = '[' + res2[0][1] + '] ' + data

            res.append((item.id, data))
        return res


class project_bid_component(orm.Model):
    _name = 'project.bid.component'
    _description = "Project Bid Component"

    def name_get(self, cr, uid, ids, context=None):

        if not ids:
            return []
        if type(ids) is int:
            ids = [ids]
        new_list = []
        for i in ids:
            if i not in new_list:
                new_list.append(i)
        ids = new_list

        res = []
        obj = self.pool.get('project.bid')
        for item in self.browse(cr, uid, ids, context=context):
            data = []
            bid_component = item
            if bid_component.name:
                data.insert(0, bid_component.name)
            else:
                data.insert(0, '')

            data.insert(0, bid_component.bid_id.name)

            data = ' / '.join(data)
            res2 = obj.code_get(cr, uid,[bid_component.bid_id.id], context=None)
            if res2:
                data = '[' + res2[0][1] + '] ' + data

            res.append((item.id, data))
        return res

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            labor_cogs = 0.0
            labor_overhead = 0.0
            labor_cost = 0.0
            labor_profit = 0.0
            labor_sell = 0.0

            material_cogs = 0.0
            material_overhead = 0.0
            material_cost = 0.0
            material_profit = 0.0
            material_sell = 0.0
            quantity = 0.0

            for labor in record.labor:
                labor_cogs += labor.cogs
                labor_overhead += labor.overhead
                labor_cost += labor.cost
                labor_profit += labor.profit
                labor_sell += labor.sell

            for material in record.material_ids:
                material_cogs += material.cogs
                material_overhead += material.overhead
                material_cost += material.cost
                material_profit += material.profit
                material_sell += material.sell
                quantity += material.quantity

            total_cogs = material_cogs + labor_cogs
            total_overhead = material_overhead + labor_overhead
            total_cost = labor_cost + material_cost
            total_profit = material_profit + labor_profit
            total_sell = total_cogs + total_overhead + total_profit
            gross_profit = total_sell - total_cogs

            res[record.id] = {
                'quantity': quantity,
                'material_cogs': material_cogs,
                'material_overhead': material_overhead,
                'material_cost': material_cost,
                'material_profit': material_profit,
                'material_sell': material_sell,
                'labor_cogs': labor_cogs,
                'labor_overhead': labor_overhead,
                'labor_cost': labor_cost,
                'labor_profit': labor_profit,
                'labor_sell': labor_sell,
                'total_cogs': total_cogs,
                'total_overhead': total_overhead,
                'total_cost': total_cost,
                'total_profit': total_profit,
                'total_sell': total_sell,
                'gross_profit': gross_profit,
            }
        return res

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'bid_template_id': fields.related('bid_id', 'bid_template_id',
                                          string="Bid Template",
                                          type='many2one',
                                          relation='project.bid.template',
                                          readonly=True),
        'labor': fields.one2many('project.bid.component.labor',
                                 'bid_component_id', 'Labor'),
        'bid_component_template_id': fields.many2one('project.bid.component',
                                            'Project Bid Component Template',
                                            required=False,
                                            ondelete='set null'),
        'material_ids': fields.one2many('project.bid.component.material',
                                        'bid_component_id',
                                        'Materials'),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'name': fields.char('Description', size=256, required=True),
        'quantity': fields.function(
            _get_totals, type='float', string='Quantity',
            multi='totals'),
        # 'unit_cost': fields.float('Unit Cost'),
        'overhead_rate': fields.float(
            'Overhead %', digits_compute=dp.get_precision('Account')),
        'profit_rate': fields.float(
            'Profit (%) over COGS', ditits_compute=dp.get_precision('Account'),
            help="Profit % over COGS"),
        'material_cogs': fields.function(
            _get_totals, type='float', string='Material COGS',
            multi='totals'),
        'material_overhead': fields.function(
            _get_totals, type='float', string='Material overhead',
            multi='totals'),
        'material_cost': fields.function(
            _get_totals, type='float', string='Material cost',
            multi='totals'),
        'material_profit': fields.function(
            _get_totals, type='float', string='Material profit',
            multi='totals'),
        'material_sell': fields.function(
            _get_totals, type='float', string='Material sell',
            multi='totals'),
        'labor_cogs': fields.function(
            _get_totals, type='float', string='Labor COGS',
            multi='totals'),
        'labor_overhead': fields.function(
            _get_totals, type='float', string='Labor overhead',
            multi='totals'),
        'labor_cost': fields.function(
            _get_totals, type='float', string='Labor cost',
            multi='totals'),
        'labor_profit': fields.function(
            _get_totals, type='float', string='Labor profit',
            multi='totals'),
        'labor_sell': fields.function(
            _get_totals, type='float', string='Labor profit',
            multi='totals'),
        'total_cogs': fields.function(
            _get_totals, type='float', string='Total COGS',
            multi='totals'),
        'gross_profit': fields.function(
            _get_totals, type='float', string='Gross profit',
            multi='totals'),
        'total_overhead': fields.function(
            _get_totals, type='float', string='Total overhead',
            multi='totals'),
        'total_cost': fields.function(
            _get_totals, type='float', string='Total cost',
            multi='totals'),
        'total_profit': fields.function(
            _get_totals, type='float', string='Net profit',
            multi='totals'),
        'total_sell': fields.function(
            _get_totals, type='float', string='Revenue',
            multi='totals'),
    }

    def _get_default_labor(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = []
        bid_template_obj = self.pool.get('project.bid.template')
        if 'bid_template_id' in context and context['bid_template_id']:
            bid_template = bid_template_obj.browse(
                cr, uid, context['bid_template_id'], context=context)
            for product in bid_template.default_component_labor:
                val = {
                    'product_id': product.id,
                    'quantity': 0.0
                }
                res.append(val)
        return res

    def _get_default_profit_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('profit_rate', 0.0)

    def _get_default_overhead_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('overhead_rate', 0.0)

    def _get_default_bid_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('bid_id')

    _defaults = {
        'labor': _get_default_labor,
        'profit_rate': _get_default_profit_rate,
        'overhead_rate': _get_default_overhead_rate,
        'bid_id': _get_default_bid_id,
    }

    def _check_overhead(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.overhead_rate < 0.0:
                return False
        return True

    _constraints = [(_check_overhead, 'Error ! The overhead % must be > 0. ',
                     ['overhead'])]

    def on_change_component_template_id(self, cr, uid, ids,
                                        bid_component_template_id,
                                        context=None):
        values = {}
        if bid_component_template_id:
            bid_component_template = self.browse(cr,uid,
                                       bid_component_template_id,
                                       context=context)
            on_write = False
            if ids:
                bid_component = self.browse(cr, uid,ids[0], context=context)
                on_write = True

            material_list = []
            labor_list = []
            if on_write:
                for material in bid_component.material_ids:
                    material_list.append((2, material.id, 0))

            for material in  bid_component_template.material_ids:
                materialdicc = {
                    'bid_component_id': bid_component.id if on_write else None,
                    'name': material.name,
                    'quantity': material.quantity,
                    'product_id':material.product_id.id,
                    'default_code': material.default_code,
                    'uom_id': material.uom_id.id,
                    'bid_id': material.bid_id.id,
                    'unit_cost': material.unit_cost,
                    'cogs': material.cogs,
                    'overhead': material.overhead,
                    'cost': material.cost,
                    'profit': material.profit,
                    'sell': material.sell,
                }

                material_list.append((0, 0, materialdicc))

            if on_write:
                for labor in bid_component.labor:
                    labor_list.append((2, labor.id, 0))

            for labor in bid_component_template.labor:
                labordicc = {
                    'bid_component_id': bid_component.id if on_write else None,
                    'name': labor.name,
                    'quantity': labor.quantity,
                    'product_id':labor.product_id.id,
                    'uom_id': labor.uom_id.id,
                    'bid_id': labor.bid_id.id,
                    'unit_cost': labor.unit_cost,
                    'cogs': labor.cogs,
                    'overhead': labor.overhead,
                    'cost': labor.cost,
                    'profit': labor.profit,
                    'sell': labor.sell,
                }

                labor_list.append((0, 0, labordicc))

            values = {
                'name': bid_component_template.name,
                'material_ids': material_list,
                'labor': labor_list,
                'bid_component_template_id':False
            }
        return {'value': values}


class project_bid_component_material(orm.Model):
    _name = 'project.bid.component.material'
    _description = "Project Bid Component Material"

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            total_cogs = record.quantity * record.unit_cost
            total_overhead = \
                record.bid_component_id.overhead_rate/100*total_cogs
            total_cost = total_cogs + total_overhead
            total_gross_profit = \
                record.bid_component_id.profit_rate/100*total_cogs
            total_sell = total_cost + total_gross_profit

            res[record.id] = {
                'cogs': total_cogs,
                'overhead': total_overhead,
                'cost': total_cost,
                'profit': total_gross_profit,
                'sell': total_sell,
            }

        return res

    def on_change_product_id(self, cr, uid, ids, product_id, context=None):
        values = {}
        if product_id:
            products = self.pool.get('product.product').browse(cr, uid,
                                                              product_id,
                                                              context=context)
            for product in [products]:
                values = {
                    'name': product.name,
                    'default_code': product.default_code,
                    'unit_cost': product.standard_price,
                }
        return {'value': values}

    _columns = {
        'bid_component_id': fields.many2one('project.bid.component',
                                            'Project Bid Component',
                                            select=True, required=True,
                                            ondelete='cascade'),
        'bid_id': fields.related('bid_component_id', 'bid_id', string="Bid",
                                 type='many2one', relation='project.bid',
                                 readonly=True),
        'product_id': fields.many2one('product.product',
                                      'Material product'),
        'name': fields.char(string="Description"),
        'quantity': fields.float('Quantity'),
        'default_code': fields.char('Part #', help="Material Code"),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'unit_cost': fields.float('Unit Cost', required=True),
        'cogs': fields.function(_get_totals, type='float', multi='totals',
                                string='Total COGS'),
        'overhead': fields.function(_get_totals, type='float',
                                    multi='totals', string='Total overhead'),
        'cost': fields.function(_get_totals, type='float',
                                multi='totals', string='Total costs'),
        'profit': fields.function(_get_totals, type='float',
                                  multi='totals', string='Net profit'),
        'sell': fields.function(_get_totals, type='float',
                                multi='totals', string='Revenue'),
    }


class project_bid_component_labor(orm.Model):
    _name = 'project.bid.component.labor'
    _description = "Project Bid Component Labor"

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            total_cogs = record.quantity * record.unit_cost
            total_overhead = \
                record.bid_component_id.overhead_rate/100*total_cogs
            total_cost = total_cogs + total_overhead
            total_gross_profit = \
                record.bid_component_id.profit_rate/100*total_cogs
            total_sell = total_cost + total_gross_profit

            res[record.id] = {
                'cogs': total_cogs,
                'overhead': total_overhead,
                'cost': total_cost,
                'profit': total_gross_profit,
                'sell': total_sell,
            }

        return res

    _columns = {
        'bid_component_id': fields.many2one('project.bid.component',
                                            'Project Bid Component',
                                            select=True, required=True,
                                            ondelete='cascade'),
        'bid_id': fields.related('bid_component_id', 'bid_id', string="Bid",
                                 type='many2one', relation='project.bid',
                                 readonly=True),
        'product_id': fields.many2one('product.product',
                                      'Labor product', required=True),
        'name': fields.related('product_id', 'name', string="Description",
                               type='char', readonly=True),
        'quantity': fields.float('Quantity'),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'unit_cost': fields.related('product_id', 'standard_price',
                                    string='Unit cost', type='float',
                                    store=False, readonly=True),
        'cogs': fields.function(_get_totals, type='float', multi='totals',
                                string='Total labor COGS'),
        'overhead': fields.function(_get_totals, type='float',
                                    multi='totals', string='Total overhead'),
        'cost': fields.function(_get_totals, type='float',
                                multi='totals', string='Total costs'),
        'profit': fields.function(_get_totals, type='float',
                                  multi='totals', string='Net profit'),
        'sell': fields.function(_get_totals, type='float',
                                multi='totals', string='Revenue'),
    }

class project_bid_other_labor(orm.Model):
    _name = 'project.bid.other.labor'
    _description = "Project Bid Other Labor"

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            cogs = record.quantity * record.unit_cost
            overhead = cogs*record.overhead_rate/100
            cost = cogs+overhead
            profit = cogs*record.profit_rate/100
            sell = cost + profit
            gross_profit = sell - cogs

            res[record.id] = {
                'cogs': cogs,
                'overhead': overhead,
                'cost': cost,
                'profit': profit,
                'sell': sell,
                'gross_profit': gross_profit,
            }
        return res

    def _check_labor_uom(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            template = record.bid_id.bid_template_id
            if record.uom_id.id is not template.labor_uom_id.id:
                return False
        return True

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'product_id': fields.many2one('product.product',
                                      'Labor product', required=True),
        'name': fields.related('product_id', 'name', string="Description",
                               type='char', readonly=True),
        'quantity': fields.float('Quantity'),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'unit_cost': fields.related('product_id', 'standard_price',
                                    string='Unit cost',
                                    store=False, readonly=True),
        'overhead_rate': fields.float(
            'Overhead %', ditits_compute=dp.get_precision('Account')),
        'profit_rate': fields.float(
            'Profit (%) over COGS', ditits_compute=dp.get_precision('Account'),
            help="Profit (%) over COGS"),
        'cogs': fields.function(_get_totals, type='float', multi='totals',
                                string='Total COGS'),
        'overhead': fields.function(_get_totals, type='float',
                                    multi='totals',
                                    string='Total overhead'),
        'cost': fields.function(_get_totals, type='float',
                                multi='totals', string='Total cost'),
        'gross_profit': fields.function(_get_totals, type='float',
                                        multi='totals',
                                        string='Gross profit'),
        'profit': fields.function(_get_totals, type='float',
                                  multi='totals',
                                  string='Net profit'),
        'sell': fields.function(_get_totals, type='float',
                                multi='totals', string='Revenue'),
    }

    def _get_default_profit_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('profit_rate', 0.0)

    def _get_default_overhead_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('overhead_rate', 0.0)

    _defaults = {
        'profit_rate': _get_default_profit_rate,
        'overhead_rate': _get_default_overhead_rate,
    }

    _constraints = [(_check_labor_uom, 'Error ! The labor must be entered '
                                       'in the default labor unit of measure.',
                     ['uom_id', 'bid_id'])]


class project_bid_other_expenses(orm.Model):
    _name = 'project.bid.other.expenses'
    _description = "Project Bid Other Expenses"

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            cogs = record.quantity*record.unit_cost
            overhead = cogs * record.overhead_rate/100
            cost = cogs + overhead
            profit = cogs*record.profit_rate/100
            sell = cost + profit
            gross_profit = sell - cogs
            res[record.id] = {
                'cogs': cogs,
                'overhead': overhead,
                'cost': cost,
                'profit': profit,
                'sell': sell,
                'gross_profit': gross_profit,
            }
        return res

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'product_id': fields.many2one('product.product',
                                      'Expenses product', required=True),
        'name': fields.related('product_id', 'name', string="Description",
                               type='char', readonly=True),
        'quantity': fields.float('Quantity', required=True),
        'unit_cost': fields.related(
            'product_id', 'standard_price', string='Unit cost',
            store=False, readonly=True,
            digits_compute=dp.get_precision('Account')),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'overhead_rate': fields.float(
            'Overhead %', required=True,
            digits_compute=dp.get_precision('Account')),
        'profit_rate': fields.float(
            'Profit (%) over COGS', required=True,
            digits_compute=dp.get_precision('Account'),
            help="Profit % over COGS"),
        'cogs': fields.function(
            _get_totals, type='float', multi='totals',
            string='Total COGS'),
        'overhead': fields.function(
            _get_totals, type='float', multi='totals',
            string='Total overhead cost'),
        'cost': fields.function(
            _get_totals, type='float', multi='totals',
            string='Total cost'),
        'gross_profit': fields.function(_get_totals, type='float',
                                        multi='totals',
                                        string='Gross profit'),
        'profit': fields.function(
            _get_totals, type='float', multi='totals',
            string='Net profit'),
        'sell': fields.function(
            _get_totals, type='float', multi='totals',
            string='Revenue'),

    }

    def _get_default_profit_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('profit_rate', 0.0)

    def _get_default_overhead_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('overhead_rate', 0.0)

    _defaults = {
        'profit_rate': _get_default_profit_rate,
        'overhead_rate': _get_default_overhead_rate,
    }