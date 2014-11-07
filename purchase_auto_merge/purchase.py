# -*- encoding: utf-8 -*-
##############################################################################
#
#   purchase_auto_merge module for OpenERP
#   Copyright (C) 2012-2014 Akretion (http://www.akretion.com)
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm, fields


class purchase_order(orm.Model):
    _inherit = "purchase.order"

    _columns = {
        'lock': fields.boolean(
            'Lock', readonly=True,
            help="An order generated automatically is locked by default "
            "and you can not edit it until you unlock it. "
            "An unlocked order is not updated automatically anymore."),
    }

    _defaults = {
        'lock': False,
    }

    def _get_po_matching_key(self, cr, uid, context=None):
        return [
            'partner_id',
            'location_id',
            'pricelist_id',
            'dest_address_id',
        ]

    def _get_existing_purchase_order(self, cr, uid, po_vals, context=None):
        matching_key = self._get_po_matching_key(cr, uid, context=context)
        domain = [('state', '=', 'draft'), ('lock', '=', True)]
        for key in matching_key:
            domain.append((key, '=', po_vals.get(key) or False))
        po_ids = self.search(cr, uid, domain, context=context)
        return po_ids and po_ids[0] or False

    def create(self, cr, uid, po_vals, context=None):
        if context is None:
            context = {}
        if context.get('purchase_auto_merge'):
            purchase_id = self._get_existing_purchase_order(
                cr, uid, po_vals, context=context)
            if purchase_id:
                purchase = self.browse(cr, uid, purchase_id, context=context)
                origin = po_vals['origin']
                if not purchase.origin:
                    pass
                elif origin and origin not in purchase.origin:
                    po_vals['origin'] += ' %s' % purchase.origin
                purchase.write(po_vals, context=context)
                return purchase_id
            po_vals['lock'] = True
        return super(purchase_order, self).create(
            cr, uid, po_vals, context=context)

    def unlock(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"lock": False}, context=context)

    def _create_pickings(self, cr, uid, order, order_lines,
                         picking_id=False, context=None):
        res = super(purchase_order, self)._create_pickings(
            cr, uid, order, order_lines, picking_id=picking_id, context=context)
        for order_line in order_lines:
            for proc in order_line.procurement_ids:
                if proc.move_id:
                    proc.move_id.write({'location_id': order.location_id.id})
        return res

class purchase_order_line(orm.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'procurement_ids': fields.one2many(
            'procurement.order', 'purchase_line_id', 'Procurements')
        #'procurement_ids': fields.many2many(
        #    'procurement.order', 'purchase_line_rel', 'line_id', 'proc_id', 'Procurements')
    }

    def _get_po_line_matching_key(self, cr, uid, context=None):
        return ['product_id', 'product_uom']

    def _get_existing_purchase_order_line(self, cr, uid, po_line_vals,
                                          context=None):
        matching_key = self._get_po_line_matching_key(cr, uid, context=context)
        domain = [
            ('order_id.state', '=', 'draft'),
            ('order_id.lock', '=', True)
        ]
        for key in matching_key:
            domain.append((key, '=', po_line_vals.get(key)))
        po_line_ids = self.search(cr, uid, domain, context=context)
        return po_line_ids and po_line_ids[0] or False  

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if context.get('purchase_auto_merge'):
            po_line_id = self._get_existing_purchase_order_line(
                cr, uid, vals, context=context)
            if po_line_id:                    
                po_line = self.browse(
                    cr, uid, po_line_id, context=context)
                added_qty = vals.get('product_qty')
                if added_qty:
                    new_qty = po_line.product_qty + added_qty
                    po_line.write({'product_qty': new_qty}, context=context)
                if vals.get('procurement_ids', False):
                    #po_line.write({'procurement_ids': [(4, vals['procurement_ids'][0][2][0])]}, context=context)
                    po_line.write({'procurement_ids': vals['procurement_ids']}, context=context)
                return po_line_id
        return super(purchase_order_line, self).create(
            cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        procurement_ids_to_cancel = []
        for line in self.browse(cr, uid, ids, context=context):
            for proc in line.procurement_ids:
                procurement_ids_to_cancel.append(proc.id)
        if procurement_ids_to_cancel:
            self.pool['procurement.order'].action_cancel(cr, uid, procurement_ids_to_cancel)
        return super(purchase_order_line, self).unlink(cr, uid, ids, context=context)

class procurement_order(orm.Model):
    _inherit = 'procurement.order'

    _columns = {
        'purchase_auto_merge': fields.boolean(
            'Purchase auto merge', readonly=True,
            help="Tell if we should try to update an existing procurement or "
            "create a new one"),
        'purchase_line_id': fields.many2one('purchase.order.line', 'Purchase Line'),
    }

    _defaults = {
        'purchase_auto_merge': True,
    }

    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals,
                                          line_vals, context=None):
        #line_vals.update({'procurement_ids': [(6, 0, [procurement.id])]})
        line_vals.update({'procurement_ids': [(4, procurement.id)]})
        return super(procurement_order, self).create_procurement_purchase_order(
            cr, uid, procurement, po_vals, line_vals, context=context)

    def make_po(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = {}
        for procurement in self.browse(cr, uid, ids, context=context):
            context['purchase_auto_merge'] = procurement.purchase_auto_merge
            res.update(super(procurement_order, self).make_po(
                cr, uid, ids, context=context
            ))
        return res

    def _product_virtual_get(self, cr, uid, order_point):
        res = self.pool['stock.location']._product_virtual_get(
            cr, uid, order_point.location_id.id, [order_point.product_id.id],
            {'uom': order_point.product_uom.id})[order_point.product_id.id]
        return res
