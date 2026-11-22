from django.db import models
from django.contrib.auth.models import User
import re
from urllib.parse import urlparse, parse_qs, urlencode 
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.utils.timezone import now

# -----------------------------------------------------------------
# 🚀 THE AUTO-MONETIZATION ENGINE
# -----------------------------------------------------------------
def auto_monetize_link(url, platform):
    """Automatically converts normal URLs into monetized links and OVERWRITES old ones"""
    if not url:
        return url
        
    # 🚀 BYPASS: Protects EarnKaro, Myntra shortlinks, and Bitli links!
    if any(domain in url for domain in ['fktr.in', 'ekaro.in', 'myntr.it', 'bitli.in']):
        return url 
        
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    # Amazon Affiliate Injection
    if platform == 'amazon' and 'amazon' in parsed.netloc:
        query['tag'] = ['glowguide-21'] 
            
    # Flipkart Affiliate Injection
    elif platform == 'flipkart' and 'flipkart' in parsed.netloc:
        query['affid'] = ['glowguide_id'] 

    new_query = urlencode(query, doseq=True)
    return parsed._replace(query=new_query).geturl()

# -----------------------------------------------------------------
# --- MAIN MODELS ---
# -----------------------------------------------------------------

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    suitable = models.CharField(max_length=200)
    price = models.CharField(max_length=50)
    stock = models.IntegerField(default=0)
    
    # 🚀 VENDOR & MRP FIELDS
    mrp = models.CharField(max_length=50, blank=True, null=True, help_text="Maximum Retail Price (e.g., 599)")
    vendor_price = models.CharField(max_length=50, blank=True, null=True, help_text="Exact price on the Official Website")
    vendor_link = models.URLField(max_length=500, blank=True, null=True)
    
    amazon_price = models.CharField(max_length=50, blank=True, null=True)
    amazon_link = models.URLField(max_length=1000, blank=True, null=True)
    flipkart_price = models.CharField(max_length=50, blank=True, null=True)
    flipkart_link = models.URLField(max_length=500, blank=True, null=True, help_text="Direct Flipkart URL")
    myntra_price = models.CharField(max_length=50, blank=True, null=True)
    myntra_link = models.URLField(max_length=1000, blank=True, null=True, help_text="Direct link to the specific product page on Myntra")
    
    available_sizes = models.CharField(max_length=200, blank=True, null=True)
    image_filename = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='', null=True, blank=True)
    normalized_name = models.CharField(max_length=500, blank=True, null=True)
    core_name = models.CharField(max_length=500, blank=True, null=True)
    size_variant = models.CharField(max_length=50, blank=True, null=True)
    auto_stack = models.BooleanField(default=True)
    buy_link = models.URLField(max_length=600, blank=True, null=True)
    store_button_image = models.ImageField(upload_to='store_buttons/', blank=True, null=True)
    size = models.CharField(max_length=50, default="100ml", help_text="Standard size of the product (e.g., 100ml)")
    # 🚀 The universal product code (UPC/EAN)
    barcode = models.CharField(max_length=50, blank=True, null=True, help_text="Scan the barcode to link it!")
    # 🚀 NEW: Dynamic text fields for the product detail page
    how_to_use = models.TextField(blank=True, null=True, help_text="Instructions for applying the product.")
    ingredients = models.TextField(blank=True, null=True, help_text="Full ingredient list or key active ingredients.")
    # 🚀 NEW: Admin toggles to hide specific vendor buttons
    show_amazon = models.BooleanField(default=True, help_text="Uncheck to completely hide Amazon for this product.")
    show_flipkart = models.BooleanField(default=True, help_text="Uncheck to completely hide Flipkart for this product.")
    show_myntra = models.BooleanField(default=True, help_text="Uncheck to completely hide Myntra for this product.")
    is_active = models.BooleanField(default=True, help_text="Uncheck this to temporarily hide the product without losing its data or images.")
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    
    
    @property
    def vendor_domain(self):
        """Smartly extracts the domain, bypassing affiliate shortlinks by checking the product name!"""
        name_lower = str(self.name).lower()
        
        if 'derma co' in name_lower:
            return 'thedermaco.com'
        elif 'mamaearth' in name_lower:
            return 'mamaearth.in'
        elif 'dot & key' in name_lower or 'dot and key' in name_lower:
            return 'dotandkey.com'
        elif 'minimalist' in name_lower:
            return 'beminimalist.co'
        elif 'cetaphil' in name_lower:
            return 'cetaphil.in'
        elif 'aqualogica' in name_lower:
            return 'aqualogica.in'
        elif 'cerave' in name_lower:
            return 'cerave.com'
        elif 'plum' in name_lower:
            return 'plumgoodness.com'
        elif 'mcaffeine' in name_lower:            # 🚀 ADD THIS LINE
            return 'mcaffeine.com'                 # 🚀 ADD THIS LINE
            
        # 2. Fallback: If brand isn't mapped above, try to pull from the URL
        if self.vendor_link:
            parsed_uri = urlparse(self.vendor_link)
            domain = parsed_uri.netloc.replace('www.', '')
            
            if domain in ['bitli.in', 'fktr.in', 'ekaro.in', 'myntr.it', 'bit.ly']:
                return "" 
                
            return domain
            
        return ""
    
    @property
    def vendor_name(self):
        """Returns the properly capitalized brand name for the UI button."""
        name_lower = str(self.name).lower()
        
        if 'derma co' in name_lower:
            return 'The Derma Co'
        elif 'mamaearth' in name_lower:
            return 'Mamaearth'
        elif 'dot & key' in name_lower or 'dot and key' in name_lower:
            return 'Dot & Key'
        elif 'minimalist' in name_lower:
            return 'Minimalist'
        elif 'cetaphil' in name_lower:
            return 'Cetaphil'
        elif 'aqualogica' in name_lower:
            return 'Aqualogica'
        elif 'cerave' in name_lower:
            return 'CeraVe'
        elif 'plum' in name_lower:
            return 'Plum'
        elif 'mcaffeine' in name_lower:            # 🚀 ADD THIS LINE
            return 'mCaffeine'                     # 🚀 ADD THIS LINE
            
        return 'Official'
        # Add any other major brands you have here...

        # 2. Fallback: If brand isn't mapped above, try to pull from the URL
        if self.vendor_link:
            parsed_uri = urlparse(self.vendor_link)
            domain = parsed_uri.netloc.replace('www.', '')
            
            # If it's an unrecognized shortlink, return nothing so the UI falls back to the dark store icon
            if domain in ['bitli.in', 'fktr.in', 'ekaro.in', 'myntr.it', 'bit.ly']:
                return "" 
                
            return domain
            
        return ""

    @property
    def lowest_price(self):
        prices = []
        for p in [self.price, self.amazon_price, self.flipkart_price, self.myntra_price, self.vendor_price]:
            if p and str(p).lower() not in ['none', '0', '0.00', '']:
                match = re.search(r'\d+(\.\d+)?', str(p).replace(',', ''))
                if match:
                    val = float(match.group())
                    if val > 0:
                        prices.append(val)
        
        if prices:
            min_val = min(prices)
            return int(min_val) if min_val.is_integer() else f"{min_val:.2f}"
        return None
    
    @property
    def auto_mrp(self):
        """Returns the real MRP if it exists, otherwise mathematically generates a realistic retail price."""
        if self.mrp and self.mrp != "None" and str(self.mrp).strip() != "":
            return self.mrp
            
        lowest = self.lowest_price
        if lowest:
            try:
                lowest_val = float(str(lowest).replace(',', ''))
                # Generate a realistic retail markup (approx 25% higher)
                fake_mrp = int(lowest_val * 1.25)
                # Retail psychology: Round to the nearest 9 (e.g., 450 becomes 459)
                fake_mrp = (fake_mrp // 10) * 10 + 9
                return str(fake_mrp)
            except Exception:
                pass
        return None

    @property
    def discount_percentage(self):
        """Calculates the discount using either the real MRP or the auto-generated one."""
        current_mrp = self.auto_mrp
        if current_mrp and self.lowest_price:
            try:
                mrp_val = float(re.search(r'\d+(\.\d+)?', str(current_mrp).replace(',', '')).group())
                lowest_val = float(str(self.lowest_price).replace(',', ''))
                
                if mrp_val > lowest_val and mrp_val > 0:
                    discount = ((mrp_val - lowest_val) / mrp_val) * 100
                    return int(discount)
            except Exception:
                pass
        return None

    # 🚀 AUTOMATION & TRACKING: Intercept links, clean categories, and log daily price!
    def save(self, *args, **kwargs):
        
        # --- STEP 1: CLEANUP & FORMATTING (Before Saving) ---
        
        # A. Inject Affiliate Tags
        self.amazon_link = auto_monetize_link(self.amazon_link, 'amazon')
        self.flipkart_link = auto_monetize_link(self.flipkart_link, 'flipkart')
        
        # B. Clean and Normalize Categories
        if self.category:
            cat_lower = str(self.category).lower().strip()
            
            if cat_lower in ['face wash', 'facewash', 'face cleansing']:
                self.category = 'Cleanser'
            elif cat_lower in ['night cream', 'night gel']:
                self.category = 'Night Cream'
            elif cat_lower in ['combo', 'kit', 'gift set', 'duo']:
                self.category = 'Combo'
            else:
                self.category = self.category.title()

        # --- STEP 2: SAVE TO DATABASE ---
        # This saves the cleaned data and gives the product an ID
        super().save(*args, **kwargs)
        
        # --- STEP 3: LOG PRICE HISTORY (After Saving) ---
        # We do this after saving so the product has a valid database ID to link to
        lowest = self.lowest_price
        if lowest:
            try:
                today = date.today()
                # Create or update today's price record
                history, created = PriceHistory.objects.get_or_create(
                    product=self,
                    date=today,
                    defaults={'price': Decimal(str(lowest))}
                )
                if not created and history.price != Decimal(str(lowest)):
                    history.price = Decimal(str(lowest))
                    history.save()
            except Exception:
                pass # Failsafe so the admin never crashes
    
   
  
    
    

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5) 
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)


