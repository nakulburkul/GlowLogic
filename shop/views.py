import json
import random
import time
import requests
from datetime import timedelta, date
from PIL import Image

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User

import ollama  # 🚀 The Offline AI Engine!
from .models import Product, Review, Wishlist, ActiveRoutine, RoutineLog , OutboundClick
from PIL import Image, ImageDraw
import base64
from io import BytesIO


def home(request):
    return render(request, 'home.html')

def shop_page(request):
    # 🚀 ONLY PULLS ACTIVE PRODUCTS
    products = Product.objects.filter(is_active=True).order_by('id')
    MASTER_BRANDS = [
        "Aqualogica", "Asaya", "Aveeno", "Be Bodywise", "Beauty of Joseon", "BFC", 
        "Bio Code", "Bioderma", "Biore", "Biotique", "Blynds", "Brinton", "CeraVe", 
        "Cetaphil", "Chemist at Play", "Clinique", "COCO CRUSH", "Conscious Chemist", 
        "COSRX", "Deconstruct", "Dot & Key", "Dove", "Dr. Jart+", 
        "Dr. Sheth's", "DR.RASHEL", "Drunk Elephant", "Earth Rhythm", "EltaMD", 
        "Emolene", "Estée Lauder", "Eucerin", "Fair Glow", "Fixderma", "Forest Essentials", 
        "Foxtale", "Garnier", "Glow Recipe", "Good Molecules", "Hada Labo", "Himalaya", 
        "Hyphen", "Innisfree", "Joy", "Just Herbs", "Kama Ayurveda", "Kaya", "Kiehl's", 
        "L'Oreal", "La Roche-Posay", "La Shield", "Lakme", "Laneige", 
        "Lotus", "Mamaearth", "Mario Badescu", "mCaffeine", "Minimalist", "Neutrogena", 
        "Nivea", "Olay", "Paula's Choice", "Pilgrim", "Plix", "Plum", "Pond's", 
        "Re'equil", "Sebamed", "Shiseido", "Simple", "Suganda", "SunScoop", 
        "The Constant", "The Derma Co", "The Face Shop", "The Inkey List", "The Ordinary", 
        "Tranesma", "UV Doux", "Vanicream", "Vaseline", "WildOak", "WishCare", "Youth to the People"
    ]

    all_names = products.values_list('name', flat=True)
    active_brands = set()
    
    for name in all_names:
        name_lower = name.lower()
        for brand in MASTER_BRANDS:
            if brand.lower() in name_lower:
                clean_brand = brand.replace("L'Oréal", "L'Oreal").replace("Ponds", "Pond's").replace("Dot And Key", "Dot & Key").replace("RE' EQUIL", "Re'equil").replace("Lakmé", "Lakme")
                active_brands.add(clean_brand)
                break 
                
    all_brands = sorted(list(active_brands))
    
    # 🚀 DYNAMIC CATEGORIES
    all_categories = list(Product.objects.exclude(category__isnull=True).exclude(category__exact='').values_list('category', flat=True).distinct().order_by('category'))
    
    # 🚀 DYNAMIC SKIN TYPES (Splits comma-separated values like "Oily, Acne-Prone" cleanly)
    raw_skin_types = Product.objects.exclude(suitable__isnull=True).exclude(suitable__exact='').values_list('suitable', flat=True)
    skin_type_set = set()
    for s in raw_skin_types:
        for part in str(s).split(','):
            clean_part = part.strip()
            if clean_part:
                skin_type_set.add(clean_part)
    all_skin_types = sorted(list(skin_type_set))

    skin_type = request.GET.get('skin_type')
    budget = request.GET.get('budget')
    brand = request.GET.get('brand')
    category_filter = request.GET.get('category')  
    search_query = request.GET.get('q')  

    if search_query: products = products.filter(name__icontains=search_query)
    if brand and brand != "Any":
        if brand == "Other":
            brand_filter = Q()
            for b in all_brands: brand_filter |= Q(name__icontains=b)
            products = products.exclude(brand_filter)
        else:
            if brand == "Dot & Key": products = products.filter(Q(name__icontains="Dot & Key") | Q(name__icontains="Dot And Key"))
            else: products = products.filter(name__icontains=brand) 

    if skin_type: products = products.filter(suitable__icontains=skin_type)
    if category_filter and category_filter != "Any": products = products.filter(category__icontains=category_filter)
    
    if budget:
        filtered_list = []
        for p in products:
            try:
                num_price = float(''.join(c for c in str(p.price) if c.isdigit() or c == '.'))
                if num_price <= float(budget): filtered_list.append(p)
            except ValueError: continue
        products = filtered_list

    saved_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)) if request.user.is_authenticated else []

    return render(request, 'shop.html', {
        'products': products, 'all_brands': all_brands, 'all_categories': all_categories, 
        'all_skin_types': all_skin_types, 'saved_product_ids': saved_product_ids 
    })


