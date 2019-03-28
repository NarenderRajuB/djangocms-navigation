from unittest.mock import patch
from django.test import RequestFactory, TestCase

from djangocms_navigation.cms_menus import CMSMenu
from djangocms_navigation.test_utils import factories
from menus.base import Menu
from menus.menu_pool import MenuRenderer
from menus.menu_pool import menu_pool
from .utils import disable_versioning_for_navigation


try:
    from djangocms_versioning.constants import ARCHIVED, DRAFT, UNPUBLISHED
except ImportError:
    ARCHIVED, DRAFT, UNPUBLISHED = None


class CMSMenuTestCase(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.user = factories.UserFactory()
        self.request.user = self.user
        self.renderer = menu_pool.get_renderer(self.request)
        self.menu = CMSMenu(self.renderer)

    def assertNavigationNodeEqual(self, node, **kwargs):
        """Helper method for asserting NavigationNode objects"""
        self.assertEqual(node.title, kwargs["title"])
        self.assertEqual(node.url, kwargs["url"])
        self.assertEqual(node.id, kwargs["id"])
        self.assertEqual(node.parent_id, kwargs["parent_id"])
        self.assertDictEqual(node.attr, kwargs["attr"])

    @disable_versioning_for_navigation()
    def test_get_nodes(self):
        menu_contents = factories.MenuContentFactory.create_batch(2)
        child1 = factories.ChildMenuItemFactory(parent=menu_contents[0].root)
        child2 = factories.ChildMenuItemFactory(parent=menu_contents[1].root)
        grandchild = factories.ChildMenuItemFactory(parent=child1)

        nodes = self.menu.get_nodes(self.request)

        self.assertEqual(len(nodes), 5)
        self.assertNavigationNodeEqual(
            nodes[0],
            title="",
            url="",
            id=menu_contents[0].menu.root_id,
            parent_id=None,
            attr={},
        )
        self.assertNavigationNodeEqual(
            nodes[1],
            title="",
            url="",
            id=menu_contents[1].menu.root_id,
            parent_id=None,
            attr={},
        )
        self.assertNavigationNodeEqual(
            nodes[2],
            title=child1.title,
            url=child1.content.get_absolute_url(),
            id=child1.id,
            parent_id=menu_contents[0].menu.root_id,
            attr={"link_target": child1.link_target},
        )
        self.assertNavigationNodeEqual(
            nodes[3],
            title=grandchild.title,
            url=grandchild.content.get_absolute_url(),
            id=grandchild.id,
            parent_id=child1.id,
            attr={"link_target": grandchild.link_target},
        )
        self.assertNavigationNodeEqual(
            nodes[4],
            title=child2.title,
            url=child2.content.get_absolute_url(),
            id=child2.id,
            parent_id=menu_contents[1].menu.root_id,
            attr={"link_target": child2.link_target},
        )

    def test_get_roots_when_draft_mode_isnt_active(self):
        """This test to check versioning would group all the versions
        of menu content and return latest of all distinct menu content
        """
        menucontent_1_v1 = factories.MenuVersionFactory(state=ARCHIVED)
        # draft version
        menucontent_1_v2 = factories.MenuVersionFactory(
            content__menu=menucontent_1_v1.content.menu
        )
        # draft version
        menucontent_2_v1 = factories.MenuVersionFactory()
        # assert to check draft_mode_active is false
        self.assertFalse(self.menu.renderer.draft_mode_active)
        roots = self.menu.get_roots(self.request)

        # renderer should only render published menucontent
        # In this testcase there isnt any published version
        self.assertEqual(roots.count(), 0)

    def test_get_roots_when_draft_mode_active(self):
        menucontent_1_v1 = factories.MenuVersionFactory(state=ARCHIVED)
        # draft version
        menucontent_1_v2 = factories.MenuVersionFactory(
            content__menu=menucontent_1_v1.content.menu
        )
        # draft version
        menucontent_2_v1 = factories.MenuVersionFactory()

        # Getting renderer to set draft_mode_active
        renderer = self.renderer
        renderer.draft_mode_active = True
        menu = CMSMenu(renderer)

        roots = menu.get_roots(self.request)
        self.assertEqual(roots.count(), 2)
        self.assertListEqual(
            list(roots), [menucontent_1_v2.content.root, menucontent_2_v1.content.root]
        )

    def test_get_roots_for_archived_and_unpublished_versions(self):
        """This test to check get_roots would not return any archived or unpublished versions
        """
        factories.MenuVersionFactory(state=ARCHIVED)
        factories.MenuVersionFactory(state=UNPUBLISHED)
        roots = self.menu.get_roots(self.request)
        self.assertEqual(roots.count(), 0)

    @disable_versioning_for_navigation()
    def test_get_roots_with_versioning_disabled(self):
        """This test will check while versioning disabled it should assert
        against all menu content created
        """
        menucontent_1 = factories.MenuContentFactory()
        menucontent_2 = factories.MenuContentFactory()
        menucontent_3 = factories.MenuContentFactory()
        roots = self.menu.get_roots(self.request)
        self.assertEqual(roots.count(), 3)
        self.assertListEqual(
            list(roots), [menucontent_1.root, menucontent_2.root, menucontent_3.root]
        )
