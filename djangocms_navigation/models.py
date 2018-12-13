from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from treebeard.mp_tree import MP_Node


class Menu(models.Model):
    title = models.CharField(verbose_name=_('title'), max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('author'),
    )
    created_on = models.DateTimeField(auto_now_add=True)
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.title


class MenuItem(MP_Node):
    title = models.CharField(verbose_name=_('title'), max_length=100)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
    )
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')
    menu = models.ForeignKey(
        Menu, on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('author'),
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Node: {}".format(self.title)