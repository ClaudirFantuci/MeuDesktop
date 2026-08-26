from django.db import migrations


def criar_grupo_administrador(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Administrador")


def remover_grupo_administrador(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Administrador").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0003_montagem_historicomontagem"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(criar_grupo_administrador, remover_grupo_administrador),
    ]
