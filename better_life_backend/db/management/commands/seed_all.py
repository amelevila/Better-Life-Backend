from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the database with all initial data (exercises + recipes)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding exercises...")
        call_command("seed_exercises")

        self.stdout.write("Seeding recipes...")
        call_command("seed_recipes")

        self.stdout.write(self.style.SUCCESS("All seed data loaded successfully."))
