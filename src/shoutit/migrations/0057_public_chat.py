# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0056_notification_user_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='city',
            field=models.CharField(db_index=True, max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='country',
            field=models.CharField(blank=True, max_length=2, db_index=True, choices=[('', 'None'), ('WF', 'Wallis and Futuna'), ('JP', 'Japan'), ('JM', 'Jamaica'), ('JO', 'Jordan'), ('WS', 'Samoa'), ('JE', 'Jersey'), ('GW', 'Guinea-Bissau'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GS', 'South Georgia and the South Sandwich Islands'), ('GR', 'Greece'), ('GQ', 'Equatorial Guinea'), ('GP', 'Guadeloupe'), ('GY', 'Guyana'), ('GG', 'Guernsey'), ('GF', 'French Guiana'), ('GE', 'Georgia'), ('GD', 'Grenada'), ('GB', 'United Kingdom'), ('GA', 'Gabon'), ('GN', 'Guinea'), ('GM', 'Gambia'), ('GL', 'Greenland'), ('GI', 'Gibraltar'), ('GH', 'Ghana'), ('PR', 'Puerto Rico'), ('PS', 'Palestinian Territory, Occupied'), ('PW', 'Palau'), ('PT', 'Portugal'), ('PY', 'Paraguay'), ('PA', 'Panama'), ('PF', 'French Polynesia'), ('PG', 'Papua New Guinea'), ('PE', 'Peru'), ('PK', 'Pakistan'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PM', 'Saint Pierre and Miquelon'), ('ZM', 'Zambia'), ('ZA', 'South Africa'), ('ZW', 'Zimbabwe'), ('ME', 'Montenegro'), ('MD', 'Moldova, Republic of'), ('MG', 'Madagascar'), ('MF', 'Saint Martin (French part)'), ('MA', 'Morocco'), ('MC', 'Monaco'), ('MM', 'Myanmar'), ('ML', 'Mali'), ('MO', 'Macao'), ('MN', 'Mongolia'), ('MH', 'Marshall Islands'), ('MK', 'Macedonia, the former Yugoslav Republic of'), ('MU', 'Mauritius'), ('MT', 'Malta'), ('MW', 'Malawi'), ('MV', 'Maldives'), ('MQ', 'Martinique'), ('MP', 'Northern Mariana Islands'), ('MS', 'Montserrat'), ('MR', 'Mauritania'), ('MY', 'Malaysia'), ('MX', 'Mexico'), ('MZ', 'Mozambique'), ('FR', 'France'), ('FI', 'Finland'), ('FJ', 'Fiji'), ('FK', 'Falkland Islands (Malvinas)'), ('FM', 'Micronesia, Federated States of'), ('FO', 'Faroe Islands'), ('CK', 'Cook Islands'), ('CI', "Cote d'Ivoire"), ('CH', 'Switzerland'), ('CO', 'Colombia'), ('CN', 'China'), ('CM', 'Cameroon'), ('CL', 'Chile'), ('CC', 'Cocos (Keeling) Islands'), ('CA', 'Canada'), ('CG', 'Congo'), ('CF', 'Central African Republic'), ('CD', 'Congo, the Democratic Republic of the'), ('CZ', 'Czech Republic'), ('CY', 'Cyprus'), ('CX', 'Christmas Island'), ('CR', 'Costa Rica'), ('CW', 'Curacao'), ('CV', 'Cape Verde'), ('CU', 'Cuba'), ('SZ', 'Swaziland'), ('SY', 'Syrian Arab Republic'), ('SX', 'Sint Maarten (Dutch part)'), ('SS', 'South Sudan'), ('SR', 'Suriname'), ('SV', 'El Salvador'), ('ST', 'Sao Tome and Principe'), ('SK', 'Slovakia'), ('SJ', 'Svalbard and Jan Mayen'), ('SI', 'Slovenia'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('SO', 'Somalia'), ('SN', 'Senegal'), ('SM', 'San Marino'), ('SL', 'Sierra Leone'), ('SC', 'Seychelles'), ('SB', 'Solomon Islands'), ('SA', 'Saudi Arabia'), ('SG', 'Singapore'), ('SE', 'Sweden'), ('SD', 'Sudan'), ('YE', 'Yemen'), ('YT', 'Mayotte'), ('LB', 'Lebanon'), ('LC', 'Saint Lucia'), ('LA', "Lao People's Democratic Republic"), ('LK', 'Sri Lanka'), ('LI', 'Liechtenstein'), ('LV', 'Latvia'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('LR', 'Liberia'), ('LS', 'Lesotho'), ('LY', 'Libya'), ('VA', 'Holy See (Vatican City State)'), ('VC', 'Saint Vincent and the Grenadines'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VG', 'Virgin Islands, British'), ('IQ', 'Iraq'), ('VI', 'Virgin Islands, U.S.'), ('IS', 'Iceland'), ('IR', 'Iran, Islamic Republic of'), ('IT', 'Italy'), ('VN', 'Viet Nam'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IO', 'British Indian Ocean Territory'), ('IN', 'India'), ('IE', 'Ireland'), ('ID', 'Indonesia'), ('BD', 'Bangladesh'), ('BE', 'Belgium'), ('BF', 'Burkina Faso'), ('BG', 'Bulgaria'), ('BA', 'Bosnia and Herzegovina'), ('BB', 'Barbados'), ('BL', 'Saint Barthelemy'), ('BM', 'Bermuda'), ('BN', 'Brunei Darussalam'), ('BO', 'Bolivia, Plurinational State of'), ('BH', 'Bahrain'), ('BI', 'Burundi'), ('BJ', 'Benin'), ('BT', 'Bhutan'), ('BV', 'Bouvet Island'), ('BW', 'Botswana'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BR', 'Brazil'), ('BS', 'Bahamas'), ('BY', 'Belarus'), ('BZ', 'Belize'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RS', 'Serbia'), ('RE', 'Reunion'), ('RO', 'Romania'), ('OM', 'Oman'), ('HR', 'Croatia'), ('HT', 'Haiti'), ('HU', 'Hungary'), ('HK', 'Hong Kong'), ('HN', 'Honduras'), ('HM', 'Heard Island and McDonald Islands'), ('EH', 'Western Sahara'), ('EE', 'Estonia'), ('EG', 'Egypt'), ('EC', 'Ecuador'), ('ET', 'Ethiopia'), ('ES', 'Spain'), ('ER', 'Eritrea'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('VU', 'Vanuatu'), ('NI', 'Nicaragua'), ('NL', 'Netherlands'), ('NO', 'Norway'), ('NA', 'Namibia'), ('NC', 'New Caledonia'), ('NE', 'Niger'), ('NF', 'Norfolk Island'), ('NG', 'Nigeria'), ('NZ', 'New Zealand'), ('NP', 'Nepal'), ('NR', 'Nauru'), ('NU', 'Niue'), ('KG', 'Kyrgyzstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KH', 'Cambodia'), ('KN', 'Saint Kitts and Nevis'), ('KM', 'Comoros'), ('KR', 'Korea, Republic of'), ('KP', "Korea, Democratic People's Republic of"), ('KW', 'Kuwait'), ('KZ', 'Kazakhstan'), ('KY', 'Cayman Islands'), ('DO', 'Dominican Republic'), ('DM', 'Dominica'), ('DJ', 'Djibouti'), ('DK', 'Denmark'), ('DE', 'Germany'), ('DZ', 'Algeria'), ('TZ', 'Tanzania, United Republic of'), ('TV', 'Tuvalu'), ('TW', 'Taiwan, Province of China'), ('TT', 'Trinidad and Tobago'), ('TR', 'Turkey'), ('TN', 'Tunisia'), ('TO', 'Tonga'), ('TL', 'Timor-Leste'), ('TM', 'Turkmenistan'), ('TJ', 'Tajikistan'), ('TK', 'Tokelau'), ('TH', 'Thailand'), ('TF', 'French Southern Territories'), ('TG', 'Togo'), ('TD', 'Chad'), ('TC', 'Turks and Caicos Islands'), ('AE', 'United Arab Emirates'), ('AD', 'Andorra'), ('AG', 'Antigua and Barbuda'), ('AF', 'Afghanistan'), ('AI', 'Anguilla'), ('AM', 'Armenia'), ('AL', 'Albania'), ('AO', 'Angola'), ('AQ', 'Antarctica'), ('AS', 'American Samoa'), ('AR', 'Argentina'), ('AU', 'Australia'), ('AT', 'Austria'), ('AW', 'Aruba'), ('AX', 'Aland Islands'), ('AZ', 'Azerbaijan'), ('QA', 'Qatar')]),
        ),
        migrations.AddField(
            model_name='conversation',
            name='creator',
            field=models.ForeignKey(related_name='created_conversations', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='icon',
            field=models.URLField(default='', blank=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='state',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='subject',
            field=models.CharField(default='', max_length=25, blank=True),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_conversations', through='shoutit.ConversationDelete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='type',
            field=models.SmallIntegerField(choices=[(0, 'chat'), (1, 'about_shout'), (2, 'public_chat')]),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='users',
            field=models.ManyToManyField(related_name='conversations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='conversationdelete',
            name='user',
            field=models.ForeignKey(related_name='deleted_conversations_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
