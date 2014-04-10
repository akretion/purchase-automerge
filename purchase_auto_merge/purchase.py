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

from openerp.osv import orm


class purchase_order(orm.Model):
    _inherit = "purchase.order"

    def _get_po_matching_key(self, cr, uid, context=None):
        return [
            'partner_id',
            'location_id',
            'pricelist_id',
            'dest_address_id',
        ]

    def _get_existing_purchase_order(self, cr, uid, po_vals, context=None):
        matching_key = self._get_po_matching_key(cr, uid, context=context)
        domain = [('state', '=', 'draft')]
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
                if origin and origin not in purchase.origin:
                    po_vals['origin'] += ' %s' % purchase.origin
                purchase.write(po_vals, context=context)
                return purchase_id
        return super(purchase_order, self).create(
            cr, uid, po_vals, context=context)


class purchase_order_line(orm.Model):
    _inherit = 'purchase.order.line'

    def _get_po_line_matching_key(self, cr, uid, context=None):
        return ['product_id', 'product_uom']

    def _get_existing_purchase_order_line(self, cr, uid, po_line_vals,
                                          context=None):
        matching_key = self._get_po_line_matching_key(cr, uid, context=context)
        domain = [('state', '=', 'draft')]
        for key in matching_key:
            domain.append((key, '=', po_line_vals.get(key)))
        po_line_ids = self.search(cr, uid, domain, context=context)
        return po_line_ids and po_line_ids[0] or False

    def create(self, cr, uid, vals, context=None):
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
                return po_line_id
        return super(purchase_order_line, self).create(
            cr, uid, vals, context=context)


class procurement_order(orm.Model):
    _inherit = 'procurement.order'

    def make_po(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context['purchase_auto_merge'] = True
        return super(procurement_order, self).make_po(
            cr, uid, ids, context=context)

    def _product_virtual_get(self, cr, uid, order_point):
        res = self.pool['stock.location']._product_virtual_get(
            cr, uid, order_point.location_id.id, [order_point.product_id.id],
            {'uom': order_point.product_uom.id})[order_point.product_id.id]
        return res