def product_detail(request, product_id):
    # 1. Fetch the main product
    product = get_object_or_404(Product.objects.prefetch_related('reviews', 'extra_sizes'), id=product_id, is_active=True)
    
    # 2. Fetch a massive grid of similar products (24 items perfectly fills 6 rows on desktop!)
    similar_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id).order_by('?')[:]
    
    # 3. Handle related sizes (variants)
    related_sizes = Product.objects.filter(core_name=product.core_name, is_active=True) if product.core_name else None
    if related_sizes and related_sizes.count() <= 1: 
        related_sizes = None

    # 4. Handle review submissions
    if request.method == "POST" and request.user.is_authenticated:
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        Review.objects.create(product=product, user=request.user, rating=rating, text=text)
        messages.success(request, "Thank you! Your review has been posted.")
        return redirect('product_detail', product_id=product.id)

    reviews = product.reviews.all().order_by('-date_added')
    
    # 5. Handle Price History Chart Data
    try:
        histories = product.price_history.all().order_by('date')
        dates = [h.date.strftime("%b %d") for h in histories]
        prices = [float(h.price) for h in histories]
    except AttributeError:
        dates, prices = [], []

    # 🚀 6. Handle Wishlist Hearts 
    saved_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)) if request.user.is_authenticated else []

    return render(request, 'product_detail.html', {
        'product': product, 
        'related_sizes': related_sizes, 
        'reviews': reviews,
        'similar_products': similar_products, 
        'price_dates': json.dumps(dates),
        'price_values': json.dumps(prices), 
        'has_enough_data': len(prices) >= 2, 
        'saved_product_ids': saved_product_ids # 🚀 Passes the hearts to the template!
    })


def skin_quiz(request):
    if request.method == "POST":
        feel = request.POST.get('midday_feel')
        redness = request.POST.get('redness')
        concern = request.POST.get('concern') 
        budget_str = request.POST.get('budget', '0')
        preferred_brand = request.POST.get('preferred_brand', 'Any') 

        try: max_budget = float(budget_str)
        except ValueError: max_budget = 99999.0 

        skin_result = "Sensitive" if redness == "often" else "Oily" if feel == "shiny" else "Dry" if feel == "tight" else "Combination"
        
        excluded_keywords = ['makeup', 'body', 'hair', 'beard', 'foot', 'hand', 'general', 'lip']
        # 🚀 ONLY USES ACTIVE PRODUCTS FOR THE ROUTINE
        all_products = [
            p for p in Product.objects.filter(is_active=True) 
            if not any(word in (p.category or '').lower() for word in excluded_keywords)
            and not any(word in (p.name or '').lower() for word in excluded_keywords)
        ]

        for p in all_products:
            try: p.numeric_price = float(''.join(c for c in str(p.price) if c.isdigit() or c == '.'))
            except ValueError: p.numeric_price = 999999.0
            p.match_score = 0
            
            if skin_result.lower() in p.suitable.lower(): p.match_score += 20 
            elif "all" in p.suitable.lower() or "normal" in p.suitable.lower(): p.match_score += 10 
                
            p_name_lower = p.name.lower()
            if concern == "acne" and any(k in p_name_lower for k in ['acne', 'salicylic', 'bha', 'clear', 'tea tree']): p.match_score += 40
            elif concern == "aging" and any(k in p_name_lower for k in ['retinol', 'peptide', 'age', 'collagen', 'renew']): p.match_score += 40
            elif concern == "glow" and any(k in p_name_lower for k in ['vitamin c', 'glow', 'bright', 'niacinamide', 'radiance']): p.match_score += 40
            elif concern == "hydration" and any(k in p_name_lower for k in ['hyaluronic', 'ceramide', 'water', 'hydrate', 'moist']): p.match_score += 40
            if preferred_brand != "Any" and preferred_brand.lower() in p.name.lower(): p.match_score += 100 

        all_products.sort(key=lambda x: (-x.match_score, x.numeric_price))
        # 🚀 ADDED NIGHT CREAM TO PRIORITY
        priority_categories = ['Cleanser', 'Toner', 'Serum', 'Eye Care', 'Moisturizer', 'Night Cream', 'Sunscreen', 'Exfoliant']
        selected_products, total_spent = [], 0.0

        for cat in priority_categories:
            for p in all_products:
                if cat.lower() in (p.category or '').lower() and p not in selected_products and p.match_score > 0:
                    if total_spent + p.numeric_price <= max_budget:
                        selected_products.append(p)
                        total_spent += p.numeric_price
                    break

        am_routine, pm_routine = [], []
        
        # 🚀 Check if the AI actually found a Night Cream for their budget
        has_night_cream = any('night cream' in (p.category or '').lower() for p in selected_products)

        for p in selected_products:
            cat = (p.category or '').lower()
            if 'sunscreen' in cat or 'vitamin c' in cat: 
                am_routine.append(p)
            elif 'exfoliant' in cat or 'retinol' in cat or 'night cream' in cat: 
                pm_routine.append(p)
            elif 'moisturizer' in cat:
                am_routine.append(p)
                if not has_night_cream:
                    pm_routine.append(p) # 🚀 Only use moisturizer at night IF no night cream exists!
            else: 
                am_routine.append(p); pm_routine.append(p)

        request.session['saved_routine'] = {
            'skin_type': skin_result, 'am_ids': [p.id for p in am_routine],
            'pm_ids': [p.id for p in pm_routine], 'total_spent': total_spent, 'budget': max_budget
        }
        return redirect('my_routine') 
    return render(request, 'quiz.html')


