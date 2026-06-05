from django.db import migrations, models

import djangoapp.branding.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppBranding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "singleton_enforcer",
                    models.CharField(default="app-branding", editable=False, max_length=32, unique=True),
                ),
                ("display_name_override", models.CharField(blank=True, max_length=255)),
                (
                    "logo_image",
                    models.FileField(blank=True, upload_to=djangoapp.branding.models.branding_logo_upload_to),
                ),
                (
                    "login_background_image",
                    models.FileField(
                        blank=True, upload_to=djangoapp.branding.models.branding_login_background_upload_to
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "App branding",
                "verbose_name_plural": "App branding",
            },
        ),
    ]
