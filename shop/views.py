import json
import random
import time
import requests
from datetime import timedelta, date
from PIL import Image
import urllib.parse
import torch
from torchvision import transforms
from PIL import Image as PILImage
import os

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib import messages
from django.db.models import Q, Case, When, Value, IntegerField
from django.contrib.auth.models import User
import re
from django.core.paginator import Paginator
from django.conf import settings

import ollama  
from .models import Product, Review, Wishlist, ActiveRoutine, RoutineLog, OutboundClick, SkinDiaryEntry, Notification, UserProfile
import base64
from io import BytesIO
import pandas as pd
from django.http import HttpResponse
from django.db.models import Count
from .tasks import scan_for_price_drops
import cv2
import numpy as np


def home(request):
    return render(request, 'home.html')

def shop_page(request):
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
    
    all_categories = list(Product.objects.exclude(category__isnull=True).exclude(category__exact='').values_list('category', flat=True).distinct().order_by('category'))
    
    raw_skin_types = Product.objects.exclude(suitable__isnull=True).exclude(suitable__exact='').values_list('suitable', flat=True)
    skin_type_set = set()
    for s in raw_skin_types:
        for part in str(s).split(','):
            clean_part = part.strip()
            if clean_part: skin_type_set.add(clean_part)
    all_skin_types = sorted(list(skin_type_set))

    # --- GET URL PARAMETERS ---
    skin_type = request.GET.get('skin_type')
    budget = request.GET.get('budget')
    brand = request.GET.get('brand')
    category_filter = request.GET.get('category')  
    search_query = request.GET.get('q')  
    sort_by = request.GET.get('sort', 'newest')

    # --- FILTERING ---
    if search_query:
        # 🚀 1. DIRECT E-COMMERCE MATCH: Instantly grab all related products!
        direct_matches = products.filter(
            Q(name__icontains=search_query) | 
            Q(category__icontains=search_query) |
            Q(ingredients__icontains=search_query)
            # Make sure there is NO trailing '|' here!
        ).distinct()
        
        if direct_matches.exists():
            products = direct_matches
        else:
            # 2. FUZZY FALLBACK: If they misspell something, use AI to guess
            from thefuzz import process, fuzz
            active_names = list(products.values_list('name', flat=True))
            matches = process.extractBests(search_query, active_names, scorer=fuzz.WRatio, score_cutoff=40, limit=100) # 🚀 Increased limit to 100
            matched_names = [m[0] for m in matches]
            products = products.filter(name__in=matched_names)

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
    
    products = list(products)
    for p in products:
        try: p.numeric_price = float(''.join(c for c in str(getattr(p, 'lowest_price', p.price) or '0') if c.isdigit() or c == '.'))
        except ValueError: p.numeric_price = 999999.0

    if budget:
        try:
            max_budget = float(budget)
            products = [p for p in products if p.numeric_price <= max_budget]
        except ValueError: pass

    if sort_by == 'price_low': products.sort(key=lambda x: x.numeric_price)
    elif sort_by == 'price_high': products.sort(key=lambda x: x.numeric_price, reverse=True)
    else: products.sort(key=lambda x: x.id, reverse=True) 

    active_filters = {}
    if search_query: active_filters['q'] = f'"{search_query}"'
    if brand and brand != "Any": active_filters['brand'] = brand
    if category_filter and category_filter != "Any": active_filters['category'] = category_filter
    if skin_type: active_filters['skin_type'] = skin_type
    if budget: active_filters['budget'] = f"Under ₹{budget}"

    paginator = Paginator(products, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    saved_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)) if request.user.is_authenticated else []

    return render(request, 'shop.html', {
        'products': page_obj, 
        'page_obj': page_obj,
        'all_brands': all_brands, 'all_categories': all_categories, 
        'all_skin_types': all_skin_types, 'saved_product_ids': saved_product_ids,
        'active_filters': active_filters, 'current_sort': sort_by
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.prefetch_related('reviews', 'extra_sizes'), id=product_id, is_active=True)
    
    all_ingredients = re.split(r'[,|\n\.]', (product.ingredients or ""))
    key_ingredients = [ing.strip().lower() for ing in all_ingredients if len(ing.strip()) > 3]
    
    ingredient_conditions = Q()
    for ing in key_ingredients[:5]: 
        ingredient_conditions |= Q(ingredients__icontains=ing)
    
    if not ingredient_conditions:
        ingredient_conditions = Q(pk=0) 
        
    similar_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id).annotate(
        relevancy_score=Case(
            When(suitable=product.suitable, then=Value(5)),
            default=Value(0),
            output_field=IntegerField(),
        ) + Case(
            When(ingredient_conditions, then=Value(3)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('-relevancy_score', '?')[:8] 
    
    related_sizes = Product.objects.filter(core_name=product.core_name, is_active=True) if product.core_name else None
    if related_sizes and related_sizes.count() <= 1: 
        related_sizes = None

    if request.method == "POST" and request.user.is_authenticated:
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        Review.objects.create(product=product, user=request.user, rating=rating, text=text)
        messages.success(request, "Thank you! Your review has been posted.")
        return redirect('product_detail', product_id=product.id)

    reviews = product.reviews.all().order_by('-date_added')
    
    try:
        histories = product.price_history.all().order_by('date')
        dates = [h.date.strftime("%b %d") for h in histories]
        prices = [float(h.price) for h in histories]
    except AttributeError:
        dates, prices = [], []

    saved_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)) if request.user.is_authenticated else []

    return render(request, 'product_detail.html', {
        'product': product, 
        'related_sizes': related_sizes, 
        'reviews': reviews,
        'similar_products': similar_products, 
        'price_dates': json.dumps(dates),
        'price_values': json.dumps(prices), 
        'has_enough_data': len(prices) >= 2, 
        'saved_product_ids': saved_product_ids 
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
        
        extras = request.POST.getlist('extras') 
        
        excluded_keywords = ['beard', 'foot', 'general', 'lip']
        if 'makeup' not in extras: excluded_keywords.append('makeup')
        if 'makeup_remover' not in extras: excluded_keywords.extend(['remover', 'micellar', 'balm'])
        if 'body_care' not in extras: excluded_keywords.extend(['body', 'lotion'])
        if 'hand_care' not in extras: excluded_keywords.append('hand')
        if 'haircare' not in extras: excluded_keywords.extend(['hair', 'shampoo', 'conditioner', 'scalp', 'oil'])

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
        
        priority_categories = []
        if 'makeup_remover' in extras: priority_categories.extend(['Makeup Remover', 'Micellar', 'Cleansing Balm', 'Cleansing Oil'])
        
        priority_categories.extend(['Cleanser', 'Toner', 'Serum', 'Eye Care', 'Moisturizer', 'Night Cream', 'Sunscreen'])
        
        if 'makeup' in extras: priority_categories.extend(['Makeup', 'Tint', 'BB Cream'])
        if 'haircare' in extras: priority_categories.extend(['Haircare', 'Shampoo', 'Conditioner'])
        if 'body_care' in extras: priority_categories.extend(['Body Care', 'Body Wash', 'Body Lotion'])
        if 'hand_care' in extras: priority_categories.append('Hand Care')
        priority_categories.append('Exfoliant')

        selected_products, total_spent = [], 0.0

        for cat in priority_categories:
            for p in all_products:
                if cat.lower() in (p.category or '').lower() and p not in selected_products and p.match_score > 0:
                    if total_spent + p.numeric_price <= max_budget:
                        selected_products.append(p)
                        total_spent += p.numeric_price
                    break

        am_routine, pm_routine = [], []
        has_night_cream = any('night cream' in (p.category or '').lower() for p in selected_products)

        for p in selected_products:
            cat = (p.category or '').lower()
            name_low = (p.name or '').lower()
            
            if 'sunscreen' in cat or 'vitamin c' in cat or 'makeup' in cat or 'bb cream' in name_low or 'tint' in name_low: 
                am_routine.append(p)
            elif 'exfoliant' in cat or 'retinol' in cat or 'night cream' in cat or 'remover' in cat or 'micellar' in cat or 'balm' in cat or 'cleansing oil' in cat: 
                pm_routine.append(p)
            elif 'moisturizer' in cat:
                am_routine.append(p)
                if not has_night_cream:
                    pm_routine.append(p)
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
    
    am_routine = [Product.objects.filter(id=pid, is_active=True).first() for pid in routine_data['am_ids'] if Product.objects.filter(id=pid, is_active=True).exists()]
    pm_routine = [Product.objects.filter(id=pid, is_active=True).first() for pid in routine_data['pm_ids'] if Product.objects.filter(id=pid, is_active=True).exists()]

    def check_routine_conflicts(routine_list, routine_name):
        warnings = []
        combined_text = " ".join([str(getattr(p, 'ingredients', '')).lower() + str(getattr(p, 'name', '')).lower() for p in routine_list if p])
        
        has_retinol = 'retinol' in combined_text or 'retinoid' in combined_text
        has_aha_bha = 'aha' in combined_text or 'glycolic' in combined_text or 'lactic' in combined_text or 'salicylic' in combined_text
        has_vit_c = 'vitamin c' in combined_text or 'ascorbic' in combined_text
        
        if has_retinol and has_aha_bha:
            warnings.append(f"⚠️ <b>{routine_name} Conflict:</b> You are combining Retinol with an AHA/BHA exfoliant. This can severely damage your skin barrier. Consider alternating nights.")
        if has_retinol and has_vit_c:
            warnings.append(f"⚠️ <b>{routine_name} Conflict:</b> Vitamin C and Retinol operate at different pH levels. Layering them can cause intense irritation. Move Vitamin C to the AM!")
            
        return warnings

    am_warnings = check_routine_conflicts(am_routine, "AM Routine")
    pm_warnings = check_routine_conflicts(pm_routine, "PM Routine")
    all_warnings = am_warnings + pm_warnings

    skin_prefix = routine_data['skin_type'].split(' ')[0]
    saved_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)) if request.user.is_authenticated else []

    def get_how_to(p):
        if p.how_to_use: return p.how_to_use 
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
        if p.ingredients: return p.ingredients 
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
        
        cat = str(p.category).lower()
        if 'cleanser' in cat: return "Gentle cleansing agents to remove impurities without stripping."
        if 'moisturizer' in cat: return "Emollients and humectants to lock in essential moisture."
        if 'sunscreen' in cat: return "Broad-spectrum UV filters to protect against sun damage."
        return "Dermatologically tested formula tailored for your specific skin profile."

    for p in am_routine + pm_routine:
        p.smart_how_to = get_how_to(p)
        p.smart_actives = get_actives(p)
        
        replacements = Product.objects.filter(
            category=p.category, is_active=True, suitable__icontains=skin_prefix 
        ).exclude(id=p.id).order_by('?')[:5]
        
        for alt in replacements:
            alt.smart_how_to = get_how_to(alt)
            alt.smart_actives = get_actives(alt)
            
        p.replacements = replacements

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
        'saved_product_ids': saved_product_ids,
        'routine_warnings': all_warnings 
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
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'avatar_image' in request.FILES:
            user_profile.avatar = request.FILES['avatar_image']
            user_profile.save()
            messages.success(request, "Profile picture updated!")
            return redirect('profile')

        if 'update_settings' in request.POST:
            request.user.email = request.POST.get('email', '')
            request.user.save()

            user_profile.phone_number = request.POST.get('phone_number', '')
            user_profile.skin_type = request.POST.get('skin_type')
            user_profile.primary_concern = request.POST.get('primary_concern')
            user_profile.budget = request.POST.get('budget')
            user_profile.no_go_ingredients = request.POST.get('no_go_ingredients')
            
            user_profile.notify_reminders = 'notify_reminders' in request.POST
            user_profile.notify_price_drops = 'notify_price_drops' in request.POST
            user_profile.notify_newsletter = 'notify_newsletter' in request.POST
            
            user_profile.save()
            messages.success(request, "Settings updated beautifully!")
            return redirect('profile')

        if request.FILES.get('diary_image'):
            notes = request.POST.get('diary_notes', '')
            SkinDiaryEntry.objects.create(
                user=request.user, 
                image=request.FILES['diary_image'], 
                notes=notes
            )
            messages.success(request, "Skin diary updated successfully!")
            return redirect('profile')
            
        if 'read_notifications' in request.POST:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return redirect('profile')

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

    diary_entries = SkinDiaryEntry.objects.filter(user=request.user).order_by('date_taken')
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    no_go_list = [i.strip() for i in user_profile.no_go_ingredients.split(',')] if user_profile.no_go_ingredients else []

    return render(request, 'profile.html', {
        'streak_data': streak_data, 
        'current_streak': current_streak,
        'diary_entries': diary_entries,
        'notifications': unread_notifications,
        'no_go_list': no_go_list
    })

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
    ml_recommendations = get_smart_recommendations(request.user)
    
    if not ml_recommendations.exists():
        wishlist_product_ids = wishlist_items.values_list('product_id', flat=True)
        ml_recommendations = Product.objects.filter(is_active=True).exclude(id__in=wishlist_product_ids).order_by('?')[:4]
                
    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items, 
        'recommended_products': ml_recommendations
    })

