from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Respuesta
from django.db.models import Avg, Count

def encuesta_publica(request):
    if request.method == 'POST':
        Respuesta.objects.create(
            comida=int(request.POST.get('comida', 3)),
            servicio=int(request.POST.get('servicio', 3)),
            ambiente=int(request.POST.get('ambiente', 3)),
            comentario=request.POST.get('comentario', '')
        )
        return render(request, 'gracias.html')
    return render(request, 'encuesta.html')

@staff_member_required
def dashboard(request):
    total = Respuesta.objects.count()
    promedio_comida = Respuesta.objects.aggregate(Avg('comida'))['comida__avg'] or 0
    promedio_servicio = Respuesta.objects.aggregate(Avg('servicio'))['servicio__avg'] or 0
    promedio_ambiente = Respuesta.objects.aggregate(Avg('ambiente'))['ambiente__avg'] or 0
    
    context = {
        'total': total,
        'promedio_comida': round(promedio_comida, 1),
        'promedio_servicio': round(promedio_servicio, 1),
        'promedio_ambiente': round(promedio_ambiente, 1),
        'respuestas_recientes': Respuesta.objects.all().order_by('-fecha')[:20]
    }
    return render(request, 'dashboard.html', context)