# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, TransactionCase


class TestMrpRepairIntegration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "tracking": "none",
            }
        )
        # Create component
        cls.component = cls.env["product.product"].create(
            {
                "name": "Test Component",
            }
        )
        # Create BOM
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.component.id, "product_qty": 1.0})
                ],
            }
        )

    def test_01_create_repair_from_mrp(self):
        """Test creation of repair order from manufacturing order"""
        # Create MO
        mo_form = Form(self.env["mrp.production"])
        mo_form.product_id = self.product
        mo_form.bom_id = self.bom
        mo_form.product_qty = 1.0
        mo = mo_form.save()

        # Create repair order from MO
        action = mo.action_create_repair_order()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "repair.order")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")

        # Check context values
        context = action["context"]
        self.assertEqual(context["default_product_id"], self.product.id)
        self.assertEqual(context["default_product_qty"], 1.0)
        self.assertEqual(context["default_mrp_ids"], [mo.id])

    def test_02_repair_mrp_navigation(self):
        """Test navigation between repair order and manufacturing order"""
        # Create MO
        mo = self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )

        # Create Repair Order
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "product_qty": 1.0,
                "mrp_ids": [(4, mo.id)],
            }
        )

        # Link MO to repair
        mo.repair_id = repair.id

        # Test navigation from repair to MO
        action = repair.action_view_repair_manufacturing_order()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "mrp.production")
        self.assertEqual(action["res_id"], mo.id)

        # Test navigation from MO to repair
        action = mo.action_view_mrp_production_repair_orders()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "repair.order")
        self.assertEqual(action["res_id"], repair.id)

    def test_03_multiple_mrp_orders(self):
        """Test handling of multiple manufacturing orders linked to repair"""
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "product_qty": 1.0,
            }
        )

        # Create multiple MOs
        mo1 = self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
                "repair_id": repair.id,
            }
        )

        mo2 = self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
                "repair_id": repair.id,
            }
        )

        # Verify mrp_ids in repair order
        self.assertEqual(len(repair.mrp_ids), 2)
        self.assertIn(mo1.id, repair.mrp_ids.ids)
        self.assertIn(mo2.id, repair.mrp_ids.ids)
