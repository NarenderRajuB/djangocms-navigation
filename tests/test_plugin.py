from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory, TestCase

from cms.test_utils.testcases import CMSTestCase
from menus.base import NavigationNode

from djangocms_navigation.cms_menus import CMSMenu, NavigationSelector
from djangocms_navigation.models import NavigationPlugin
from djangocms_navigation.test_utils import factories

from .utils import disable_versioning_for_navigation


class CMSMenuTestCase(TestCase):
    def setUp(self):
        self.menu = CMSMenu(None)
        self.request = RequestFactory().get('/')

    def assertNavigationNodeEqual(self, node, **kwargs):
        """Helper method for asserting NavigationNode objects"""
        self.assertEqual(node.title, kwargs['title'])
        self.assertEqual(node.url, kwargs['url'])
        self.assertEqual(node.id, kwargs['id'])
        self.assertEqual(node.parent_id, kwargs['parent_id'])
        self.assertDictEqual(node.attr, kwargs['attr'])

    def test_get_nodes(self):
        menu_contents = factories.MenuContentFactory.create_batch(2)
        child1 = factories.ChildMenuItemFactory(parent=menu_contents[0].root)
        child2 = factories.ChildMenuItemFactory(parent=menu_contents[1].root)
        grandchild = factories.ChildMenuItemFactory(parent=child1)

        nodes = self.menu.get_nodes(self.request)

        self.assertEqual(len(nodes), 5)
        self.assertNavigationNodeEqual(
            nodes[0], title='', url='', id=menu_contents[0].menu.root_id,
            parent_id=None, attr={}
        )
        self.assertNavigationNodeEqual(
            nodes[1], title='', url='', id=menu_contents[1].menu.root_id,
            parent_id=None, attr={}
        )
        self.assertNavigationNodeEqual(
            nodes[2], title=child1.title, url=child1.content.get_absolute_url(),
            id=child1.id, parent_id=menu_contents[0].menu.root_id,
            attr={'link_target': child1.link_target}
        )
        self.assertNavigationNodeEqual(
            nodes[3], title=grandchild.title, url=grandchild.content.get_absolute_url(),
            id=grandchild.id, parent_id=child1.id,
            attr={'link_target': grandchild.link_target}
        )
        self.assertNavigationNodeEqual(
            nodes[4], title=child2.title, url=child2.content.get_absolute_url(),
            id=child2.id, parent_id=menu_contents[1].menu.root_id,
            attr={'link_target': child2.link_target}
        )


class NavigationSelectorTestCase(TestCase):

    def setUp(self):
        self.selector = NavigationSelector(None)
        self.request = RequestFactory().get('/')

    def _get_nodes(self):
        """Helper method to set up a list of NavigationNode instances"""
        self.fruit = NavigationNode(
            title='',
            url='',
            id='root-fruit',
            parent_id=None,
            attr={},
        )
        self.vegetables = NavigationNode(
            title='',
            url='',
            id='root-vegetables',
            parent_id=None,
            attr={},
        )
        self.apples = NavigationNode(
            title='Apples',
            url='/fruit/apples/',
            id=26,
            parent_id='root-fruit',
            attr={'link_target': '_self'},
        )
        self.celery = NavigationNode(
            title='Celery',
            url='/vegetables/celery/',
            id=12,
            parent_id='root-vegetables',
            attr={'link_target': '_self'},
        )
        self.carrots = NavigationNode(
            title='Carrots',
            url='/vegetables/carrots/',
            id=28,
            parent_id='root-vegetables',
            attr={'link_target': '_self'},
        )
        self.purple_carrots = NavigationNode(
            title='Purple Carrots',
            url='/vegetables/carrots/purple/',
            id=267,
            parent_id=28,
            attr={'link_target': '_self'},
        )
        self.fruit.children = [self.apples]
        self.vegetables.children = [self.celery, self.carrots]
        self.carrots.children = [self.purple_carrots]
        return [
            self.fruit,
            self.vegetables,
            self.apples,
            self.celery,
            self.carrots,
            self.purple_carrots,
        ]

    def test_modify_with_namespace(self):
        result = self.selector.modify(
            self.request, nodes=self._get_nodes(), namespace='root-vegetables',
            root_id=None, post_cut=False, breadcrumb=False)
        self.assertListEqual(result, [self.celery, self.carrots])

    def test_modify_without_namespace(self):
        result = self.selector.modify(
            self.request, nodes=self._get_nodes(), namespace=None,
            root_id=None, post_cut=False, breadcrumb=False)
        # With no namespace supplied, the first node in the list of nodes
        # will be used as root - in this case fruit
        self.assertListEqual(result, [self.apples])


