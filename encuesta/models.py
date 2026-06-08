from django.db import models

class Respuesta(models.Model):
    CALIFICACIONES = [(1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐')]
    
    comida = models.IntegerField(choices=CALIFICACIONES, verbose_name="Comida")
    servicio = models.IntegerField(choices=CALIFICACIONES, verbose_name="Servicio")
    ambiente = models.IntegerField(choices=CALIFICACIONES, verbose_name="Ambiente")
    comentario = models.TextField(blank=True, verbose_name="Comentario (opcional)")
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Encuesta del {self.fecha.strftime('%d/%m/%Y %H:%M')}"