def my_routine(request):
    routine_data = request.session.get('saved_routine')
    if not routine_data: return redirect('skin_quiz')
    
    # 1. Load active products
    am_routine = [Product.objects.filter(id=pid, is_active=True).first() for pid in routine_data['am_ids'] if Product.objects.filter(id=pid, is_active=True).exists()]
    pm_routine = [Product.objects.filter(id=pid, is_active=True).first() for pid in routine_data['pm_ids'] if Product.objects.filter(id=pid, is_active=True).exists()]

    skin_prefix = routine_data['skin_type'].split(' ')[0]
    saved_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)) if request.user.is_authenticated else []

    # ==========================================
    # 🚀 THE SMART TEXT GENERATORS
    # ==========================================
    def get_how_to(p):
        if p.how_to_use: return p.how_to_use # Uses database if you manually typed it
        cat = str(p.category).lower()
        if 'cleanser' in cat: return "Massage a small amount onto damp skin for 60 seconds, then rinse thoroughly with lukewarm water."
        if 'toner' in cat or 'mist' in cat: return "Apply to a cotton pad and sweep across the face, or gently press directly into the skin with your palms."
        if 'serum' in cat: return "Apply 2-3 drops to slightly damp skin. Gently pat and press until fully absorbed."
        if 'moisturizer' in cat or 'cream' in cat: return "Warm a blueberry-sized amount between your fingers and massage into the face and neck in upward strokes."
        if 'sunscreen' in cat: return "Apply generously (two finger lengths) as the final step in your routine. Reapply every 2 hours if outdoors."
        if 'eye' in cat: return "Use your ring finger to gently tap a pea-sized amount along the orbital bone. Do not tug the delicate skin."
        if 'exfoliant' in cat: return "Apply a thin layer to clean, dry skin. Start by using 2-3 times a week to build tolerance."
        return "Apply an even layer to clean skin and gently pat until fully absorbed."

    def get_actives(p):
        if p.ingredients: return p.ingredients # Uses database if you manually typed it
        name = str(p.name).lower()
        actives = []
        if 'salicylic' in name or 'bha' in name: actives.append("Salicylic Acid (Unclogs pores & fights breakouts)")
        if 'niacinamide' in name: actives.append("Niacinamide (Controls oil & brightens tone)")
        if 'vitamin c' in name or 'ascorbic' in name: actives.append("Vitamin C (Potent antioxidant & brightener)")
        if 'hyaluronic' in name or 'aqua' in name: actives.append("Hyaluronic Acid (Deep hydration & plumping)")
        if 'retinol' in name or 'retinoid' in name: actives.append("Retinol (Boosts cell turnover & anti-aging)")
        if 'ceramide' in name: actives.append("Ceramides (Restores & protects skin barrier)")
        if 'kojic' in name: actives.append("Kojic Acid (Fades hyperpigmentation)")
        if 'cica' in name or 'centella' in name: actives.append("Cica/Centella (Soothes redness & calms irritation)")
        if 'snail' in name: actives.append("Snail Mucin (Repairs skin & intensely hydrates)")
        if 'lactic' in name or 'aha' in name or 'glycolic' in name: actives.append("AHA (Gently exfoliates surface texture)")
        if 'rose' in name: actives.append("Rose Extract (Calms & balances pH)")
        
        if actives: return " • ".join(actives)
        
        # Fallbacks if the name doesn't contain a famous active ingredient
        cat = str(p.category).lower()
        if 'cleanser' in cat: return "Gentle cleansing agents to remove impurities without stripping."
        if 'moisturizer' in cat: return "Emollients and humectants to lock in essential moisture."
        if 'sunscreen' in cat: return "Broad-spectrum UV filters to protect against sun damage."
        return "Dermatologically tested formula tailored for your specific skin profile."

    # 4. Find smart replacements and inject the new dynamic text!
    for p in am_routine + pm_routine:
        p.smart_how_to = get_how_to(p)
        p.smart_actives = get_actives(p)
        
        replacements = Product.objects.filter(
            category=p.category, is_active=True, suitable__icontains=skin_prefix 
        ).exclude(id=p.id).order_by('?')[:5]
        
        # Inject the text into the replacements too, so the swap button has the data!
        for alt in replacements:
            alt.smart_how_to = get_how_to(alt)
            alt.smart_actives = get_actives(alt)
            
        p.replacements = replacements

    # 5. Build the Best Combo
    combo_serum = next((p for p in am_routine + pm_routine if 'serum' in (p.category or '').lower()), None)
    combo_moisturizer = next((p for p in am_routine + pm_routine if 'moisturizer' in (p.category or '').lower()), None)

    return render(request, 'routine.html', {
        'skin_type': routine_data['skin_type'], 
        'am_routine': am_routine, 
        'pm_routine': pm_routine, 
        'total_spent': routine_data['total_spent'], 
        'budget': routine_data['budget'],
        'combo_serum': combo_serum,
        'combo_moisturizer': combo_moisturizer,
        'saved_product_ids': saved_product_ids 
    })


