# Generated by Django 5.1b1 on 2024-07-18 17:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0004_event"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="action",
            field=models.CharField(
                choices=[
                    ("user-logged-in", "user logged in"),
                    ("project-access-granted", "project access granted"),
                    ("catalog-created", "created catalog"),
                    ("catalog-updated", "updated catalog"),
                    ("catalog-submitted", "submitted catalog"),
                    ("catalog-replaced", "replaced catalog"),
                    ("catalog-deleted", "deleted catalog"),
                ],
                max_length=40,
                verbose_name="action",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="created at"
            ),
        ),
    ]
