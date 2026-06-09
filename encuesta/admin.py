from django.contrib import admin
from .models import Pregunta, Respuesta, CodigoQR

class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['texto', 'tipo', 'activa', 'orden', 'creada']
    list_editable = ['activa', 'orden']
    list_filter = ['tipo', 'activa']
    search_fields = ['texto']
    fields = ['texto', 'tipo', 'opciones', 'activa', 'orden']

class RespuestaAdmin(admin.ModelAdmin):
    list_display = ['pregunta', 'valor_estrella', 'valor_seleccion', 'fecha']
    list_filter = ['fecha', 'pregunta__tipo']
    search_fields = ['valor_seleccion']

class CodigoQRAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activo', 'fecha_creacion']
    list_editable = ['activo']

admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Respuesta, RespuestaAdmin)
admin.site.register(CodigoQR, CodigoQRAdmin)