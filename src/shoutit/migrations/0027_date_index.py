# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0026_auto_20160806_1749'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='cluser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='cluser',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='confirmtoken',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='confirmtoken',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='conversationdelete',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='conversationdelete',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='dbclconversation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='dbclconversation',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='dbz2user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='dbz2user',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='discoveritem',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='discoveritem',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='featuredtag',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='featuredtag',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='googlelocation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='googlelocation',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedfacebookaccount',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedfacebookaccount',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedfacebookpage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedfacebookpage',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedgoogleaccount',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedgoogleaccount',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='listen2',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='listen2',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='messagedelete',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='messagedelete',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='messageread',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='messageread',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pageadmin',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pageadmin',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pagecategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pagecategory',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pageverification',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pageverification',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='permission',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='permission',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='profilecontact',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='profilecontact',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pushbroadcast',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pushbroadcast',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='sharedlocation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='sharedlocation',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='shoutbookmark',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='shoutbookmark',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='shoutlike',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='shoutlike',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='tagkey',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='tagkey',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='userpermission',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='userpermission',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
    ]