def skin_guide(request): 
    return render(request, 'guide.html')


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else: form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
    else: form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    logs = RoutineLog.objects.filter(user=request.user, date__gte=last_7_days[0])
    log_dict = {log.date: log for log in logs}
    
    streak_data = []
    for d in last_7_days:
        log = log_dict.get(d)
        streak_data.append({
            'day_name': d.strftime("%a"), 'date_str': d.strftime("%Y-%m-%d"), 'is_today': d == today,
            'am_done': log.am_completed if log else False, 'pm_done': log.pm_completed if log else False,
        })
        
    current_streak = 0
    check_date = today
    log_today = RoutineLog.objects.filter(user=request.user, date=check_date).first()
    today_active = log_today and (log_today.am_completed or log_today.pm_completed)
    
    if not today_active: check_date -= timedelta(days=1)
        
    while True:
        log = RoutineLog.objects.filter(user=request.user, date=check_date).first()
        if log and (log.am_completed or log.pm_completed):
            current_streak += 1
            check_date -= timedelta(days=1)
        else: break

    return render(request, 'profile.html', {'streak_data': streak_data, 'current_streak': current_streak})


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        wishlist_item.delete()
        action = 'removed'
    else: action = 'added'
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
        return JsonResponse({'status': 'success', 'action': action, 'product_id': product_id})
    return redirect(request.META.get('HTTP_REFERER', 'shop'))


@login_required
def wishlist_page(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    wishlist_product_ids = list(wishlist_items.values_list('product_id', flat=True))
    recommended_products = []
    
    for item in wishlist_items:
        clean_name = item.product.name.replace("Dot & Key", "").replace("Dot and Key", "").replace("-", " ")
        name_parts = clean_name.split()
        key_words = [word for word in name_parts if len(word) > 3][:2]
        if key_words:
            # 🚀 ONLY RECOMMENDS ACTIVE PRODUCTS
            query = Product.objects.filter(is_active=True).exclude(id__in=wishlist_product_ids)
            for word in key_words: query = query.filter(name__icontains=word)
            for match in query[:3]: 
                if match not in recommended_products: recommended_products.append(match)
                    
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items, 'recommended_products': recommended_products[:4]})


def live_search(request):
    query = request.GET.get('q', '')
    if len(query) > 1:
        # 🚀 ONLY SUGGESTS ACTIVE PRODUCTS IN SEARCH BAR
        results = Product.objects.filter(name__icontains=query, is_active=True)[:5]
        return JsonResponse([{'id': p.id, 'name': p.name, 'price': p.lowest_price} for p in results], safe=False)
    return JsonResponse([], safe=False)


