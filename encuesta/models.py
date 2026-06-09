from django.db import models
import uuid

class Pregunta(models.Model):
    TIPO_PREGUNTA = [
        ('estrella', 'Calificación por estrellas (1-5)'),
        ('seleccion', 'Selección múltiple (opciones)'),
    ]
    
    texto = models.CharField(max_length=500, verbose_name="Texto de la pregunta")
    tipo = models.CharField(max_length=20, choices=TIPO_PREGUNTA, default='estrella')
    opciones = models.TextField(blank=True, null=True, verbose_name="Opciones (una por línea)")
    activa = models.BooleanField(default=True, verbose_name="¿Activa?")
    orden = models.IntegerField(default=0, verbose_name="Orden de aparición")
    creada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['orden', 'id']
    
    def __str__(self):
        return f"{self.texto[:50]}"
    
    def get_opciones_lista(self):
        if self.opciones:
            return [op.strip() for op in self.opciones.split('\n') if op.strip()]
        return []

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    valor_estrella = models.IntegerField(null=True, blank=True)
    valor_seleccion = models.CharField(max_length=200, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.valor_estrella:
            return f"⭐ {self.valor_estrella} - {self.pregunta.texto[:30]}"
        if self.valor_seleccion:
            return f"📌 {self.valor_seleccion} - {self.pregunta.texto[:30]}"
        return f"Respuesta a: {self.pregunta.texto[:30]}"

class CodigoQR(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del QR")
    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    def get_url(self):
        return f"/qr/{self.codigo}/"