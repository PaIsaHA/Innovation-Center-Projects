import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import re
import traceback
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, ListFlowable, ListItem, PageBreak, KeepTogether
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
if 'mostrar_rubricas' not in st.session_state:
    st.session_state.mostrar_rubricas = False

def confirmar_descarga():
    st.session_state.descargado = True

def activar_motor():
    st.session_state.vista = 'transition'
    st.session_state.descargado = False

def volver():
    st.session_state.vista = 'landing'
    st.session_state.descargado = False
    st.session_state.mostrar_rubricas = False

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
    .btn-comenzar > button { background-color: #002855 !important; color: #FFFFFF !important; font-size: 20px !important; padding: 15px !important; font-weight: bold; border-radius: 8px;}
    .btn-comenzar > button:hover { background-color: #001533 !important; color: #FFFFFF !important; border: 1px solid #FFFFFF;}
    .aam-gold { color: #D49A00; font-weight: bold; }
    
    .grid-contenedor { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;}
    
    @media (max-width: 800px) {
        .grid-contenedor { grid-template-columns: 1fr; }
    }
    
    .perfil-caja { background-color: #FFFFFF !important; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 6px solid #002855; display: flex; flex-direction: column; height: 100%;}
    .perfil-caja p, .perfil-caja b, .perfil-caja i { color: #333333 !important; }
    .perfil-caja h4 { margin-top: 0; margin-bottom: 15px; }
    
    .stFileUploader > div > div { background-color: #F8F9FA !important; border: 2px dashed #002855 !important; border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

# --- 3. BASE DE DATOS DE CURSOS AAM ---
CURSOS = {
    "PLC AB + Cognex": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y principios básicos de redes Ethernet/IP.",
            "Identifica diagramas eléctricos y el proceso correcto de asignación de direcciones IP para módulos de visión.",
            "Explica teóricamente el procedimiento de instalación de archivos EDS en el software.",
            "Comprende la estructura de 'Controller tags' y componentes lógicos para la comunicación PLC-Cámara.",
            "Conoce la configuración de hardware requerida en el software In-Sight de Cognex."
        ],
        "SOCIAL (Colaborativo)": [
            "Documenta correctamente en la orden de trabajo los cambios de IP, cableado o reemplazos de hardware.",
            "Comunica efectivamente los hallazgos al rastrear fallas de red entre RS Linx y la cámara Cognex."
        ],
        "PRACTICA (Experiencial)": [
            "Configura el módulo Ethernet genérico usando RS Linx y asigna IPs en la red física.",
            "Instala archivos EDS exitosamente y crea un nuevo módulo en Studio 5000.",
            "Configura las variables (tags) y la lógica de escalera necesaria para enviar/recibir datos de visión.",
            "Navega en el software In-Sight y crea/modifica una tarea de detección (Job).",
            "Ejecuta prácticas de programación en celda viva, resolviendo fallas de comunicación.",
            "Diagnostica fallas del PLC por falta de señal usando referencias cruzadas en Studio 5000."
        ]
    },
    "PLC AB + Keyence": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y principios básicos de redes Ethernet/IP.",
            "Identifica diagramas eléctricos y el proceso correcto de asignación de direcciones IP para módulos de visión.",
            "Explica teóricamente el procedimiento de instalación de archivos EDS en el software.",
            "Comprende la structure de 'Controller tags' y componentes lógicos para la comunicación PLC-Cámara.",
            "Conoce la configuration de hardware requerida en el software IV Navigator de Keyence."
        ],
        "SOCIAL (Colaborativo)": [
            "Documenta correctamente en la orden de trabajo los cambios de IP, cableado o reemplazos de hardware.",
            "Comunica efectivamente los hallazgos al rastrear fallas de red entre RS Linx y la cámara Keyence."
        ],
        "PRACTICA (Experiencial)": [
            "Configura el módulo Ethernet genérico usando RS Linx y asigna IPs en la red física.",
            "Instala archivos EDS exitosamente y crea un nuevo módulo en Studio 5000.",
            "Configura las variables (tags) y la lógica de escalera necesaria para enviar/recibir datos de visión.",
            "Navega en el software IV Navigator y crea/modifica una tarea de detección (Job).",
            "Ejecuta prácticas de programación en celda viva, resolviendo fallas de comunicación.",
            "Diagnostica fallas del PLC por falta de señal usando referencias cruzadas en Studio 5000."
        ]
    },
    "PLC S7 + Cognex": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y principios de arquitectura Profinet IO.",
            "Identifica diagramas eléctricos y el proceso de asignación de direcciones IP y Nombres de Dispositivo.",
            "Explica teóricamente el procedimiento de instalación de archivos GSD en el entorno TIA Portal.",
            "Comprende la estructura de hojas de cálculo y transmisión de datos I/O para comunicación PLC-Cámara.",
            "Conoce la configuración de hardware requerida en el software In-Sight de Cognex."
        ],
        "SOCIAL (Colaborativo)": [
            "Documenta correctamente en la orden de trabajo los cambios de IP, nombres de nodo o reemplazos de hardware.",
            "Comunica efectivamente los hallazgos al rastrear fallas de red Profinet entre TIA Portal y la cámara Cognex."
        ],
        "PRACTICA (Experiencial)": [
            "Crea un proyecto nuevo en TIA Portal, configura el hardware y asigna dispositivos de campo Profinet IO.",
            "Instala archivos GSD exitosamente y agrega el lector/sensor Cognex a la arquitectura de red.",
            "Asigna direcciones IP y nombres de dispositivo correctamente, realizando la descarga al PLC.",
            "Navega en el software In-Sight, configura la hoja de cálculo y establece la transmisión de datos I/O.",
            "Ejecuta prácticas de programación en celda viva, resolviendo fallas de comunicación.",
            "Diagnostica fallas del PLC por pérdida de conexión usando herramientas de diagnóstico en TIA Portal."
        ]
    },
    "PLC S7 + Keyence": {
        "TEORIA (Cognitivo)": [
            "Menciona equipo de protección (EPP), sistema CAE y principios de arquitectura Profinet IO.",
            "Identifica diagramas eléctricos y el proceso de asignación de direcciones IP y Nombres de Dispositivo.",
            "Explica teóricamente el procedimiento de instalación de archivos GSD en el entorno TIA Portal.",
            "Comprende la estructura de transmisión de datos I/O para la comunicación PLC-Cámara.",
            "Conoce la configuración del protocolo Profinet y la tarjeta de red en IV Navigator de Keyence."
        ],
        "SOCIAL (Colaborativo)": [
            "Documenta correctamente en la orden de trabajo los cambios de IP, nombres de nodo o reemplazos de hardware.",
            "Comunica efectivamente los hallazgos al rastrear fallas de red Profinet entre TIA Portal y la cámara Keyence."
        ],
        "PRACTICA (Experiencial)": [
            "Configura la tarjeta de red, el protocolo Profinet y asigna la IP al sensor usando IV Navigator.",
            "Crea un proyecto nuevo en TIA Portal, configura el hardware e instala los archivos GSD correspondientes.",
            "Asigna dispositivos de campo Profinet IO (sensores Keyence), direcciones IP y nombres de dispositivo.",
            "Establece la transmisión de datos I/O y ejecuta la descarga de configuración al PLC.",
            "Ejecuta prácticas de programación en celda viva, resolviendo fallas de comunicación.",
            "Diagnostica fallas del PLC por pérdida de conexión usando herramientas de diagnóstico en TIA Portal."
        ]
    }
}

def calcular_pct_normalizado(valores):
    if not valores: return 0
    puntuaciones = [(v - 1) * 50 for v in valores]
    return sum(puntuaciones) / len(puntuaciones)

