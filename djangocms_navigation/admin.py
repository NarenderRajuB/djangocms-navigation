from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import reverse, HttpResponseRedirect
from django.contrib.admin.utils import quote

from django.utils.text import slugify
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from treebeard.admin import TreeAdmin

from .models import Menu, MenuContent, MenuItem
from .forms import MenuItemForm, MenuContentForm


class MenuItemChangeList(ChangeList):
    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse(
            "admin:%s_%s_change" % (self.opts.app_label, self.opts.model_name),
            args=(self.request.menu_content_id, quote(pk)),
            current_app=self.model_admin.admin_site.name,
        )

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)


class MenuContentAdmin(admin.ModelAdmin):
    # exclude = ["menu", "root"]
    form = MenuContentForm
    list_display = ["title", "get_menuitem_link"]
    list_display_links = ["get_menuitem_link"]

    def save_model(self, request, obj, form, change):
        if not change:
            title = form.data.get("title")
            # Creating grouper object for menu content
            obj.menu = Menu.objects.create(
                identifier=slugify(title), site=get_current_site(request)
            )
            # Creating root menu item with title
            obj.root = MenuItem.add_root(title=title, depth=1)
        super().save_model(request, obj, form, change)

    def get_menuitem_link(self, obj):
        object_preview_url = reverse(
            "admin:{app}_{model}_list".format(
                app=obj._meta.app_label, model=MenuItem._meta.model_name
            ),
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}" class="js-moderation-close-sideframe" target="_top">'
            '<span class="cms-icon cms-icon-eye"></span> {}'
            "</a>",
            object_preview_url,
            _("Items"),
        )

    get_menuitem_link.short_description = _("Menu Items")


class MenuItemAdmin(TreeAdmin):
    form = MenuItemForm
    change_list_template = "/admin/djangocms_navigation/menuitem/change_list.html"

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            url(
                r"^(?P<menu_content_id>\d+)/list/",
                self.admin_site.admin_view(self.changelist_view),
                name="{}_{}_list".format(*info),
            ),
            url(
                r"^(?P<menu_content_id>\d+)/add/",
                self.admin_site.admin_view(self.add_view),
                name="{}_{}_add".format(*info),
            ),
            url(
                r"^(?P<menu_content_id>\d+)/(?P<object_id>\d+)/change/",
                self.admin_site.admin_view(self.change_view),
                name="{}_{}_change".format(*info),
            ),
        ] + super().get_urls()

    def get_queryset(self, request):
        if hasattr(request, "menu_content_id"):
            menu_content = MenuContent.objects.get(id=request.menu_content_id)
            root_node = MenuItem.objects.filter(id=menu_content.root.id)

            # django-treebeard doesnt have api that return current node and all descendants
            # hence merging two queryset
            return root_node | root_node[0].get_descendants()
        return self.model().get_tree()

    def change_view(
        self, request, object_id, menu_content_id=None, form_url="", extra_context=None
    ):
        extra_context = extra_context or {}
        if menu_content_id:
            request.menu_content_id = menu_content_id
            extra_context["list_url"] = reverse(
                "admin:djangocms_navigation_menuitem_list",
                kwargs={"menu_content_id": menu_content_id},
            )
        return super().change_view(
            request, object_id, form_url="", extra_context=extra_context
        )

    def add_view(self, request, menu_content_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if menu_content_id:
            request.menu_content_id = menu_content_id
            extra_context["list_url"] = reverse(
                "admin:djangocms_navigation_menuitem_list",
                kwargs={"menu_content_id": menu_content_id},
            )

        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    def changelist_view(self, request, menu_content_id=None, extra_context=None):
        extra_context = extra_context or {}

        if menu_content_id:
            request.menu_content_id = menu_content_id
            extra_context["add_url"] = reverse(
                "admin:djangocms_navigation_menuitem_add",
                kwargs={"menu_content_id": menu_content_id},
            )
            extra_context["list_url"] = reverse(
                "admin:djangocms_navigation_menuitem_list",
                kwargs={"menu_content_id": menu_content_id},
            )

        return super().changelist_view(request, extra_context)

    def response_change(self, request, obj):
        url = reverse(
            "admin:djangocms_navigation_menuitem_list",
            kwargs={"menu_content_id": request.menu_content_id},
        )
        return HttpResponseRedirect(url)

    def response_add(self, request, obj, post_url_continue=None):
        url = reverse(
            "admin:djangocms_navigation_menuitem_list",
            kwargs={"menu_content_id": request.menu_content_id},
        )
        return HttpResponseRedirect(url)

    def has_add_permission(self, request):
        if hasattr(request, "menu_content_id"):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if hasattr(request, "menu_content_id"):
            return True
        if obj is not None:
            return True
        return False

    def get_changelist(self, request, **kwargs):
        return MenuItemChangeList


admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(MenuContent, MenuContentAdmin)
