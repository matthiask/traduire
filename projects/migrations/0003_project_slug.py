# Generated by Django 5.1b1 on 2024-07-04 08:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0002_alter_catalog_options_alter_project_token_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="slug",
            field=models.SlugField(
                default="financemission-world", unique=True, verbose_name="slug"
            ),
            preserve_default=False,
        ),
    ]