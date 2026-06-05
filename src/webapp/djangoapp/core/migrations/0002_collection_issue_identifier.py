import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def backfill_issue_collections(apps, schema_editor):
    Collection = apps.get_model("core", "Collection")
    Issue = apps.get_model("core", "Issue")

    default_collection, _created = Collection.objects.get_or_create(
        prefix="TASK",
        defaults={
            "name": "Task",
            "description": "Default collection for migrated issues.",
            "is_active": True,
            "next_issue_sequence": 1,
        },
    )

    next_issue_sequence = 1
    issues = list(Issue.objects.order_by("created_at", "id"))
    for issue in issues:
        issue.collection_id = default_collection.pk
        issue.collection_issue_sequence = next_issue_sequence
        issue.issue_number = f"{default_collection.prefix}-{next_issue_sequence:03d}"
        next_issue_sequence += 1

    if issues:
        Issue.objects.bulk_update(
            issues,
            ["collection", "collection_issue_sequence", "issue_number"],
        )

    default_collection.next_issue_sequence = next_issue_sequence
    default_collection.save(update_fields=["next_issue_sequence"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "prefix",
                    models.CharField(
                        help_text="Prefix used for issue identifiers, for example TASK.",
                        max_length=16,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Use uppercase letters and digits only, starting with a letter.",
                                regex="^[A-Z][A-Z0-9]*$",
                            )
                        ],
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("next_issue_sequence", models.PositiveIntegerField(default=1)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="issue",
            name="collection",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="issues",
                to="core.collection",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="collection_issue_sequence",
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(backfill_issue_collections, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="issue",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="issues",
                to="core.collection",
            ),
        ),
    ]
