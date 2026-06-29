from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Pregunta, Respuesta, CodigoQR
import json
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

# Reportlab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

# ==================== VISTAS PÚBLICAS ====================

@ensure_csrf_cookie
@never_cache
def encuesta_publica(request):
    """Vista pública de la encuesta"""
    preguntas = Pregunta.objects.filter(activa=True).order_by('orden')
    
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

@ensure_csrf_cookie
@never_cache
def encuesta_qr(request, codigo_uuid):
    """Vista para QR (misma encuesta, diferente URL)"""
    codigo_qr = get_object_or_404(CodigoQR, codigo=codigo_uuid, activo=True)
    preguntas = Pregunta.objects.filter(activa=True).order_by('orden')
    
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

# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    """Vista principal del dashboard"""
    hoy = timezone.now().date()
    
    # ==================== ESTADÍSTICAS CORREGIDAS ====================
    
    # Total de encuestas completadas (respondientes únicos)
    total_encuestas = Respuesta.objects.values('session_id').distinct().count()
    
    # Total de respuestas individuales (por pregunta)
    total_respuestas = Respuesta.objects.count()
    
    # Respuestas hoy
    respuestas_hoy = Respuesta.objects.filter(fecha__date=hoy).count()
    
    # Promedio general de estrellas
    respuestas_estrellas = Respuesta.objects.filter(valor_estrella__isnull=False)
    promedio_general = respuestas_estrellas.aggregate(
        Avg('valor_estrella')
    )['valor_estrella__avg'] or 0
    
    # Respuestas por día (últimos 7 días)
    respuestas_por_dia = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        count = Respuesta.objects.filter(fecha__date=dia).count()
        respuestas_por_dia.append({
            'fecha': dia.strftime('%d/%m'),
            'total': count
        })
    
    # Estadísticas detalladas por pregunta
    preguntas = Pregunta.objects.filter(activa=True).order_by('orden')
    stats_preguntas = []
    
    for pregunta in preguntas:
        respuestas_qs = Respuesta.objects.filter(pregunta=pregunta)
        total = respuestas_qs.count()
        
        pregunta_stats = {
            'pregunta': pregunta,
            'total': total,
            'tipo': pregunta.tipo,
            'opciones': pregunta.get_opciones_lista(),
            'total_respuestas': total,
        }
        
        if pregunta.tipo == 'estrella':
            distribucion = {}
            distribucion_con_porcentaje = {}
            for i in range(1, 6):
                count = respuestas_qs.filter(valor_estrella=i).count()
                distribucion[str(i)] = count
                distribucion_con_porcentaje[str(i)] = {
                    'count': count,
                    'percentage': (count / total * 100) if total > 0 else 0
                }
            
            pregunta_stats.update({
                'promedio': round(respuestas_qs.aggregate(
                    Avg('valor_estrella')
                )['valor_estrella__avg'] or 0, 1),
                'distribucion': distribucion,
                'distribucion_con_porcentaje': distribucion_con_porcentaje,
            })
            
        elif pregunta.tipo == 'seleccion':
            distribucion = {}
            distribucion_con_porcentaje = {}
            opciones = pregunta.get_opciones_lista()
            
            if not opciones:
                opciones_from_respuestas = respuestas_qs.values_list('valor_seleccion', flat=True).distinct()
                opciones = list(opciones_from_respuestas)
            
            for opcion in opciones:
                count = respuestas_qs.filter(valor_seleccion=opcion).count()
                distribucion[opcion] = count
                distribucion_con_porcentaje[opcion] = {
                    'count': count,
                    'percentage': (count / total * 100) if total > 0 else 0
                }
            
            pregunta_stats.update({
                'distribucion': distribucion,
                'distribucion_con_porcentaje': distribucion_con_porcentaje,
            })
        
        stats_preguntas.append(pregunta_stats)
    
    # Códigos QR
    codigos_qr = CodigoQR.objects.all().order_by('-fecha_creacion')
    
    # TODAS las preguntas (para la gestión)
    todas_preguntas = Pregunta.objects.all().order_by('orden')
    
    context = {
        # Métricas principales
        'total_encuestas': total_encuestas,
        'total_respuestas': total_respuestas,
        'respuestas_hoy': respuestas_hoy,
        'promedio_general': round(promedio_general, 1),
        'respuestas_por_dia': respuestas_por_dia,
        'stats_preguntas': stats_preguntas,
        'codigos_qr': codigos_qr,
        'preguntas': todas_preguntas,
        'hoy': hoy,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def estadisticas_filtradas(request):
    """API para filtrar estadísticas por fecha"""
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
    
    # Encuestas completadas en el período
    sesiones_periodo = respuestas.values('session_id').distinct().count()
    
    # Promedio general de estrellas
    respuestas_estrellas = Respuesta.objects.filter(valor_estrella__isnull=False)
    promedio_general = respuestas_estrellas.aggregate(
        Avg('valor_estrella')
    )['valor_estrella__avg'] or 0
    
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
        for i in range(6, -1, -1):
            dia = hoy - timedelta(days=i)
            count = respuestas.filter(fecha__date=dia).count()
            respuestas_por_dia.append({
                'fecha': dia.strftime('%d/%m'),
                'total': count
            })
    
    # Estadísticas por pregunta
    preguntas = Pregunta.objects.filter(activa=True).order_by('orden')
    preguntas_stats = []
    
    for pregunta in preguntas:
        respuestas_qs = respuestas.filter(pregunta=pregunta)
        total = respuestas_qs.count()
        
        pregunta_data = {
            'id': pregunta.id,
            'texto': pregunta.texto,
            'tipo': pregunta.tipo,
            'total': total,
        }
        
        if pregunta.tipo == 'estrella':
            distribucion = []
            for i in range(1, 6):
                count = respuestas_qs.filter(valor_estrella=i).count()
                distribucion.append(count)
            
            pregunta_data.update({
                'promedio': round(respuestas_qs.aggregate(
                    Avg('valor_estrella')
                )['valor_estrella__avg'] or 0, 1),
                'distribucion': distribucion,
            })
            
        elif pregunta.tipo == 'seleccion':
            distribucion = {}
            opciones = pregunta.get_opciones_lista()
            
            if not opciones:
                opciones_from_respuestas = respuestas_qs.values_list('valor_seleccion', flat=True).distinct()
                opciones = list(opciones_from_respuestas)
            
            for opcion in opciones:
                count = respuestas_qs.filter(valor_seleccion=opcion).count()
                distribucion[opcion] = count
            
            pregunta_data['distribucion'] = distribucion
        
        preguntas_stats.append(pregunta_data)
    
    return JsonResponse({
        'success': True,
        'total_encuestas': sesiones_periodo,
        'total_respuestas': total_respuestas,
        'respuestas_periodo': respuestas_periodo,
        'promedio_general': round(promedio_general, 1),
        'fechas': [d['fecha'] for d in respuestas_por_dia],
        'totales': [d['total'] for d in respuestas_por_dia],
        'preguntas_stats': preguntas_stats,
    })

# ==================== REPORTE PDF ====================

@login_required
def generar_reporte_pdf(request):
    """Genera un reporte ejecutivo en PDF de la encuesta"""
    
    # Crear el buffer para el PDF
    buffer = io.BytesIO()
    
    # Configurar el documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#ff6b00'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=12,
        spaceBefore=20
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )
    stat_style = ParagraphStyle(
        'StatStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#ff6b00'),
        spaceAfter=4
    )
    
    # ==================== RECOPILAR DATOS ====================
    
    # Métricas principales
    total_encuestas = Respuesta.objects.values('session_id').distinct().count()
    total_respuestas = Respuesta.objects.count()
    respuestas_estrella = Respuesta.objects.filter(valor_estrella__isnull=False).count()
    respuestas_seleccion = Respuesta.objects.filter(valor_seleccion__isnull=False).count()
    promedio_general = Respuesta.objects.filter(valor_estrella__isnull=False).aggregate(Avg('valor_estrella'))['valor_estrella__avg'] or 0
    
    # Preguntas activas
    preguntas = Pregunta.objects.filter(activa=True).order_by('orden')
    total_preguntas = preguntas.count()
    
    # Calcular promedio de respuestas por encuesta
    promedio_respuestas_por_encuesta = (total_respuestas / total_encuestas) if total_encuestas > 0 else 0
    
    # Construir el contenido del PDF
    story = []
    
    # ==================== TÍTULO ====================
    story.append(Paragraph("📊 Reporte Ejecutivo de Satisfacción", title_style))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    story.append(Paragraph("Chiwu Banderillas Coreanas", subtitle_style))
    story.append(Spacer(1, 20))
    
    # ==================== RESUMEN EJECUTIVO ====================
    story.append(Paragraph("📈 Resumen Ejecutivo", heading_style))
    
    # Tabla de resumen
    data_resumen = [
        ['Métrica', 'Valor', 'Descripción'],
        ['Total de Encuestas', str(total_encuestas), 'Respondientes únicos'],
        ['Total de Respuestas', str(total_respuestas), 'Respuestas individuales'],
        ['Respuestas de Estrellas', str(respuestas_estrella), 'Preguntas tipo estrella'],
        ['Respuestas de Selección', str(respuestas_seleccion), 'Preguntas tipo selección'],
        ['Promedio General', f'{promedio_general:.1f}/5', 'Calificación promedio'],
        ['Preguntas Activas', str(total_preguntas), 'Preguntas en la encuesta'],
        ['Respuestas por Encuesta', f'{promedio_respuestas_por_encuesta:.1f}', 'Promedio de respuestas por encuesta'],
    ]
    
    tabla_resumen = Table(data_resumen, colWidths=[3*inch, 1.5*inch, 2.5*inch])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6b00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(tabla_resumen)
    story.append(Spacer(1, 20))
    
    # ==================== INSIGHTS ====================
    story.append(Paragraph("💡 Insights Clave", heading_style))
    
    insights = []
    if promedio_general >= 4.5:
        insights.append(f"✅ Excelente calificación general ({promedio_general:.1f}★/5). Los clientes están muy satisfechos.")
    elif promedio_general >= 3.5:
        insights.append(f"👍 Buena calificación general ({promedio_general:.1f}★/5). Hay oportunidades de mejora.")
    else:
        insights.append(f"⚠️ Calificación por debajo del promedio ({promedio_general:.1f}★/5). Se recomienda revisar áreas de mejora.")
    
    if total_encuestas < 10:
        insights.append(f"📊 Pocas encuestas respondidas ({total_encuestas}). Considera promover más la encuesta.")
    elif total_encuestas >= 50:
        insights.append(f"📊 Buen número de encuestas respondidas ({total_encuestas}). La muestra es representativa.")
    
    if respuestas_seleccion < total_encuestas * 0.5:
        participacion = round((respuestas_seleccion / total_encuestas * 100) if total_encuestas > 0 else 0, 1)
        insights.append(f"📋 La pregunta de selección tiene baja participación ({participacion}%).")
    
    for insight in insights:
        story.append(Paragraph(f"• {insight}", body_style))
        story.append(Spacer(1, 4))
    
    story.append(Spacer(1, 15))
    
    # ==================== ANÁLISIS POR PREGUNTA ====================
    story.append(PageBreak())
    story.append(Paragraph("📝 Análisis Detallado por Pregunta", heading_style))
    story.append(Paragraph(
        f"Total de preguntas activas: {total_preguntas} | Total de encuestas: {total_encuestas}",
        subtitle_style
    ))
    story.append(Spacer(1, 10))
    
    for idx, pregunta in enumerate(preguntas, 1):
        respuestas_qs = Respuesta.objects.filter(pregunta=pregunta)
        total = respuestas_qs.count()
        porcentaje_participacion = (total / total_encuestas * 100) if total_encuestas > 0 else 0
        
        icono = "⭐" if pregunta.tipo == 'estrella' else "📋"
        story.append(Paragraph(f"{icono} {idx}. {pregunta.texto}", heading_style))
        story.append(Paragraph(f"Total de respuestas: {total} ({porcentaje_participacion:.1f}% de participación)", body_style))
        
        if pregunta.tipo == 'estrella':
            avg = Respuesta.objects.filter(pregunta=pregunta, valor_estrella__isnull=False).aggregate(Avg('valor_estrella'))['valor_estrella__avg']
            story.append(Paragraph(f"Promedio: {avg:.1f}/5" if avg else "Promedio: N/A", stat_style))
            
            data_dist = [['Estrellas', 'Cantidad', 'Porcentaje', 'Barra']]
            max_count = max([respuestas_qs.filter(valor_estrella=i).count() for i in range(1, 6)] + [1])
            
            for i in range(1, 6):
                count = respuestas_qs.filter(valor_estrella=i).count()
                percentage = (count / total * 100) if total > 0 else 0
                bar_length = int((count / max_count) * 20) if max_count > 0 else 0
                bar = "█" * bar_length if bar_length > 0 else "·"
                data_dist.append([
                    f"{'★' * i}",
                    str(count),
                    f"{percentage:.1f}%",
                    bar
                ])
            
            tabla_dist = Table(data_dist, colWidths=[1.5*inch, 1.2*inch, 1.5*inch, 2.8*inch])
            tabla_dist.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(tabla_dist)
            
        elif pregunta.tipo == 'seleccion':
            opciones = pregunta.get_opciones_lista()
            if not opciones:
                opciones_from_respuestas = respuestas_qs.values_list('valor_seleccion', flat=True).distinct()
                opciones = list(opciones_from_respuestas)
            
            data_dist = [['Opción', 'Cantidad', 'Porcentaje', 'Barra']]
            max_count = max([respuestas_qs.filter(valor_seleccion=opcion).count() for opcion in opciones] + [1])
            
            for opcion in opciones:
                count = respuestas_qs.filter(valor_seleccion=opcion).count()
                percentage = (count / total * 100) if total > 0 else 0
                bar_length = int((count / max_count) * 20) if max_count > 0 else 0
                bar = "█" * bar_length if bar_length > 0 else "·"
                data_dist.append([
                    opcion[:20] + "..." if len(opcion) > 20 else opcion,
                    str(count),
                    f"{percentage:.1f}%",
                    bar
                ])
            
            tabla_dist = Table(data_dist, colWidths=[2*inch, 1.2*inch, 1.5*inch, 2.3*inch])
            tabla_dist.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(tabla_dist)
        
        story.append(Spacer(1, 15))
    
    # ==================== EVOLUCIÓN TEMPORAL ====================
    story.append(PageBreak())
    story.append(Paragraph("📈 Evolución Temporal de Respuestas", heading_style))
    
    hoy = timezone.now().date()
    data_evolucion = [['Fecha', 'Respuestas', 'Barra']]
    max_count = 1
    
    counts = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        count = Respuesta.objects.filter(fecha__date=dia).count()
        counts.append(count)
        if count > max_count:
            max_count = count
    
    for i, count in enumerate(counts):
        dia = hoy - timedelta(days=(6 - i))
        bar_length = int((count / max_count) * 20) if max_count > 0 else 0
        bar = "█" * bar_length if bar_length > 0 else "·"
        data_evolucion.append([
            dia.strftime('%d/%m'),
            str(count),
            bar
        ])
    
    tabla_evolucion = Table(data_evolucion, colWidths=[2*inch, 1.5*inch, 3.5*inch])
    tabla_evolucion.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6b00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(tabla_evolucion)
    
    # ==================== PIE DE PÁGINA ====================
    story.append(Spacer(1, 30))
    story.append(Paragraph("---", body_style))
    story.append(Paragraph(
        f"Reporte generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')} | Chiwu Banderillas Coreanas",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER
        )
    ))
    story.append(Paragraph(
        "Este reporte contiene información confidencial de la encuesta de satisfacción.",
        ParagraphStyle(
            'FooterNote',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER
        )
    ))
    
    # Construir el PDF
    doc.build(story)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_encuesta_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    response.write(pdf)
    
    return response

# ==================== GESTIÓN DE QR ====================

@login_required
def generar_qr(request):
    """Generar un nuevo código QR"""
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

@login_required
def eliminar_qr(request, qr_id):
    """Eliminar un código QR"""
    if request.method == 'POST':
        qr = get_object_or_404(CodigoQR, id=qr_id)
        qr.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# ==================== GESTIÓN DE PREGUNTAS ====================

@login_required
def crear_pregunta_api(request):
    """API para crear una nueva pregunta"""
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
    """API para editar una pregunta existente"""
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
    """API para eliminar una pregunta"""
    if request.method == 'POST':
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        pregunta.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def obtener_pregunta_api(request, pregunta_id):
    """API para obtener datos de una pregunta"""
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
    """API para activar/desactivar una pregunta"""
    if request.method == 'POST':
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        activa = request.POST.get('activa') == 'true'
        pregunta.activa = activa
        pregunta.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})