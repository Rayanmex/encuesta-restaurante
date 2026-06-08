from django.urls import path
from . import views

urlpatterns = [
    path('', views.encuesta_publica, name='encuesta'),
    path('dashboard/', views.dashboard, name='dashboard'),
]


