from django.contrib import admin
from .models import Pregunta, Respuesta, CodigoQR

class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['texto', 'activa', 'orden', 'creada']
    list_editable = ['activa', 'orden']

class RespuestaAdmin(admin.ModelAdmin):
    list_display = ['pregunta', 'valor_estrella', 'fecha']
    list_filter = ['fecha']

class CodigoQRAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activo', 'fecha_creacion']
    list_editable = ['activo']

admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Respuesta, RespuestaAdmin)
admin.site.register(CodigoQR, CodigoQRAdmin)