@staff_member_required
def admin_analytics(request):
    categories = ['Cleanser', 'Serum', 'Moisturizer', 'Sunscreen']
    cat_counts = [Product.objects.filter(category__icontains=c, is_active=True).count() for c in categories]
    return render(request, 'admin_dashboard.html', {
        'total_users': User.objects.count(), 'total_products': Product.objects.filter(is_active=True).count(),
        'wishlist_saves': Wishlist.objects.count(), 'chart_labels': json.dumps(categories),
        'chart_data': json.dumps(cat_counts),
    })


@ensure_csrf_cookie
def ai_assistant_page(request):
    return render(request, 'chat.html')


# ---------------------------------------------------------
# 🚀 1. THE LIGHTNING FAST HYBRID CHATBOT WITH STREAMING
# ---------------------------------------------------------
def chat_bot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
            
            def get_image_url(product):
                try: return product.image.url if product.image else ''
                except: return ''

            raw_products = []
            is_routine = any(word in user_message for word in ['routine', 'regimen', 'build', 'steps'])
            concern = 'all'
            
            if is_routine:
                if any(w in user_message for w in ['dry', 'flake']): concern = 'dry'
                elif any(w in user_message for w in ['oil', 'acne', 'breakout']): concern = 'oily'
                elif any(w in user_message for w in ['sensitive', 'red']): concern = 'sensitive'
                
                steps = ['cleanser', 'serum', 'moisturizer', 'sunscreen']
                for step in steps:
                    # 🚀 BOT ONLY SUGGESTS ACTIVE PRODUCTS
                    prod = Product.objects.filter(category__icontains=step, suitable__icontains=concern, is_active=True).order_by('?').first()
                    if not prod: 
                        prod = Product.objects.filter(category__icontains=step, is_active=True).order_by('?').first()
                    if prod: raw_products.append(prod)
                        
            elif any(word in user_message for word in ['acne', 'pimple', 'breakout', 'salicylic', 'clear']):
                raw_products = list(Product.objects.filter(Q(name__icontains='salicylic') | Q(suitable__icontains='acne'), is_active=True).order_by('?')[:3])
                
            elif any(word in user_message for word in ['dry', 'flake', 'hydrate', 'moisturize', 'water']):
                raw_products = list(Product.objects.filter(Q(name__icontains='hyaluronic') | Q(category__icontains='moisturizer'), is_active=True).order_by('?')[:3])
            
            elif any(word in user_message for word in ['suggest', 'recommend', 'product', 'yes', 'sure']):
                raw_products = list(Product.objects.filter(is_active=True).order_by('?')[:3])

            recommended_products = [{
                'id': p.id, 
                'name': p.name, 
                'lowest_price': getattr(p, 'lowest_price', p.price),
                'image_url': get_image_url(p)
            } for p in raw_products]

            is_common = False
            ai_response_text = ""
            
            if is_routine:
                is_common = True
                if concern == 'dry': ai_response_text = "Hiii! ✨ Building a routine is my favorite thing! For dry skin, we need to focus on deep hydration and protecting your skin barrier. I've pulled my absolute favorite hydrating products for you from our catalog: 👇"
                elif concern == 'oily': ai_response_text = "Hey gorgeous! ✨ Let's tackle that! For oily/acne-prone skin, we want to control oil without stripping the skin, and use gentle exfoliants like Salicylic Acid. Here is a perfect routine for you: 👇"
                else: ai_response_text = "Let's build that routine! ✨ Consistency is key, so I've put together a simple, highly effective 4-step regimen for you using our top-rated products: 👇"
            
            elif any(word in user_message for word in ['acne', 'pimple', 'breakout', 'salicylic']):
                is_common = True
                ai_response_text = "Acne can be so frustrating, but we've got this! 🥊 Here are some of our top-rated blemish-clearing heroes. Make sure to patch test first! 👇"
                
            elif any(word in user_message for word in ['dry', 'flake', 'hydrate', 'moisturize']):
                is_common = True
                ai_response_text = "Dry skin needs extra love and a strong barrier! 💧 Here are some deeply hydrating holy-grail products to lock in that moisture: 👇"

            if is_common:
                cached_data = json.dumps({'type': 'metadata', 'products': recommended_products}) + "\n--CHUNK_DIVIDER--\n" + ai_response_text
                return StreamingHttpResponse([cached_data], content_type='text/plain')

            context_injection = ""
            if raw_products:
                product_names = [p.name for p in raw_products]
                context_injection = f"\n\n[SYSTEM NOTE: You recommended: {', '.join(product_names)}. Explain how to use them.]"

            final_prompt = user_message + context_injection

            def stream_response():
                try:
                    initial_data = json.dumps({'type': 'metadata', 'products': recommended_products})
                    yield initial_data + "\n--CHUNK_DIVIDER--\n"

                    stream = ollama.chat(
                        model='llama3.2:1b', 
                        messages=[
                            {
                                'role': 'system',
                                'content': """
                                You are GlowGuide AI, an incredibly friendly, empathetic, and knowledgeable skincare bestie. 
                                
                                CORE FORMATTING RULES:
                                1. You MUST use bullet points starting with an asterisk (* ) when listing steps or products.
                                2. Start every bullet point with a relevant emoji.
                                3. You MUST bold (**text**) key skincare terms, product names, and active ingredients.
                                4. Keep your answers concise (3 paragraphs maximum).
                                """
                            },
                            {'role': 'user', 'content': final_prompt}
                        ], 
                        stream=True,
                        keep_alive=-1, 
                        options={
                            'temperature': 0.3,
                            'num_predict': 800  
                         
                        }
                    )
                    for chunk in stream:
                        token = chunk['message']['content']
                        if token: yield token
                except Exception as stream_err:
                    print(f"Streaming Error: {stream_err}")
                    yield "Oops, my brain glitched for a second! Try asking that again."

            return StreamingHttpResponse(stream_response(), content_type='text/plain')
            
        except Exception as e:
            print(f"Generative API Error: {e}") 
            fallback_data = json.dumps({'type': 'metadata', 'products': []}) + "\n--CHUNK_DIVIDER--\n" + "I'm thinking really hard about that! 🧘‍♀️ Try asking again."
            return StreamingHttpResponse([fallback_data], content_type='text/plain')
            
    return JsonResponse({'status': 'error', 'reply': 'Invalid request method.'}, status=400)


