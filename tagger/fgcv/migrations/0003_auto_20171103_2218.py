# Generated by Django 2.0b1 on 2017-11-03 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fgcv', '0002_auto_20171103_2158'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='time_taken',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='photo',
            name='date_taken',
            field=models.DateField(blank=True, null=True),
        ),
    ]