def live_search(request):
    query = request.GET.get('q', '')
    if len(query) > 1:
        # 🚀 1. EXACT MATCHES FIRST: Instantly find exactly what the user typed
        exact_matches = Product.objects.filter(name__icontains=query, is_active=True)[:5]
        results = [{'id': p.id, 'name': p.name, 'price': getattr(p, 'lowest_price', p.price)} for p in exact_matches]
        
        # 🚀 2. FUZZY TYPO GUESSER: If we didn't find 5 exact matches, use AI to fill the rest
        if len(results) < 5:
            from thefuzz import process, fuzz
            all_active = Product.objects.filter(is_active=True).exclude(id__in=[r['id'] for r in results])
            names_dict = {p.id: p.name for p in all_active}
            
            matches = process.extractBests(query, names_dict, scorer=fuzz.WRatio, score_cutoff=45, limit=5 - len(results))
            
            for match in matches:
                p = all_active.get(id=match[2])
                results.append({'id': p.id, 'name': p.name, 'price': getattr(p, 'lowest_price', p.price)})
                
        return JsonResponse(results, safe=False)
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


# ==========================================
# 🚀 3. THE CLINICAL-GRADE AI SKIN SCANNER
# ==========================================
@csrf_exempt
def ai_skin_scanner(request):
    if request.method == "POST" and request.FILES.get('skin_image'):
        try:
            image_file = request.FILES['skin_image']
            img = PILImage.open(image_file).convert('RGB')
            
            img.thumbnail((600, 600)) 
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            encoded_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            time.sleep(1.0) 
            
            # --- Default scores if no face is found (CRITICAL FALLBACKS) ---
            redness_score, oil_score, pore_score = 15, 20, 30
            hydration_score, acne_score, pigment_score, aging_score, glow_score = 85, 0, 12, 10, 50
            fine_line_score, deep_wrinkle_score, dark_circle_score = 10, 5, 15 
            
            detected_skin = "Normal"
            multiple_concerns = ["glow", "hydration"]
            
            real_acne_coords = []
            real_pigment_coords = []
            center_x, center_y, face_w, face_h = 50, 50, 75, 75
            
            image_file.seek(0)
            file_bytes = np.frombuffer(image_file.read(), np.uint8)
            img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # 🚀 ADD THIS DEBUG CHECK
            cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
            if not os.path.exists(cascade_path):
                print(f"CRITICAL ERROR: Haar Cascade file not found at {cascade_path}")
                return JsonResponse({'status': 'error', 'message': 'Detection model missing on server'}, status=500)
            
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
                
                # 🎯 1. STRICT ANATOMICAL ROI (Shave off background)
                y_offset = int(h * 0.15)
                h_roi = int(h * 0.75)
                x_offset = int(w * 0.15)
                w_roi = int(w * 0.70)

                roi_color = img_cv[y + y_offset : y + y_offset + h_roi, x + x_offset : x + x_offset + w_roi]
                
                hsv_roi = cv2.cvtColor(roi_color, cv2.COLOR_BGR2HSV)
                gray_roi = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
                lab_roi = cv2.cvtColor(roi_color, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab_roi)

                # =======================================================
                # 🛡️ THE PURE SKIN MASK (Extended to cover full eye socket!)
                # =======================================================
                skin_mask = np.ones(gray_roi.shape, dtype=np.uint8) * 255
                # 1. Erase Eyes & Eyebrows (Leaves Forehead Open, extends lower to block pupils!)
                cv2.rectangle(skin_mask, (0, int(h_roi * 0.18)), (w_roi, int(h_roi * 0.48)), 0, -1)
                # 2. Erase Nose Bridge & Nostrils
                cv2.rectangle(skin_mask, (int(w_roi * 0.30), int(h_roi * 0.48)), (int(w_roi * 0.70), int(h_roi * 0.68)), 0, -1)
                # 3. Erase Mouth, Lips, & Beard
                cv2.rectangle(skin_mask, (0, int(h_roi * 0.68)), (w_roi, h_roi), 0, -1)

                # =======================================================
                # 🌸 THE AGING MASK 
                # =======================================================
                aging_mask = np.zeros(gray_roi.shape, dtype=np.uint8)
                cv2.rectangle(aging_mask, (int(w_roi * 0.15), int(h_roi * 0.05)), (int(w_roi * 0.85), int(h_roi * 0.42)), 255, -1)

                # --- REDNESS ANALYSIS ---
                lower_red1, upper_red1 = np.array([0, 80, 50]), np.array([6, 255, 255])
                lower_red2, upper_red2 = np.array([174, 80, 50]), np.array([180, 255, 255])
                red_mask = cv2.inRange(hsv_roi, lower_red1, upper_red1) + cv2.inRange(hsv_roi, lower_red2, upper_red2)
                red_mask = cv2.bitwise_and(red_mask, red_mask, mask=skin_mask)

                # --- PIGMENTATION ANALYSIS ---
                valid_skin_pixels = max(cv2.countNonZero(skin_mask), 1)
                l_mean = np.mean(l_channel[skin_mask == 255]) if valid_skin_pixels > 0 else 127
                _, dark_mask = cv2.threshold(l_channel, int(max(l_mean - 15, 0)), 255, cv2.THRESH_BINARY_INV)
                dark_mask = cv2.bitwise_and(dark_mask, dark_mask, mask=skin_mask)

                # =======================================================
                # 👁️ FEATURE 3: DEDICATED UNDER-EYE ANALYSIS (Fixed Baseline)
                # =======================================================
                undereye_mask = np.zeros(gray_roi.shape, dtype=np.uint8)
                cv2.rectangle(undereye_mask, (int(w_roi * 0.15), int(h_roi * 0.45)), (int(w_roi * 0.40), int(h_roi * 0.55)), 255, -1)
                cv2.rectangle(undereye_mask, (int(w_roi * 0.60), int(h_roi * 0.45)), (int(w_roi * 0.85), int(h_roi * 0.55)), 255, -1)
                
                valid_undereye_pixels = max(cv2.countNonZero(undereye_mask), 1)
                undereye_l_mean = np.mean(l_channel[undereye_mask == 255]) if valid_undereye_pixels > 0 else l_mean
                
                # 🚀 FIX: Create a dedicated "Cheek Baseline" to compare the eyes against.
                # Cheeks are naturally the brightest/flattest part of the face.
                cheek_mask = np.zeros(gray_roi.shape, dtype=np.uint8)
                cv2.rectangle(cheek_mask, (int(w_roi * 0.20), int(h_roi * 0.55)), (int(w_roi * 0.80), int(h_roi * 0.65)), 255, -1)
                valid_cheek_pixels = max(cv2.countNonZero(cheek_mask), 1)
                cheek_l_mean = np.mean(l_channel[cheek_mask == 255]) if valid_cheek_pixels > 0 else l_mean
                
                # Calculates Dark Circles by measuring how much darker the bag is vs the upper cheek
                dark_circle_diff = max(cheek_l_mean - undereye_l_mean, 0)
                dark_circle_score = int(np.clip((dark_circle_diff * 4.0) + 5, 0, 100)) # Added a +5 floor to prevent absolute zero

                # =======================================================
                # 📈 FEATURE 5: WRINKLE DEPTH vs FINE LINES (Tuned Multipliers)
                # =======================================================
                grad_x = cv2.Sobel(gray_roi, cv2.CV_32F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(gray_roi, cv2.CV_32F, 0, 1, ksize=3)
                grad_mag = cv2.magnitude(grad_x, grad_y)
                
                grad_mag = cv2.convertScaleAbs(grad_mag) 
                grad_mag = cv2.bitwise_and(grad_mag, grad_mag, mask=aging_mask)
                
                valid_aging_pixels = max(cv2.countNonZero(aging_mask), 1)
                
                # 🚀 FIX: Raised thresholds to ignore normal skin texture, and massively lowered multipliers!
                fine_lines_count = np.sum((grad_mag > 60) & (grad_mag <= 150))
                fine_line_score = int(np.clip((fine_lines_count / valid_aging_pixels) * 50, 0, 100)) 
                
                deep_wrinkles_count = np.sum(grad_mag > 150)
                deep_wrinkle_score = int(np.clip((deep_wrinkles_count / valid_aging_pixels) * 80, 0, 100)) 
                
                aging_score = int(np.clip((fine_line_score * 0.5) + (deep_wrinkle_score * 0.5), 0, 100))

                # 🎯 EXTRACT REAL SPOTS
                contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                acne_spots = [c for c in contours if cv2.contourArea(c) > 5] 
                pig_contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                pigment_spots = [c for c in pig_contours if cv2.contourArea(c) > 5]

                # =======================================================
                # 📊 2. CLINICAL-GRADE SCORING (Strict & Honest Math)
                # =======================================================
                redness_ratio = (cv2.countNonZero(red_mask) / valid_skin_pixels) * 100
                redness_score = int(np.clip((redness_ratio - 5) * 1.5, 0, 100)) 

                v_channel = hsv_roi[:,:,2]
                high_value_mask = cv2.inRange(v_channel, 200, 255) 
                high_value_mask = cv2.bitwise_and(high_value_mask, high_value_mask, mask=skin_mask)
                shine_ratio = (cv2.countNonZero(high_value_mask) / valid_skin_pixels) * 100
                oil_score = int(np.clip(shine_ratio * 1.2, 0, 100)) 

                texture_std = np.std(gray_roi[skin_mask == 255]) if valid_skin_pixels > 0 else 5
                pore_score = int(np.clip((texture_std - 10) * 1.5, 0, 100))
                hydration_score = 100 - pore_score

                tone_variance = np.std(l_channel[skin_mask == 255]) if valid_skin_pixels > 0 else 5
                pigment_score = int(np.clip((tone_variance - 10) * 2.0, 0, 100)) 
                acne_score = int(np.clip(len(acne_spots) * 6, 0, 100))

                glow_score = int(np.clip(100 - (pore_score * 0.35) - (pigment_score * 0.3) - (aging_score * 0.3) + (oil_score * 0.1), 0, 100))

                # ==========================================
                # 🧠 PHASE 3: PYTORCH DEEP LEARNING INFERENCE
                # ==========================================
                roi_rgb = cv2.cvtColor(roi_color, cv2.COLOR_BGR2RGB)
                pil_roi = PILImage.fromarray(roi_rgb)

                preprocess = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                ])
                input_tensor = preprocess(pil_roi).unsqueeze(0)

                try:
                    model_path = os.path.join(settings.BASE_DIR, 'skin_model.pt') 
                    if not os.path.exists(model_path):
                        model_path = os.path.join(settings.BASE_DIR, 'skin.pt')

                    device = torch.device("cpu")
                    skin_ai = torch.jit.load(model_path, map_location=device)
                    skin_ai.eval() 

                    with torch.no_grad():
                        output = skin_ai(input_tensor)
                        _, predicted_idx = torch.max(output, 1)

                    ai_classes = ['Combination', 'Dry', 'Normal', 'Oily', 'Sensitive']
                    detected_skin = ai_classes[predicted_idx.item()]
                    
                except Exception as e:
                    detected_skin = "Normal" 

                multiple_concerns = []
                if redness_score > 35: multiple_concerns.append("redness")
                if pore_score > 55: multiple_concerns.append("texture")
                if acne_score > 25 or oil_score > 60: multiple_concerns.append("acne")
                if hydration_score < 45: multiple_concerns.append("hydration")
                if pigment_score > 40: multiple_concerns.append("pigmentation")
                if aging_score > 35: multiple_concerns.append("aging")
                
                if glow_score > 60 and acne_score < 20: multiple_concerns.append("glow")
                if not multiple_concerns: multiple_concerns = ["glow", "hydration"]

                # ✂️ CLINICAL HEADSHOT CROP
                padding = int(w * 0.15) 
                y1 = max(0, y - padding)
                y2 = min(img_cv.shape[0], y + h + padding)
                x1 = max(0, x - padding)
                x2 = min(img_cv.shape[1], x + w + padding)
                headshot_cv = img_cv[y1:y2, x1:x2]

                hw = x2 - x1
                hh = y2 - y1

                # =======================================================
                # 🎯 MAP REAL COORDINATES (ACCOUNTING FOR ROI OFFSETS)
                # =======================================================
                
                # 🚀 FIXED: We increased the limit from 6 to 50 spots each to capture abundant marks!
                # If your face has 40 acne marks, we will now catch all 40 of them.

                for spot in sorted(acne_spots, key=cv2.contourArea, reverse=True)[:50]: 
                    M = cv2.moments(spot)
                    if M["m00"] != 0:
                        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                        # Apply ROI offsets to get absolute position on input image
                        abs_x = x + x_offset + cx
                        abs_y = y + y_offset + cy
                        # Convert to percentage relative to the final cropped headshot
                        px = min(max(((abs_x) - x1) / hw * 100, 5), 95)
                        py = min(max(((abs_y) - y1) / hh * 100, 5), 95)
                        real_acne_coords.append({'x': round(px, 1), 'y': round(py, 1)})
                        
                # 🚀 FIXED: We increased the limit from 6 to 50 spots each to capture abundant marks!
                for spot in sorted(pigment_spots, key=cv2.contourArea, reverse=True)[:50]: 
                    M = cv2.moments(spot)
                    if M["m00"] != 0:
                        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                        abs_x = x + x_offset + cx
                        abs_y = y + y_offset + cy
                        px = min(max(((abs_x) - x1) / hw * 100, 5), 95)
                        py = min(max(((abs_y) - y1) / hh * 100, 5), 95)
                        real_pigment_coords.append({'x': round(px, 1), 'y': round(py, 1)})

                # 📐 Global Face Tracking Metrics
                center_x = (((x + w/2) - x1) / hw) * 100
                center_y = (((y + h/2) - y1) / hh) * 100
                face_w = (w / hw) * 100
                face_h = (h / hh) * 100

                # 📸 RE-ENCODE THE CLEAN IMAGE
                img_rgb = cv2.cvtColor(headshot_cv, cv2.COLOR_BGR2RGB)
                pil_annotated = PILImage.fromarray(img_rgb)
                pil_annotated.thumbnail((600, 600))
                buffered = BytesIO()
                pil_annotated.save(buffered, format="JPEG", quality=85)
                encoded_img = base64.b64encode(buffered.getvalue()).decode('utf-8')

                dataset_dir = os.path.join(settings.MEDIA_ROOT, 'dataset', detected_skin)
                os.makedirs(dataset_dir, exist_ok=True)
                cv2.imwrite(os.path.join(dataset_dir, f"face_scan_{int(time.time())}.jpg"), roi_color)

            excluded_cats = ['makeup', 'body', 'hair', 'beard', 'foot', 'general', 'lip', 'hand']
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
                    'aging': aging_score,
                    'fine_lines': fine_line_score,
                    'deep_wrinkles': deep_wrinkle_score,
                    'dark_circles': dark_circle_score,
                    'acne': acne_score,
                    'glow': glow_score,
                    'map_data': {
                        'acne': real_acne_coords,
                        'pigment': real_pigment_coords,
                        'center_x': center_x,
                        'center_y': center_y,
                        'face_w': face_w,   
                        'face_h': face_h    
                    }
                }
            })
            
        except Exception as e:
            print(f"General Scanner Error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return render(request, 'scanner.html')


@csrf_exempt
def barcode_lookup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            scanned_code = data.get('barcode', '').strip()
            
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
                    return JsonResponse({'status': 'external_found', 'product': product_info})
                else:
                    return JsonResponse({'status': 'not_found', 'message': 'Product not found locally or globally.'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'invalid_request'})


def track_and_redirect(request, product_id, store):
    product = get_object_or_404(Product, id=product_id)
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if "python" not in user_agent and "bot" not in user_agent:
        OutboundClick.objects.create(
            user=request.user if request.user.is_authenticated else None,
            product_name=product.name,
            store_name=store.capitalize()
        )
    
    encoded_name = urllib.parse.quote(product.name)

    if store == 'amazon':
        link = product.amazon_link if product.amazon_link and product.amazon_link != 'None' else f"https://www.amazon.in/s?k={encoded_name}"
        return redirect(f"{link}?tag=glowlogic-21" if "?" not in link else f"{link}&tag=glowlogic-21")
    elif store == 'flipkart':
        link = product.flipkart_link if product.flipkart_link and product.flipkart_link != 'None' else f"https://www.flipkart.com/search?q={encoded_name}"
        return redirect(f"{link}&affid=glowlogic_id" if "?" in link else f"{link}?affid=glowlogic_id")
    elif store == 'myntra':
        link = product.myntra_link if product.myntra_link and product.myntra_link != 'None' else f"https://www.myntra.com/search?q={encoded_name}"
        return redirect(link)
    elif store == 'vendor':
        return redirect(product.vendor_link if product.vendor_link else "/")
        
    return redirect('product_detail', product_id=product.id)

def get_smart_recommendations(user):
    user_likes = Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
    similar_users = Wishlist.objects.filter(product_id__in=user_likes).exclude(user=user).values_list('user_id', flat=True)
    recommendations = Product.objects.filter(
        wishlist__user_id__in=similar_users,
        is_active=True
    ).exclude(id__in=user_likes).annotate(
        match_score=Count('wishlist')
    ).order_by('-match_score')[:4]
    
    return recommendations


@staff_member_required
def export_affiliate_analytics(request):
    clicks = OutboundClick.objects.all().values(
        'clicked_at', 'product_name', 'store_name', 
        'user__username', 'user__id'
    )
    df = pd.DataFrame(list(clicks))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="GlowLogic_PowerBI_Dataset.csv"'
    
    if not df.empty:
        df['user__username'] = df['user__username'].fillna('Guest')
        df['user__id'] = df['user__id'].fillna('Anonymous')
        df['clicked_at'] = pd.to_datetime(df['clicked_at'])
        
        df['Date'] = df['clicked_at'].dt.date
        df['Time'] = df['clicked_at'].dt.time
        df['Year'] = df['clicked_at'].dt.year
        df['Month'] = df['clicked_at'].dt.month_name()
        df['Week_Number'] = df['clicked_at'].dt.isocalendar().week
        df['Day_of_Week'] = df['clicked_at'].dt.day_name()
        
        df = df.rename(columns={
            'clicked_at': 'Exact_Timestamp',
            'product_name': 'Product',
            'store_name': 'Retailer',
            'user__username': 'Username',
            'user__id': 'User_ID'
        })
        
        columns_order = [
            'Exact_Timestamp', 'Date', 'Time', 'Year', 'Month', 'Week_Number', 'Day_of_Week',
            'User_ID', 'Username', 'Product', 'Retailer'
        ]
        df = df[columns_order]
        df.to_csv(path_or_buf=response, index=False)
    else:
        response.write("No affiliate click data available yet.")
        
    return response

@staff_member_required
def trigger_price_analysis_api(request):
    if request.method == 'POST':
        scan_for_price_drops.delay()
        messages.success(request, "Background worker started! Scanning product databases now.")
        return redirect('admin_analytics')
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)