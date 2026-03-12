import os
import io
import json
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Sistema 5S - INOVA",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = "data_5s"
REPORTS_DIR = os.path.join(DATA_DIR, "reportes")
EVIDENCE_DIR = os.path.join(DATA_DIR, "evidencias")
DB_PATH = os.path.join(DATA_DIR, "inspecciones.json")
SCHEDULE_PATH = os.path.join(DATA_DIR, "cronograma.json")
EXCEL_PATH = os.path.join(DATA_DIR, "historico_5s.xlsx")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

LOGO_INOVA = "INOVA.png"
LOGO_EASY = "FOND EASY.png"

# =========================================================
# ESTILO UI WOW
# =========================================================
st.markdown("""
<style>
:root{
    --azul:#061f45;
    --azul2:#082b5c;
    --azul3:#0d3b73;
    --fondo:#f3f7fb;
    --borde:#d7e3ef;
    --texto:#1f2937;
    --verde:#13a35b;
    --amarillo:#d99b00;
    --rojo:#d53333;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", sans-serif;
}

body {
    color: var(--texto);
}

.block-container{
    padding-top: 0.7rem;
    padding-bottom: 1rem;
    padding-left: 1.25rem;
    padding-right: 1.25rem;
    max-width: 100% !important;
}

section[data-testid="stSidebar"]{
    background: linear-gradient(180deg, #f7fafe 0%, #eef4fb 100%);
    border-right: 1px solid #d7e3ef;
}

.top-shell{
    background: white;
    border: 1px solid #dbe6f1;
    border-radius: 24px;
    padding: 16px 18px;
    box-shadow: 0 10px 26px rgba(11, 37, 71, 0.06);
    margin-bottom: 14px;
}

.top-banner{
    background: linear-gradient(135deg, #061f45 0%, #0d3b73 55%, #174f95 100%);
    color: white;
    border-radius: 20px;
    padding: 22px 28px;
    min-height: 110px;
    display: flex;
    align-items: center;
    box-shadow: 0 14px 30px rgba(6,31,69,0.22);
}

.top-title{
    font-size: 2.05rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 6px;
}

.top-subtitle{
    font-size: 0.96rem;
    color: #dce8f8;
}

.main-wrap{
    background: linear-gradient(180deg, #fbfdff 0%, #f4f8fc 100%);
    border: 1px solid #dce7f1;
    border-radius: 24px;
    padding: 20px 22px;
    box-shadow: 0 10px 24px rgba(14, 30, 52, 0.05);
    margin-bottom: 16px;
}

.section-title{
    color: #082b5c;
    font-size: 1.22rem;
    font-weight: 800;
    margin-bottom: 12px;
}

.kpi-card{
    background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid #dbe6f1;
    border-radius: 18px;
    padding: 18px;
    min-height: 115px;
    box-shadow: 0 8px 18px rgba(8, 32, 68, 0.04);
}

.kpi-label{
    color: #667085;
    font-size: 0.92rem;
    margin-bottom: 8px;
    font-weight: 700;
}

.kpi-value{
    color: #061f45;
    font-size: 2rem;
    font-weight: 800;
}

.ins-card{
    background: white;
    border: 1px solid #d9e6f2;
    border-radius: 18px;
    padding: 16px 16px 10px 16px;
    box-shadow: 0 6px 16px rgba(8, 32, 68, 0.04);
    margin-bottom: 14px;
}

.punto-title{
    font-size: 1rem;
    font-weight: 800;
    color: #082b5c;
    margin-bottom: 8px;
}

.punto-sub{
    color: #4b5563;
    font-size: 0.95rem;
    line-height: 1.35;
}

.badge-green, .badge-yellow, .badge-red{
    display:inline-block;
    padding:6px 12px;
    border-radius:999px;
    font-weight:800;
    font-size:0.9rem;
}
.badge-green{background:#e9f8ef;color:#118a4c;border:1px solid #bfe9ce;}
.badge-yellow{background:#fff7df;color:#9b7400;border:1px solid #ecd995;}
.badge-red{background:#fdecec;color:#bf2525;border:1px solid #efbbbb;}

.stButton > button{
    border-radius: 14px !important;
    min-height: 46px !important;
    border: 1px solid #c8d8e8 !important;
    background: linear-gradient(180deg, #ffffff 0%, #f4f8fd 100%) !important;
    color: #082b5c !important;
    font-weight: 800 !important;
}

div[data-testid="stDownloadButton"] > button{
    border-radius: 14px !important;
    min-height: 46px !important;
    font-weight: 800 !important;
}

div[data-testid="stExpander"]{
    border-radius: 16px !important;
    overflow: hidden;
}

hr{
    border: none;
    border-top: 1px solid #e3edf6;
    margin: 14px 0;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATA
# =========================================================
BODEGAS = {
    "Bodega General": [
        "Limpieza pisos pasillos (Pasillo 1, 2, zonas de tránsito)",
        "Limpieza pisos naves de almacenamiento lata y zona alistamiento",
        "Limpieza pisos zona de revisión",
        "Limpieza pisos ETO",
        "Limpieza pisos oficina administrativa",
        "Limpieza pisos muelle de descargue",
        "Limpieza patio 1 y línea de vida",
        "Limpieza estaciones de aseo bodega y patio",
        "Limpieza de estanterías (Pasillo 1, pasillo 2, estantería azúcar)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Almacenamiento de materiales por fuera de layout designado",
        "Limpieza herramientas manuales y ubicación en layout designado",
        "Limpieza gabinetes (Implementos 5S e implementos oficina administrativa)",
        "Limpieza equipos de cómputo oficina administrativa",
        "Validación identificación materiales"
    ],
    "Bodega Tierras": [
        "Limpieza pisos zona de tránsito y muelle descargue",
        "Limpieza pisos almacenamiento a piso",
        "Limpieza de estanterías (Polvo, telarañas)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Limpieza herramientas 5S y portón muelle descargue",
        "Almacenamiento de materiales cumpliendo layout designado",
        "Limpieza herramientas manuales y ubicación en layout designado",
        "Muelle de descargue libre de estibas",
        "Limpieza rampa ubicación externa de bodega",
        "Cumplimiento patrón de estibado de materiales",
        "Validación estibas en buen estado",
        "Validación identificación materiales"
    ],
    "Bodega Preforma": [
        "Limpieza pisos zona de tránsito y muelle descargue",
        "Limpieza pisos almacenamiento a piso",
        "Limpieza de estanterías (Polvo, telarañas)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Limpieza herramientas 5S y portón muelle descargue",
        "Almacenamiento de materiales cumpliendo layout designado",
        "Limpieza herramientas manuales y ubicación en layout designado",
        "Muelle de descargue libre de estibas",
        "Limpieza rampa ubicación externa de bodega",
        "Cumplimiento patrón de estibado de materiales",
        "Validación estibas en buen estado",
        "Validación identificación materiales"
    ],
    "Bodega Químico": [
        "Limpieza pisos zona de tránsito y muelle descargue",
        "Limpieza pisos pasillos (Pasillo 1, Pasillo 2, Pasillo 3)",
        "Limpieza pasillo externo de bodega",
        "Limpieza de estanterías (Polvo, telarañas)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Limpieza gabinetes (EPPs)",
        "Limpieza herramientas manuales y ubicación en layout designado",
        "Almacenamiento de materiales cumpliendo layout designado",
        "Cumplimiento patrón de estibado de materiales",
        "Validación estibas en buen estado",
        "Cumplimiento compatibilidad SQ almacenamiento",
        "Validación identificación materiales"
    ],
    "Bodega Cuarto Frío": [
        "Limpieza pisos almacenamiento a piso (color caramelo)",
        "Limpieza pisos bodega",
        "Limpieza pasillo externo de bodega",
        "Limpieza de estanterías (Polvo, telarañas)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Almacenamiento de materiales cumpliendo layout designado",
        "Cumplimiento patrón de estibado de materiales",
        "Validación estibas en buen estado",
        "Validación identificación materiales"
    ],
    "Bodega Cuarto Atemparado": [
        "Limpieza pisos bodega",
        "Limpieza pasillo externo de bodega",
        "Limpieza de estanterías (Polvo, telarañas)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Almacenamiento de materiales cumpliendo layout designado",
        "Cumplimiento patrón de estibado de materiales",
        "Validación estibas en buen estado",
        "Validación identificación materiales"
    ],
    "Bodega Alterna": [
        "Limpieza pasillos (Pasillo 1, Pasillo 2)",
        "Limpieza jaula de almacenamiento gases comprimidos",
        "Limpieza de estanterías (Polvo, telarañas)",
        "Limpieza de materiales (Cambio de pelex y retiro de polvo)",
        "Almacenamiento de materiales cumpliendo layout designado",
        "Validación estibas en buen estado",
        "Validación identificación materiales"
    ]
}

# =========================================================
# HELPERS
# =========================================================
def safe_load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def safe_save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_uploaded_image(uploaded_file, folder, file_prefix):
    if uploaded_file is None:
        return None
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split(".")[-1].lower()
    filename = f"{file_prefix}.{ext}"
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def resize_image(path, max_width=1200):
    try:
        img = Image.open(path)
        w, h = img.size
        if w > max_width:
            ratio = max_width / w
            img = img.resize((int(w * ratio), int(h * ratio)))
            img.save(path)
    except Exception:
        pass

def fit_image_box(path, max_w_px=900, max_h_px=520):
    try:
        img = Image.open(path)
        w, h = img.size
        ratio = min(max_w_px / w, max_h_px / h)
        ratio = min(ratio, 1.0)
        return int(w * ratio), int(h * ratio)
    except Exception:
        return 800, 450

def cumplimiento_texto(valor):
    if valor >= 90:
        return "Excelente"
    elif valor >= 75:
        return "Aceptable / Atención"
    return "Crítico"

def cumplimiento_badge(valor):
    if valor >= 90:
        return '<span class="badge-green">🟢 Excelente</span>'
    elif valor >= 75:
        return '<span class="badge-yellow">🟡 Atención</span>'
    return '<span class="badge-red">🔴 Crítico</span>'

def get_week_label(fecha_ref=None):
    if fecha_ref is None:
        fecha_ref = datetime.today()
    year, week_num, _ = fecha_ref.isocalendar()
    return f"Semana_{week_num:02d}_{year}"

def normalizar_items_legacy(items):
    normalizados = []
    for item in items:
        if "fotos" not in item:
            foto_unica = item.get("foto")
            item["fotos"] = [foto_unica] if foto_unica else []
        normalizados.append(item)
    return normalizados

def append_to_excel(registro):
    rows = []
    for item in registro["items"]:
        fotos = item.get("fotos", [])
        if not fotos and item.get("foto"):
            fotos = [item.get("foto")]

        rows.append({
            "Fecha": registro["fecha"],
            "Responsable": registro["responsable"],
            "Bodega": registro["bodega"],
            "Área": registro["area"],
            "Punto": item["punto"],
            "Cumple": "Sí" if item["cumple"] else "No",
            "Observación": item["observacion"],
            "Fotos": " | ".join(fotos) if fotos else "",
            "Cantidad fotos": len(fotos),
            "Cumplimiento Total %": registro["cumplimiento"]
        })

    df_new = pd.DataFrame(rows)

    if os.path.exists(EXCEL_PATH):
        try:
            df_old = pd.read_excel(EXCEL_PATH)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        except Exception:
            df_all = df_new
    else:
        df_all = df_new

    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_all.to_excel(writer, index=False, sheet_name="Historico")

    return EXCEL_PATH

def rebuild_excel_from_inspections(inspecciones):
    rows = []
    for registro in inspecciones:
        items = normalizar_items_legacy(registro.get("items", []))
        for item in items:
            fotos = item.get("fotos", [])
            if not fotos and item.get("foto"):
                fotos = [item.get("foto")]

            rows.append({
                "Fecha": registro["fecha"],
                "Responsable": registro["responsable"],
                "Bodega": registro["bodega"],
                "Área": registro["area"],
                "Punto": item["punto"],
                "Cumple": "Sí" if item["cumple"] else "No",
                "Observación": item["observacion"],
                "Fotos": " | ".join(fotos) if fotos else "",
                "Cantidad fotos": len(fotos),
                "Cumplimiento Total %": registro["cumplimiento"]
            })

    if rows:
        df = pd.DataFrame(rows)
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Historico")
    else:
        if os.path.exists(EXCEL_PATH):
            try:
                os.remove(EXCEL_PATH)
            except Exception:
                pass

def export_cronograma_excel(df_crono):
    semana = get_week_label()
    filename = f"Cronograma_{semana}.xlsx"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_crono.to_excel(writer, index=False, sheet_name="Cronograma")
    buffer.seek(0)

    return buffer, filename

def guardar_gantt_png(fig):
    import plotly.io as pio

    semana = get_week_label()
    filename = f"Cronograma_{semana}.png"
    output_path = os.path.join(DATA_DIR, filename)

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1f2937"),
        title_font=dict(color="#061f45"),
        legend=dict(bgcolor="rgba(255,255,255,0.85)"),
        margin=dict(l=180, r=50, t=80, b=50)
    )

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    img_bytes = pio.to_image(
        fig,
        format="png",
        width=2200,
        height=1000,
        scale=2
    )

    with open(output_path, "wb") as f:
        f.write(img_bytes)

    return output_path, filename

def exportar_gantt_html(fig):
    semana = get_week_label()
    filename = f"Cronograma_{semana}.html"
    buffer = io.StringIO()
    html = fig.to_html(full_html=True, include_plotlyjs=True)
    buffer.write(html)
    buffer.seek(0)
    return buffer, filename

def generar_pdf(registro):
    fecha_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(
        REPORTS_DIR,
        f"Informe_5S_{registro['bodega'].replace(' ', '_')}_{fecha_id}.pdf"
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=1.25 * cm,
        leftMargin=1.25 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleBlue",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#061f45"),
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="SubBlue",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4f6279")
    ))
    styles.add(ParagraphStyle(
        name="HBlue",
        parent=styles["Heading2"],
        fontSize=14,
        leading=16,
        textColor=colors.HexColor("#061f45"),
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="NormalSmall",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name="PhotoCaption",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#425466")
    ))
    styles.add(ParagraphStyle(
        name="MetaCenterValue",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#061f45")
    ))

    story = []

    header_logo = ""
    easy_logo = ""

    if os.path.exists(LOGO_INOVA):
        try:
            header_logo = RLImage(LOGO_INOVA, width=2.2 * cm, height=2.2 * cm)
        except Exception:
            header_logo = ""

    if os.path.exists(LOGO_EASY):
        try:
            easy_logo = RLImage(LOGO_EASY, width=1.25 * cm, height=1.25 * cm)
        except Exception:
            easy_logo = ""

    top_header = Table(
        [[
            header_logo,
            Paragraph(
                "<b>INFORME DE AUDITORÍA 5S</b><br/>"
                "<font size='10' color='#52667A'>Sistema de seguimiento, control visual y verificación operativa por bodegas</font>",
                styles["TitleBlue"]
            ),
            easy_logo
        ]],
        colWidths=[2.7 * cm, 11.0 * cm, 2.0 * cm]
    )
    top_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(top_header)
    story.append(Spacer(1, 0.25 * cm))

    meta_center_html = f"""
    <b>Fecha inspección</b><br/>
    <font color="#061f45">{registro["fecha"]}</font><br/><br/>

    <b>Responsable</b><br/>
    <font color="#061f45">{registro["responsable"]}</font><br/><br/>

    <b>Bodega</b><br/>
    <font color="#061f45">{registro["bodega"]}</font><br/><br/>

    <b>Área / proceso</b><br/>
    <font color="#061f45">{registro["area"]}</font>
    """

    meta_center_box = Table(
        [[Paragraph(meta_center_html, styles["MetaCenterValue"])]],
        colWidths=[15.8 * cm]
    )
    meta_center_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D5E0EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_center_box)
    story.append(Spacer(1, 0.35 * cm))

    desc_box = Table(
        [[Paragraph(
            "Este documento consolida el resultado técnico de la auditoría 5S ejecutada sobre la bodega evaluada, "
            "incluyendo el porcentaje de cumplimiento, los hallazgos registrados, las observaciones operativas, "
            "la trazabilidad del responsable y las evidencias fotográficas asociadas a cada punto de control.",
            styles["Normal"]
        )]],
        colWidths=[15.8 * cm]
    )
    desc_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFD")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7E2EC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(desc_box)
    story.append(Spacer(1, 0.40 * cm))

    items = normalizar_items_legacy(registro["items"])
    cumplimiento = registro["cumplimiento"]
    total_items = len(items)
    cumplidos = sum(1 for x in items if x["cumple"])
    no_conformes = total_items - cumplidos
    hallazgos = [x for x in items if (not x["cumple"]) or (x["observacion"] and x["observacion"].strip())]

    story.append(Paragraph("1. Resumen ejecutivo", styles["HBlue"]))
    resumen_data = [
        ["Indicador", "Resultado"],
        ["Porcentaje de cumplimiento", f"{cumplimiento:.1f}%"],
        ["Nivel de desempeño", cumplimiento_texto(cumplimiento)],
        ["Puntos evaluados", str(total_items)],
        ["Puntos conformes", str(cumplidos)],
        ["Puntos no conformes", str(no_conformes)],
        ["Puntos con hallazgo o novedad", str(len(hallazgos))]
    ]
    resumen_table = Table(resumen_data, colWidths=[7.8 * cm, 7.1 * cm])
    resumen_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#061f45")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d6e5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 0.45 * cm))

    story.append(Paragraph("2. Matriz técnica de verificación", styles["HBlue"]))
    detalle = [["Ítem", "Punto evaluado", "Estado", "Observación", "Fotos"]]
    for i, item in enumerate(items, start=1):
        fotos = item.get("fotos", [])
        detalle.append([
            str(i),
            Paragraph(item["punto"], styles["NormalSmall"]),
            "Conforme" if item["cumple"] else "No conforme",
            Paragraph(item["observacion"] if item["observacion"] else "-", styles["NormalSmall"]),
            str(len(fotos))
        ])

    detalle_table = Table(detalle, colWidths=[1.0 * cm, 7.0 * cm, 2.2 * cm, 4.2 * cm, 1.4 * cm], repeatRows=1)
    detalle_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#061f45")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7d6e5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(detalle_table)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("3. Hallazgos y observaciones relevantes", styles["HBlue"]))
    if hallazgos:
        for i, item in enumerate(hallazgos, start=1):
            texto = f"<b>{i}.</b> {item['punto']}<br/>"
            texto += "Estado: Conforme con observación.<br/>" if item["cumple"] else "Estado: No conforme.<br/>"
            texto += f"Observación: {item['observacion'] if item['observacion'] else 'Sin detalle adicional.'}<br/>"
            texto += f"Cantidad de evidencias: {len(item.get('fotos', []))}"
            story.append(Paragraph(texto, styles["Normal"]))
            story.append(Spacer(1, 0.15 * cm))
    else:
        story.append(Paragraph("No se registraron hallazgos relevantes en la evaluación realizada.", styles["Normal"]))

    evidencias = [x for x in items if x.get("fotos")]
    if evidencias:
        story.append(PageBreak())
        story.append(Paragraph("4. Evidencias fotográficas", styles["HBlue"]))
        story.append(Spacer(1, 0.15 * cm))

        contador_evidencia = 1
        for item in evidencias:
            story.append(Paragraph(f"<b>Punto evaluado:</b> {item['punto']}", styles["Normal"]))
            if item["observacion"]:
                story.append(Paragraph(f"Observación asociada: {item['observacion']}", styles["PhotoCaption"]))
            story.append(Spacer(1, 0.10 * cm))

            for foto in item.get("fotos", []):
                try:
                    story.append(Paragraph(f"<b>Evidencia {contador_evidencia}</b>", styles["PhotoCaption"]))
                    resize_image(foto, max_width=1300)
                    w_px, h_px = fit_image_box(foto, max_w_px=980, max_h_px=520)
                    w_scale = min((w_px / 96), 15.2)
                    h_scale = min((h_px / 96), 8.3)

                    img = RLImage(foto, width=w_scale * cm, height=h_scale * cm)

                    img_table = Table([[img]], colWidths=[16.0 * cm])
                    img_table.setStyle(TableStyle([
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d1dce8")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fbff")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ]))
                    story.append(img_table)
                    story.append(Spacer(1, 0.25 * cm))
                    contador_evidencia += 1
                except Exception:
                    story.append(Paragraph("No fue posible cargar una de las evidencias fotográficas.", styles["PhotoCaption"]))
                    story.append(Spacer(1, 0.15 * cm))

            story.append(Spacer(1, 0.18 * cm))

    doc.build(story)
    return pdf_path

def init_session():
    if "selected_bodega" not in st.session_state:
        st.session_state.selected_bodega = list(BODEGAS.keys())[0]
    if "cronograma" not in st.session_state:
        st.session_state.cronograma = safe_load_json(SCHEDULE_PATH, [])
    if "inspecciones" not in st.session_state:
        inspecciones_cargadas = safe_load_json(DB_PATH, [])
        for reg in inspecciones_cargadas:
            reg["items"] = normalizar_items_legacy(reg.get("items", []))
        st.session_state.inspecciones = inspecciones_cargadas

init_session()

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="top-shell">', unsafe_allow_html=True)
h1, h2 = st.columns([1.1, 6.4], gap="small")
with h1:
    if os.path.exists(LOGO_INOVA):
        st.image(LOGO_INOVA, width=120)
with h2:
    st.markdown("""
    <div class="top-banner">
        <div>
            <div class="top-title">Sistema 5S - INOVA</div>
            <div class="top-subtitle">Cronograma, auditoría fotográfica, trazabilidad de cumplimiento, indicadores y reportes ejecutivos por bodega.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

menu = st.sidebar.radio("Módulos", ["Inicio", "Cronograma", "Inspección", "Dashboard"])

# =========================================================
# BOTONES EXCLUSIVOS DE ELIMINAR POR DÍA
# =========================================================
st.sidebar.markdown("---")
st.sidebar.subheader("Eliminar por día")

fecha_borrar_crono = st.sidebar.date_input("Fecha cronograma a eliminar", value=date.today(), key="fecha_borrar_crono")
if st.sidebar.button("Eliminar cronograma del día", use_container_width=True):
    antes = len(st.session_state.cronograma)
    fecha_txt = str(fecha_borrar_crono)
    st.session_state.cronograma = [
        x for x in st.session_state.cronograma
        if str(x.get("fecha_inicio", ""))[:10] != fecha_txt
    ]
    safe_save_json(SCHEDULE_PATH, st.session_state.cronograma)
    borrados = antes - len(st.session_state.cronograma)
    if borrados > 0:
        st.sidebar.success(f"Se eliminaron {borrados} actividades del cronograma del día {fecha_txt}.")
    else:
        st.sidebar.info(f"No había actividades de cronograma para {fecha_txt}.")

fecha_borrar_insp = st.sidebar.date_input("Fecha inspección a eliminar", value=date.today(), key="fecha_borrar_insp")
if st.sidebar.button("Eliminar inspecciones del día", use_container_width=True):
    antes = len(st.session_state.inspecciones)
    fecha_txt = str(fecha_borrar_insp)
    st.session_state.inspecciones = [
        x for x in st.session_state.inspecciones
        if str(x.get("fecha", ""))[:10] != fecha_txt
    ]
    safe_save_json(DB_PATH, st.session_state.inspecciones)
    rebuild_excel_from_inspections(st.session_state.inspecciones)
    borrados = antes - len(st.session_state.inspecciones)
    if borrados > 0:
        st.sidebar.success(f"Se eliminaron {borrados} inspecciones del día {fecha_txt}.")
    else:
        st.sidebar.info(f"No había inspecciones para {fecha_txt}.")

# =========================================================
# INICIO
# =========================================================
if menu == "Inicio":
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Resumen general del sistema</div>', unsafe_allow_html=True)

    total_bodegas = len(BODEGAS)
    total_puntos = sum(len(v) for v in BODEGAS.values())
    total_inspecciones = len(st.session_state.inspecciones)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Bodegas activas</div><div class="kpi-value">{total_bodegas}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Puntos de control</div><div class="kpi-value">{total_puntos}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Inspecciones registradas</div><div class="kpi-value">{total_inspecciones}</div></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# CRONOGRAMA
# =========================================================
elif menu == "Cronograma":
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Cronograma maestro y diagrama de Gantt</div>', unsafe_allow_html=True)

    with st.form("form_cronograma"):
        c1, c2, c3 = st.columns(3)
        with c1:
            bodega = st.selectbox("Bodega", list(BODEGAS.keys()))
        with c2:
            responsable = st.text_input("Responsable")
        with c3:
            actividad = st.text_input("Actividad", value="Inspección 5S")

        c4, c5 = st.columns(2)
        with c4:
            fecha_inicio = st.date_input("Fecha inicio", value=date.today())
        with c5:
            fecha_fin = st.date_input("Fecha fin", value=date.today())

        observacion = st.text_area("Observación / alcance", height=90)
        guardar = st.form_submit_button("Guardar actividad", use_container_width=True)

        if guardar:
            fecha_fin_real = fecha_fin
            if fecha_fin_real <= fecha_inicio:
                fecha_fin_real = fecha_inicio + timedelta(days=1)

            nuevo = {
                "bodega": bodega,
                "responsable": responsable,
                "actividad": actividad,
                "fecha_inicio": str(fecha_inicio),
                "fecha_fin": str(fecha_fin_real),
                "observacion": observacion
            }
            st.session_state.cronograma.append(nuevo)
            safe_save_json(SCHEDULE_PATH, st.session_state.cronograma)
            st.success("Actividad agregada al cronograma.")

    if st.session_state.cronograma:
        df_crono = pd.DataFrame(st.session_state.cronograma)
        df_crono["fecha_inicio"] = pd.to_datetime(df_crono["fecha_inicio"])
        df_crono["fecha_fin"] = pd.to_datetime(df_crono["fecha_fin"])

        with st.expander("Ver programación registrada", expanded=False):
            st.dataframe(df_crono, use_container_width=True)

        st.markdown("#### Diagrama de Gantt")

        color_map = {
            "Bodega General": "#156CC1",
            "Bodega Tierras": "#7EC0EE",
            "Bodega Químico": "#FF2D2D",
            "Bodega Cuarto Frío": "#F2A6A6",
            "Bodega Cuarto Atemparado": "#2BB3A3",
            "Bodega Preforma": "#76E09B",
            "Bodega Alterna": "#FF8A00"
        }

        fig = px.timeline(
            df_crono,
            x_start="fecha_inicio",
            x_end="fecha_fin",
            y="bodega",
            color="bodega",
            text="actividad",
            hover_data=["responsable", "observacion"],
            color_discrete_map=color_map
        )

        fig.update_yaxes(
            autorange="reversed",
            showgrid=True,
            gridcolor="#f1f6fb",
            automargin=True
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor="#e5edf6",
            automargin=True
        )
        fig.update_traces(
            textposition="inside",
            insidetextanchor="middle"
        )
        fig.update_layout(
            height=700,
            title="Cronograma 5S por bodegas",
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title="Fechas programadas",
            yaxis_title="Bodegas",
            legend_title="Bodega",
            font=dict(size=13, color="#1f2937"),
            margin=dict(l=150, r=40, t=70, b=40),
            title_font=dict(size=20, color="#061f45")
        )
        st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)

        excel_buffer, excel_name = export_cronograma_excel(df_crono)
        with col_a:
            st.download_button(
                "Exportar cronograma Excel",
                data=excel_buffer.getvalue(),
                file_name=excel_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_b:
            try:
                gantt_png, gantt_name = guardar_gantt_png(fig)
                with open(gantt_png, "rb") as f:
                    st.download_button(
                        "Exportar imagen gráfica Gantt",
                        data=f.read(),
                        file_name=gantt_name,
                        mime="image/png",
                        use_container_width=True
                    )
            except Exception:
                html_buffer, html_name = exportar_gantt_html(fig)
                st.download_button(
                    "Exportar Gantt HTML",
                    data=html_buffer.getvalue(),
                    file_name=html_name,
                    mime="text/html",
                    use_container_width=True
                )
                st.warning("En este servidor no se pudo generar PNG. Se habilitó la descarga HTML del Gantt.")

    else:
        st.info("No hay actividades registradas todavía.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# INSPECCIÓN
# =========================================================
elif menu == "Inspección":
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Inspección por bodega con evidencia fotográfica múltiple</div>', unsafe_allow_html=True)

    st.markdown("### Selecciona una bodega")
    cols = st.columns(4)
    nombres = list(BODEGAS.keys())

    for i, bod in enumerate(nombres):
        with cols[i % 4]:
            if st.button(bod, use_container_width=True):
                st.session_state.selected_bodega = bod

    bodega_actual = st.session_state.selected_bodega
    st.markdown(f"**Bodega seleccionada:** {bodega_actual}")

    c1, c2, c3 = st.columns(3)
    with c1:
        fecha_inspeccion = st.date_input("Fecha de inspección", value=date.today())
    with c2:
        responsable = st.text_input("Responsable de inspección")
    with c3:
        area = st.text_input("Área / proceso", value="Almacenamiento")

    st.markdown("---")
    st.markdown(f"### Checklist técnico - {bodega_actual}")

    puntos = BODEGAS[bodega_actual]
    items = []

    for idx, punto in enumerate(puntos, start=1):
        st.markdown('<div class="ins-card">', unsafe_allow_html=True)
        box1, box2 = st.columns([1.1, 2.4])

        with box1:
            cumple = st.checkbox("Cumple", key=f"{bodega_actual}_{idx}_cumple")
            fotos = st.file_uploader(
                f"Fotos evidencia {idx}",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"{bodega_actual}_{idx}_foto"
            )

            if fotos:
                with st.expander(f"Ver {len(fotos)} evidencia(s) cargada(s)", expanded=False):
                    for n_foto, foto_item in enumerate(fotos, start=1):
                        st.image(foto_item, caption=f"Evidencia {idx}.{n_foto}", use_container_width=True)

        with box2:
            st.markdown(f'<div class="punto-title">Punto {idx}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="punto-sub">{punto}</div>', unsafe_allow_html=True)
            observacion = st.text_area(
                "Observación",
                key=f"{bodega_actual}_{idx}_obs",
                height=105,
                placeholder="Describe hallazgo, novedad, condición observada o acción requerida..."
            )

        st.markdown('</div>', unsafe_allow_html=True)

        items.append({
            "punto": punto,
            "cumple": cumple,
            "observacion": observacion,
            "foto_obj": fotos
        })

    if st.button("Guardar inspección y generar informe PDF", type="primary", use_container_width=True):
        if not responsable.strip():
            st.error("Debes ingresar el responsable.")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder = os.path.join(EVIDENCE_DIR, f"{bodega_actual.replace(' ', '_')}_{timestamp}")
            os.makedirs(folder, exist_ok=True)

            total = len(items)
            cumplidos = 0
            items_final = []

            for i, item in enumerate(items, start=1):
                if item["cumple"]:
                    cumplidos += 1

                foto_paths = []
                if item["foto_obj"]:
                    for j, foto_subida in enumerate(item["foto_obj"], start=1):
                        foto_path = save_uploaded_image(foto_subida, folder, f"evidencia_{i}_{j}")
                        if foto_path:
                            foto_paths.append(foto_path)

                items_final.append({
                    "punto": item["punto"],
                    "cumple": item["cumple"],
                    "observacion": item["observacion"],
                    "fotos": foto_paths
                })

            cumplimiento = (cumplidos / total) * 100 if total > 0 else 0

            registro = {
                "id": timestamp,
                "fecha": str(fecha_inspeccion),
                "responsable": responsable,
                "area": area,
                "bodega": bodega_actual,
                "cumplimiento": round(cumplimiento, 2),
                "items": items_final
            }

            st.session_state.inspecciones.append(registro)
            safe_save_json(DB_PATH, st.session_state.inspecciones)

            excel_file = append_to_excel(registro)

            try:
                pdf_file = generar_pdf(registro)
                st.success("Inspección guardada correctamente.")
                st.markdown(cumplimiento_badge(cumplimiento), unsafe_allow_html=True)

                with open(pdf_file, "rb") as f:
                    st.download_button(
                        "Descargar informe PDF",
                        data=f.read(),
                        file_name=os.path.basename(pdf_file),
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error generando PDF: {e}")

            if os.path.exists(excel_file):
                with open(excel_file, "rb") as f:
                    st.download_button(
                        "Descargar histórico Excel",
                        data=f.read(),
                        file_name=os.path.basename(excel_file),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# DASHBOARD
# =========================================================
elif menu == "Dashboard":
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Dashboard de cumplimiento 5S</div>', unsafe_allow_html=True)

    inspecciones = st.session_state.inspecciones

    if not inspecciones:
        st.info("Aún no hay inspecciones guardadas.")
    else:
        resumen = []
        for reg in inspecciones:
            resumen.append({
                "Fecha": reg["fecha"],
                "Responsable": reg["responsable"],
                "Bodega": reg["bodega"],
                "Cumplimiento": reg["cumplimiento"]
            })

        df = pd.DataFrame(resumen)
        df["Fecha"] = pd.to_datetime(df["Fecha"])

        c1, c2, c3 = st.columns(3)
        promedio = df["Cumplimiento"].mean()

        with c1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Promedio global</div><div class="kpi-value">{promedio:.1f}%</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Inspecciones</div><div class="kpi-value">{len(df)}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Estado</div><div style="margin-top:12px;">{cumplimiento_badge(promedio)}</div></div>', unsafe_allow_html=True)

        st.markdown("#### Cumplimiento promedio por bodega")
        df_bodega = df.groupby("Bodega", as_index=False)["Cumplimiento"].mean().sort_values("Cumplimiento", ascending=False)

        fig_bar = px.bar(
            df_bodega,
            x="Bodega",
            y="Cumplimiento",
            text="Cumplimiento",
            color="Cumplimiento",
            color_continuous_scale="Blues"
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_bar.update_layout(
            height=500,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=25, r=25, t=40, b=25),
            font=dict(color="#1f2937")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### Tendencia histórica")
        fig_line = px.line(
            df.sort_values("Fecha"),
            x="Fecha",
            y="Cumplimiento",
            color="Bodega",
            markers=True
        )
        fig_line.update_layout(
            height=450,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=25, r=25, t=40, b=25),
            font=dict(color="#1f2937")
        )
        st.plotly_chart(fig_line, use_container_width=True)

        with st.expander("Ver histórico de inspecciones", expanded=False):
            st.dataframe(df.sort_values("Fecha", ascending=False), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)