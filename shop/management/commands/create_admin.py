from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Creates an admin user if it does not exist'

    def handle(self, *args, **kwargs):
        username = 'admin'
        email = 'admin@glowlogic.com'
        password = 'securepassword123'  # Change this to a better password!

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
        else:
<<<<<<< HEAD
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
=======
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
>>>>>>> 80376b32d2d3103955d25d605a70c70e2b1cc83f
