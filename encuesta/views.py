from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import Pregunta, Respuesta, CodigoQR
import json
from django.db.models import Q
from datetime import datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

@login_required
def estadisticas_filtradas(request):
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    
    # Filtrar respuestas por fecha
    respuestas = Respuesta.objects.all()
    
    if desde:
        fecha_desde = datetime.strptime(desde, '%Y-%m-%d').date()
        respuestas = respuestas.filter(fecha__date__gte=fecha_desde)
    
    if hasta:
        fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d').date()
        respuestas = respuestas.filter(fecha__date__lte=fecha_hasta)
    
    # Estadísticas generales
    total_respuestas = Respuesta.objects.count()
    respuestas_periodo = respuestas.count()
    promedio_general = respuestas.aggregate(Avg('valor_estrella'))['valor_estrella__avg'] or 0
    
    # Datos para gráfico de evolución
    respuestas_por_dia = []
    if desde and hasta:
        fecha_actual = datetime.strptime(desde, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(hasta, '%Y-%m-%d').date()
        delta = (fecha_fin - fecha_actual).days
        for i in range(delta + 1):
            dia = fecha_actual + timedelta(days=i)
            count = respuestas.filter(fecha__date=dia).count()
            respuestas_por_dia.append({
                'fecha': dia.strftime('%d/%m'),
                'total': count
            })
    else:
        # Últimos 7 días por defecto
        hoy = timezone.now().date()
        for i in range(7):
            dia = hoy - timedelta(days=6 - i)
            count = respuestas.filter(fecha__date=dia).count()
            respuestas_por_dia.append({
                'fecha': dia.strftime('%d/%m'),
                'total': count
            })
    
    # Estadísticas por pregunta
    preguntas = Pregunta.objects.filter(activa=True)
    preguntas_stats = []
    for pregunta in preguntas:
        respuestas_qs = respuestas.filter(pregunta=pregunta)
        preguntas_stats.append({
            'id': pregunta.id,
            'total': respuestas_qs.count(),
            'promedio': round(respuestas_qs.aggregate(Avg('valor_estrella'))['valor_estrella__avg'] or 0, 1),
            'distribucion': [
                respuestas_qs.filter(valor_estrella=1).count(),
                respuestas_qs.filter(valor_estrella=2).count(),
                respuestas_qs.filter(valor_estrella=3).count(),
                respuestas_qs.filter(valor_estrella=4).count(),
                respuestas_qs.filter(valor_estrella=5).count(),
            ]
        })
    
    return JsonResponse({
        'success': True,
        'total_respuestas': total_respuestas,
        'respuestas_periodo': respuestas_periodo,
        'promedio_general': round(promedio_general, 1),
        'fechas': [d['fecha'] for d in respuestas_por_dia],
        'totales': [d['total'] for d in respuestas_por_dia],
        'preguntas_stats': preguntas_stats,
    })


# Vista pública de la encuesta

@ensure_csrf_cookie
@never_cache
def encuesta_publica(request):
    preguntas = Pregunta.objects.filter(activa=True)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            respuestas_data = data.get('respuestas', [])
            session_id = request.session.session_key or request.META.get('REMOTE_ADDR')
            
            if not request.session.session_key:
                request.session.create()
                session_id = request.session.session_key
            
            for resp_data in respuestas_data:
                pregunta_id = resp_data.get('pregunta_id')
                valor = resp_data.get('valor')
                pregunta = Pregunta.objects.get(id=pregunta_id)
                
                # Guardar según el tipo de pregunta
                if pregunta.tipo == 'estrella':
                    Respuesta.objects.create(
                        pregunta=pregunta,
                        valor_estrella=int(valor),
                        session_id=session_id
                    )
                elif pregunta.tipo == 'seleccion':
                    Respuesta.objects.create(
                        pregunta=pregunta,
                        valor_seleccion=valor,
                        session_id=session_id
                    )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    if not request.session.session_key:
        request.session.create()
    
    return render(request, 'encuesta.html', {'preguntas': preguntas})



# Vista para QR (misma encuesta, diferente URL)
@ensure_csrf_cookie
@never_cache
def encuesta_qr(request, codigo_uuid):
    codigo_qr = get_object_or_404(CodigoQR, codigo=codigo_uuid, activo=True)
    preguntas = Pregunta.objects.filter(activa=True)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            respuestas_data = data.get('respuestas', [])
            session_id = request.session.session_key or request.META.get('REMOTE_ADDR')
            
            if not request.session.session_key:
                request.session.create()
                session_id = request.session.session_key
            
            for resp_data in respuestas_data:
                pregunta_id = resp_data.get('pregunta_id')
                valor = resp_data.get('valor')
                pregunta = Pregunta.objects.get(id=pregunta_id)
                
                # Guardar según el tipo de pregunta
                if pregunta.tipo == 'estrella':
                    Respuesta.objects.create(
                        pregunta=pregunta,
                        valor_estrella=int(valor),
                        session_id=session_id
                    )
                elif pregunta.tipo == 'seleccion':
                    Respuesta.objects.create(
                        pregunta=pregunta,
                        valor_seleccion=valor,
                        session_id=session_id
                    )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    if not request.session.session_key:
        request.session.create()
    
    return render(request, 'encuesta.html', {'preguntas': preguntas, 'qr_nombre': codigo_qr.nombre})

@login_required
def dashboard(request):
    hoy = timezone.now().date()
    
    total_respuestas = Respuesta.objects.count()
    respuestas_hoy = Respuesta.objects.filter(fecha__date=hoy).count()
    promedio_hoy = Respuesta.objects.filter(fecha__date=hoy).aggregate(Avg('valor_estrella'))['valor_estrella__avg'] or 0
    
    # Respuestas por día (últimos 7 días)
    respuestas_por_dia = []
    for i in range(7):
        dia = hoy - timedelta(days=i)
        count = Respuesta.objects.filter(fecha__date=dia).count()
        respuestas_por_dia.append({
            'fecha': dia.strftime('%d/%m'),
            'total': count
        })
    respuestas_por_dia.reverse()
    
    # Estadísticas por pregunta
    preguntas = Pregunta.objects.filter(activa=True)
    stats_preguntas = []
    for pregunta in preguntas:
        respuestas_qs = Respuesta.objects.filter(pregunta=pregunta)
        stats_preguntas.append({
            'pregunta': pregunta,
            'total': respuestas_qs.count(),
            'promedio': round(respuestas_qs.aggregate(Avg('valor_estrella'))['valor_estrella__avg'] or 0, 1),
            'distribucion': {
                1: respuestas_qs.filter(valor_estrella=1).count(),
                2: respuestas_qs.filter(valor_estrella=2).count(),
                3: respuestas_qs.filter(valor_estrella=3).count(),
                4: respuestas_qs.filter(valor_estrella=4).count(),
                5: respuestas_qs.filter(valor_estrella=5).count(),
            }
        })
    
    # Códigos QR
    codigos_qr = CodigoQR.objects.all().order_by('-fecha_creacion')
    
    # TODAS las preguntas (para la gestión)
    todas_preguntas = Pregunta.objects.all().order_by('orden')
    
    context = {
        'total_respuestas': total_respuestas,
        'respuestas_hoy': respuestas_hoy,
        'promedio_hoy': round(promedio_hoy, 1),
        'respuestas_por_dia': respuestas_por_dia,
        'stats_preguntas': stats_preguntas,
        'codigos_qr': codigos_qr,
        'preguntas': todas_preguntas,  # ← Agrega esta línea
    }
    return render(request, 'dashboard/dashboard.html', context)

# Generar QR
@login_required
def generar_qr(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            qr = CodigoQR.objects.create(nombre=nombre, activo=True)
            return JsonResponse({
                'success': True,
                'id': qr.id,
                'nombre': qr.nombre,
                'codigo': str(qr.codigo),
                'url': qr.get_url()
            })
    return JsonResponse({'success': False, 'error': 'Nombre requerido'})

# Eliminar QR
@login_required
def eliminar_qr(request, qr_id):
    if request.method == 'POST':
        qr = get_object_or_404(CodigoQR, id=qr_id)
        qr.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# API para gestionar preguntas desde el dashboard
@login_required
def crear_pregunta_api(request):
    if request.method == 'POST':
        texto = request.POST.get('texto')
        tipo = request.POST.get('tipo', 'estrella')
        opciones = request.POST.get('opciones', '')
        orden = request.POST.get('orden', 0)
        activa = request.POST.get('activa') == 'True'
        
        if texto:
            pregunta = Pregunta.objects.create(
                texto=texto,
                tipo=tipo,
                opciones=opciones if tipo == 'seleccion' else None,
                orden=orden,
                activa=activa
            )
            return JsonResponse({'success': True, 'id': pregunta.id})
    return JsonResponse({'success': False, 'error': 'Datos inválidos'})

@login_required
def editar_pregunta_api(request, pregunta_id):
    if request.method == 'POST':
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        pregunta.texto = request.POST.get('texto', pregunta.texto)
        pregunta.tipo = request.POST.get('tipo', pregunta.tipo)
        pregunta.opciones = request.POST.get('opciones', pregunta.opciones)
        pregunta.orden = request.POST.get('orden', pregunta.orden)
        pregunta.activa = request.POST.get('activa') == 'True'
        pregunta.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def eliminar_pregunta_api(request, pregunta_id):
    if request.method == 'POST':
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        pregunta.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def obtener_pregunta_api(request, pregunta_id):
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    return JsonResponse({
        'id': pregunta.id,
        'texto': pregunta.texto,
        'tipo': pregunta.tipo,
        'opciones': pregunta.opciones or '',
        'orden': pregunta.orden,
        'activa': pregunta.activa
    })
    
@login_required
def toggle_activa_pregunta(request, pregunta_id):
    if request.method == 'POST':
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        activa = request.POST.get('activa') == 'true'
        pregunta.activa = activa
        pregunta.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
