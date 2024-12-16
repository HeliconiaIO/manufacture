from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


class TestMrpTag(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.MrpTag = self.env["mrp.tag"]

        # Create test tags
        self.tag_parent = self.MrpTag.create(
            {
                "name": "Production",
            }
        )

        self.tag_child = self.MrpTag.create(
            {
                "name": "Assembly",
                "parent_id": self.tag_parent.id,
            }
        )

        self.tag_grandchild = self.MrpTag.create(
            {
                "name": "Electronics",
                "parent_id": self.tag_child.id,
            }
        )

    def test_compute_display_name(self):
        """Test the computation of hierarchical display names"""
        self.assertEqual(self.tag_parent.display_name, "Production")
        self.assertEqual(self.tag_child.display_name, "Production / Assembly")
        self.assertEqual(
            self.tag_grandchild.display_name, "Production / Assembly / Electronics"
        )

    def test_search_display_name(self):
        """Test searching tags by display name"""
        # Test exact match
        tags = self.MrpTag.search([("display_name", "=", "Production / Assembly")])
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], self.tag_child)

        # Test partial match
        tags = self.MrpTag.search([("display_name", "ilike", "Electronics")])
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], self.tag_grandchild)

        # Test non-existent tag
        tags = self.MrpTag.search([("display_name", "=", "Non-existent")])
        self.assertEqual(len(tags), 0)

    def test_recursive_constraint(self):
        """Test prevention of recursive tag hierarchies"""
        with self.assertRaises(ValidationError), mute_logger("odoo.models"):
            # Try to create a recursive hierarchy
            self.tag_parent.write({"parent_id": self.tag_grandchild.id})

    def test_create_tag_without_parent(self):
        """Test creation of tag without parent"""
        tag = self.MrpTag.create({"name": "Standalone"})
        self.assertEqual(tag.display_name, "Standalone")
        self.assertFalse(tag.parent_id)

    def test_update_parent(self):
        """Test updating tag parent"""
        new_parent = self.MrpTag.create({"name": "NewParent"})

        self.tag_child.write({"parent_id": new_parent.id})

        self.assertEqual(self.tag_child.display_name, "NewParent / Assembly")
        self.assertEqual(
            self.tag_grandchild.display_name, "NewParent / Assembly / Electronics"
        )

    def test_delete_parent(self):
        """Test behavior when parent tag is deleted"""
        self.tag_parent.unlink()

        # Refresh records from database
        self.tag_child.invalidate_cache()
        self.tag_grandchild.invalidate_cache()

        # Child tags should still exist but with updated display names
        self.assertTrue(self.tag_child.exists())
        self.assertTrue(self.tag_grandchild.exists())
        self.assertEqual(self.tag_child.display_name, "Assembly")
        self.assertEqual(self.tag_grandchild.display_name, "Assembly / Electronics")
