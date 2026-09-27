from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .forms import PromptConstructorForm
from .models import Category, PromptTemplate, GeneratedPrompt, GuideArticle


def home(request):
    """Главная страница"""
    return render(request, 'core/home.html')


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
    
    return render(request, 'core/constructor.html', {
        'form': form,
        'categories': categories,
    })


@require_POST
def generate_prompt_api(request):
    """API endpoint для генерации промпта"""
    try:
        data = json.loads(request.body)
        
        category_slug = data.get('category')
        context_data = data.get('context', {})
        
        # Находим шаблон
        template = PromptTemplate.objects.filter(
            category__slug=category_slug,
            is_active=True
        ).first()
        
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
            'qwen_url': f"https://chat.qwen.ai/?prompt={generated_prompt}"
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def templates_list(request):
    """Библиотека шаблонов"""
    templates = PromptTemplate.objects.filter(is_active=True)
    return render(request, 'core/templates.html', {'templates': templates})


@login_required
def profile(request):
    """Личный кабинет с историей промптов"""
    prompts = GeneratedPrompt.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    return render(request, 'core/profile.html', {'prompts': prompts})