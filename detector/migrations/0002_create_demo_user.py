from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations

# Demo account so anyone who downloads the project can log in right away.
# It is a normal user (not staff / not superuser), so it cannot open the
# admin panel. The app also has no "change password" page, so the password
# cannot be changed from the website.
DEMO_USERNAME = "Shajjar_Abbas"
DEMO_PASSWORD = "Testuser12345"


def create_demo_user(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    if not User.objects.filter(username=DEMO_USERNAME).exists():
        User.objects.create(
            username=DEMO_USERNAME,
            password=make_password(DEMO_PASSWORD),
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("detector", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_demo_user, migrations.RunPython.noop),
    ]
