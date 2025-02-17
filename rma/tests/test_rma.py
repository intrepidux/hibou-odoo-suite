# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import common
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class TestRMA(common.TransactionCase):
    def setUp(self):
        super(TestRMA, self).setUp()
        self.product1 = self.env.ref('product.product_product_24')
        self.product2 = self.env.ref('product.product_product_25')
        self.template_missing = self.env.ref('rma.template_missing_item')
        self.template_return = self.env.ref('rma.template_picking_return')
        self.template_rtv = self.env.ref('rma.template_rtv')
        self.partner1 = self.env.ref('base.res_partner_2')
        self.user1 = self.env.ref('base.user_demo')
        # Additional partner in tests or vendor in Return To Vendor
        self.partner2 = self.env.ref('base.res_partner_12')

    def test_00_basic_rma(self):
        self.template_missing.responsible_user_ids += self.user1
        self.template_missing.usage = False
        rma = self.env['rma.rma'].create({
            'template_id': self.template_missing.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        self.assertTrue(rma.activity_ids)
        self.assertEqual(rma.activity_ids.user_id, self.user1)
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Should have made pickings
        self.assertEqual(rma.state, 'confirmed')
        # No inbound picking
        self.assertFalse(rma.in_picking_id)
        # Good outbound picking
        self.assertTrue(rma.out_picking_id)
        self.assertEqual(rma_line.product_id, rma.out_picking_id.move_lines.product_id)
        self.assertEqual(rma_line.product_uom_qty, rma.out_picking_id.move_lines.product_uom_qty)

        with self.assertRaises(UserError):
            rma.action_done()

        rma.out_picking_id.move_lines.quantity_done = 2.0
        rma.out_picking_id.button_validate()
        rma.action_done()
        self.assertEqual(rma.state, 'done')

    def test_10_rma_cancel(self):
        self.template_missing.usage = False
        rma = self.env['rma.rma'].create({
            'template_id': self.template_missing.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Good outbound picking
        self.assertEqual(rma.out_picking_id.move_lines.state, 'assigned')
        rma.action_cancel()
        self.assertEqual(rma.out_picking_id.move_lines.state, 'cancel')

    def test_20_picking_rma(self):
        self.product1.type = 'product'
        type_out = self.env.ref('stock.picking_type_out')
        location = self.env.ref('stock.stock_location_stock')
        location_customer = self.env.ref('stock.stock_location_customers')

        adjust_to_zero_quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.product1.id,
            'location_id': location.id,
            'inventory_quantity': 0.0
        }).action_apply_inventory()

        # No Quants after moving inventory out (quant exists with qty == 0 in Odoo 14)
        quant = self.env['stock.quant'].search([('product_id', '=', self.product1.id),
                                                ('location_id', '=', location.id),
                                                ('quantity', '!=', 0)])
        self.assertEqual(len(quant), 0)

        # Adjust in a single serial
        self.product1.tracking = 'serial'

        # Need to ensure this is the only quant that can be reserved for this move.
        lot = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': 'X1000',
            'product_uom_id': self.product1.uom_id.id,
            'company_id': self.env.user.company_id.id,
        })

        adjust_to_zero_quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.product1.id,
            'location_id': self.env.ref('stock.warehouse0').lot_stock_id.id,
            'inventory_quantity': 1.0,
            'lot_id': lot.id,
        }).action_apply_inventory()

        self.assertEqual(self.product1.qty_available, 1.0)
        self.assertTrue(lot.quant_ids)
        # Test some internals in Odoo 12.0
        lot_internal_quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
        self.assertEqual(len(lot_internal_quants), 1)
        self.assertEqual(lot_internal_quants.mapped('quantity'), [1.0])
        # Re-compute qty as it does not depend on anything.
        lot._product_qty()
        self.assertEqual(lot.product_qty, 1.0)

        # Create initial picking that will be returned by RMA
        picking_out = self.env['stock.picking'].create({
            'partner_id': self.partner1.id,
            'name': 'testpicking',
            'picking_type_id': type_out.id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
        })
        self.env['stock.move'].create({
            'name': self.product1.name,
            'product_id': self.product1.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product1.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
        })
        picking_out.with_context(planned_picking=True).action_confirm()

        # Try to RMA item not delivered yet
        rma = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'stock_picking_id': picking_out.id,
        })
        self.assertEqual(rma.state, 'draft')
        wizard = self.env['rma.picking.make.lines'].create({
            'rma_id': rma.id,
        })
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma.lines), 1)

        # Make sure that we cannot 'return' if we cannot 'reverse' a stock move
        # (this is what `in_require_return` and `out_require_return` do on `rma.template`)
        with self.assertRaises(UserError):
            rma.action_confirm()

        # Finish our original picking
        picking_out.action_assign()
        self.assertEqual(picking_out.state, 'assigned')

        # The only lot should be reserved, so we shouldn't get an exception finishing the transfer.
        picking_out.move_line_ids.write({
            'qty_done': 1.0,
        })
        picking_out.button_validate()
        self.assertEqual(picking_out.state, 'done')

        # Now we can 'return' that picking
        rma.action_confirm()
        self.assertEqual(rma.in_picking_id.state, 'assigned')
        pack_opt = rma.in_picking_id.move_line_ids[0]
        self.assertTrue(pack_opt)

        # unlink the lot so that we can re-add it later
        self.assertTrue(pack_opt.lot_id)
        pack_opt.write({'lot_id': False})

        # We cannot check this directly anymore.  Instead just try to return the same lot and make sure you can.
        # self.assertEqual(pack_opt.lot_id, lot)

        with self.assertRaises(UserError):
            rma.action_done()

        pack_opt.qty_done = 1.0
        with self.assertRaises(UserError):
            # require a lot
            rma.in_picking_id.button_validate()

        pack_opt.lot_id = lot
        rma.in_picking_id.button_validate()
        rma.action_done()

        # Ensure that the same lot was in fact returned into our destination inventory
        quant = self.env['stock.quant'].search([('product_id', '=', self.product1.id),
                                                ('location_id', '=', location.id),
                                                ('quantity', '!=', 0)])
        self.assertEqual(len(quant), 1)
        self.assertEqual(quant.lot_id, lot)

        # Make another RMA for the same picking
        rma2 = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'stock_picking_id': picking_out.id,
        })
        wizard = self.env['rma.picking.make.lines'].create({
            'rma_id': rma2.id,
        })
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma2.lines), 1)

        rma2.action_confirm()

        # In Odoo 10, this would not have been able to reserve.
        # In Odoo 11, reservation can still happen, but at least we can't move the same lot twice!
        # self.assertEqual(rma2.in_picking_id.state, 'confirmed')

        # Requires Lot
        with self.assertRaises(UserError):
            rma2.in_picking_id.move_line_ids.write({'qty_done': 1.0})
            rma2.in_picking_id.button_validate()


        self.assertTrue(rma2.in_picking_id.move_line_ids)
        self.assertFalse(rma2.in_picking_id.move_line_ids.lot_id.name)

        # Assign existing lot
        # TODO: Investigate
        # rma2.in_picking_id.move_line_ids.write({
        #     'lot_id': lot.id
        # })

        # Existing lot cannot be re-used.
        # TODO: Investigate
        # It appears that in Odoo 13 You can move the lot again...
        # with self.assertRaises(ValidationError):
        #     rma2.in_picking_id.action_done()

        # RMA cannot be completed because the inbound picking state is confirmed
        with self.assertRaises(UserError):
            rma2.action_done()

    def test_30_next_rma_rtv(self):
        self.template_return.usage = False
        self.template_return.in_require_return = False
        self.template_return.next_rma_template_id = self.template_rtv
        rma = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Should have made pickings
        self.assertEqual(rma.state, 'confirmed')

        # No outbound picking
        self.assertFalse(rma.out_picking_id)
        # Good inbound picking
        self.assertTrue(rma.in_picking_id)
        self.assertEqual(rma_line.product_id, rma.in_picking_id.move_lines.product_id)
        self.assertEqual(rma_line.product_uom_qty, rma.in_picking_id.move_lines.product_uom_qty)

        with self.assertRaises(UserError):
            rma.action_done()

        rma.in_picking_id.move_lines.quantity_done = 2.0
        rma.in_picking_id.button_validate()
        rma.action_done()
        self.assertEqual(rma.state, 'done')

        # RTV RMA
        rma_rtv = self.env['rma.rma'].search([('parent_id', '=', rma.id)])
        self.assertTrue(rma_rtv)
        self.assertEqual(rma_rtv.state, 'draft')

        wiz = self.env['rma.make.rtv'].with_context(active_model='rma.rma', active_ids=rma_rtv.ids).create({})
        self.assertTrue(wiz.rma_line_ids)
        wiz.partner_id = self.partner2
        wiz.create_batch()
        self.assertTrue(rma_rtv.out_picking_id)
        self.assertEqual(rma_rtv.out_picking_id.partner_id, self.partner2)
        self.assertEqual(rma_rtv.state, 'confirmed')

        # ship and finish
        rma_rtv.out_picking_id.move_lines.quantity_done = 2.0
        rma_rtv.out_picking_id.button_validate()
        rma_rtv.action_done()
        self.assertEqual(rma_rtv.state, 'done')

        # ensure invoice and type
        rtv_invoice = rma_rtv.invoice_ids
        self.assertTrue(rtv_invoice)
        self.assertEqual(rtv_invoice.move_type, 'in_refund')