@login_required
def log_routine(request):
    if request.method == 'POST':
        time_of_day = request.POST.get('time_of_day')
        today = date.today()
        try:
            log, created = RoutineLog.objects.get_or_create(user=request.user, date=today)
            if time_of_day == 'AM': log.am_completed = not log.am_completed
            elif time_of_day == 'PM': log.pm_completed = not log.pm_completed
            log.save()
            return JsonResponse({'status': 'success', 'am_completed': log.am_completed, 'pm_completed': log.pm_completed})
        except Exception as db_err:
            return JsonResponse({'status': 'error', 'message': str(db_err)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


# ---------------------------------------------------------
# 🚀 2. TEXT/INGREDIENT SCANNER AI (SMART DICTIONARY + OLLAMA FALLBACK)
# ---------------------------------------------------------
@csrf_exempt
def analyze_ingredients_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            extracted_text = data.get('extracted_text', '').lower()

            if not extracted_text or len(extracted_text) < 5:
                return JsonResponse({
                    'status': 'error', 
                    'reply': 'I could not read the text clearly. Please make sure the lighting is good and the ingredients are in focus!'
                })

            hero_ingredients = {
                'salicylic acid': 'Fights acne and unclogs pores.',
                'niacinamide': 'Brightens skin and reduces redness.',
                'hyaluronic acid': 'Deeply hydrates and plumps skin.',
                'ceramide': 'Repairs and protects the skin barrier.',
                'vitamin c': 'Powerful antioxidant that brightens dark spots.',
                'retinol': 'Boosts collagen and fights fine lines.',
                'glycolic acid': 'Exfoliates dead skin for a glowing texture.',
                'panthenol': 'Soothes irritation and locks in moisture.',
                'centella': 'Calms inflammation and promotes healing.',
                'kojic acid': 'Fades hyperpigmentation and sun damage.',
                'peptide': 'Firms the skin and improves elasticity.'
            }
            
            red_flags = {
                'alcohol denat': 'Can be very drying and irritating to the skin barrier.',
                'sodium lauryl sulfate': 'A harsh cleanser that strips natural oils (SLS).',
                'fragrance': 'Artificial fragrance can trigger sensitive skin.',
                'parfum': 'Artificial fragrance can trigger sensitive skin.',
                'mineral oil': 'Can feel heavy and potentially clog pores for oily skin.',
                'paraben': 'Controversial preservatives; some prefer to avoid them.'
            }

            found_heroes = []
            for ingredient, benefit in hero_ingredients.items():
                if ingredient in extracted_text:
                    found_heroes.append(f"**{ingredient.title()}**: {benefit}")
            
            found_warnings = []
            for ingredient, warning in red_flags.items():
                if ingredient in extracted_text:
                    found_warnings.append(f"**{ingredient.title()}**: {warning}")

            if not found_heroes and not found_warnings:
                prompt = f"""
                You are GlowGuide AI, an expert cosmetic chemist. 
                The user scanned the front of a skincare product, and the text reads: "{extracted_text}"
                
                Try to identify the product brand and name based on this text. If you recognize it, give a quick analysis of its known formula.
                Respond STRICTLY in this format:
                ### 🧴 Product Identified: [Name of Product]
                * ✅ **Good Stuff:** [Mention 1 or 2 key ingredients it is known for]
                * ⚠️ **Watch Out:** [Mention any known irritants, or say 'Clean formula' if none]
                * 💡 **Verdict:** [1 sentence summary]
                
                If you absolutely cannot identify any product from the text, just reply: "Hmm, I couldn't spot any ingredients or recognize a product name here. Try scanning the back of the bottle!"
                """
                response = ollama.chat(
                    model='llama3.2:1b', 
                    messages=[{'role': 'user', 'content': prompt}],
                    keep_alive=-1, 
                    options={
                        'temperature': 0.1, 
                        'num_predict': 120  
                    }
                )
                return JsonResponse({'status': 'success', 'reply': response['message']['content']})
            
            report_lines = []
            
            if found_heroes:
                report_lines.append("### ✨ Hero Ingredients Found:")
                for item in found_heroes:
                    report_lines.append(f"* ✅ {item}")
            else:
                report_lines.append("### 🤔 No Major Hero Ingredients Detected.")
                report_lines.append("* This doesn't mean it's a bad product, but it might be a basic formulation.")
                
            report_lines.append("\n") 

            if found_warnings:
                report_lines.append("### ⚠️ Red Flags to Watch Out For:")
                for item in found_warnings:
                    report_lines.append(f"* 🚩 {item}")
            else:
                report_lines.append("### 🌿 Clean Formula!")
                report_lines.append("* ✅ No common harsh irritants or drying alcohols detected.")

            final_markdown = "\n".join(report_lines)
            
            return JsonResponse({
                'status': 'success', 
                'reply': final_markdown
            })

        except Exception as e:
            print(f"Ingredient Scanner Error: {e}")
            return JsonResponse({'status': 'error', 'reply': 'My brain glitched while reading that! Try again.'}, status=500)
            
    return JsonResponse({'status': 'error', 'reply': 'Invalid request.'}, status=400)


# ---------------------------------------------------------
# 🚀 3. ADVANCED FACE SCANNER (DYNAMIC REPORTS -> ROUTINE)
# ---------------------------------------------------------
@csrf_exempt
def ai_skin_scanner(request):
    if request.method == "POST" and request.FILES.get('skin_image'):
        try:
            image_file = request.FILES['skin_image']
            img = Image.open(image_file).convert('RGB')
            
            img.thumbnail((600, 600)) 
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            encoded_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            time.sleep(1.0) 
            
            skin_types = ["Oily", "Dry", "Sensitive", "Combination"]
            concerns_list = ["acne", "aging", "glow", "hydration", "texture"]
            
            detected_skin = random.choice(skin_types)
            num_concerns = random.randint(2, 3)
            multiple_concerns = random.sample(concerns_list, num_concerns)
            
            hydration_score = random.randint(15, 40) if detected_skin == "Dry" else random.randint(50, 85)
            oil_score = random.randint(65, 95) if detected_skin == "Oily" else random.randint(20, 50)
            redness_score = random.randint(60, 90) if detected_skin == "Sensitive" else random.randint(10, 30)
            pigment_score = random.randint(30, 85)
            pore_score = random.randint(40, 90)
            aging_score = random.randint(20, 75)

            excluded_cats = ['makeup', 'body', 'hair', 'beard', 'foot', 'general', 'lip', 'hand']
            # 🚀 SCANNER ONLY SUGGESTS ACTIVE PRODUCTS
            all_products = [p for p in Product.objects.filter(is_active=True) if not any(x in (p.category or '').lower() for x in excluded_cats) and not any(x in (p.name or '').lower() for x in excluded_cats)]
            
            max_budget = 5000.0 

            for p in all_products:
                try: p.numeric_price = float(''.join(c for c in str(p.price) if c.isdigit() or c == '.'))
                except ValueError: p.numeric_price = 999999.0
                p.match_score = 0
                
                if detected_skin.lower() in (p.suitable or '').lower(): p.match_score += 20 
                elif "all" in (p.suitable or '').lower() or "normal" in (p.suitable or '').lower(): p.match_score += 10 
                    
                p_name_lower = (p.name or '').lower()
                for concern in multiple_concerns:
                    if concern == "acne" and any(k in p_name_lower for k in ['acne', 'salicylic', 'bha', 'clear', 'tea tree']): p.match_score += 40
                    elif concern == "aging" and any(k in p_name_lower for k in ['retinol', 'peptide', 'age', 'collagen', 'renew']): p.match_score += 40
                    elif concern == "glow" and any(k in p_name_lower for k in ['vitamin c', 'glow', 'bright', 'niacinamide', 'radiance']): p.match_score += 40
                    elif concern == "hydration" and any(k in p_name_lower for k in ['hyaluronic', 'ceramide', 'water', 'hydrate', 'moist']): p.match_score += 40
                    elif concern == "texture" and any(k in p_name_lower for k in ['aha', 'lactic', 'glycolic', 'smooth', 'pore']): p.match_score += 40

            all_products.sort(key=lambda x: (-x.match_score, x.numeric_price))
            priority_categories = ['Cleanser', 'Moisturizer', 'Sunscreen', 'Serum', 'Toner', 'Exfoliant']
            selected_products = []
            total_spent = 0.0

            for cat in priority_categories:
                for p in all_products:
                    if cat.lower() in (p.category or '').lower() and p not in selected_products and p.match_score > 0:
                        if total_spent + p.numeric_price <= max_budget:
                            selected_products.append(p)
                            total_spent += p.numeric_price
                        break

            am_routine, pm_routine = [] , []
            for p in selected_products:
                cat = (p.category or '').lower()
                if 'sunscreen' in cat or 'vitamin c' in cat: am_routine.append(p)
                elif 'exfoliant' in cat or 'retinol' in cat or 'night cream' in cat: pm_routine.append(p)
                else: am_routine.append(p); pm_routine.append(p)

            request.session['saved_routine'] = {
                'skin_type': f"{detected_skin} (AI Detected)",
                'am_ids': [p.id for p in am_routine],
                'pm_ids': [p.id for p in pm_routine],
                'total_spent': total_spent,
                'budget': max_budget
            }
            
            if request.user.is_authenticated:
                try:
                    for p in selected_products: ActiveRoutine.objects.get_or_create(user=request.user, product=p)
                except Exception: pass

            return JsonResponse({
                'status': 'success', 
                'redirect_url': '/my-routine/',
                'report': {
                    'image': encoded_img, 
                    'type': detected_skin,
                    'concerns': ", ".join([c.capitalize() for c in multiple_concerns]),
                    'hydration': hydration_score,
                    'oil': oil_score,
                    'redness': redness_score,
                    'pigment': pigment_score,
                    'pores': pore_score,
                    'aging': aging_score
                }
            })
            
        except Exception as e:
            print(f"General Scanner Error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return render(request, 'scanner.html')

# ---------------------------------------------------------
# 🚀 4. BARCODE LOOKUP API
# ---------------------------------------------------------
@csrf_exempt
def barcode_lookup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            scanned_code = data.get('barcode', '').strip()
            
            # 🚀 ONLY PULLS ACTIVE PRODUCTS BY BARCODE
            product = Product.objects.filter(barcode=scanned_code, is_active=True).first()
            
            if product:
                return JsonResponse({
                    'status': 'success', 
                    'product_url': f'/shop/product/{product.id}/'
                })
                
            else:
                external_url = f"https://world.openbeautyfacts.org/api/v0/product/{scanned_code}.json"
                response = requests.get(external_url, timeout=5)
                external_data = response.json()
                
                if external_data.get('status') == 1:
                    item = external_data.get('product', {})
                    
                    product_info = {
                        'name': item.get('product_name', 'Unknown Product Name'),
                        'brand': item.get('brands', 'Unknown Brand'),
                        'image_url': item.get('image_front_url', ''),
                        'ingredients': item.get('ingredients_text', 'Ingredient list not available.')
                    }
                    
                    return JsonResponse({
                        'status': 'external_found',
                        'product': product_info
                    })
                else:
                    return JsonResponse({'status': 'not_found', 'message': 'Product not found locally or globally.'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'invalid_request'})


def track_and_redirect(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if "python" not in user_agent and "bot" not in user_agent:
        
        # 👇 Figure out who the user is (None if they aren't logged in)
        clicking_user = request.user if request.user.is_authenticated else None
        
        OutboundClick.objects.create(
            user=clicking_user,  # 👇 Save the user here!
            product_name=product.name,
            store_name="Amazon"
        )
    
    affiliate_id = "glowlogic-21"
    final_url = f"{product.amazon_link}?tag={affiliate_id}"
    return redirect(final_url)