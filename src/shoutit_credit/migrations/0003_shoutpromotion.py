# -*- coding: utf-8 -*-
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_credit', '0002_fill_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoutPromotion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('days', models.PositiveSmallIntegerField(db_index=True, null=True, blank=True)),
                ('label', models.ForeignKey(to='shoutit_credit.PromoteLabel')),
                ('option', models.ForeignKey(to='shoutit_credit.CreditRule')),
                ('shout', models.ForeignKey(related_name='promotions', to='shoutit.Shout')),
                ('transaction', models.OneToOneField(related_name='shout_promotion', to='shoutit_credit.CreditTransaction')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
