import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
import tempfile
import plotly.express as px
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTADO ---
st.set_page_config(page_title="AAM SkillMatrix Pro", layout="wide")

if 'vista' not in st.session_state:
    st.session_state.vista = 'landing'
if 'descargado' not in st.session_state:
    st.session_state.descargado = False

def confirmar_descarga():
    st.session_state.descargado = True

def activar_motor():
    st.session_state.vista = 'transition'
    st.session_state.descargado = False

def volver():
    st.session_state.vista = 'landing'
    st.session_state.descargado = False

# --- SCRIPTS DE SCROLL INVISIBLE ---
def scroll_to_top():
    components.html(
        """
        <script>
            window.parent.document.querySelector('.main').scrollTo(0, 0);
        </script>
        """,
        height=0
    )

# --- 2. CSS BLINDADO ---
st.markdown("""
    <style>
    .btn-comenzar > button { background-color: #E31837 !important; color: #FFFFFF !important; font-size: 20px !important; padding: 15px !important; font-weight: bold; border-radius: 8px;}
    .btn-comenzar > button:hover { background-color: #9B0F22 !important; color: #FFFFFF !important; border: 1px solid #FFFFFF;}
    .aam-red { color: #E31837; font-weight: bold; }
    
    .perfil-caja { background-color: #FFFFFF !important; padding: 15px; border-radius: 8px; border-left: 5px solid #002855; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%;}
    .perfil-caja p, .perfil-caja b, .perfil-caja i { color: #333333 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BASE DE DATOS DE CURSOS OFICIALES AAM ---
CURSOS = {
    "PLC S7 + Cognex": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y fuentes de energía primaria/secundaria.",
            "Diferencia herramientas de maquinado (taladros eléctricos/neumáticos, barrenos con/sin cuerda).",
            "Diferencia sensores capacitivos/inductivos y tipos de conexión PNP/NPN.",
            "Identifica elementos de un diagrama eléctrico y el RFL en sistemas neumáticos.",
            "Conoce el funcionamiento de cilindros neumáticos, candados en cadena y transportadores."
        ],
        "SOCIAL (Colaborativo)": [
            "Explica cómo colocar en la orden de trabajo la información de la actividad que realizó.",
            "Comunica efectivamente los hallazgos y el origen de señales durante el diagnóstico de fallas."
        ],
        "PRACTICA (Experiencial)": [
            "Agrega sensores, contactores, temporizadores y tarjetas de entradas/salidas.",
            "Navega en software In-Sight de Cognex y crea una nueva tarea de detección.",
            "Establece comunicación con el PLC S7 para enviar datos de visión.",
            "Realiza cambios de lógica en TIA Portal (secuencias automáticas, manuales y limpieza).",
            "Las variables (tags) en TIA Portal describen correctamente la acción con sus comentarios.",
            "Diagnostica fallas de PLC por falta de señal usando referencias cruzadas."
        ]
    },
    "PLC S7 + Keyence": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y fuentes de energía primaria/secundaria.",
            "Diferencia herramientas de maquinado (taladros eléctricos/neumáticos, barrenos con/sin cuerda).",
            "Diferencia sensores capacitivos/inductivos y tipos de conexión PNP/NPN.",
            "Identifica elementos de un diagrama eléctrico y el RFL en sistemas neumáticos.",
            "Conoce el funcionamiento de cilindros neumáticos, candados en cadena y transportadores."
        ],
        "SOCIAL (Colaborativo)": [
            "Explica cómo colocar en la orden de trabajo la información de la actividad que realizó.",
            "Comunica efectivamente los hallazgos y el origen de señales durante el diagnóstico de fallas."
        ],
        "PRACTICA (Experiencial)": [
            "Agrega sensores, contactores, temporizadores y tarjetas de entradas/salidas.",
            "Navega en software CV-X de Keyence y crea una nueva tarea de detección.",
            "Establece comunicación con el PLC S7 para enviar datos de visión.",
            "Realiza cambios de lógica en TIA Portal (secuencias automáticas, manuales y limpieza).",
            "Las variables (tags) en TIA Portal describen correctamente la acción con sus comentarios.",
            "Diagnostica fallas de PLC por falta de señal usando referencias cruzadas."
        ]
    },
    "PLC AB + Cognex": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y fuentes de energía primaria/secundaria.",
            "Diferencia herramientas de maquinado (taladros eléctricos/neumáticos, barrenos con/sin cuerda).",
            "Diferencia sensores capacitivos/inductivos y tipos de conexión PNP/NPN.",
            "Identifica elementos de un diagrama eléctrico y el RFL en sistemas neumáticos.",
            "Conoce el funcionamiento de cilindros neumáticos, candados en cadena y transportadores."
        ],
        "SOCIAL (Colaborativo)": [
            "Explica cómo colocar en la orden de trabajo la información de la actividad que realizó.",
            "Comunica efectivamente los hallazgos y el origen de señales durante el diagnóstico de fallas."
        ],
        "PRACTICA (Experiencial)": [
            "Agrega sensores, contactores, temporizadores y tarjetas de entradas/salidas.",
            "Navega en software In-Sight de Cognex y crea una nueva tarea de detección.",
            "Establece comunicación con el PLC AB para enviar datos de visión.",
            "Realiza cambios de lógica en Studio 5000 (secuencias automáticas, manuales y limpieza).",
            "Las variables (tags) en Studio 5000 describen correctamente la acción con sus comentarios.",
            "Diagnostica fallas de PLC por falta de señal usando referencias cruzadas."
        ]
    },
    "PLC AB + Keyence": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y fuentes de energía primaria/secundaria.",
            "Diferencia herramientas de maquinado (taladros eléctricos/neumáticos, barrenos con/sin cuerda).",
            "Diferencia sensores capacitivos/inductivos y tipos de conexión PNP/NPN.",
            "Identifica elementos de un diagrama eléctrico y el RFL en sistemas neumáticos.",
            "Conoce el funcionamiento de cilindros neumáticos, candados en cadena y transportadores."
        ],
        "SOCIAL (Colaborativo)": [
            "Explica cómo colocar en la orden de trabajo la actividad realizada.",
            "Comunica efectivamente los hallazgos y el origen de señales durante el diagnóstico de fallas."
        ],
        "PRACTICA (Experiencial)": [
            "Agrega sensores, contactores, temporizadores y tarjetas de entradas/salidas.",
            "Navega en software CV-X de Keyence y crea una nueva tarea de detección.",
            "Establece comunicación con el PLC AB para enviar datos de visión.",
            "Realiza cambios de lógica en Studio 5000 (secuencias automáticas, manuales y limpieza).",
            "Las variables (tags) en Studio 5000 describen correctamente la acción con sus comentarios.",
            "Diagnostica fallas de PLC por falta de señal usando referencias cruzadas."
        ]
    }
}

def calcular_pct_normalizado(valores):
    if not valores: return 0
    puntuaciones = [(v - 1) * 50 for v in valores]
    return sum(puntuaciones) / len(puntuaciones)

# --- 4. MOTOR LÓGICO INTELIGENTE ---
def generar_textos_dinamicos(pt, ps, pp, d_score, f_score, s_score, nombre, modulo):
    calif_absoluta = ( (pt*0.1 + ps*0.2 + pp*0.7) + (d_score*0.1 + f_score*0.3 + s_score*0.6) ) / 2
    
    if calif_absoluta >= 80 and pp >= 80 and pt >= 80:
        perfil = 1 
    elif pt >= 75 and pp < 75:
        perfil = 2 
    elif pp >= 75 and pt < 75:
        perfil = 3 
    elif calif_absoluta >= 60 and pp >= 60:
        perfil = 5 
    else:
        perfil = 4 
        
    software_plc = "TIA Portal" if "S7" in modulo else "Studio 5000"
    software_cam = "Cognex" if "Cognex" in modulo else "Keyence"

    # 1. Dona
    if calif_absoluta >= 90:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> Con un sobresaliente <b>{calif_absoluta:.1f}%</b>, el asociado consolida el Nivel 3. La capacitación se ha traducido en un cambio de conducta medible en la línea de producción."
    elif calif_absoluta >= 75:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> El <b>{calif_absoluta:.1f}%</b> indica una retención favorable. Transita hacia el Nivel 3, requiriendo un último empuje en piso para lograr independencia total."
    elif calif_absoluta >= 50:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> El puntaje de <b>{calif_absoluta:.1f}%</b> refleja asimilación parcial. Se encuentra estancado en el Nivel 2; entiende conceptos pero duda al aplicarlos."
    else:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> Alerta de riesgo operativo (<b>{calif_absoluta:.1f}%</b>). No hay evidencia de retención. Liberar al asociado en estas condiciones representa un riesgo para los equipos."

    # 2. Barras
    if perfil == 1:
        txt_barras = f"<b>Metodología 70-20-10:</b> Balance visual excelente. El sólido <b>{pt:.1f}% en Teoría</b> soporta exitosamente el <b>{pp:.1f}% de Ejecución Práctica</b>. El aprendizaje colaborativo también destaca positivamente."
    elif perfil == 2:
        txt_barras = f"<b>Metodología 70-20-10:</b> La gráfica evidencia fricción psicomotriz. Mantiene un <b>{pt:.1f}% en Teoría</b>, pero al enfrentarse a la máquina, la ejecución cae a un <b>{pp:.1f}%</b>."
    elif perfil == 3:
        txt_barras = f"<b>Metodología 70-20-10:</b> Riesgo de inercia mecánica detectado. La barra práctica es alta (<b>{pp:.1f}%</b>), pero el deficiente <b>{pt:.1f}% teórico</b> indica que no domina la lógica de las conexiones."
    else:
        txt_barras = f"<b>Metodología 70-20-10:</b> Las barras se encuentran sumamente deprimidas (Práctica en <b>{pp:.1f}%</b>). Esta carencia transversal demuestra que el asociado requiere reiniciar el módulo instruccional."

    # 3. Curva
    if s_score >= f_score and s_score >= 80:
        txt_curva = f"<b>Curva Cognitiva:</b> Trayectoria ascendente cerrando en <b>{s_score} pts</b>. Superó exitosamente la fase diagnóstica y logró aplicar los conocimientos en la prueba final autónoma."
    elif s_score < f_score and s_score < 70:
        txt_curva = f"<b>Curva Cognitiva:</b> Desplome en la fase final (bajó a <b>{s_score} pts</b>). Esto señala que el asociado sufre ansiedad o bloqueo de memoria cuando se le retira la supervisión guiada."
    elif d_score < 40 and f_score < 40 and s_score < 40:
        txt_curva = f"<b>Curva Cognitiva:</b> La línea roja permanece plana y deficiente en la base. Según la Taxonomía de Bloom, el alumno ni siquiera logró cimentar la etapa básica de 'Memorizar'."
    else:
        txt_curva = f"<b>Curva Cognitiva:</b> El avance es inconsistente o moderado. Cerrar con <b>{s_score} pts</b> indica que existen huecos técnicos que impidieron una comprensión fluida del sistema."

    # 4. Radar Inteligente (Corrección de Simetría)
    if pt < 20 and pp < 20 and ps < 20:
        txt_radar = f"<b>Huella de Brecha:</b> El polígono colapsado en el centro ({pt:.1f}%) evidencia una carencia estructural en todas las dimensiones formativas. Se requiere reiniciar el entrenamiento base."
    elif abs(pt - pp) <= 10 and pt >= 80:
        txt_radar = f"<b>Huella de Brecha:</b> El polígono muestra un equilibrio geométrico de alto rendimiento. Con <b>{pt:.1f}% en lógica teórica</b> y <b>{pp:.1f}% en destreza manual</b>, el asociado tiene un perfil ideal."
    elif abs(pt - pp) <= 10 and pt < 80:
        txt_radar = f"<b>Huella de Brecha:</b> El polígono es simétrico, pero sus vértices de <b>{pt:.1f}%</b> indican que el asociado requiere un desarrollo proporcional en ambas áreas (teoría y práctica)."
    elif pt > pp:
        txt_radar = f"<b>Huella de Brecha:</b> Este polígono mapea una clara asimetría cognitiva. Se detecta un fuerte sesgo hacia la abstracción lógica (<b>{pt:.1f}%</b>), dejando rezagada la destreza manual (<b>{pp:.1f}%</b>)."
    else:
        txt_radar = f"<b>Huella de Brecha:</b> Este polígono mapea una clara asimetría operativa. Se detecta un fuerte sesgo hacia la repetición mecánica (<b>{pp:.1f}%</b>), dejando vulnerable la comprensión lógica (<b>{pt:.1f}%</b>)."

    # 5. DICTAMEN TÉCNICO Y GANTT
    if perfil == 1:
        bloom_txt = f"<b>Evaluación de Dominio:</b> {nombre} es capaz de deducir lógicas de programación y diagnosticar fallas en <b>{software_plc}</b> y visión <b>{software_cam}</b> sin depender de rutinas pre-memorizadas."
        modelo_txt = "<b>Justificación del Cronograma:</b> No requiere rescate. Se proponen <b>2 sesiones</b> enfocadas exclusivamente en validación autónoma en piso y funciones de mentoría."
        dist_sesiones = [(0.0, 1.0, 3.0), (0.0, 0.0, 4.0)] 
        pasos_cortos = ["Mentoría Guiada", "Autonomía Total"]
        pasos = [
            "Validar su independencia asignándole órdenes de trabajo preventivas de alta complejidad.",
            "Asignarle el rol de asociado guía ('Presentar') para apoyar a compañeros con menor desempeño."
        ]
    elif perfil == 2:
        bloom_txt = f"<b>Evaluación de Dominio:</b> Domina la teoría y lee planos correctamente. Su área de oportunidad radica en transitar de la teoría a la conexión física de hardware."
        modelo_txt = "<b>Justificación del Cronograma:</b> Se requiere construir confianza táctil. El plan asigna <b>4 sesiones</b> aumentando gradualmente el tiempo de 'Intentar' (Ejecución libre)."
        dist_sesiones = [(1.0, 2.0, 1.0), (0.5, 1.5, 2.0), (0.0, 1.0, 3.0), (0.0, 0.0, 4.0)]
        pasos_cortos = ["Observación", "Práctica Asistida", "Práctica Media", "Ejecución Libre"]
        pasos = [
            f"Frenar el uso de manuales. Priorizar rutinas repetitivas de conexión de tarjetas I/O en {software_plc}.",
            "Implementar sesiones de observación activa donde el instructor solo intervenga en caso de riesgo a la maquinaria."
        ]
    elif perfil == 3:
        bloom_txt = f"<b>Evaluación de Dominio:</b> Ejecución operativa frágil. Logra mover la máquina, pero carece de la base analítica necesaria para rastrear fallas atípicas de red o voltaje."
        modelo_txt = "<b>Justificación del Cronograma:</b> Se debe corregir el empirismo. El plan exige <b>3 sesiones</b> con alta carga de 'Preparar' (Revisión teórica) antes de dejarlo tocar el equipo."
        dist_sesiones = [(3.0, 1.0, 0.0), (2.0, 1.0, 1.0), (0.5, 1.0, 2.5)]
        pasos_cortos = ["Revisión Teórica", "Balance en Piso", "Validación Técnica"]
        pasos = [
            "Impedir intervenciones correctivas sin supervisión hasta que valide la lectura fluida de esquemáticos.",
            f"Obligar al asociado a explicar verbalmente el flujo lógico de la señal en {software_plc} antes de puentear señales."
        ]
    elif perfil == 5:
        bloom_txt = f"<b>Evaluación de Dominio:</b> Desempeño medio. Logra resolver problemas básicos, pero la falta de soltura indica que la fase de 'Aplicación' aún requiere refuerzo continuo."
        modelo_txt = "<b>Justificación del Cronograma:</b> Perfil en maduración. Se sugieren <b>3 sesiones</b> estándar de refuerzo equilibrado para solidificar la competencia."
        dist_sesiones = [(1.0, 1.0, 2.0), (0.5, 1.0, 2.5), (0.0, 1.0, 3.0)]
        pasos_cortos = ["Repaso General", "Práctica Continua", "Liberación en Celda"]
        pasos = [
            "Continuar asignándole mantenimientos preventivos regulares para que gane velocidad.",
            "Agendar una breve validación diagnóstica en un mes para asegurar que no haya pérdida de conocimiento."
        ]
    else: 
        bloom_txt = f"<b>Evaluación de Dominio:</b> Riesgo Crítico. El asociado carece de las bases mínimas requeridas. Incapaz de leer diagramas o de diagnosticar fallas básicas en <b>{software_plc}</b>."
        if calif_absoluta <= 20: 
            modelo_txt = "<b>Justificación del Cronograma:</b> Foco rojo formativo. El sistema levanta un <b>Plan de Rescate de 6 Sesiones</b> iniciando completamente desde el escritorio."
            dist_sesiones = [(3.5, 0.5, 0.0), (3.0, 1.0, 0.0), (2.0, 1.5, 0.5), (1.0, 2.0, 1.0), (0.5, 1.0, 2.5), (0.0, 1.0, 3.0)]
            pasos_cortos = ["Principios Eléctricos", "Fundamentos PLC", "Observación Directa", "Práctica Controlada", "Práctica Media", "Examen Final"]
        elif calif_absoluta <= 45:
            modelo_txt = "<b>Justificación del Cronograma:</b> Deficiencia grave detectada. Se estructura un <b>Plan Correctivo de 5 Sesiones</b> para renivelación teórica y práctica guiada."
            dist_sesiones = [(3.0, 1.0, 0.0), (2.0, 1.5, 0.5), (1.0, 2.0, 1.0), (0.5, 1.5, 2.0), (0.0, 1.0, 3.0)]
            pasos_cortos = ["Bases Teóricas", "Análisis de Fallas", "Práctica Ligera", "Práctica Continua", "Evaluación Final"]
        else:
            modelo_txt = "<b>Justificación del Cronograma:</b> Incompetencia superable. Se dictamina un <b>Plan de Apoyo de 4 Sesiones</b> para solventar las dudas que están bloqueando la ejecución."
            dist_sesiones = [(2.0, 1.5, 0.5), (1.0, 2.0, 1.0), (0.5, 1.5, 2.0), (0.0, 1.0, 3.0)]
            pasos_cortos = ["Nivelación Aula", "Observación Táctica", "Ejecución Guiada", "Liberación a Piso"]
            
        pasos = [
            "Pausar inmediatamente la autorización del asociado para manipular celdas vivas para evitar riesgos de averías.",
            "Regresar a las bases de aula: instrucción intensiva sobre el funcionamiento de multímetros y tipos de sensores físicos."
        ]

    return txt_dona, txt_barras, txt_curva, txt_radar, bloom_txt, modelo_txt, pasos, pasos_cortos, dist_sesiones

# ==========================================
#        VISTA 1: PORTAL ESTRATÉGICO
# ==========================================
if st.session_state.vista == 'landing':
    scroll_to_top() 
    
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if os.path.exists("logo_aam.png"):
            st.image("logo_aam.png", use_container_width=True) 
    st.markdown("<h1 style='text-align: center;'>Estrategia de Certificación Técnica AAM</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; font-weight: normal; color: gray;'>Marco Pedagógico para la Evaluación y Desarrollo de Competencias Industriales</h4>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🎯 Fundamentación Operativa: El Reto del Piso de Producción")
    st.write("La capacitación industrial tradicional presenta un sesgo conocido como *'Ilusión de Competencia'* (Kruger & Dunning, 1999). Los asociados suelen retener conceptos en un aula, pero al enfrentarse a la presión de la línea de producción y a fallas dinámicas de hardware, la tasa de resolución cae drásticamente. **AAM SkillMatrix Pro** fue diseñado en el Centro de Innovación para eliminar este sesgo midiendo la transferencia real del conocimiento.")
    st.markdown("<br>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1.2, 1])
    with col_t1:
        st.markdown("### 📊 1. El Marco 70:20:10 (Lombardo & Eichinger)")
        st.write("Desarrollado por el Center for Creative Leadership, estipula que el aprendizaje de alto impacto en adultos no ocurre leyendo manuales, sino en la ejecución iterativa:")
        st.markdown("""
        *   <span class='aam-red'>TEORÍA (Cognitivo):</span> Representa la carga formal e instruccional (10%).
        *   <span class='aam-red'>SOCIAL (Colaborativo):</span> Representa la capacidad de documentar y colaborar técnicamente (20%).
        *   <span class='aam-red'>PRÁCTICA (Experiencial):</span> Representa el núcleo de destreza operativa en máquina (70%).
        """, unsafe_allow_html=True)
    with col_t2:
        df_70 = pd.DataFrame({'Dimensión': ['Experiencia en Piso', 'Aprendizaje Social', 'Teoría Formal'], 'Impacto (%)': [70, 20, 10]})
        fig_70 = px.pie(df_70, values='Impacto (%)', names='Dimensión', hole=0.5, color='Dimensión', color_discrete_map={'Experiencia en Piso':'#E31837', 'Aprendizaje Social':'#4682B4', 'Teoría Formal':'#002855'})
        fig_70.update_layout(title_text='Modelo de Retención Organizacional', title_x=0.5, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig_70, use_container_width=True)

    st.markdown("---")
    
    col_b1, col_b2 = st.columns([1, 1.2])
    with col_b1:
        df_bloom = pd.DataFrame({'Fase de Evaluación': ['Diagnóstica (S1)', 'Formativa (S3)', 'Sumativa (Final)'], 'Peso en Calificación': [10, 30, 60], 'Nivel Cognitivo': ['LOTS (Recordar)', 'MOTS (Aplicar)', 'HOTS (Crear/Resolver)']})
        fig_bloom = px.bar(df_bloom, x='Peso en Calificación', y='Fase de Evaluación', orientation='h', color='Fase de Evaluación', text='Nivel Cognitivo', color_discrete_sequence=['#A0AAB5', '#4682B4', '#E31837'])
        fig_bloom.update_layout(title_text='Evaluación Continua (Modelo Kirkpatrick)', title_x=0.5, showlegend=False)
        st.plotly_chart(fig_bloom, use_container_width=True)
    with col_b2:
        st.markdown("### 🧠 2. Taxonomía de Bloom & Metodología TWI")
        st.write("AAM SkillMatrix no solo mide el *qué*, sino el *cómo*. El motor genera un cronograma dinámico basado en el estándar automotriz **Training Within Industry (TWI)**, dividiendo las sesiones de 4 horas en:")
        st.markdown("""
        1.  **Preparar (Teoría):** El instructor valida la comprensión teórica de manuales y diagramas.
        2.  **Presentar (Social):** El instructor realiza el trabajo mientras el asociado analiza (Observación Activa).
        3.  **Intentar (Práctica):** El asociado interviene operativamente la máquina bajo estrés controlado.
        """)
        st.info("La combinación de la **Rúbrica Matricial** y las evaluaciones continuas permite a nuestros algoritmos predecir y formular **Cronogramas de Rescate** personalizados.")

    st.markdown("---")
    
    st.markdown("### 🔬 Matriz Diagnóstica: Perfiles de Ejecución Esperados")
    st.write("El Motor de Evaluación procesa las métricas para encasillar al asociado en perfiles técnicos basados en el modelo de las **Etapas de la Competencia (Broadwell, 1969)**:")
    
    c_perf1, c_perf2 = st.columns(2)
    with c_perf1:
        st.markdown("""
        <div class="perfil-caja" style="border-left-color: #28A745;">
            <h4 style="color: #28A745; margin-top: 0;">1. Competencia Inconsciente (Perfil Óptimo)</h4>
            <p><b>Síntoma:</b> Altos puntajes teóricos y prácticos consistentes.</p>
            <p><b>Diagnóstico:</b> El asociado opera por naturaleza. Deduce lógicas de programación sin necesidad de consultar el manual en cada paso.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="perfil-caja" style="border-left-color: #FFC107;">
            <h4 style="color: #FFC107; margin-top: 0;">3. Ejecución Empírica (Riesgo Mecánico)</h4>
            <p><b>Síntoma:</b> Baja Teoría, Alta Práctica en celda.</p>
            <p><b>Diagnóstico:</b> Sabe <i>qué</i> botón presionar por pura memoria repetitiva, pero ignora el <i>por qué</i>. Existe un alto riesgo ante fallas atípicas.</p>
        </div>
        """, unsafe_allow_html=True)

    with c_perf2:
        st.markdown("""
        <div class="perfil-caja" style="border-left-color: #4682B4;">
            <h4 style="color: #4682B4; margin-top: 0;">2. Ilusión de Competencia (Sesgo de Aula)</h4>
            <p><b>Síntoma:</b> Alta retención Teórica, Baja destreza Práctica.</p>
            <p><b>Diagnóstico:</b> Fenómeno clásico del alumno destacado que se congela frente a la presión de la maquinaria real y viva.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="perfil-caja" style="border-left-color: #E31837;">
            <h4 style="color: #E31837; margin-top: 0;">4. Incompetencia Consciente (Crítico)</h4>
            <p><b>Síntoma:</b> Caída transversal en evaluaciones y rúbricas en piso.</p>
            <p><b>Diagnóstico:</b> Sobrecarga cognitiva severa. Obligar al asociado a intervenir el equipo generará estrés innecesario y probables averías.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="btn-comenzar">', unsafe_allow_html=True)
    st.button("⚙️ Inicializar Motor de Certificación AAM", on_click=activar_motor, type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
#        VISTA 1.5: TRANSICIÓN ANIMADA
# ==========================================
elif st.session_state.vista == 'transition':
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    with st.spinner("Conectando con bases de datos AAM University..."):
        time.sleep(0.3)
    with st.spinner("Calibrando rúbricas de desempeño operativo..."):
        time.sleep(0.3)
    st.session_state.vista = 'app'
    st.rerun()

# ==========================================
#        VISTA 2: APLICACIÓN (MOTOR)
# ==========================================
elif st.session_state.vista == 'app':
    scroll_to_top() 
    
    st.button("⬅️ Volver al Marco Estratégico", on_click=volver)
    
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if os.path.exists("logo_aam.png"):
            st.image("logo_aam.png", use_container_width=True) 
    st.markdown("<h2 style='text-align: center; margin-top: -10px;'>Motor de Evaluación Técnica</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("📋 Información de la Evaluación")
    col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns([2, 2, 1.5, 2.5, 2.0])
    nombre = col_d1.text_input("Asociado:")
    evaluador = col_d2.text_input("Instructor:")
    fecha = col_d3.date_input("Fecha:")
    modulo = col_d4.selectbox("Certificación AAM a evaluar:", list(CURSOS.keys()))
    num_ses = col_d5.number_input("Sesiones Impartidas (Histórico):", min_value=1, max_value=10, value=5, help="Dato estadístico. El Motor propondrá un nuevo plan a futuro.")

    st.markdown("---")

    st.subheader("1. Progreso Académico (Exámenes)")
    c_ex1, c_ex2, c_ex3 = st.columns(3)
    with c_ex1:
        diag_score = st.number_input("Diagnóstica (Sesión 1 - Base)", min_value=0, max_value=100, value=45)
    with c_ex2:
        form_score = st.number_input("Formativa (Intermedia - Guiada)", min_value=0, max_value=100, value=80)
    with c_ex3:
        sum_score = st.number_input("Sumativa (Final - Autónoma)", min_value=0, max_value=100, value=90)

    st.markdown("---")

    st.subheader("2. Rúbrica de Desempeño Operativo")
    st.info("""
    **📘 Guía de Calificación (Escala AAM)**
    * **1 - Conoce:** Sabe la teoría básica, pero es incapaz de intervenir físicamente.
    * **2 - Con Ayuda:** Logra ejecutar rutinas operativas pero requiere constante supervisión.
    * **3 - Domina:** Ejecuta reparaciones y ajustes de manera autónoma, rápida y segura.
    """)

    calificaciones = {"TEORIA (Cognitivo)": [], "SOCIAL (Colaborativo)": [], "PRACTICA (Experiencial)": []}

    for bloque, criterios in CURSOS[modulo].items():
        st.markdown(f"#### {bloque}")
        st.markdown("<hr style='margin: 5px 0; border: 1px solid #CCC;'>", unsafe_allow_html=True)
        
        for crit in criterios:
            c1, c2 = st.columns([2, 3]) 
            c1.markdown(f"<div style='padding-top: 10px; font-weight: 600; font-size: 15px;'>{crit}</div>", unsafe_allow_html=True)
            val = c2.radio(f"Eval: {crit}", ["1 - Conoce", "2 - Con Ayuda", "3 - Domina"], horizontal=True, label_visibility="collapsed")
            calificaciones[bloque].append(int(val[0])) 

    st.markdown("---")

    if st.session_state.descargado:
        st.success(f"✅ **¡Reporte Generado Exitosamente!** El análisis avanzado de competencias de {nombre} ya se encuentra en tus descargas.")
        st.toast('Reporte Ejecutivo procesado', icon='⚙️')

    if st.button("📄 Procesar y Generar Plan de Acción Dinámico (PDF)", type="primary", use_container_width=True):
        if not nombre:
            st.error("Por favor, ingresa el nombre del asociado.")
        else:
            with st.spinner("Analizando variables y estructurando cronograma preventivo TWI..."):
                
                pct_t = calcular_pct_normalizado(calificaciones["TEORIA (Cognitivo)"])
                pct_s = calcular_pct_normalizado(calificaciones["SOCIAL (Colaborativo)"])
                pct_p = calcular_pct_normalizado(calificaciones["PRACTICA (Experiencial)"])
                
                txt_dona, txt_barras, txt_curva, txt_radar, bloom_txt, modelo_txt, pasos, pasos_cortos, dist_sesiones = generar_textos_dinamicos(pct_t, pct_s, pct_p, diag_score, form_score, sum_score, nombre, modulo)
                num_ses_propuestas = len(dist_sesiones)
                
                calif_final_matriz = (pct_t * 0.10) + (pct_s * 0.20) + (pct_p * 0.70)
                calif_examenes = (diag_score * 0.10) + (form_score * 0.30) + (sum_score * 0.60)
                calif_absoluta = (calif_final_matriz + calif_examenes) / 2

                # === GRÁFICAS ===
                fig1, ax1 = plt.subplots(figsize=(4, 4))
                color_f = '#28A745' if calif_absoluta >= 80 else ('#FFC107' if calif_absoluta >= 70 else '#E31837')
                ax1.pie([calif_absoluta, 100-calif_absoluta], colors=[color_f, '#EEEEEE'], startangle=90, wedgeprops=dict(width=0.3))
                ax1.text(0, 0, f'{calif_absoluta:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold', color='#002855')
                ax1.set_title("Score de Competencia Global", fontweight='bold', color='#002855', fontsize=11)
                img_dona = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_dona.name, dpi=300, bbox_inches='tight')
                plt.close(fig1)

                fig2, ax2 = plt.subplots(figsize=(5, 4))
                barras = ax2.bar(['Teoría\n(10%)', 'Social\n(20%)', 'Práctica\n(70%)'], [pct_t, pct_s, pct_p], color=['#002855', '#4682B4', '#E31837'])
                ax2.set_ylim(0, 110)
                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                ax2.set_title("Dimensiones de Dominio Técnico", fontweight='bold', color='#002855', fontsize=11)
                for b in barras:
                    ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 2, f"{b.get_height():.1f}%", ha='center', fontweight='bold', fontsize=10)
                img_barras = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_barras.name, dpi=300, bbox_inches='tight')
                plt.close(fig2)

                fig3, ax3 = plt.subplots(figsize=(5, 4))
                fases = ['S1(Diag)', 'S3(Form)', 'Final']
                ax3.plot(fases, [45, 75, 95], marker='o', linestyle='--', color='gray', label='Meta', linewidth=2)
                ax3.plot(fases, [diag_score, form_score, sum_score], marker='s', linestyle='-', color='#E31837', label='Real', linewidth=3, markersize=6)
                ax3.set_ylim(0, 110)
                ax3.grid(True, linestyle=':', alpha=0.6)
                ax3.legend(loc='lower right', fontsize=8)
                ax3.set_title("Trayectoria de Curva de Aprendizaje", fontweight='bold', color='#002855', fontsize=11)
                for i, val in enumerate([diag_score, form_score, sum_score]):
                    ax3.annotate(f"{val}", (fases[i], val+4), ha='center', fontweight='bold', color='#E31837', fontsize=9)
                img_tendencia = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_tendencia.name, dpi=300, bbox_inches='tight')
                plt.close(fig3)

                fig4, ax4 = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
                cat = [f'Teoría\n({pct_t:.1f}%)', f'Social\n({pct_s:.1f}%)', f'Práctica\n({pct_p:.1f}%)']
                val_r = [pct_t, pct_s, pct_p]
                ang = np.linspace(0, 2*np.pi, len(cat), endpoint=False)
                val_r = np.concatenate((val_r,[val_r[0]]))
                ang = np.concatenate((ang,[ang[0]]))
                ax4.fill(ang, val_r, color='#002855', alpha=0.2)
                ax4.plot(ang, val_r, color='#002855', linewidth=2)
                ax4.set_ylim(0, 100) 
                ax4.set_xticks(ang[:-1])
                ax4.set_xticklabels(cat, fontweight='bold', color='#002855', fontsize=9)
                ax4.set_yticklabels([])
                ax4.set_title("Análisis de Brecha de Ejecución", fontweight='bold', color='#002855', fontsize=11, pad=15)
                img_radar = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_radar.name, dpi=300, bbox_inches='tight')
                plt.close(fig4)

                # === GANTT TWI ===
                height_in = max(3.0, num_ses_propuestas * 0.45) 
                fig_g, ax_g = plt.subplots(figsize=(7, height_in))
                y_pos = np.arange(num_ses_propuestas)[::-1] 
                
                t_hrs = [d[0] for d in dist_sesiones]
                s_hrs = [d[1] for d in dist_sesiones]
                p_hrs = [d[2] for d in dist_sesiones]
                
                ax_g.barh(y_pos, t_hrs, color='#002855', label='Teoría (Preparar)', height=0.55, edgecolor='white')
                ax_g.barh(y_pos, s_hrs, left=t_hrs, color='#4682B4', label='Colaborativo (Presentar)', height=0.55, edgecolor='white')
                ax_g.barh(y_pos, p_hrs, left=np.array(t_hrs)+np.array(s_hrs), color='#E31837', label='Práctica (Intentar)', height=0.55, edgecolor='white')
                
                for i in range(num_ses_propuestas):
                    if t_hrs[i] > 0: ax_g.text(t_hrs[i]/2, y_pos[i], f"{t_hrs[i]}h", va='center', ha='center', color='white', fontweight='bold', fontsize=9)
                    if s_hrs[i] > 0: ax_g.text(t_hrs[i] + s_hrs[i]/2, y_pos[i], f"{s_hrs[i]}h", va='center', ha='center', color='white', fontweight='bold', fontsize=9)
                    if p_hrs[i] > 0: ax_g.text(t_hrs[i] + s_hrs[i] + p_hrs[i]/2, y_pos[i], f"{p_hrs[i]}h", va='center', ha='center', color='white', fontweight='bold', fontsize=9)
                    ax_g.text(4.1, y_pos[i], f"➤ {pasos_cortos[i]}", va='center', ha='left', color='#333333', fontsize=9, fontstyle='italic')

                ax_g.set_yticks(y_pos)
                ax_g.set_yticklabels([f'Sesión {i+1}' for i in range(num_ses_propuestas)], fontweight='bold', color='#002855')
                ax_g.set_xticks([0, 1, 2, 3, 4])
                ax_g.set_xticklabels(['0h', '1h', '2h', '3h', '4h (Fin)'], color='#666666')
                ax_g.spines['top'].set_visible(False)
                ax_g.spines['right'].set_visible(False)
                ax_g.spines['left'].set_color('#CCCCCC')
                ax_g.spines['bottom'].set_color('#CCCCCC')
                ax_g.set_title(f"Plan de Acción Propuesto: {num_ses_propuestas} Sesiones", fontweight='bold', color='#002855', fontsize=12, loc='left')
                ax_g.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, fontsize=10)
                plt.tight_layout()
                img_gantt = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_gantt.name, dpi=300, bbox_inches='tight')
                plt.close(fig_g)

                # === PDF REPORTLAB ===
                pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                doc = SimpleDocTemplate(pdf_temp.name, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
                estilos = getSampleStyleSheet()
                
                estilo_tit = ParagraphStyle('Titulo', parent=estilos['Heading1'], textColor=colors.HexColor("#002855"), alignment=TA_LEFT, fontSize=18)
                estilo_sub = ParagraphStyle('Sub', parent=estilos['Heading2'], textColor=colors.HexColor("#E31837"), fontSize=13)
                estilo_mini_tit = ParagraphStyle('MiniTit', parent=estilos['Heading3'], textColor=colors.HexColor("#002855"), fontSize=11, fontName="Helvetica-Bold")
                estilo_txt = ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=9.5, leading=13, alignment=TA_JUSTIFY)
                estilo_pie = ParagraphStyle('Pie', parent=estilos['Normal'], fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))
                estilo_blanco = ParagraphStyle('Blanco', parent=estilos['Normal'], textColor=colors.whitesmoke, fontName="Helvetica-Bold", alignment=TA_CENTER)
                estilo_bullet = ParagraphStyle('Bullet', parent=estilos['Normal'], fontSize=9.5, leading=13, leftIndent=15)
                
                # Estilo especial para el glosario TWI
                estilo_glosario = ParagraphStyle('Glosario', parent=estilos['Normal'], fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), fontName="Helvetica-Oblique")
                
                elementos = []

                header_data = []
                title_para = Paragraph("<b>REPORTE OFICIAL DE CERTIFICACIÓN TÉCNICA</b>", estilo_tit)
                if os.path.exists("logo_aam.png"):
                    logo_img = RLImage("logo_aam.png", width=70, height=70)
                    header_data = [[logo_img, title_para]]
                else:
                    header_data = [["", title_para]]
                t_header = Table(header_data, colWidths=[80, 400])
                t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                elementos.append(t_header)
                elementos.append(Spacer(1, 10))
                
                datos_cabecera = [
                    [Paragraph(f"<b>Asociado Evaluado:</b> {nombre}"), Paragraph(f"<b>Fecha Cierre:</b> {fecha}")],
                    [Paragraph(f"<b>Módulo AAM:</b> {modulo}"), Paragraph(f"<b>Instructor Titular:</b> {evaluador}")]
                ]
                t = Table(datos_cabecera, colWidths=[260, 260])
                t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")), ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#A0AAB5")), ('PADDING', (0,0), (-1,-1), 6)]))
                elementos.append(t)
                elementos.append(Spacer(1, 12))

                elementos.append(Paragraph("<b>Registro de Evaluaciones Continuas</b>", estilo_sub))
                datos_examenes = [
                    [Paragraph("Fase", estilo_blanco), Paragraph("Propósito Metodológico", estilo_blanco), Paragraph("Peso", estilo_blanco), Paragraph("Score", estilo_blanco)],
                    ["Diagnóstica", "Línea base cognitiva de pre-requisitos (Bloom: Recordar).", "10%", f"{diag_score}/100"],
                    ["Formativa", "Validación asimilativa durante observación guiada.", "30%", f"{form_score}/100"],
                    ["Sumativa", "Dictamen de resolución técnica en equipo vivo.", "60%", f"{sum_score}/100"]
                ]
                t_exam = Table(datos_examenes, colWidths=[70, 310, 50, 90])
                t_exam.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#002855")), 
                    ('ALIGN', (2,1), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CCCCCC")),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
                ]))
                elementos.append(t_exam)
                elementos.append(Spacer(1, 12))

                img1 = RLImage(img_dona.name, width=150, height=150)
                img2 = RLImage(img_barras.name, width=200, height=160)
                img3 = RLImage(img_tendencia.name, width=200, height=160)
                img4 = RLImage(img_radar.name, width=150, height=150)

                dash_data = [
                    [img1, img2],
                    [Paragraph(txt_dona, estilo_pie), Paragraph(txt_barras, estilo_pie)],
                    [Spacer(1, 10), Spacer(1, 10)], 
                    [img3, img4],
                    [Paragraph(txt_curva, estilo_pie), Paragraph(txt_radar, estilo_pie)]
                ]
                t_dash = Table(dash_data, colWidths=[260, 260])
                t_dash.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
                elementos.append(t_dash)
                elementos.append(Spacer(1, 15))

                elementos.append(Paragraph("<b>DICTAMEN TÉCNICO Y PLAN DE RESCATE (Siguientes Pasos)</b>", estilo_sub))
                elementos.append(Paragraph(bloom_txt, estilo_txt))
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(modelo_txt, estilo_txt))
                elementos.append(Spacer(1, 10))
                
                elementos.append(Paragraph("<b>Recomendaciones de Acción Preventiva:</b>", estilo_mini_tit))
                lista_pasos = []
                for p in pasos:
                    lista_pasos.append(ListItem(Paragraph(p, estilo_bullet)))
                elementos.append(ListFlowable(lista_pasos, bulletType='bullet', leftIndent=10))
                elementos.append(Spacer(1, 10))
                
                img_height_rl = 450 * (height_in / 7.0)
                elementos.append(RLImage(img_gantt.name, width=450, height=img_height_rl))
                
                # GLOSARIO TWI AL FINAL DEL GANTT
                texto_glosario = "*Glosario de Fases TWI: <b>Preparar:</b> Revisión teórica y comprensión de diagramas. <b>Presentar:</b> Observación activa y mentoría por parte del instructor. <b>Intentar:</b> Ejecución autónoma en piso por parte del asociado."
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(texto_glosario, estilo_glosario))

                doc.build(elementos)

            with open(pdf_temp.name, "rb") as pdf_file:
                st.download_button(
                    label="📥 DESCARGAR PLAN DE ACCIÓN GERENCIAL (PDF)",
                    data=pdf_file,
                    file_name=f"Reporte_AAM_{nombre.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    on_click=confirmar_descarga
                )