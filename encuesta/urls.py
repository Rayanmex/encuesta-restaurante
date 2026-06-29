from django.urls import path
from . import views

urlpatterns = [
    # Vistas públicas
    path('', views.encuesta_publica, name='encuesta'),
    path('qr/<uuid:codigo_uuid>/', views.encuesta_qr, name='encuesta_qr'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('estadisticas-filtradas/', views.estadisticas_filtradas, name='estadisticas_filtradas'),
    path('reporte-pdf/', views.generar_reporte_pdf, name='generar_reporte_pdf'),  # <-- NUEVA URL
    
    # Gestión de QR
    path('generar-qr/', views.generar_qr, name='generar_qr'),
    path('eliminar-qr/<int:qr_id>/', views.eliminar_qr, name='eliminar_qr'),
    
    # Gestión de preguntas
    path('pregunta/crear/', views.crear_pregunta_api, name='crear_pregunta_api'),
    path('pregunta/<int:pregunta_id>/editar/', views.editar_pregunta_api, name='editar_pregunta_api'),
    path('pregunta/<int:pregunta_id>/eliminar/', views.eliminar_pregunta_api, name='eliminar_pregunta_api'),
    path('pregunta/<int:pregunta_id>/datos/', views.obtener_pregunta_api, name='obtener_pregunta_api'),
    path('pregunta/<int:pregunta_id>/toggle-activa/', views.toggle_activa_pregunta, name='toggle_activa_pregunta'),
]