# --- 4. MOTOR LECTOR DE EXCEL INTELIGENTE (NLP A PRUEBA DE BALAS) ---
@st.cache_data
def procesar_excel_aam(file):
    try:
        df = pd.read_excel(file, sheet_name=0)
        # PARCHE CRÍTICO: Forzamos a todo el DataFrame a ser interpretado como string (texto) 
        # antes de llenar los vacíos con "". Esto evita el TypeError en Linux por las columnas float64.
        df = df.astype(str)
        df.fillna("", inplace=True)
        
        nombre_curso = "Certificación Dinámica AAM"
        for r in range(len(df)):
            for c in range(len(df.columns)):
                if "NOMBRE DEL CURSO" in str(df.iloc[r, c]).upper():
                    try:
                        nombre_raw = str(df.iloc[r+1, c]).strip()
                        if not nombre_raw or nombre_raw.lower() == 'nan':
                            nombre_raw = str(df.iloc[r, c+1]).strip()
                        if nombre_raw and nombre_raw.lower() != 'nan':
                            nombre_curso = nombre_raw
                    except: pass
                    break

        competencias = []
        for r in range(len(df)):
            for c in range(len(df.columns)):
                val = str(df.iloc[r, c]).strip().upper()
                if "COMPETENCIAS A DESARROLLAR" in val:
                    for nc in range(c+1, len(df.columns)):
                        comp_str = str(df.iloc[r, nc]).strip()
                        if comp_str and comp_str.lower() != 'nan':
                            if '\n' in comp_str:
                                competencias = [x.strip() for x in comp_str.split('\n') if len(x.strip()) > 3]
                            else:
                                competencias = [x.strip() for x in re.split(r'[,;]', comp_str) if len(x.strip()) > 3]
                            break

        temas_raw = []
        subtemas_raw = []
        found_tema = False
        
        skip_words = ["APERTURA", "CIERRE", "INTRODUCCI", "BIENVENIDA", "ENCUADRE", "REGISTRO", "SONDEO", "EXPECTATIVAS", "EVALUACI", "CLAUSURA", "DINÁMICA"]
        
        for r in range(len(df)):
            if found_tema: break
            for c in range(len(df.columns)):
                if str(df.iloc[r, c]).strip().upper() == "TEMA":
                    for row_i in range(r+1, len(df)):
                        t_val = str(df.iloc[row_i, c]).strip()
                        
                        if "ELABOR" in t_val.upper() or "BIBLIOGRAF" in t_val.upper() or "AUTOR" in t_val.upper() or "INSTRUCTOR" in t_val.upper():
                            found_tema = True
                            break
                            
                        if t_val and t_val.lower() != "nan":
                            upper_t = t_val.upper()
                            if not any(sw in upper_t for sw in skip_words):
                                t_clean = re.sub(r'^(Tema\s*\d+[\.\-]?\s*|Unidad\s*\d+[\.\-]?\s*|\d+[\.\-]?\s*)', '', t_val, flags=re.IGNORECASE).strip()
                                temas_raw.append(t_clean)
                                
                                if c+1 < len(df.columns):
                                    st_val = str(df.iloc[row_i, c+1]).strip()
                                    if st_val and st_val.lower() != "nan":
                                        sub_list = [x.strip() for x in st_val.split('\n') if len(x.strip()) > 3]
                                        for sub_tema in sub_list:
                                            if not any(sw in sub_tema.upper() for sw in skip_words):
                                                st_clean = re.sub(r'^(\d+[\.\-]?\s*)', '', sub_tema).strip()
                                                subtemas_raw.append(st_clean)
                    found_tema = True
                    break
        
        if not temas_raw:
            temas_raw = ["Fundamentos Técnicos", "Configuración de Hardware y Software", "Troubleshooting Operativo"]

        teoria = []
        practica = []
        social = []
        
        verbos_teoria = ['conoce', 'comprende', 'identifica', 'analiza', 'entiende', 'evalúa', 'describe', 'interpreta', 'lee']
        verbos_practica = ['configura', 'programa', 'realiza', 'ejecuta', 'interviene', 'implementa', 'conecta', 'arma', 'diagnostica', 'puesta', 'soluciona', 'calibra']

        def limpiar_pedagogia(txt):
            for word in ["Introducción a la ", "Introducción a los ", "Introducción al ", "Introducción a ", "Conceptos de ", "Principios de ", "Tema ", "Unidad "]:
                txt = re.sub(f"(?i)^{word}", "", txt)
            return txt.strip()
            
        def procesar_verbo(txt, categoria):
            txt = limpiar_pedagogia(txt)
            txt = re.sub(r'^(\d+[\.\-]?\s*)', '', txt).strip()
            if not txt or len(txt) < 4: return None
            
            words = txt.split()
            first_word = words[0]
            
            if txt.isupper():
                txt_adj = txt.lower()
                txt_cap = txt.capitalize()
            else:
                if first_word.isupper() and len(first_word) > 1:
                    txt_adj = txt
                    txt_cap = txt
                else:
                    txt_adj = txt[0].lower() + txt[1:]
                    txt_cap = txt[0].upper() + txt[1:]
            
            idx = len(txt)
            first_word_lower = first_word.lower()
            
            if categoria == 'TEORIA':
                if first_word_lower in verbos_teoria:
                    sufijos = [" aplicando un enfoque de análisis sistémico.", " con alto rigor técnico.", " para prevenir fallos operativos en la línea."]
                    return f"{txt_cap}{sufijos[idx % len(sufijos)]}"
                else:
                    plantillas = [
                        f"Demuestra dominio teórico y analítico avanzado sobre {txt_adj}.",
                        f"Fundamenta los principios de ingeniería necesarios para {txt_adj}.",
                        f"Comprende a detalle la lógica técnica implicada en {txt_adj}."
                    ]
                    return plantillas[idx % len(plantillas)]
                    
            elif categoria == 'PRACTICA':
                if first_word_lower in verbos_practica:
                    sufijos = [" de forma 100% autónoma en equipo energizado.", " aplicando estándares de la industria automotriz.", " asegurando los tiempos de ciclo en línea."]
                    return f"{txt_cap}{sufijos[idx % len(sufijos)]}"
                else:
                    plantillas = [
                        f"Realiza maniobras y procedimientos de {txt_adj} bajo estrés operativo.",
                        f"Lleva a cabo la configuración y validación para {txt_adj} en piso.",
                        f"Aplica técnicas de troubleshooting avanzado asociadas a {txt_adj}."
                    ]
                    return plantillas[idx % len(plantillas)]
                    
            elif categoria == 'SOCIAL':
                plantillas = [
                    f"Asegura la trazabilidad en bitácora tras realizar intervenciones relativas a {txt_adj}.",
                    f"Comunica parámetros modificados y hallazgos al equipo de turno respecto a {txt_adj}.",
                    f"Documenta técnicamente las incidencias operativas derivadas de {txt_adj}."
                ]
                return plantillas[idx % len(plantillas)]

        for c in competencias:
            if any(verb in c.lower() for verb in verbos_teoria):
                val = procesar_verbo(c, 'TEORIA')
                if val: teoria.append(val)
            else:
                val = procesar_verbo(c, 'PRACTICA')
                if val: practica.append(val)
                
        for st_raw in subtemas_raw:
            if len(teoria) < 5:
                val = procesar_verbo(st_raw, 'TEORIA')
                if val and val not in teoria: teoria.append(val)
            elif len(practica) < 5:
                val = procesar_verbo(st_raw, 'PRACTICA')
                if val and val not in practica: practica.append(val)

        mezcla = temas_raw + competencias
        for m in mezcla:
            if len(social) < 3:
                val = procesar_verbo(m, 'SOCIAL')
                if val and val not in social: social.append(val)
                
        if len(teoria) == 0: teoria.append("Interpreta esquemáticos del fabricante y manuales corporativos (AAM) con precisión.")
        if len(practica) == 0: practica.append("Ejecuta tareas operativas de diagnóstico en piso bajo demanda de producción.")
        if len(social) == 0: social.append("Mantiene un registro de control de cambios riguroso en los sistemas de la planta.")

        def dedup(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]

        return {
            "nombre": nombre_curso,
            "rubrica": {
                "TEORIA (Cognitivo)": dedup(teoria)[:6],
                "SOCIAL (Colaborativo)": dedup(social)[:3],
                "PRACTICA (Experiencial)": dedup(practica)[:6]
            }
        }
    except Exception as e:
        # Reporta el rastro técnico en la terminal oculta por si acaso
        print(f"Error detectado en motor: {e}")
        print(traceback.format_exc())
        return None

# --- 5. LÓGICA DE SYLLABUS Y TEXTOS DINÁMICOS CON IA ---
def generar_temario(calificaciones, curso_dict, dist_sesiones):
    temas_teoria = []
    temas_practica = []
    
    def extraer_nucleo(txt):
        txt = re.sub(r'[^\w\s\.\:\,\(\)\-áéíóúÁÉÍÓÚñÑüÜ]', '', txt).strip()
        sufijos = [r" aplicando un enfoque de análisis sistémico.*", r" con alto rigor técnico.*", r" para prevenir fallos operativos en la línea.*", r" de forma 100% autónoma en equipo energizado.*", r" aplicando estándares de la industria automotriz.*", r" asegurando los tiempos de ciclo en línea.*", r" bajo estrés operativo.*", r" en piso.*"]
        for s in sufijos: txt = re.sub(s, "", txt, flags=re.IGNORECASE)
        prefijos = [r"^Demuestra dominio teórico y analítico avanzado sobre ", r"^Fundamenta los principios de ingeniería necesarios para ", r"^Comprende a detalle la lógica técnica implicada en ", r"^Realiza maniobras y procedimientos de ", r"^Lleva a cabo la configuración y validación para ", r"^Aplica técnicas de troubleshooting avanzado asociadas a "]
        for p in prefijos: txt = re.sub(p, "", txt, flags=re.IGNORECASE)
        
        if txt: return txt[0].upper() + txt[1:]
        return txt

    for i, score in enumerate(calificaciones["TEORIA (Cognitivo)"]):
        if score <= 2.2: temas_teoria.append(extraer_nucleo(curso_dict["TEORIA (Cognitivo)"][i]))
    for i, score in enumerate(calificaciones["PRACTICA (Experiencial)"]):
        if score <= 2.2: temas_practica.append(extraer_nucleo(curso_dict["PRACTICA (Experiencial)"][i]))
        
    if not temas_teoria: temas_teoria.append("Optimización de tiempos de escaneo y revisión de protocolos")
    if not temas_practica: temas_practica.append("Recuperación de desastres y simulación de fallas críticas")
    
    twi_preparar = [
        "Análisis en escritorio, validación de diagramas e identificación de componentes críticos.",
        "Estudio de manuales del fabricante y mapeo de secuencias lógicas de operación.",
        "Auditoría de parámetros, revisión de históricos de falla y planeación de la intervención."
    ]
    twi_mixto = [
        "Observación activa (Shadowing) seguida de intervención en hardware bajo supervisión estricta.",
        "Demostración técnica del instructor, transicionando a práctica guiada paso a paso (Try-Out).",
        "Simulación controlada de fallas: el asociado identifica y el instructor asiste en la corrección."
    ]
    twi_intentar = [
        "Ejecución 100% autónoma en celda viva, auditando tiempos de respuesta y precisión diagnóstica.",
        "Troubleshooting bajo estrés operativo: aislamiento y corrección de anomalías sin asistencia.",
        "Liberación técnica: Validation de destreza mecánica y toma de decisiones en tiempo real."
    ]
    
    head_teoria = ["Refuerzo cognitivo orientado a: ", "Clínica analítica enfocada en: ", "Revisión arquitectónica de: "]
    head_practica = ["Clínica operativa y calibración de: ", "Intervención táctil y troubleshooting de: ", "Maniobras de alta precisión en: "]

    temario_estructurado = []
    for s, horas in enumerate(dist_sesiones):
        t_hrs, s_hrs, p_hrs = horas
        core_t = temas_teoria[s % len(temas_teoria)].rstrip('.')
        core_p = temas_practica[s % len(temas_practica)].rstrip('.')
        
        h_t = head_teoria[s % len(head_teoria)] + core_t
        h_p = head_practica[s % len(head_practica)] + core_p
        
        bloque = {"sesion": "", "teoria": None, "practica": None, "actividad": ""}
        
        if p_hrs == 0:
            bloque["sesion"] = f"<b>Sesión {s+1} [Teoría {t_hrs}h]</b>"
            bloque["teoria"] = f"<b>Foco Teórico:</b> {h_t}."
            act = twi_preparar[s % len(twi_preparar)]
            bloque["actividad"] = f"<font color='#555555'><i>Actividad TWI (Preparar): {act}</i></font>"
        elif t_hrs == 0:
            bloque["sesion"] = f"<b>Sesión {s+1} [Práctica {p_hrs}h]</b>"
            bloque["practica"] = f"<b>Foco Práctico:</b> {h_p}."
            act = twi_intentar[s % len(twi_intentar)]
            bloque["actividad"] = f"<font color='#D49A00'><i>Actividad TWI (Intentar): {act}</i></font>"
        else:
            bloque["sesion"] = f"<b>Sesión {s+1} [Teoría {t_hrs}h | Práctica {p_hrs}h]</b>"
            bloque["teoria"] = f"<b>Foco Teórico:</b> {h_t}."
            bloque["practica"] = f"<b>Foco Práctico:</b> {h_p}."
            act = twi_mixto[s % len(twi_mixto)]
            bloque["actividad"] = f"<font color='#4682B4'><i>Actividad TWI (Presentar/Intentar): {act}</i></font>"
            
        temario_estructurado.append(bloque)
            
    return temario_estructurado

