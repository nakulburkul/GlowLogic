import os
import urllib.request
import urllib.parse
from django.core.management.base import BaseCommand
from django.conf import settings
from shop.models import Product
from django.db.models import Q

class Command(BaseCommand):
    help = 'Dynamically generates and links new placeholder images for missing products.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🎨 Booting up GlowGuide Auto-Image Generator..."))

        images_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
        os.makedirs(images_dir, exist_ok=True)

        # Using our newly created database column!
        missing_images = Product.objects.filter(
            Q(image_filename__isnull=True) | 
            Q(image_filename__exact='')
        )

        updated_count = 0

        for p in missing_images:
            self.stdout.write(f"⏳ Generating image for: {p.name}")
            
            short_name = " ".join(p.name.replace("Dot & Key", "").strip().split()[:3])
            if not short_name:
                short_name = "Skincare Product"
                
            encoded_name = urllib.parse.quote(short_name)
            image_url = f"https://dummyimage.com/600x600/fff9fa/d81b60.png&text={encoded_name}"
            
            filename = f"generated_fix_{p.id}.png"
            filepath = os.path.join(images_dir, filename)
            
            try:
                urllib.request.urlretrieve(image_url, filepath)
                p.image_filename = filename  # Saving to the new column!
                p.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ Saved and linked as {filename}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Failed to generate for {p.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Success! Generated and linked {updated_count} new images!"))