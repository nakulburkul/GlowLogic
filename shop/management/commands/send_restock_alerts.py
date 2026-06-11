from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from shop.models import ActiveRoutine

class Command(BaseCommand):
    help = 'Scans active routines and emails users who are about to run out of products.'

    def handle(self, *args, **kwargs):
        # Find all routines where the product is running out, and we haven't emailed them yet
        routines = ActiveRoutine.objects.filter(reminder_sent=False)
        alerts_sent = 0

        for routine in routines:
            if routine.needs_restock:
                user = routine.user
                product = routine.product
                
                # 🚀 Send the Predictive Email!
                subject = f"Running low on {product.name}? 💧"
                message = f"Hi {user.username},\n\nOur AI predicts you are about to run out of your {product.name} in the next 5 days! Keep your GlowGuide routine intact by restocking now.\n\nCurrent Lowest Price: ₹{product.lowest_price}\n\nRestock here: https://yourwebsite.com/product/{product.id}/"
                
                send_mail(
                    subject,
                    message,
                    'alerts@glowguide.com',
                    [user.email],
                    fail_silently=True,
                )
                
                # Mark as sent so we don't spam them tomorrow
                routine.reminder_sent = True
                routine.save()
                alerts_sent += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {alerts_sent} restock alerts.'))