def generar_textos_dinamicos(pt, ps, pp, d_score, f_score, s_score, nombre, titulo_curso, calificaciones_raw, curso_dict, es_grupo=False):
    calif_absoluta = ( (pt*0.1 + ps*0.2 + pp*0.7) + (d_score*0.1 + f_score*0.3 + s_score*0.6) ) / 2
    
    if calif_absoluta >= 80 and pp >= 80 and pt >= 80: perfil = 1 
    elif pt >= 75 and pp < 75: perfil = 2 
    elif pp >= 75 and pt < 75: perfil = 3 
    elif calif_absoluta >= 60 and pp >= 60: perfil = 5 
    else: perfil = 4 
        
    software_plc = "TIA Portal" if "S7" in titulo_curso or "SIEMENS" in titulo_curso.upper() else ("Studio 5000" if "AB" in titulo_curso or "ALLEN" in titulo_curso.upper() else "el equipo")
    software_cam = "Cognex" if "COGNEX" in titulo_curso.upper() else ("Keyence" if "KEYENCE" in titulo_curso.upper() else "el sistema")

    if calif_absoluta >= 90:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> {calif_absoluta:.1f}%. Este círculo lleno consolida el Nivel 3. La capacitación se ha traducido en una conducta operativa autónoma."
    elif calif_absoluta >= 70:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> {calif_absoluta:.1f}%. Retención favorable. La franja gris representa la brecha restante para lograr la independencia total en piso."
    elif calif_absoluta >= 50:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> {calif_absoluta:.1f}%. Asimilación parcial. Entiende conceptos (Nivel 2) pero la gráfica demuestra dudas al momento de ejecutarlos."
    else:
        txt_dona = f"<b>Nivel Kirkpatrick:</b> {calif_absoluta:.1f}%. Ausencia de retención. Liberar al asociado en estas condiciones representa un riesgo operativo para la maquinaria."

    if perfil == 1:
        txt_barras = f"<b>Metodología 70-20-10:</b> Balance visual excelente. El sólido {pt:.1f}% en Teoría soporta exitosamente el {pp:.1f}% de ejecución Práctica en piso."
    elif perfil == 2:
        txt_barras = f"<b>Metodología 70-20-10:</b> Fricción psicomotriz. Mantiene un alto {pt:.1f}% en Teoría, pero frente a la máquina real, la barra de ejecución se desploma a {pp:.1f}%."
    elif perfil == 3:
        txt_barras = f"<b>Metodología 70-20-10:</b> Inercia mecánica. Práctica alta ({pp:.1f}%), pero el {pt:.1f}% teórico indica que el asociado no domina la lógica de los procesos."
    else:
        txt_barras = f"<b>Metodología 70-20-10:</b> Barras deprimidas de forma transversal (Teoría: {pt:.1f}%, Práctica: {pp:.1f}%). Evidencia la necesidad de reiniciar el módulo instruccional."

    if s_score >= f_score and s_score >= 80:
        txt_curva = f"<b>Curva Cognitiva:</b> Trayectoria ascendente cerrando en {s_score:.0f} pts. Superó la fase diagnóstica y logró aplicar los conocimientos en la evaluación final."
    elif s_score < f_score and s_score < 75:
        txt_curva = f"<b>Curva Cognitiva:</b> Desplome en la fase final (cayendo a {s_score:.0f} pts). La gráfica señala ansiedad o bloqueo cuando se le retira la supervisión del instructor."
    elif d_score < 50 and f_score < 50 and s_score < 50:
        txt_curva = f"<b>Curva Cognitiva:</b> La trayectoria permanece plana y deficiente. Según Bloom, el alumno no logró cimentar la etapa básica de 'Memorizar' los conceptos."
    else:
        txt_curva = f"<b>Curva Cognitiva:</b> Avance inconsistente cerrando en {s_score:.0f} pts. Existen huecos técnicos que impidieron una progresión fluida hacia la meta operativa."

    if pt < 20 and pp < 20 and ps < 20: txt_radar = f"<b>Huella de Brecha:</b> Polígono colapsado. Carencia estructural formativa transversal."
    elif abs(pt - pp) <= 10 and pt >= 80: txt_radar = f"<b>Huella de Brecha:</b> Equilibrio de alto rendimiento. Perfil simétrico ideal y competente."
    elif abs(pt - pp) <= 10 and pt < 80: txt_radar = f"<b>Huella de Brecha:</b> Simétrico, pero requiere desarrollo equitativo en todas las áreas evaluadas."
    elif pt > pp: txt_radar = f"<b>Huella de Brecha:</b> Asimetría operativa. Fuerte sesgo hacia la abstracción lógica, baja destreza manual en equipo."
    else: txt_radar = f"<b>Huella de Brecha:</b> Asimetría cognitiva. Fuerte sesgo mecánico, vulnerable en deducción de lógicas."

    if perfil == 1:
        bloom_txt = f"<b>Evaluación:</b> Capaz de deducir lógicas y diagnosticar fallas en <b>{software_plc}</b> y <b>{software_cam}</b> sin rutinas pre-memorizadas."
        modelo_txt = "<b>Justificación del Cronograma:</b> El asociado presenta un equilibrio ideal 70-20-10. Se recetan 2 sesiones de mantenimiento enfocadas 100% en piso para consolidar autonomía."
        dist_sesiones = [(0.0, 1.0, 3.0), (0.0, 0.0, 4.0)] 
        pasos_cortos = ["Mentoría Guiada", "Autonomía Total"]
        pasos = ["Validar su independencia asignándole órdenes preventivas de alta complejidad.", "Asignarle el rol de asociado guía ('Presentar') para apoyar a compañeros con menor desempeño."]
        dictamen_final = "<font color='#28A745'><b>DICTAMEN: APROBADO.</b> El asociado cumple y excede los estándares operativos de AAM.</font>"
    elif perfil == 2:
        bloom_txt = f"<b>Evaluación:</b> Domina la lectura de manuales. Área de oportunidad en la transición táctil hacia la conexión física."
        modelo_txt = "<b>Justificación del Cronograma:</b> Para corregir el sesgo y acercarlo al balance 70-20-10, el plan invierte la carga forzando 4 sesiones con mayoría de práctica en celda (Try-Out)."
        dist_sesiones = [(1.0, 2.0, 1.0), (0.5, 1.5, 2.0), (0.0, 1.0, 3.0), (0.0, 0.0, 4.0)]
        pasos_cortos = ["Observación", "Práctica Asistida", "Práctica Media", "Ejecución Libre"]
        pasos = [f"Frenar el uso de manuales. Priorizar rutinas repetitivas de conexión y configuración en {software_plc}.", "Implementar sesiones de observación activa donde el instructor solo intervenga en caso de riesgo."]
        dictamen_final = "<font color='#D49A00'><b>DICTAMEN: CONDICIONADO.</b> Certificación sujeta al cumplimiento estricto del Plan de Acción y Syllabus operativo.</font>"
    elif perfil == 3:
        bloom_txt = f"<b>Evaluación:</b> Ejecución operativa frágil. Carece de la base analítica para rastrear fallas atípicas."
        modelo_txt = "<b>Justificación del Cronograma:</b> Para restituir el balance 70-20-10, este plan correctivo frena temporalmente la práctica y compensa inyectando las horas de teoría faltantes."
        dist_sesiones = [(3.0, 1.0, 0.0), (2.0, 1.0, 1.0), (0.5, 1.0, 2.5)]
        pasos_cortos = ["Revisión Teórica", "Balance en Piso", "Validación Técnica"]
        pasos = ["Impedir intervenciones correctivas sin supervisión hasta que valide la lectura fluida del proceso.", f"Obligar al asociado a explicar verbalmente el flujo lógico en {software_plc} antes de intervenir el equipo."]
        dictamen_final = "<font color='#D49A00'><b>DICTAMEN: CONDICIONADO.</b> Certificación sujeta a la asimilación teórica dictada en el Syllabus y Plan de Acción.</font>"
    elif perfil == 5:
        bloom_txt = f"<b>Evaluación:</b> Desempeño medio. Resuelve problemas básicos pero requiere refuerzo para solidificar tiempos de respuesta."
        modelo_txt = "<b>Justificación del Cronograma:</b> Perfil en maduración. Se sugieren 3 sesiones de refuerzo balanceadas para acercar el perfil a la proporción operativa óptima (70-20-10)."
        dist_sesiones = [(1.0, 1.0, 2.0), (0.5, 1.0, 2.5), (0.0, 1.0, 3.0)]
        pasos_cortos = ["Repaso General", "Práctica Continua", "Liberación"]
        pasos = ["Continuar asignándole mantenimientos preventivos regulares para que gane velocidad.", "Agendar una breve validación diagnóstica en un mes para asegurar retención."]
        dictamen_final = "<font color='#4682B4'><b>DICTAMEN: EN TRANSICIÓN.</b> Se requiere validar tiempos de respuesta tras concluir las sesiones de refuerzo.</font>"
    else: 
        bloom_txt = f"<b>Evaluación:</b> Riesgo Crítico. Incapaz de comprender flujos o diagnosticar fallas básicas en <b>{software_plc}</b>."
        if calif_absoluta <= 20: 
            modelo_txt = "<b>Justificación del Cronograma:</b> Brecha profunda. Se formula un plan de rescate de 6 Sesiones iniciando desde el escritorio para reconstruir las bases del modelo formativo."
            dist_sesiones = [(3.5, 0.5, 0.0), (3.0, 1.0, 0.0), (2.0, 1.5, 0.5), (1.0, 2.0, 1.0), (0.5, 1.0, 2.5), (0.0, 1.0, 3.0)]
            pasos_cortos = ["Fundamentos", "Lectura de Bases", "Observación", "Práctica Controlada", "Práctica Media", "Examen Final"]
        elif calif_absoluta <= 45:
            modelo_txt = "<b>Justificación del Cronograma:</b> Deficiencia grave. Se estructura un Plan de 5 Sesiones enfocando la primera mitad en nivelación teórica, para luego saltar a la práctica."
            dist_sesiones = [(3.0, 1.0, 0.0), (2.0, 1.5, 0.5), (1.0, 2.0, 1.0), (0.5, 1.5, 2.0), (0.0, 1.0, 3.0)]
            pasos_cortos = ["Bases Teóricas", "Análisis Fallas", "Práctica Ligera", "Práctica Continua", "Evaluación Final"]
        else:
            modelo_txt = "<b>Justificación del Cronograma:</b> Incompetencia superable. Se dictamina un Plan de 4 Sesiones dosificando las horas de forma guiada para recuperar la confianza del asociado."
            dist_sesiones = [(2.0, 1.5, 0.5), (1.0, 2.0, 1.0), (0.5, 1.5, 2.0), (0.0, 1.0, 3.0)]
            pasos_cortos = ["Nivelación Aula", "Observación", "Ejecución Guiada", "Liberación Piso"]
        pasos = ["Pausar autorización para manipular celdas vivas temporalmente.", "Regresar a las bases de aula: instrucción intensiva sobre el funcionamiento básico."]
        dictamen_final = "<font color='#343A40'><b>DICTAMEN: SUSPENDIDO.</b> Riesgo operativo crítico. Requiere re-certificación obligatoria y nula intervención autónoma en piso.</font>"

    if es_grupo:
        txt_dona = txt_dona.replace("El asociado", "El grupo").replace("Entiende", "Entienden")
        txt_barras = txt_barras.replace("el asociado", "el grupo").replace("Mantiene", "Mantienen")
        txt_curva = txt_curva.replace("el alumno", "el grupo").replace("Superó", "Superaron").replace("logró", "lograron")
        txt_radar = txt_radar.replace("equipo", "grupo").replace("vulnerable", "vulnerables")
        bloom_txt = bloom_txt.replace("Capaz", "Grupo capaz").replace("Domina", "Dominan").replace("Carece", "Carecen").replace("Resuelve", "Resuelven").replace("Incapaz", "Incapaces")
        modelo_txt = modelo_txt.replace("El asociado", "El grupo")
        pasos = [p.replace("su independencia", "su independencia colectiva").replace("al asociado", "al grupo") for p in pasos]
        dictamen_final = dictamen_final.replace("El asociado", "El grupo").replace("APROBADO", "GRUPO APROBADO").replace("CONDICIONADO", "GRUPO CONDICIONADO").replace("SUSPENDIDO", "GRUPO SUSPENDIDO").replace("EN TRANSICIÓN", "GRUPO EN TRANSICIÓN").replace("cumple y excede", "cumplen y exceden")

    temario_estructurado = generar_temario(calificaciones_raw, curso_dict, dist_sesiones)

    return txt_dona, txt_barras, txt_curva, txt_radar, bloom_txt, modelo_txt, pasos, temario_estructurado, pasos_cortos, dist_sesiones, dictamen_final

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
    st.write("La capacitación industrial tradicional presenta un sesgo conocido como *'Ilusión de Competencia'* (Kruger & Dunning, 1999). Los asociados suelen retener conceptos en un aula, pero al enfrentarse a la presión de la línea de producción y a fallas dinámicas de hardware, la tasa de resolución cae drásticamente. **AAM SkillMatrix Pro** fue diseñado en el Centro de Innovación para eliminar este sesgo mantiendo la transferencia real del conocimiento.")
    st.markdown("<br>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1.2, 1])
    with col_t1:
        st.markdown("### 📊 1. El Marco 70:20:10")
        st.write("Medición de transferencia real del conocimiento (Lombardo & Eichinger):")
        st.markdown("""
        *   <span class='aam-gold'>TEORÍA (Cognitivo):</span> Carga formal e instruccional (10%).
        *   <span class='aam-gold'>SOCIAL (Colaborativo):</span> Capacidad de documentar y colaborar (20%).
        *   <span class='aam-gold'>PRÁCTICA (Experiencial):</span> Destreza operativa en máquina viva (70%).
        """, unsafe_allow_html=True)
    with col_t2:
        df_70 = pd.DataFrame({'Dimensión': ['Experiencia en Piso', 'Aprendizaje Social', 'Teoría Formal'], 'Impacto (%)': [70, 20, 10]})
        fig_70 = px.pie(df_70, values='Impacto (%)', names='Dimensión', hole=0.5, color='Dimensión', color_discrete_map={'Experiencia en Piso':'#FFB81C', 'Aprendizaje Social':'#8CB4E2', 'Teoría Formal':'#002855'})
        fig_70.update_layout(title_text='Modelo de Retención Ideal', title_x=0.5, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_70, use_container_width=True)

    st.markdown("---")
    
    col_b1, col_b2 = st.columns([1, 1.2])
    with col_b1:
        df_bloom = pd.DataFrame({'Fase de Evaluación': ['Diagnóstica (S1)', 'Formativa (S3)', 'Sumativa (Final)'], 'Peso en Calificación': [10, 30, 60], 'Nivel Cognitivo': ['LOTS (Recordar)', 'MOTS (Aplicar)', 'HOTS (Crear/Resolver)']})
        fig_bloom = px.bar(df_bloom, x='Peso en Calificación', y='Fase de Evaluación', orientation='h', color='Fase de Evaluación', text='Nivel Cognitivo', color_discrete_sequence=['#A0AAB5', '#8CB4E2', '#FFB81C'])
        fig_bloom.update_layout(title_text='Evaluación Continua', title_x=0.5, showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_bloom, use_container_width=True)
    with col_b2:
        st.markdown("### 🧠 2. Taxonomía de Bloom & Metodología TWI")
        st.write("Generación de Syllabus Dinámico basado en **Training Within Industry (TWI)**:")
        st.markdown("""
        1.  **Preparar (Teoría):** El instructor valida manuales y diagramas eléctricos/redes.
        2.  **Presentar (Social):** Observación Activa (Shadowing) y documentación.
        3.  **Intentar (Práctica):** Intervención operativa en maquinaria bajo estrés.
        """)
        st.info("La plataforma procesa micro-evaluaciones para formular un **Syllabus (Plan de Estudios Automático)** compensatorio para restituir el balance 70-20-10.")

    st.markdown("---")
    
    st.markdown("### 🔬 Matriz Diagnóstica: Perfiles de Ejecución Esperados")
    st.write("El Motor de Evaluación procesa las métricas para encasillar al asociado en perfiles técnicos basados en el modelo de las **Etapas de la Competencia (Broadwell, 1969)**:")
    
    st.markdown("""
    <div class="grid-contenedor">
        <div class="perfil-caja" style="border-left-color: #28A745;">
            <h4 style="color: #28A745;">1. Competencia Inconsciente (Perfil Óptimo)</h4>
            <p><b>Síntoma:</b> Altos puntajes teóricos y prácticos consistentes.</p>
            <p><b>Diagnóstico:</b> El asociado opera por naturaleza. Deduce lógicas de programación sin necesidad de consultar el manual en cada paso.</p>
        </div>
        <div class="perfil-caja" style="border-left-color: #4682B4;">
            <h4 style="color: #4682B4;">2. Ilusión de Competencia (Sesgo de Aula)</h4>
            <p><b>Síntoma:</b> Alta retención Teórica, Baja destreza Práctica.</p>
            <p><b>Diagnóstico:</b> Fenómeno clásico del alumno destacado que se congela frente a la presión de la maquinaria real y viva.</p>
        </div>
        <div class="perfil-caja" style="border-left-color: #FFC107;">
            <h4 style="color: #FFC107;">3. Ejecución Empírica (Riesgo Mecánico)</h4>
            <p><b>Síntoma:</b> Baja Teoría, Alta Práctica en celda.</p>
            <p><b>Diagnóstico:</b> Sabe <i>qué</i> botón presionar por pura memoria repetitiva, pero ignora el <i>por qué</i>. Existe un alto riesgo ante fallas atípicas.</p>
        </div>
        <div class="perfil-caja" style="border-left-color: #343A40;">
            <h4 style="color: #343A40;">4. Incompetencia Consciente (Crítico)</h4>
            <p><b>Síntoma:</b> Caída transversal en evaluaciones y rúbricas en piso.</p>
            <p><b>Diagnóstico:</b> Sobrecarga cognitiva severa. Obligar al asociado a intervenir el equipo generará estrés innecesario y probables averías.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="btn-comenzar">', unsafe_allow_html=True)
    st.button("⚙️ Inicializar Motor de Certificación AAM", on_click=activar_motor, type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
#        VISTA 1.5: TRANSICIÓN ANIMADA
# ==========================================
elif st.session_state.vista == 'transition':
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    with st.spinner("Sincronizando con temarios oficiales AAM University..."):
        time.sleep(0.4)
    with st.spinner("Calibrando algoritmos de predicción ROI..."):
        time.sleep(0.4)
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
    st.markdown("<h2 style='text-align: center; margin-top: -10px;'>Motor de Micro-Evaluación Técnica (Grupal)</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("⚙️ Configuración del Módulo a Evaluar")
    modo_carga = st.radio("Modo de Selección de Temario:", ["Usar Catálogo Precargado (Fase 1)", "Cargar Temario desde Excel (Fase 2 - Automático)"], horizontal=True)
    
    curso_actual = None
    titulo_modulo_pdf = ""

    if modo_carga == "Usar Catálogo Precargado (Fase 1)":
        modulo_sel = st.selectbox("Certificación AAM a evaluar:", list(CURSOS.keys()))
        curso_actual = CURSOS[modulo_sel]
        titulo_modulo_pdf = modulo_sel
    else:
        col_up1, col_up2 = st.columns([1, 1.2])
        
        with col_up2:
            st.markdown("**📊 Formato Requerido (Plantilla FDTA004):**")
            if os.path.exists("template_fdta004.png"):
                st.image("template_fdta004.png", use_container_width=True)
            elif os.path.exists("template_fdta004.jpg"):
                st.image("template_fdta004.jpg", use_container_width=True)
            else:
                st.warning("⚠️ Falta la imagen guía. Guarda un pantallazo de tu Excel como 'template_fdta004.png' en esta misma carpeta para que aparezca aquí.")
                
        with col_up1:
            st.info("Arrastra la plantilla estándar de contenido temático (FDTA004) de AAM University.")
            
            archivo_excel = st.file_uploader(
                "Subir Archivo Excel", 
                type=["xlsx"], 
                label_visibility="collapsed",
                accept_multiple_files=False, 
                help="Sube un archivo a la vez. Si subes otro, reemplazará al anterior."
            )
            
            if archivo_excel:
                datos_dinamicos = procesar_excel_aam(archivo_excel)
                if datos_dinamicos:
                    st.success(f"✅ ¡Temario escaneado exitosamente: **{datos_dinamicos['nombre']}**!")
                    curso_actual = datos_dinamicos["rubrica"]
                    titulo_modulo_pdf = datos_dinamicos["nombre"]
                else:
                    st.error("No se pudo procesar el formato. Asegúrate de usar la plantilla oficial con 'NOMBRE DEL CURSO' y columna 'TEMA'. Revisa la terminal de Codespaces para el error exacto.")
                    st.stop()
            else:
                st.stop()

    st.markdown("---")
    
    col_e1, col_e2 = st.columns([2, 1])
    evaluador = col_e1.text_input("Instructor Responsable:")
    fecha = col_e2.date_input("Fecha de Cierre:")

    st.markdown("---")

    # --- 1. PROGRESO ACADÉMICO ---
    st.subheader("1. Progreso Académico de los Integrantes")
    st.info("💡 Ingresa los nombres y calificaciones de las 3 fases. La calificación final se promediará automáticamente.")

    cantidad_integrantes = st.number_input("Cantidad de integrantes a evaluar", min_value=1, max_value=50, value=3)

    if "df_base" not in st.session_state or len(st.session_state.df_base) != cantidad_integrantes:
        st.session_state.df_base = pd.DataFrame({
            "Nombre del Integrante": [f"Asociado {i+1}" for i in range(cantidad_integrantes)],
            "Diagnóstica (S1)": [45.0] * cantidad_integrantes,
            "Formativa (S3)": [80.0] * cantidad_integrantes,
            "Sumativa (Final)": [90.0] * cantidad_integrantes
        })

    config_columnas = {
        "Nombre del Integrante": st.column_config.TextColumn("Nombre del Integrante", required=True),
        "Diagnóstica (S1)": st.column_config.NumberColumn("Diagnóstica (S1)", min_value=0.0, max_value=100.0, step=1.0),
        "Formativa (S3)": st.column_config.NumberColumn("Formativa (S3)", min_value=0.0, max_value=100.0, step=1.0),
        "Sumativa (Final)": st.column_config.NumberColumn("Sumativa (Final)", min_value=0.0, max_value=100.0, step=1.0)
    }

    df_editado = st.data_editor(st.session_state.df_base, column_config=config_columnas, num_rows="fixed", use_container_width=True, hide_index=True)
    
    df_valido = df_editado.copy()
    df_valido["Calificación Final"] = df_valido[["Diagnóstica (S1)", "Formativa (S3)", "Sumativa (Final)"]].mean(axis=1)

    st.markdown("---")

    # --- 2. RÚBRICAS INDIVIDUALES ---
    st.subheader("2. Rúbricas de Desempeño Operativo")
    
    if st.button("📝 Generar Rúbricas para Evaluar", type="primary"):
        st.session_state.mostrar_rubricas = True

    calificaciones_individuales = {}

    if st.session_state.mostrar_rubricas:
        st.info("""
        **📘 Guía de Calificación (Escala de Campo AAM)**
        * **1 - Conoce:** Entiende el concepto, pero es incapaz de configurar el software/hardware físicamente.
        * **2 - Con Ayuda:** Logra realizar las conexiones/programación pero requiere asistencia técnica constante.
        * **3 - Domina:** Ejecuta el Troubleshooting y la configuración de red de forma 100% autónoma.
        """)

        for idx, row in df_valido.iterrows():
            nombre = row["Nombre del Integrante"]
            if str(nombre).strip() == "":
                nombre = f"Integrante {idx + 1}"
                
            calificaciones_individuales[nombre] = {"TEORIA (Cognitivo)": [], "SOCIAL (Colaborativo)": [], "PRACTICA (Experiencial)": []}
            
            with st.expander(f"👨‍🔧 Evaluación de: {nombre}", expanded=False):
                for bloque, criterios in curso_actual.items():
                    st.markdown(f"#### {bloque}")
                    st.markdown("<hr style='margin: 5px 0; border: 1px solid #CCC;'>", unsafe_allow_html=True)
                    for j, crit in enumerate(criterios):
                        c1, c2 = st.columns([2, 3]) 
                        c1.markdown(f"<div style='padding-top: 10px; font-weight: 600; font-size: 15px;'>{crit}</div>", unsafe_allow_html=True)
                        val = c2.radio(f"Eval: {nombre}_{bloque}_{j}", ["1 - Conoce", "2 - Con Ayuda", "3 - Domina"], horizontal=True, label_visibility="collapsed")
                        calificaciones_individuales[nombre][bloque].append(int(val[0])) 

        st.markdown("---")

        if st.session_state.descargado:
            st.success(f"✅ **¡Sistema Predictivo Ejecutado!** El Plan de Acción y Proyección de Retorno (ROI) grupal están listos en tu PDF.")
            st.toast('Syllabus generado exitosamente', icon='📈')

        if st.button("📄 Generar Manual Grupal y Syllabus Dinámico (PDF)", type="primary", use_container_width=True):
            
            with st.spinner("Analizando escuadrón, generando dashboards y calculando proyección..."):
                
                nombres_lista = []
                finales_lista = []
                pt_grupo, ps_grupo, pp_grupo = [], [], []
                
                imagenes_individuales = [] 

                # 1. Procesamiento de Gráficas Individuales (El Dashboard 2x2)
                for idx, row in df_valido.iterrows():
                    n = row["Nombre del Integrante"]
                    if str(n).strip() == "": n = f"Integrante {idx + 1}"
                    nombres_lista.append(n)
                    finales_lista.append(row["Calificación Final"])
                    
                    s1, s3, final = row["Diagnóstica (S1)"], row["Formativa (S3)"], row["Sumativa (Final)"]
                    
                    c_rub = calificaciones_individuales[n]
                    pt_i = calcular_pct_normalizado(c_rub["TEORIA (Cognitivo)"])
                    ps_i = calcular_pct_normalizado(c_rub["SOCIAL (Colaborativo)"])
                    pp_i = calcular_pct_normalizado(c_rub["PRACTICA (Experiencial)"])
                    
                    pt_grupo.append(pt_i); ps_grupo.append(ps_i); pp_grupo.append(pp_i)

                    # Textos dinámicos individuales para los pies de gráfica
                    txt_dona_i, txt_bar_i, txt_curv_i, txt_rad_i, _, _, _, _, _, _, dictamen_i = generar_textos_dinamicos(pt_i, ps_i, pp_i, s1, s3, final, n, titulo_modulo_pdf, c_rub, curso_actual, es_grupo=False)
                    calif_abs_i = ((pt_i*0.1 + ps_i*0.2 + pp_i*0.7) + (s1*0.1 + s3*0.3 + final*0.6)) / 2

                    # Fig 1: Dona
                    fig1, ax1 = plt.subplots(figsize=(4, 4))
                    color_f = '#28A745' if calif_abs_i >= 80 else ('#FFC107' if calif_abs_i >= 70 else '#FFB81C')
                    ax1.pie([calif_abs_i, 100-calif_abs_i], colors=[color_f, '#EEEEEE'], startangle=90, wedgeprops=dict(width=0.3))
                    ax1.text(0, 0, f'{calif_abs_i:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold', color='#002855')
                    ax1.set_title("Score de Competencia Global", fontweight='bold', color='#002855', fontsize=11)
                    img_dona = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    plt.savefig(img_dona.name, dpi=300, bbox_inches='tight'); plt.close(fig1)

                    # Fig 2: Barras 70-20-10
                    fig2, ax2 = plt.subplots(figsize=(5, 4))
                    barras = ax2.bar(['Teoría\n(10%)', 'Social\n(20%)', 'Práctica\n(70%)'], [pt_i, ps_i, pp_i], color=['#002855', '#8CB4E2', '#FFB81C'])
                    ax2.set_ylim(0, 110); ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
                    ax2.set_title("Dimensiones de Dominio Técnico", fontweight='bold', color='#002855', fontsize=11)
                    for b in barras: ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 2, f"{b.get_height():.1f}%", ha='center', fontweight='bold', fontsize=10)
                    img_barras = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    plt.savefig(img_barras.name, dpi=300, bbox_inches='tight'); plt.close(fig2)

                    # Fig 3: Tendencia
                    fig3, ax3 = plt.subplots(figsize=(5, 4))
                    fases = ['S1', 'S3', 'Final']
                    ax3.plot(fases, [45, 75, 95], marker='o', linestyle='--', color='gray', label='Meta', linewidth=2)
                    ax3.plot(fases, [s1, s3, final], marker='s', linestyle='-', color='#FFB81C', label='Real', linewidth=3, markersize=6)
                    ax3.set_ylim(0, 110); ax3.grid(True, linestyle=':', alpha=0.6); ax3.legend(loc='lower right', fontsize=8)
                    ax3.set_title("Trayectoria de Aprendizaje", fontweight='bold', color='#002855', fontsize=11)
                    for i, val in enumerate([s1, s3, final]): ax3.annotate(f"{val}", (fases[i], val+4), ha='center', fontweight='bold', color='#D49A00', fontsize=9)
                    img_tendencia = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    plt.savefig(img_tendencia.name, dpi=300, bbox_inches='tight'); plt.close(fig3)

                    # Fig 4: Radar
                    fig4, ax4 = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
                    cat = [f'Teoría\n({pt_i:.1f}%)', f'Social\n({ps_i:.1f}%)', f'Práctica\n({pp_i:.1f}%)']
                    val_r = [pt_i, ps_i, pp_i]
                    ang = np.linspace(0, 2*np.pi, len(cat), endpoint=False)
                    val_r = np.concatenate((val_r,[val_r[0]])); ang = np.concatenate((ang,[ang[0]]))
                    ax4.fill(ang, val_r, color='#002855', alpha=0.2); ax4.plot(ang, val_r, color='#002855', linewidth=2)
                    ax4.set_ylim(0, 100); ax4.set_xticks(ang[:-1]); ax4.set_xticklabels(cat, fontweight='bold', color='#002855', fontsize=9); ax4.set_yticklabels([])
                    ax4.set_title("Análisis de Brecha", fontweight='bold', color='#002855', fontsize=11, pad=15)
                    img_radar = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    plt.savefig(img_radar.name, dpi=300, bbox_inches='tight'); plt.close(fig4)

                    imagenes_individuales.append({
                        "nombre": n, "img1": img_dona.name, "img2": img_barras.name, "img3": img_tendencia.name, "img4": img_radar.name,
                        "txt1": txt_dona_i, "txt2": txt_bar_i, "txt3": txt_curv_i, "txt4": txt_rad_i, "dictamen": dictamen_i
                    })

                # 2. Promedios y Textos Grupales
                grp_pt = sum(pt_grupo) / len(pt_grupo)
                grp_ps = sum(ps_grupo) / len(ps_grupo)
                grp_pp = sum(pp_grupo) / len(pp_grupo)
                grp_d = df_valido["Diagnóstica (S1)"].mean()
                grp_f = df_valido["Formativa (S3)"].mean()
                grp_s = df_valido["Sumativa (Final)"].mean()
                calif_abs_g = ((grp_pt*0.1 + grp_ps*0.2 + grp_pp*0.7) + (grp_d*0.1 + grp_f*0.3 + grp_s*0.6)) / 2
                
                calif_promedio_matriz = {"TEORIA (Cognitivo)": [], "SOCIAL (Colaborativo)": [], "PRACTICA (Experiencial)": []}
                for bloque, criterios in curso_actual.items():
                    for i in range(len(criterios)):
                        scores = [calificaciones_individuales[n][bloque][i] for n in calificaciones_individuales]
                        calif_promedio_matriz[bloque].append(sum(scores) / len(scores))

                txt_dona_g, txt_bar_g, txt_curv_g, txt_rad_g, bloom_g, modelo_g, pasos_g, temario_g, pasos_c_g, dist_sesiones_g, dictamen_g = generar_textos_dinamicos(grp_pt, grp_ps, grp_pp, grp_d, grp_f, grp_s, "Grupo", titulo_modulo_pdf, calif_promedio_matriz, curso_actual, es_grupo=True)
                num_ses_propuestas = len(dist_sesiones_g)

                # Gráficas del Grupo para el Dashboard
                fig1_g, ax1_g = plt.subplots(figsize=(4, 4))
                color_f = '#28A745' if calif_abs_g >= 80 else ('#FFC107' if calif_abs_g >= 70 else '#FFB81C')
                ax1_g.pie([calif_abs_g, 100-calif_abs_g], colors=[color_f, '#EEEEEE'], startangle=90, wedgeprops=dict(width=0.3))
                ax1_g.text(0, 0, f'{calif_abs_g:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold', color='#002855')
                ax1_g.set_title("Score de Competencia Global", fontweight='bold', color='#002855', fontsize=11)
                img_dona_g = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_dona_g.name, dpi=300, bbox_inches='tight'); plt.close(fig1_g)

                fig2_g, ax2_g = plt.subplots(figsize=(5, 4))
                barras_g = ax2_g.bar(['Teoría\n(10%)', 'Social\n(20%)', 'Práctica\n(70%)'], [grp_pt, grp_ps, grp_pp], color=['#002855', '#8CB4E2', '#FFB81C'])
                ax2_g.set_ylim(0, 110); ax2_g.spines['top'].set_visible(False); ax2_g.spines['right'].set_visible(False)
                ax2_g.set_title("Dimensiones de Dominio Técnico", fontweight='bold', color='#002855', fontsize=11)
                for b in barras_g: ax2_g.text(b.get_x() + b.get_width()/2, b.get_height() + 2, f"{b.get_height():.1f}%", ha='center', fontweight='bold', fontsize=10)
                img_barras_g = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_barras_g.name, dpi=300, bbox_inches='tight'); plt.close(fig2_g)

                fig3_g, ax3_g = plt.subplots(figsize=(5, 4))
                fases = ['S1', 'S3', 'Final']
                ax3_g.plot(fases, [45, 75, 95], marker='o', linestyle='--', color='gray', label='Meta', linewidth=2)
                ax3_g.plot(fases, [grp_d, grp_f, grp_s], marker='s', linestyle='-', color='#FFB81C', label='Real', linewidth=3, markersize=6)
                ax3_g.set_ylim(0, 110); ax3_g.grid(True, linestyle=':', alpha=0.6); ax3_g.legend(loc='lower right', fontsize=8)
                ax3_g.set_title("Trayectoria de Aprendizaje", fontweight='bold', color='#002855', fontsize=11)
                for i, val in enumerate([grp_d, grp_f, grp_s]): ax3_g.annotate(f"{val:.0f}", (fases[i], val+4), ha='center', fontweight='bold', color='#D49A00', fontsize=9)
                img_tendencia_g = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_tendencia_g.name, dpi=300, bbox_inches='tight'); plt.close(fig3_g)

                fig4_g, ax4_g = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
                cat = [f'Teoría\n({grp_pt:.1f}%)', f'Social\n({grp_ps:.1f}%)', f'Práctica\n({grp_pp:.1f}%)']
                val_r = [grp_pt, grp_ps, grp_pp]
                ang = np.linspace(0, 2*np.pi, len(cat), endpoint=False)
                val_r = np.concatenate((val_r,[val_r[0]])); ang = np.concatenate((ang,[ang[0]]))
                ax4_g.fill(ang, val_r, color='#002855', alpha=0.2); ax4_g.plot(ang, val_r, color='#002855', linewidth=2)
                ax4_g.set_ylim(0, 100); ax4_g.set_xticks(ang[:-1]); ax4_g.set_xticklabels(cat, fontweight='bold', color='#002855', fontsize=9); ax4_g.set_yticklabels([])
                ax4_g.set_title("Análisis de Brecha", fontweight='bold', color='#002855', fontsize=11, pad=15)
                img_radar_g = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_radar_g.name, dpi=300, bbox_inches='tight'); plt.close(fig4_g)

                # 3. Gráfica Comparativa Global
                fig_comp, ax_comp = plt.subplots(figsize=(9, 4.5))
                colores = ['#28A745' if x >= 80 else ('#D49A00' if x >= 70 else '#DC3545') for x in finales_lista]
                barras_comp = ax_comp.bar(nombres_lista, finales_lista, color=colores, width=0.55, zorder=3)
                
                ax_comp.set_facecolor('#F8F9FA') 
                fig_comp.patch.set_facecolor('#FFFFFF')
                ax_comp.yaxis.grid(True, linestyle='--', alpha=0.7, color='#CCCCCC', zorder=0)
                
                ax_comp.axhline(y=80, color='#002855', linestyle='-', linewidth=1.5, alpha=0.5, zorder=1)
                ax_comp.text(-0.3, 82, 'Meta AAM (80%)', color='#002855', fontsize=9, fontweight='bold', va='bottom')
                
                ax_comp.set_ylim(0, 115) 
                ax_comp.set_yticks([0, 20, 40, 60, 80, 100])
                ax_comp.spines['top'].set_visible(False)
                ax_comp.spines['right'].set_visible(False)
                ax_comp.spines['left'].set_visible(False)
                ax_comp.spines['bottom'].set_color('#A0AAB5')
                ax_comp.tick_params(axis='both', length=0) 
                ax_comp.tick_params(axis='y', colors='#666666')
                
                for i, bar in enumerate(barras_comp):
                    yval = bar.get_height()
                    ax_comp.text(bar.get_x() + bar.get_width()/2, yval + 2.5, f"{yval:.1f}%",
                                 ha='center', va='bottom', fontweight='bold', fontsize=9,
                                 color=colores[i],
                                 bbox=dict(facecolor='white', edgecolor=colores[i], boxstyle='round,pad=0.3', alpha=0.9))
                
                ax_comp.set_title("Leaderboard: Nivel de Competencia Operativa por Asociado", fontweight='bold', color='#002855', fontsize=13, loc='left', pad=15)
                plt.xticks(rotation=15, ha='right', fontsize=9, fontweight='bold', color='#333333')
                plt.tight_layout()
                
                img_comparativa = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_comparativa.name, dpi=300, bbox_inches='tight', facecolor=fig_comp.get_facecolor())
                plt.close(fig_comp)

                # 4. Gantt Grupal
                height_in = max(2.5, num_ses_propuestas * 0.45) 
                fig_g, ax_g = plt.subplots(figsize=(7, height_in))
                y_pos = np.arange(num_ses_propuestas)[::-1] 
                
                t_hrs = [d[0] for d in dist_sesiones_g]
                s_hrs = [d[1] for d in dist_sesiones_g]
                p_hrs = [d[2] for d in dist_sesiones_g]
                
                ax_g.barh(y_pos, t_hrs, color='#002855', label='Teoría (Preparar)', height=0.55, edgecolor='white')
                ax_g.barh(y_pos, s_hrs, left=t_hrs, color='#8CB4E2', label='Colaborativo (Presentar)', height=0.55, edgecolor='white')
                ax_g.barh(y_pos, p_hrs, left=np.array(t_hrs)+np.array(s_hrs), color='#FFB81C', label='Práctica (Intentar)', height=0.55, edgecolor='white')
                
                for i in range(num_ses_propuestas):
                    if t_hrs[i] > 0: ax_g.text(t_hrs[i]/2, y_pos[i], f"{t_hrs[i]}h", va='center', ha='center', color='white', fontweight='bold', fontsize=9)
                    if s_hrs[i] > 0: ax_g.text(t_hrs[i] + s_hrs[i]/2, y_pos[i], f"{s_hrs[i]}h", va='center', ha='center', color='white', fontweight='bold', fontsize=9)
                    if p_hrs[i] > 0: ax_g.text(t_hrs[i] + s_hrs[i] + p_hrs[i]/2, y_pos[i], f"{p_hrs[i]}h", va='center', ha='center', color='#333333', fontweight='bold', fontsize=9)
                    ax_g.text(4.1, y_pos[i], f"➤ {pasos_c_g[i]}", va='center', ha='left', color='#333333', fontsize=9, fontstyle='italic')

                ax_g.set_yticks(y_pos)
                ax_g.set_yticklabels([f'Sesión {i+1}' for i in range(num_ses_propuestas)], fontweight='bold', color='#002855')
                ax_g.set_xticks([0, 1, 2, 3, 4])
                ax_g.set_xticklabels(['0h', '1h', '2h', '3h', '4h (Fin)'], color='#666666')
                ax_g.spines['top'].set_visible(False)
                ax_g.spines['right'].set_visible(False)
                ax_g.spines['left'].set_color('#CCCCCC')
                ax_g.spines['bottom'].set_color('#CCCCCC')
                ax_g.set_title(f"Plan de Acción Propuesto para el Grupo", fontweight='bold', color='#002855', fontsize=12, loc='left')
                ax_g.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, fontsize=10)
                plt.tight_layout()
                img_gantt = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_gantt.name, dpi=300, bbox_inches='tight')
                plt.close(fig_g)

                # 5. ROI Predictivo Grupal
                fig_perf, ax_perf = plt.subplots(figsize=(8, 3.5)) 
                x_perf = np.arange(3)
                labels_x = ['Teoría Cognitiva', 'Resolución Social', 'Destreza en Piso']
                actual_vals = [grp_pt, grp_ps, grp_pp]
                expected_vals = [max(grp_pt, 90), max(grp_ps, 95), max(grp_pp, 95)] 

                ax_perf.fill_between(x_perf, actual_vals, color='#A0AAB5', alpha=0.3)
                ax_perf.fill_between(x_perf, actual_vals, expected_vals, color='#28A745', alpha=0.3)
                
                ax_perf.plot(x_perf, actual_vals, marker='o', markersize=8, color='#A0AAB5', linewidth=3, label='Nivel Base Actual Grupo')
                ax_perf.plot(x_perf, expected_vals, marker='s', markersize=8, color='#28A745', linewidth=3, label='Performance Proyectado Post-Syllabus')

                ax_perf.set_title('Proyección de Retorno de Inversión Formativo (ROI Grupal)', fontweight='bold', color='#002855', fontsize=14, pad=20)
                ax_perf.set_xticks(x_perf)
                ax_perf.set_xticklabels(labels_x, fontweight='bold', color='#002855', fontsize=11)
                ax_perf.set_ylim(0, 110)
                ax_perf.grid(True, linestyle=':', alpha=0.6)
                ax_perf.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False, fontsize=10)
                ax_perf.spines['top'].set_visible(False)
                ax_perf.spines['right'].set_visible(False)

                for i in range(3):
                    ax_perf.annotate(f"{actual_vals[i]:.0f}%", (x_perf[i], actual_vals[i]-8), ha='center', fontsize=10, fontweight='bold', color='#555555')
                    ax_perf.annotate(f"{expected_vals[i]:.0f}%", (x_perf[i], expected_vals[i]+4), ha='center', fontsize=10, fontweight='bold', color='#155724')

                plt.tight_layout()
                img_perf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(img_perf.name, dpi=300, bbox_inches='tight')
                plt.close(fig_perf)

                # ================= REPORTLAB PDF =================
                pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                
                # REPORTE COMPACTO CON MÁRGENES REDUCIDOS A 25
                doc = SimpleDocTemplate(pdf_temp.name, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
                estilos = getSampleStyleSheet()
                
                estilo_tit = ParagraphStyle('Titulo', parent=estilos['Heading1'], textColor=colors.HexColor("#002855"), alignment=TA_LEFT, fontSize=18)
                estilo_sub = ParagraphStyle('Sub', parent=estilos['Heading2'], textColor=colors.HexColor("#002855"), fontSize=13)
                estilo_mini_tit = ParagraphStyle('MiniTit', parent=estilos['Heading3'], textColor=colors.HexColor("#002855"), fontSize=12, fontName="Helvetica-Bold")
                estilo_txt = ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=9.5, leading=13, alignment=TA_JUSTIFY)
                estilo_pie = ParagraphStyle('Pie', parent=estilos['Normal'], fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))
                estilo_blanco = ParagraphStyle('Blanco', parent=estilos['Normal'], textColor=colors.whitesmoke, fontName="Helvetica-Bold", alignment=TA_CENTER)
                estilo_glosario = ParagraphStyle('Glosario', parent=estilos['Normal'], fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), fontName="Helvetica-Oblique")
                
                estilo_bullet_main = ParagraphStyle('BulletMain', parent=estilos['Normal'], fontSize=10, leading=14, spaceAfter=2)
                estilo_subbullet = ParagraphStyle('SubBullet', parent=estilos['Normal'], fontSize=9, leading=12, spaceAfter=2)
                
                elementos = []

                # HEADER
                header_data = []
                title_para = Paragraph("<b>REPORTE OFICIAL DE CERTIFICACIÓN TÉCNICA (GRUPAL)</b>", estilo_tit)
                if os.path.exists("logo_aam.png"):
                    header_data = [[RLImage("logo_aam.png", width=70, height=70), title_para]]
                else:
                    header_data = [["", title_para]]
                t_header = Table(header_data, colWidths=[80, 400])
                t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                elementos.append(t_header)
                elementos.append(Spacer(1, 10))
                
                datos_cabecera = [
                    [Paragraph(f"<b>Grupo Evaluado:</b> {len(nombres_lista)} Asociados"), Paragraph(f"<b>Fecha:</b> {fecha}")],
                    [Paragraph(f"<b>Certificación AAM:</b> {titulo_modulo_pdf}"), Paragraph(f"<b>Instructor:</b> {evaluador}")]
                ]
                t = Table(datos_cabecera, colWidths=[260, 260])
                t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")), ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#A0AAB5")), ('PADDING', (0,0), (-1,-1), 6)]))
                elementos.append(t)
                elementos.append(Spacer(1, 15))

                # --- 1. ANÁLISIS DE PERFORMANCE INDIVIDUAL ---
                elementos.append(Paragraph("<b>1. Análisis de Performance Individual</b>", estilo_sub))
                
                for ind in imagenes_individuales:
                    bloque_individual = []
                    bloque_individual.append(Paragraph(f"<b>Evaluación de Destreza: {ind['nombre']}</b>", estilo_mini_tit))
                    bloque_individual.append(Spacer(1, 5))
                    
                    dash_data_ind = [
                        [RLImage(ind["img1"], width=130, height=130), RLImage(ind["img2"], width=180, height=140)],
                        [Paragraph(ind["txt1"], estilo_pie), Paragraph(ind["txt2"], estilo_pie)],
                        [Spacer(1, 2), Spacer(1, 2)], 
                        [RLImage(ind["img3"], width=180, height=140), RLImage(ind["img4"], width=130, height=130)],
                        [Paragraph(ind["txt3"], estilo_pie), Paragraph(ind["txt4"], estilo_pie)]
                    ]
                    t_dash_ind = Table(dash_data_ind, colWidths=[260, 260])
                    t_dash_ind.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
                    bloque_individual.append(t_dash_ind)
                    
                    estilo_dictamen = ParagraphStyle('Dictamen', parent=estilos['Normal'], fontSize=11, alignment=TA_CENTER, spaceBefore=10, spaceAfter=5, backColor=colors.HexColor("#F8F9FA"), borderPadding=6, borderWidth=1, borderColor=colors.HexColor("#CCCCCC"))
                    bloque_individual.append(Paragraph(ind["dictamen"], estilo_dictamen))
                    
                    # Evita el desperdicio de hojas blancas obligando al bloque a mantenerse compacto
                    elementos.append(KeepTogether(bloque_individual))
                    elementos.append(Spacer(1, 10))

                elementos.append(PageBreak()) 

                # --- 2. COMPARATIVA GLOBAL DEL GRUPO ---
                elementos.append(Paragraph("<b>2. Comparativa Global del Grupo</b>", estilo_sub))
                elementos.append(RLImage(img_comparativa.name, width=480, height=max(240, len(nombres_lista)*30)))
                elementos.append(Spacer(1, 20))

                # --- 3. REGISTRO DE EVALUACIONES CONTINUAS ---
                elementos.append(Paragraph("<b>3. Registro de Evaluaciones Continuas (Promedio Grupal)</b>", estilo_sub))
                
                datos_examenes = [
                    [Paragraph("Fase", estilo_blanco), Paragraph("Propósito Metodológico", estilo_blanco), Paragraph("Peso", estilo_blanco), Paragraph("Score Promedio", estilo_blanco)],
                    ["Diagnóstica", "Línea base cognitiva de pre-requisitos (Bloom: Recordar).", "10%", f"{grp_d:.1f}/100"],
                    ["Formativa", "Validación asimilativa durante observación guiada.", "30%", f"{grp_f:.1f}/100"],
                    ["Sumativa", "Dictamen de resolución técnica en equipo vivo.", "60%", f"{grp_s:.1f}/100"]
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
                elementos.append(Spacer(1, 10))

                dash_data_g = [
                    [RLImage(img_dona_g.name, width=130, height=130), RLImage(img_barras_g.name, width=180, height=140)],
                    [Paragraph(txt_dona_g, estilo_pie), Paragraph(txt_bar_g, estilo_pie)],
                    [Spacer(1, 2), Spacer(1, 2)], 
                    [RLImage(img_tendencia_g.name, width=180, height=140), RLImage(img_radar_g.name, width=130, height=130)],
                    [Paragraph(txt_curv_g, estilo_pie), Paragraph(txt_rad_g, estilo_pie)]
                ]
                t_dash_g = Table(dash_data_g, colWidths=[260, 260])
                t_dash_g.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
                elementos.append(t_dash_g)
                
                elementos.append(Paragraph(dictamen_g, estilo_dictamen))
                elementos.append(PageBreak()) 

                # --- 4. PLAN DE ASIGNACIÓN DE RECURSOS GRUPAL ---
                elementos.append(Paragraph("<b>4. Plan de Asignación de Recursos Grupal (TWI)</b>", estilo_sub))
                elementos.append(Paragraph(bloom_g, estilo_txt))
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(modelo_g, estilo_txt))
                elementos.append(Spacer(1, 8))
                
                img_height_rl = 450 * (height_in / 7.0)
                elementos.append(RLImage(img_gantt.name, width=450, height=img_height_rl))
                
                texto_glosario = "*Glosario de Fases TWI: <b>Preparar:</b> Revisión teórica y lectura de diagramas. <b>Presentar:</b> Observación activa (Shadowing). <b>Intentar:</b> Ejecución autónoma en piso (Try-Out). <br/><br/><i>Nota de Compensación: La distribución de horas en este plan correctivo es intencionalmente asimétrica. Su propósito es inyectar recursos en las áreas deficientes para devolver al grupo al equilibrio del modelo 70-20-10.</i>"
                elementos.append(Spacer(1, 3))
                elementos.append(Paragraph(texto_glosario, estilo_glosario))
                elementos.append(Spacer(1, 20))
                
                elementos.append(Paragraph("<b>Recomendaciones de Acción Preventiva (Para el Instructor):</b>", estilo_mini_tit))
                lista_pasos = []
                for p in pasos_g:
                    lista_pasos.append(ListItem(Paragraph(p, estilo_bullet_main), bulletText="•"))
                elementos.append(ListFlowable(lista_pasos, bulletType='bullet', leftIndent=10))
                elementos.append(PageBreak())

                # --- 5. SYLLABUS AUTOMATIZADO DEL GRUPO ---
                elementos.append(Paragraph("<b>5. Syllabus Automatizado del Grupo (Basado en Brechas Operativas)</b>", estilo_sub))
                texto_explicativo = "<i>Nota Metodológica: ¿Qué es el Syllabus Automatizado? En lugar de generar temarios genéricos, el algoritmo del sistema cruza en tiempo real las deficiencias promedio detectadas en el equipo con el mapa curricular oficial de AAM, estructurando un plan de rescate académico jerarquizado y 100% a la medida grupal.</i>"
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(texto_explicativo, estilo_txt))
                elementos.append(Spacer(1, 15))

                lista_principal_syllabus = []
                for bloque in temario_g:
                    sub_items = []
                    if bloque["teoria"]:
                        sub_items.append(ListItem(Paragraph(bloque["teoria"], estilo_subbullet), bulletText="•"))
                    if bloque["practica"]:
                        sub_items.append(ListItem(Paragraph(bloque["practica"], estilo_subbullet), bulletText="•"))
                    
                    sub_items.append(ListItem(Paragraph(bloque["actividad"], estilo_subbullet), bulletText="➤"))
                    
                    sub_list = ListFlowable(sub_items, bulletType='bullet', leftIndent=15, spaceAfter=10)
                    item_principal = ListItem([Paragraph(bloque["sesion"], estilo_bullet_main), sub_list], bulletText="■")
                    lista_principal_syllabus.append(item_principal)

                elementos.append(ListFlowable(lista_principal_syllabus, bulletType='bullet', leftIndent=10))
                elementos.append(Spacer(1, 20))
                
                # --- 6. ANALÍTICA PREDICTIVA DE COMPETENCIA ---
                elementos.append(Paragraph("<b>6. Analítica Predictiva de Competencia (Nivel Esperado)</b>", estilo_sub))
                texto_roi = "La siguiente gráfica proyecta el crecimiento formativo del equipo al concluir el Syllabus estructurado. El área verde representa la recuperación de competencia operativa proyectada tras ejecutar las sesiones TWI sugeridas."
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(texto_roi, estilo_txt))
                elementos.append(Spacer(1, 10))
                
                elementos.append(RLImage(img_perf.name, width=500, height=218))

                doc.build(elementos)

            with open(pdf_temp.name, "rb") as pdf_file:
                st.download_button(
                    label="📥 DESCARGAR REPORTE TÉCNICO Y SYLLABUS GRUPAL (PDF)",
                    data=pdf_file,
                    file_name=f"Reporte_Grupo_AAM_{fecha}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    on_click=confirmar_descarga
                )

# --- FOOTER / FIRMA DEL DESARROLLADOR ---
st.markdown("""
    <hr style="margin-top: 3rem; margin-bottom: 1rem; border: 0; border-top: 1px solid #CCC;">
    <div style="text-align: center; color: #666; font-size: 14px;">
        Desarrollado en el Centro de Innovación IECA + AAM por <b>Ing. Pablo Horta</b><br>
        <i>AAM SkillMatrix Pro v0.1</i>
    </div>
""", unsafe_allow_html=True)

# --- LOGO DEL CENTRO DE INNOVACIÓN ---
# Usamos 3 columnas para que el logo quede perfectamente centrado
col_espacio1, col_logo, col_espacio2 = st.columns([4.5, 1, 4.5])     
with col_logo:
    st.image("logo_ci.png", use_container_width=True)
