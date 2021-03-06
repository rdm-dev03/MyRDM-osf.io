# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-09 20:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0049_preprintprovider_preprint_word'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenancestate',
            name='level',
            field=models.IntegerField(choices=[(1, b'info'), (2, b'warning'), (3, b'danger')], default=1),
        ),
        migrations.AddField(
            model_name='maintenancestate',
            name='message',
            field=models.TextField(blank=True),
        ),
    ]
