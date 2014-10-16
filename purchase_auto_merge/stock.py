# -*- encoding: utf-8 -*-
##############################################################################
#
#   purchase_auto_merge module for OpenERP
#   Copyright (C) 2012-2014 Akretion (http://www.akretion.com)
#   @author Florian da Costa <florian.dacosta@akretion.com>
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


class StockMove(orm.Model):
    _inherit = "stock.move"

    def action_done(self, cr, uid, ids, context=None):
        for m in self.browse(cr, uid, ids, context=context):
            other_upstream_move_ids = self.search(cr, uid, [('id','!=',m.id),('state','not in',['done','cancel']),
                                                        ('move_dest_id','=',m.move_dest_id.id)], context=context)
            if not other_upstream_move_ids:
                if m.purchase_line_id and len(m.purchase_line_id.procurement_ids) > 1 and m.state !='done':
                    for proc in m.purchase_line_id.procurement_ids:
                        if proc.move_id.state in ('waiting', 'confirmed'):
                            self.force_assign(cr, uid, [proc.move_id.id],
                                              context=context)
                            if proc.move_id.auto_validate:
                                self.action_done(cr, uid, [proc.move_id.id], context=context)
        res = super(StockMove, self).action_done(
                    cr, uid, ids, context=context)
        return res
