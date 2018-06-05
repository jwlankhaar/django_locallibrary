# Generated by Django 2.0.5 on 2018-05-29 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_auto_20180528_1645'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['last_name', 'first_name'], 'permissions': (('can_create_update_delete_author', 'Create, update or delete author details'),)},
        ),
        migrations.AlterModelOptions(
            name='book',
            options={'permissions': (('can_create_update_delete_book', 'Create, update or delete a book'),)},
        ),
        migrations.AlterModelOptions(
            name='bookinstance',
            options={'ordering': ['due_back'], 'permissions': (('can_mark_returned', 'Set book as returned'), ('can_create_update_delete_bookinstance', 'Create, update or delete a book copy'))},
        ),
        migrations.AlterModelOptions(
            name='genre',
            options={'permissions': (('can_create_update_delete_genre', 'Create, update or delete a genre'),)},
        ),
    ]
