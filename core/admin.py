from django.contrib import admin
from .models import Category, PromptTemplate, GeneratedPrompt, GuideArticle


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'system_prompt']
    list_editable = ['is_active']
    filter_horizontal = []  # Если будут ManyToMany


@admin.register(GeneratedPrompt)
class GeneratedPromptAdmin(admin.ModelAdmin):
    list_display = ['category', 'ai_model', 'is_favorite', 'created_at', 'user']
    list_filter = ['category', 'ai_model', 'is_favorite', 'created_at']
    search_fields = ['generated_prompt', 'context_data']
    readonly_fields = ['generated_prompt', 'context_data', 'created_at']


@admin.register(GuideArticle)
class GuideArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'published_at', 'views']
    list_filter = ['category', 'is_published', 'published_at']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'