from django.db import migrations


def seed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    database = schema_editor.connection.alias

    for role in ["Admin", "Editor", "Viewer"]:
        Group.objects.using(database).get_or_create(
            name=role
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_roles,
            migrations.RunPython.noop,
        ),
    ]