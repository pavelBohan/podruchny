# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('guide/', views.guide, name='guide'),
    path('constructor/', views.constructor, name='constructor'),
    path('constructor/generate/', views.generate_prompt_api, name='generate_prompt'),
    path('templates/', views.templates_list, name='templates'),
    path('profile/', views.profile, name='profile'),
    path('guide/', views.guide, name='guide'),
    path('guide/<slug:slug>/', views.article_detail, name='article_detail'),
]