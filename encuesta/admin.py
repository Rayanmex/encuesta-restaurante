from django.contrib import admin
from .models import Respuesta

@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'comida', 'servicio', 'ambiente', 'comentario_corto']
    list_filter = ['comida', 'servicio', 'ambiente']
    readonly_fields = ['fecha']
    
    def comentario_corto(self, obj):
        return obj.comentario[:50] if obj.comentario else '-'
    comentario_corto.short_description = 'Comentario'