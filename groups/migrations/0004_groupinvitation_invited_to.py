# Generated by Django 5.1.1 on 2024-10-23 07:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_rename_connection_connections'),
        ('groups', '0003_remove_group_members'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupinvitation',
            name='invited_to',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='invitations_received', to='accounts.profile'),
            preserve_default=False,
        ),
    ]
