"""Commande d'initialisation : crée le premier compte administrateur.
Usage : python manage.py bootstrap_admin --email admin@cimetiere.cg --password ... --full-name "..."
"""
from django.core.management.base import BaseCommand, CommandError
from apps.accounts.models import User, UserRole


class Command(BaseCommand):
    help = "Crée le premier compte administrateur du système (à exécuter une seule fois après les migrations)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--full-name", required=True, dest="full_name")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]
        full_name = options["full_name"].strip()

        if len(password) < 8:
            raise CommandError("Le mot de passe doit contenir au moins 8 caractères.")
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError(f"Un utilisateur avec l'email {email} existe déjà.")

        User.objects.create_superuser(
            username=email, email=email, password=password,
            full_name=full_name, role=UserRole.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f"Compte administrateur créé avec succès : {email}"))