# -----------------------------------------------------------------
# --- VARIANT MODELS ---
# -----------------------------------------------------------------

class ParentProduct(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    suitable = models.CharField(max_length=100, help_text="e.g., Oily, Acne")
    slug = models.SlugField(unique=True, help_text="For clean URLs")

    def __str__(self):
        return f"{self.brand} - {self.name}"

class ProductVariant(models.Model):
    parent_product = models.ForeignKey(ParentProduct, related_name='variants', on_delete=models.CASCADE, null=True, blank=True)
    size_variant_display_name = models.CharField(max_length=100, default="Standard", help_text="e.g., 150ml (Pack of 3)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True)
    amazon_link = models.URLField(max_length=1000, blank=True, null=True)
    myntra_link = models.URLField(max_length=1000, blank=True, null=True)
    official_store_link = models.URLField(max_length=1000, blank=True, null=True)
    slug = models.SlugField(unique=True, null=True, blank=True, help_text="Unique slug for this specific variant")

    def __str__(self):
        if self.parent_product:
            return f"{self.parent_product.name} - {self.size_variant_display_name}"
        return f"Unlinked Variant - {self.size_variant_display_name}"

class ExtraSize(models.Model):
    product = models.ForeignKey(Product, related_name='extra_sizes', on_delete=models.CASCADE)
    size_name = models.CharField(max_length=100, help_text="e.g., 150ml (Pack of 3)")
    
    price = models.CharField(max_length=50, blank=True, null=True, help_text="Official Store Price")
    amazon_price = models.CharField(max_length=50, blank=True, null=True)
    amazon_link = models.URLField(max_length=1000, blank=True, null=True, help_text="The exact Amazon link")
    
    flipkart_price = models.CharField(max_length=50, blank=True, null=True)
    flipkart_link = models.URLField(max_length=1000, blank=True, null=True, help_text="The exact Flipkart link")
    
    myntra_price = models.CharField(max_length=50, blank=True, null=True)
    myntra_link = models.URLField(max_length=1000, blank=True, null=True, help_text="The exact Myntra link")

    def __str__(self):
        return f"{self.size_name} for {self.product.name}"

    def save(self, *args, **kwargs):
        self.amazon_link = auto_monetize_link(self.amazon_link, 'amazon')
        self.flipkart_link = auto_monetize_link(self.flipkart_link, 'flipkart')
        super().save(*args, **kwargs)

# -----------------------------------------------------------------
# 🚀 NEW: PRICE HISTORY TRACKER
# -----------------------------------------------------------------
class PriceHistory(models.Model):
    product = models.ForeignKey(Product, related_name='price_history', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.product.name} on {self.date} - ₹{self.price}"

# -----------------------------------------------------------------
# 🚀 FEATURE 4: PREDICTIVE RESTOCK TRACKER
# -----------------------------------------------------------------
class ActiveRoutine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_routines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_started = models.DateTimeField(auto_now_add=True)
    estimated_days_to_empty = models.IntegerField(default=45) 
    reminder_sent = models.BooleanField(default=False)

    @property
    def needs_restock(self):
        empty_date = self.date_started + timedelta(days=self.estimated_days_to_empty)
        warning_date = empty_date - timedelta(days=5)
        return timezone.now() >= warning_date and not self.reminder_sent

    def __str__(self):
        return f"{self.user.username}'s {self.product.name}"
    
class RoutineLog(models.Model):
    """Tracks daily consistency and habit streaks."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routine_logs')
    date = models.DateField(default=now)
    
    # Track which parts of the day they completed
    am_completed = models.BooleanField(default=False)
    pm_completed = models.BooleanField(default=False)
    
    # Optional: Let them upload a daily selfie to watch their skin adapt
    progress_photo = models.ImageField(upload_to='progress_photos/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        # A user can only have ONE log per day
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    @property
    def is_fully_completed(self):
        """Helper to easily check if they did both routines."""
        return self.am_completed and self.pm_completed

class OutboundClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) 
    
    product_name = models.CharField(max_length=255)
    store_name = models.CharField(max_length=50) 
    clicked_at = models.DateTimeField(default=now)
    
    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} clicked {self.product_name} at {self.clicked_at}"
    

# --- 📸 SKIN PROGRESS TIMELINE ---
class SkinDiaryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary_entries')
    image = models.ImageField(upload_to='skin_diary/')
    date_taken = models.DateField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-date_taken']

    def __str__(self):
        return f"{self.user.username}'s skin on {self.date_taken}"

# --- 🔔 PRICE DROP NOTIFICATIONS ---
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# --- 👤 USER PROFILE EXTENSION ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True) # 🚀 NEW FIELD
    
    # 1. Skin Identity
    skin_type = models.CharField(max_length=50, blank=True, null=True)
    primary_concern = models.CharField(max_length=50, blank=True, null=True)
    budget = models.CharField(max_length=50, blank=True, null=True)
    
    # 2. Sensitivities
    no_go_ingredients = models.TextField(blank=True, null=True, help_text="Comma-separated list")
    
    # 3. Notification Settings
    notify_reminders = models.BooleanField(default=True)
    notify_price_drops = models.BooleanField(default=True)
    notify_newsletter = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"