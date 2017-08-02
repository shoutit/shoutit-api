# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0023_facebook_page'),
    ]

    operations = [
        migrations.RenameField(
            model_name='smsinvitation',
            old_name='message',
            new_name='sent_text',
        ),
        migrations.RenameField(
            model_name='smsinvitation',
            old_name='old_message',
            new_name='user_text',
        ),
        migrations.AddField(
            model_name='smsinvitation',
            name='category',
            field=models.ForeignKey(blank=True, to='shoutit.Category', null=True),
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='mobile',
            field=models.CharField(max_length=20, db_index=True)
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='user_text',
            field=models.CharField(default='', max_length=500, blank=True),
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='sent_text',
            field=models.CharField(default='', max_length=160, blank=True),
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='status',
            field=models.SmallIntegerField(default=0, db_index=True,
                                           choices=[(0, 'added'), (1, 'queued'), (2, 'sent'), (3, 'delivered'),
                                                    (4, 'parked'), (5, 'error')]),
        ),
    ]
