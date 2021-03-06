# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-14 13:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

from ..constants import TARGETS


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Menu",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "identifier",
                    models.CharField(max_length=100, verbose_name="identifier"),
                ),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="sites.Site"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MenuContent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100, verbose_name="title")),
                (
                    "menu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="djangocms_navigation.Menu",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MenuItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                ("title", models.CharField(max_length=100, verbose_name="title")),
                ("object_id", models.PositiveIntegerField()),
                (
                    "link_target",
                    models.CharField(choices=TARGETS, default="_self", max_length=20),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="contenttypes.ContentType",
                    ),
                ),
                (
                    "menu_content",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="djangocms_navigation.MenuContent",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AlterUniqueTogether(
            name="menu", unique_together=set([("identifier", "site")])
        ),
    ]
