from django.contrib import admin
from django.urls import path
from shop import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. 🚀 YOUR CUSTOM ADMIN URLS MUST GO FIRST!
    path('admin/analytics/export/', views.export_affiliate_analytics, name='export_analytics'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/analytics/trigger-scan/', views.trigger_price_analysis_api, name='trigger_scan'),   
    
    # 2. THEN THE DEFAULT DJANGO ADMIN!
    path('admin/', admin.site.urls),
    
    # Storefront Root
    path('', views.home, name='home'), 
    path('shop/', views.shop_page, name='shop'), 
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('guide/', views.skin_guide, name='guide'),
    path('quiz/', views.skin_quiz, name='skin_quiz'), 
    path('my-routine/', views.my_routine, name='my_routine'), 
    
    # User Accounts
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('wishlist/', views.wishlist_page, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('live-search/', views.live_search, name='live_search'),
    
   # AI Assistant
    path('log-routine/', views.log_routine, name='log_routine'),
    path('api/ai-skin-scanner/', views.ai_skin_scanner, name='ai_skin_scanner'),
    path('chat/', views.ai_assistant_page, name='ai_assistant_page'),
    path('api/analyze-ingredients/', views.analyze_ingredients_api, name='analyze_ingredients_api'),
    path('api/barcode/', views.barcode_lookup, name='barcode_lookup'),
    path('api/chat/', views.chat_bot_api, name='chat_bot_api'),
    
    # Affiliate Tracker
    path('track/<int:product_id>/<str:store>/', views.track_and_redirect, name='track_outbound'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)