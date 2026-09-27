from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from urllib.parse import quote
from .forms import PromptConstructorForm
from .models import Category, PromptTemplate, GeneratedPrompt, GuideArticle


def home(request):
    """Главная страница"""
    return render(request, 'core/home.html')


def offline_page(request):
    """Заглушка для полностью оффлайн-режима (отдаётся Service Worker'ом)"""
    return render(request, 'offline.html')


def guide(request):
    """Страница гайдбука с фильтрацией"""
    category = request.GET.get('category', '')
    
    articles = GuideArticle.objects.filter(is_published=True)
    
    if category:
        articles = articles.filter(category=category)
    
    categories = GuideArticle._meta.get_field('category').choices
    
    return render(request, 'core/guide.html', {
        'articles': articles,
        'categories': categories,
        'current_category': category,
    })


def article_detail(request, slug):
    """Детальная страница статьи"""
    article = GuideArticle.objects.get(slug=slug, is_published=True)
    article.views += 1
    article.save()
    
    # Похожие статьи
    related = GuideArticle.objects.filter(
        category=article.category,
        is_published=True
    ).exclude(pk=article.pk)[:3]
    
    return render(request, 'core/article_detail.html', {
        'article': article,
        'related': related,
    })


def constructor(request):
    """Конструктор промптов"""
    categories = Category.objects.filter(is_active=True).order_by('order')
    form = PromptConstructorForm()

    # Предустановка из query-параметров (?category=slug&template=id) —
    # ссылки из библиотеки шаблонов
    return render(request, 'core/constructor.html', {
        'form': form,
        'categories': categories,
        'preset_category': request.GET.get('category', ''),
        'preset_template': request.GET.get('template', ''),
    })


@require_POST
def generate_prompt_api(request):
    """API endpoint для генерации промпта"""
    try:
        data = json.loads(request.body)
        
        category_slug = data.get('category')
        context_data = data.get('context', {})
        
        # Серверная валидация (зеркалит JS-валидатор prompt-generator.js)
        required_fields = ['subject', 'grade', 'topic']
        missing = [f for f in required_fields
                   if not str(context_data.get(f, '')).strip()]
        if missing:
            return JsonResponse(
                {'error': 'Не заполнены обязательные поля: ' + ', '.join(missing)},
                status=400
            )

        allowed_tones = ['professional', 'friendly', 'strict', 'motivational']
        tone = context_data.get('tone', 'professional')
        context_data['tone'] = tone if tone in allowed_tones else 'professional'

        extra = str(context_data.get('additional_context', '')).strip()[:500]
        context_data['additional_context'] = extra
        context_data.setdefault('context', extra)

        # Находим шаблон (можно передать template_id для выбора конкретного)
        template_id = data.get('template_id')
        qs = PromptTemplate.objects.filter(is_active=True)
        if template_id:
            template = qs.filter(pk=template_id).first()
        else:
            template = qs.filter(category__slug=category_slug).first()
        
        if not template:
            return JsonResponse({'error': 'Шаблон не найден'}, status=404)
        
        # Генерируем промпт (упрощённая версия без C# для теста)
        generated_prompt = template.generate_prompt(context_data)
        
        # Сохраняем в историю (если пользователь авторизован)
        if request.user.is_authenticated:
            GeneratedPrompt.objects.create(
                user=request.user,
                template=template,
                category=template.category,
                context_data=context_data,
                generated_prompt=generated_prompt,
                ai_model='qwen'
            )
        
        return JsonResponse({
            'success': True,
            'prompt': generated_prompt,
            'qwen_url': 'https://chat.qwen.ai/?prompt=' + quote(generated_prompt[:1800])
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def templates_list(request):
    """Библиотека шаблонов"""
    templates = (PromptTemplate.objects
                 .filter(is_active=True, category__is_active=True)
                 .select_related('category'))
    return render(request, 'core/templates_page.html', {'templates': templates})


def history_page(request):
    """Оффлайн-история промптов (данные берутся из localStorage на клиенте)"""
    return render(request, 'core/history.html')


@login_required
def profile(request):
    """Личный кабинет с историей промптов"""
    prompts = GeneratedPrompt.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    return render(request, 'core/profile.html', {'prompts': prompts})