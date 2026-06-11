from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin 
from unfold.contrib.import_export.forms import ExportForm, ImportForm 
from .models import Product, Wishlist, ExtraSize, OutboundClick

class PriceRangeFilter(admin.SimpleListFilter):
    title = 'Cost / Price Range'
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return (
            ('under_500', 'Under ₹500'),
            ('500_to_1000', '₹500 - ₹1000'),
            ('over_1000', 'Over ₹1000'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'under_500':
            return queryset.filter(price__lt=500)
        if self.value() == '500_to_1000':
            return queryset.filter(price__gte=500, price__lte=1000)
        if self.value() == 'over_1000':
            return queryset.filter(price__gt=1000)
        return queryset

class ExtraSizeInline(TabularInline):
    model = ExtraSize
    extra = 1
    tab = True 

class ProductAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    # 🚀 Tells Django to append our custom buttons exactly here!
    change_form_template = "admin/custom_change_form.html"
    
    inlines = [ExtraSizeInline] 

    # 🚀 Added 'id' to the front so the product number shows up!
    list_display = ("id",
        "name",
        "category",
        "lowest_price",        # Use 'price' or whichever base price field your model uses
        "is_active",    # Must be here so list_editable can see it!
    )

    # 🚀 FIXED: Toggles 'is_active' right from the main list screen
    list_editable = ("is_active",)
    list_filter = ('is_active', 'category', PriceRangeFilter, 'suitable', 'auto_stack') 
    search_fields = ('name', 'category', 'suitable') 

    fieldsets = (
        ('📦 Basic Information', {
            # 🚀 ADDED 'size' HERE SO IT SHOWS UP IN THE ADMIN FORM!
            'fields': ('is_active', 'name', 'category','size', 'price','mrp', 'suitable', 'stock', 'image','show_amazon', 'show_flipkart', 'show_myntra')
        }),
        ('🔗 Grouping Data', {
            # 🚀 Added core_name here so you can link different sizes!
            'fields': ('core_name', 'auto_stack'),
            'description': "To link different sizes of the same product, give them the exact same Core Name (e.g., 'cetaphil-gentle-cleanser'). Leave 'Auto Stack' CHECKED for standalone products."
        }),
        ('🟧 Amazon Data', {
            'fields': ('amazon_price', 'amazon_link')
        }),
        ('🟦 Flipkart Data', {  
            'fields': ('flipkart_price', 'flipkart_link'),
            'description': 'Paste the exact Flipkart URL and price here to activate the Buy button.'
        }),
        ('🩷 Myntra Data', {
            'fields': ('myntra_price', 'myntra_link'),
            'description': 'Paste the exact Myntra URL and price here to activate the Buy button.'
        }),
        ('🛍️ Official Store Data', {
            'fields': ('vendor_price', 'vendor_link')
        }),
    )

    # ==========================================
    # ⚙️ BULLETPROOF REDIRECT LOGIC
    # ==========================================
    def response_change(self, request, obj):
        if "_save_and_next" in request.POST:
            next_obj = Product.objects.filter(id__gt=obj.id).order_by('id').first()
            if next_obj:
                self.message_user(request, f"✅ Saved '{obj.name}'. Moving forward.", level=messages.SUCCESS)
                return HttpResponseRedirect(reverse("admin:shop_product_change", args=[next_obj.id]))
            else:
                self.message_user(request, f"⚠️ Saved '{obj.name}'. You are already on the last product!", level=messages.WARNING)
                return HttpResponseRedirect(reverse("admin:shop_product_changelist"))

        if "_save_and_prev" in request.POST:
            prev_obj = Product.objects.filter(id__lt=obj.id).order_by('-id').first()
            if prev_obj:
                self.message_user(request, f"✅ Saved '{obj.name}'. Moving backward.", level=messages.SUCCESS)
                return HttpResponseRedirect(reverse("admin:shop_product_change", args=[prev_obj.id]))
            else:
                self.message_user(request, f"⚠️ Saved '{obj.name}'. You are already on the first product!", level=messages.WARNING)
                return HttpResponseRedirect(reverse("admin:shop_product_changelist"))

        return super().response_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        prev_obj = Product.objects.filter(id__lt=obj_id).order_by('-id').first()
        response = super().response_delete(request, obj_display, obj_id)
        if prev_obj:
            return HttpResponseRedirect(reverse("admin:shop_product_change", args=[prev_obj.id]))
        return response

admin.site.register(Product, ProductAdmin)
admin.site.register(Wishlist)


# ==========================================
# 📊 OUTBOUND CLICK TRACKER
# ==========================================
@admin.register(OutboundClick)
class OutboundClickAdmin(ModelAdmin): # Using Unfold's ModelAdmin for better UI
    # This creates columns in your admin dashboard
    list_display = ('product_name', 'store_name', 'clicked_at')
    
    # This adds a filter box on the right side to easily sort by store or date
    list_filter = ('store_name', 'clicked_at')
    
    # This adds a search bar at the top to find specific products
    search_fields = ('product_name',)
    
    # This prevents anyone from accidentally editing a log
    readonly_fields = ('product_name', 'store_name', 'clicked_at')