class NavigationPluginViewTestCase(CMSTestCase):

    def setUp(self):
        self.language = settings.LANGUAGES[0][0]
        self.client.force_login(self.get_superuser())

    def _add_nav_plugin_and_assert(self, placeholder, menu, template):
        """Helper method to do an http call to add a nav plugin and
        assert the results"""
        add_url = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='Navigation',
            language=self.language,
        )
        # First do a GET on the add view
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)
        # Now do a POST call on the add view
        data = {'template': template, 'menu': menu.pk}
        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 200)
        created_plugin = NavigationPlugin.objects.latest('pk')
        self.assertEqual(created_plugin.template, template)
        self.assertEqual(created_plugin.menu, menu)
        return created_plugin

    def _edit_nav_plugin_and_assert(self, created_plugin, menu, template):
        """Helper method to do an http call to edit a nav plugin and
        assert the results"""
        change_url = self.get_change_plugin_uri(created_plugin)
        # Start with a GET call on the change view
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        # Now do a POST call on the change view
        data = {'template': template, 'menu': menu.pk}
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 200)
        plugin = NavigationPlugin.objects.get(
            pk=created_plugin.pk).get_bound_plugin()
        self.assertEqual(plugin.template, template)
        self.assertEqual(plugin.menu, menu)
        return plugin

    def _delete_nav_plugin_and_assert(self, placeholder, plugin):
        """Helper method to do an http call to delete a nav plugin and
        assert the results"""
        delete_url = self.get_delete_plugin_uri(plugin)
        # Start with a GET call on the delete view
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        # Now do a POST call on the delete view
        response = self.client.post(delete_url, {'plugin_id': plugin.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/en/admin/')
        self.assertEqual(NavigationPlugin.objects.filter(id=plugin.id).count(), 0)
        self.assertEqual(placeholder.get_plugins().count(), 0)

    def test_crud_for_navigation_plugin_when_versioning_enabled(self):
        # NOTE: This test is based on a similar one from django-cms:
        # https://github.com/divio/django-cms/blob/2daeb7d63cb5fee49575a834d0f23669ce46144e/cms/tests/test_plugins.py#L160

        # Set up a versioned page with one placeholder
        page_content = factories.PageContentWithVersionFactory(language=self.language)
        placeholder = factories.PlaceholderFactory(source=page_content)
        menu_content1 = factories.MenuContentWithVersionFactory()
        menu_content2 = factories.MenuContentWithVersionFactory()
        child = factories.ChildMenuItemFactory(parent=menu_content2.root)
        grandchild = factories.ChildMenuItemFactory(parent=child)

        # Patch the choices on the template field, so we don't get
        # form validation errors
        template_field = [
            field for field in NavigationPlugin._meta.fields
            if field.name == 'template'
        ][0]
        patched_choices = [
            ('menu/menu.html', 'Default'),
            ('menu/menuismo.html', 'Menuismo')
        ]
        with patch.object(template_field, 'choices', patched_choices):
            # First add the plugin and assert
            # The added plugin will have the template menu/menuismo.html
            # and the menu from menu1
            created_plugin = self._add_nav_plugin_and_assert(
                placeholder, menu_content1.menu, 'menu/menuismo.html')

            # Now edit the plugin and assert
            # After editing the plugin will have the template menu/menu.html
            # and the menu from menu2
            self._edit_nav_plugin_and_assert(
                created_plugin, menu_content2.menu, 'menu/menu.html')

        # Now publish the page content containing the plugin,
        # so the page can be viewed
        version = page_content.versions.get()
        version.publish(self.get_superuser())
        # TODO: Possibly there's a bug where MenuItem objects from
        # unpublished MenuContent objects are being displayed. If yes
        # then the menu_content2 will need to be published in this test
        # once that bug is fixed

        # And view the page
        page_url = page_content.page.get_absolute_url()
        response = self.client.get(page_url)
        self.assertIn(child.title, str(response.content))
        self.assertIn(grandchild.title, str(response.content))
        self.assertEqual(response.status_code, 200)

        # To delete, the version has to be a draft
        new_version = version.copy(self.get_superuser())
        new_placeholder = new_version.content.placeholders.first()
        new_plugin = new_placeholder.get_plugins()[0]

        # Now delete the plugin from the page and assert
        self._delete_nav_plugin_and_assert(new_placeholder, new_plugin)

    @disable_versioning_for_navigation()
    def test_crud_for_navigation_plugin_when_versioning_disabled(self):
        # The page content here is versioned because we're only disabling
        # versioning for navigation (i.e. MenuContent)
        page_content = factories.PageContentWithVersionFactory(language=self.language)
        placeholder = factories.PlaceholderFactory(source=page_content)
        menu_content1 = factories.MenuContentFactory()
        menu_content2 = factories.MenuContentFactory()
        child = factories.ChildMenuItemFactory(parent=menu_content2.root)
        grandchild = factories.ChildMenuItemFactory(parent=child)

        # Patch the choices on the template field, so we don't get
        # form validation errors
        template_field = [
            field for field in NavigationPlugin._meta.fields
            if field.name == 'template'
        ][0]
        patched_choices = [
            ('menu/menu.html', 'Default'),
            ('menu/menuismo.html', 'Menuismo')
        ]
        with patch.object(template_field, 'choices', patched_choices):
            # First add the plugin and assert
            # The added plugin will have the template menu/menuismo.html
            # and the menu from menu1
            created_plugin = self._add_nav_plugin_and_assert(
                placeholder, menu_content1.menu, 'menu/menuismo.html')

            # Now edit the plugin and assert
            # After editing the plugin will have the template menu/menu.html
            # and the menu from menu2
            self._edit_nav_plugin_and_assert(
                created_plugin, menu_content2.menu, 'menu/menu.html')

        # Now publish the page content containing the plugin,
        # so the page can be viewed
        version = page_content.versions.get()
        version.publish(self.get_superuser())

        # And view the page
        page_url = page_content.page.get_absolute_url()
        response = self.client.get(page_url)
        self.assertIn(child.title, str(response.content))
        self.assertIn(grandchild.title, str(response.content))
        self.assertEqual(response.status_code, 200)

        # To delete, the version (of the PageContent object) has to be a draft
        new_version = version.copy(self.get_superuser())
        new_placeholder = new_version.content.placeholders.first()
        new_plugin = new_placeholder.get_plugins()[0]

        # Now delete the plugin from the page and assert
        self._delete_nav_plugin_and_assert(new_placeholder, new_plugin)