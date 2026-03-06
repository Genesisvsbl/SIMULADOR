import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, time, timedelta
import json
import os
import uuid   # 👈 AGREGA ESTA LINEA

st.set_page_config(layout="wide")

# ================= INTERFAZ WMS =================
st.markdown("""
<style>

/* ===== FONDO GENERAL ===== */
.stApp {
    background-color: #f1f3f6;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background: #ffffff;
    border-right:1px solid #e1e6ef;
}

/* TEXTO SIDEBAR */
section[data-testid="stSidebar"] *{
    color:#2c3e50;
    font-weight:500;
}

/* ===== TITULOS ===== */
h1{
    color:#1f2d3d;
    font-weight:700;
}

h2,h3{
    color:#34495e;
}

/* ===== CONTENEDOR PRINCIPAL ===== */
.block-container{
    background:white;
    padding:2rem;
    border-radius:10px;
    border:1px solid #e6eaf0;
    box-shadow:0 2px 6px rgba(0,0,0,0.04);
}

/* BOTÓN PRINCIPAL */
.stButton>button{
    background-color:#020046;   /* azul marino oscuro */
    color:white;                /* texto blanco */
    border-radius:6px;
    border:none;
    padding:8px 18px;
    font-weight:600;
    transition:all 0.2s ease;
}

/* HOVER */
.stButton>button:hover{
    background-color:#010033;   /* un poco más oscuro */
    color:white;
    box-shadow:0 3px 8px rgba(0,0,0,0.25);
}

/* ===== INPUTS ===== */
input, textarea{
    border-radius:6px !important;
    border:1px solid #d9e0ea !important;
}

/* ===== TABLAS ===== */
[data-testid="stDataFrame"]{
    border:1px solid #e4e9f2;
    border-radius:8px;
}

/* ===== LABELS ===== */
label{
    font-weight:600;
    color:#2c3e50;
}

</style>
""", unsafe_allow_html=True)

# ================= CONFIG =================
MUELLES = ["Muelle 1", "Muelle 2", "Contingencia"]

CATALOGO = {
    "LATA": {"vh": "TRACTOCAMION-A", "min": 60},
    "TAPA LATA": {"vh": "SENCILLO-A", "min": 80},
    "AZUCAR": {"vh": "TRACTOCAMION-D", "min": 200},
    "PREFORMA": {"vh": "TRACTOCAMION-B", "min": 120},
    "TAPA PET": {"vh": "TRACTOCAMION-B", "min": 120},
    "QUIMICOS": {"vh": "SENCILLO-A", "min": 80},
    "ETIQUETA IGL": {"vh": "TRACTOCAMION-C", "min": 150},
    "TAPA CORONA": {"vh": "TRACTOCAMION-B", "min": 120},
    "PLASTICO": {"vh": "SENCILLO-A", "min": 80},
    "ETIQUETA PET": {"vh": "SENCILLO-A", "min": 80},
    "CARTON": {"vh": "SENCILLO-A", "min": 80},
    "CUARTO FRIO": {"vh": "SENCILLO-A", "min": 80},
    "PEGANTE": {"vh": "TRACTOCAMION-B", "min": 120},
    "TIERRA": {"vh": "TRACTOCAMION-B", "min": 120},
}

# ================= PERSISTENCIA =================
DATA_FILE = "simulador_data.json"

def serializar():
    return {
        "confirmadas": [
            {**c, "inicio": str(c["inicio"]), "fin": str(c["fin"])}
            for c in st.session_state.confirmadas
        ],
        "bloqueos": [
            {**b, "inicio": str(b["inicio"]), "fin": str(b["fin"])}
            for b in st.session_state.bloqueos
        ],
        "franjas": [
            {**f, "inicio": str(f["inicio"]), "fin": str(f["fin"])}
            for f in st.session_state.franjas
        ]
    }

def deserializar(data):
    st.session_state.confirmadas = [
        {**c,
         "inicio": datetime.strptime(c["inicio"], "%H:%M:%S").time(),
         "fin": datetime.strptime(c["fin"], "%H:%M:%S").time()}
        for c in data.get("confirmadas", [])
    ]
    st.session_state.bloqueos = [
        {**b,
         "inicio": datetime.strptime(b["inicio"], "%H:%M:%S").time(),
         "fin": datetime.strptime(b["fin"], "%H:%M:%S").time()}
        for b in data.get("bloqueos", [])
    ]
    st.session_state.franjas = [
        {**f,
         "inicio": datetime.strptime(f["inicio"], "%H:%M:%S").time(),
         "fin": datetime.strptime(f["fin"], "%H:%M:%S").time()}
        for f in data.get("franjas", [])
    ]

def guardar_datos():
    with open(DATA_FILE, "w") as f:
        json.dump(serializar(), f)
    st.success("Datos guardados correctamente")

def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            deserializar(data)

def reset_total():
    for k in [
        "necesidades",
        "confirmadas",
        "no_programadas",
        "bloqueos",
        "franjas",
        "ejecutados"
    ]:
        st.session_state[k] = []
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.success("Sistema reiniciado completamente")

# ================= SESSION =================
for k in [
    "necesidades",
    "confirmadas",
    "no_programadas",
    "bloqueos",
    "franjas",
    "franjas_inhabilitadas",
    "ejecutados"
]:
    if k not in st.session_state:
        st.session_state[k] = []

cargar_datos()

pagina = st.sidebar.radio(
    "FASES",
    ["📋 Fase 1 - Listado", "🛠 Fase 2 - Configuración", "📅 Fase 3 - Simulación", "📊 Fase 4 - Indicadores"]
)

st.sidebar.markdown("---")
if st.sidebar.button("💾 Guardar Todo"):
    guardar_datos()

if st.sidebar.button("🗑 Resetear TODO"):
    reset_total()

# ================= FASE 1 =================
if pagina == "📋 Fase 1 - Listado":

    st.title("Listado de Necesidades")

    if "necesidades" not in st.session_state:
        st.session_state.necesidades = []

    fecha = st.date_input("Fecha")

    st.markdown("### Seleccionar cantidades a agendar")

    materiales = list(CATALOGO.keys())

    col_izq, col_der = st.columns(2)
    mitad = len(materiales) // 2

    cantidades = {}

    # 🔹 Función muelle
    def muelle_por_material(mat):
        if mat == "LATA":
            return "Muelle 2"
        return "Muelle 1"

    # ---------------- IZQUIERDA ----------------
    with col_izq:
        for material in materiales[:mitad]:
            col1, col2 = st.columns([2,1])
            col1.write(f"**{material}**")
            cantidades[material] = col2.number_input(
                "Cant",
                min_value=0,
                step=1,
                key=f"cant_{material}"
            )

    # ---------------- DERECHA ----------------
    with col_der:
        for material in materiales[mitad:]:
            col1, col2 = st.columns([2,1])
            col1.write(f"**{material}**")
            cantidades[material] = col2.number_input(
                "Cant",
                min_value=0,
                step=1,
                key=f"cant_{material}"
            )

    # 🔥 BOTÓN ÚNICO
    st.divider()

    if st.button("🚀 Agregar Todo"):

        total_agregado = 0

        for material, cantidad in cantidades.items():

            if cantidad > 0:

                for _ in range(int(cantidad)):
                    st.session_state.necesidades.append({
                        "fecha": str(fecha),
                        "material": material,
                        "vh": CATALOGO[material]["vh"],
                        "duracion": CATALOGO[material]["min"],
                        "muelle": muelle_por_material(material)
                    })

                total_agregado += cantidad

        if total_agregado > 0:
            st.success(f"Se agregaron {total_agregado} necesidades correctamente ✅")
        else:
            st.warning("No se ingresaron cantidades")

    # ================= TABLA =================
    st.divider()

    if st.session_state.necesidades:

        st.dataframe(
            pd.DataFrame(st.session_state.necesidades),
            use_container_width=True
        )

        if st.button("🗑 Limpiar listado"):
            st.session_state.necesidades = []
            st.success("Listado limpiado")
# ================= FASE 2 =================
if pagina == "🛠 Fase 2 - Configuración":

    st.title("Configuración de Franjas y Bloqueos")

    # ================= FRANJAS =================
    st.subheader("Franja Operativa")

    fecha_franja = st.date_input("Fecha franja")
    muelle_franja = st.selectbox("Muelle franja", MUELLES, key="muelle_franja")

    c1, c2 = st.columns(2)
    inicio = c1.time_input("Inicio franja", time(6, 0), key="ini_franja")
    fin = c2.time_input("Fin franja", time(23, 59), key="fin_franja")

    if st.button("Guardar franja", key="btn_guardar_franja"):

        fecha_str = str(fecha_franja)
        existe = False

        for f in st.session_state.franjas:
            if f["fecha"] == fecha_str and f["muelle"] == muelle_franja:
                f["inicio"] = inicio
                f["fin"] = fin
                existe = True
                break

        if not existe:
            st.session_state.franjas.append({
                "fecha": fecha_str,
                "muelle": muelle_franja,
                "inicio": inicio,
                "fin": fin
            })

        guardar_datos()
        st.success(f"Franja guardada/actualizada para {muelle_franja}")

    if st.session_state.franjas:

        ocultar_franjas = st.checkbox(
            "Ocultar franjas guardadas",
            value=True,
            key="chk_ocultar_franjas"
        )

        if not ocultar_franjas:
            st.markdown("### Franjas Guardadas")
            st.dataframe(pd.DataFrame(st.session_state.franjas), use_container_width=True)

    st.markdown("---")

    # ================= BLOQUEOS =================
    st.subheader("Bloqueos")

    mu_b = st.selectbox("Muelle del bloqueo", MUELLES, key="muelle_bloq")
    fecha_bloqueo = st.date_input("Fecha bloqueo", key="fecha_bloq")

    c3, c4 = st.columns(2)
    bi = c3.time_input("Inicio bloqueo", key="ini_bloq")
    bf = c4.time_input("Fin bloqueo", key="fin_bloq")
    motivo = st.text_input("Motivo", key="motivo_bloq")

    def agregar_bloqueo(inicio_b, fin_b, motivo_b):
        st.session_state.bloqueos.append({
            "fecha": str(fecha_bloqueo),
            "inicio": inicio_b,
            "fin": fin_b,
            "motivo": motivo_b,
            "muelle": mu_b
        })
        guardar_datos()
        st.success(f"Bloqueo agregado SOLO para {mu_b}")

    if st.button("Agregar bloqueo personalizado", key="btn_add_bloq"):
        agregar_bloqueo(bi, bf, motivo)

    st.markdown("### Bloqueos rápidos")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Ruta/Reunión 7:30–8:30", key="b1"):
        agregar_bloqueo(time(7, 30), time(8, 30), "Ruta/Reunión")

    if col2.button("Tanqueo 6:00–6:30", key="b2"):
        agregar_bloqueo(time(6, 0), time(6, 30), "Tanqueo")

    if col3.button("Ruta 2 15:30–16:30", key="b3"):
        agregar_bloqueo(time(15, 30), time(16, 30), "Ruta 2")

    if col4.button("Tanqueo 18:00–18:30", key="b4"):
        agregar_bloqueo(time(18, 0), time(18, 30), "Tanqueo Tarde")

    # ================= VER / EDITAR BLOQUEOS =================
    if st.session_state.bloqueos:

        ocultar_bloqueos = st.checkbox(
            "Ocultar bloqueos guardados",
            value=True,
            key="chk_ocultar_bloqueos"
        )

        if not ocultar_bloqueos:

            st.markdown("### Bloqueos Guardados")

            df_bloq = pd.DataFrame(st.session_state.bloqueos)
            st.dataframe(df_bloq, use_container_width=True)

            st.markdown("### Editar / Eliminar")

            idx = st.number_input(
                "Número de bloqueo (fila)",
                min_value=0,
                max_value=len(st.session_state.bloqueos) - 1,
                step=1,
                key="idx_bloqueo"
            )

            b_sel = st.session_state.bloqueos[idx]

            e1, e2 = st.columns(2)
            nuevo_inicio = e1.time_input(
                "Nuevo inicio",
                b_sel["inicio"],
                key=f"edit_ini_{idx}"
            )
            nuevo_fin = e2.time_input(
                "Nuevo fin",
                b_sel["fin"],
                key=f"edit_fin_{idx}"
            )
            nuevo_motivo = st.text_input(
                "Nuevo motivo",
                b_sel["motivo"],
                key=f"edit_motivo_{idx}"
            )

            c1, c2 = st.columns(2)

            if c1.button("Actualizar bloqueo", key=f"btn_upd_{idx}"):

                st.session_state.bloqueos[idx]["inicio"] = nuevo_inicio
                st.session_state.bloqueos[idx]["fin"] = nuevo_fin
                st.session_state.bloqueos[idx]["motivo"] = nuevo_motivo

                guardar_datos()
                st.success("Bloqueo actualizado")

            if c2.button("Eliminar bloqueo", key=f"btn_del_{idx}"):

                st.session_state.bloqueos.pop(idx)

                guardar_datos()
                st.warning("Bloqueo eliminado")


# ================= FUNCIONES =================
def conflicto(fecha, ini, fin, muelle):

    # 🔵 FRANJA
    for f in st.session_state.franjas:
        if f["fecha"] == fecha and f["muelle"] == muelle:
            if ini < f["inicio"] or fin > f["fin"]:
                return True

    # 🟢 CITAS
    for c in st.session_state.confirmadas:
        if c["fecha"] == fecha and c["muelle"] == muelle:
            if not (fin <= c["inicio"] or ini >= c["fin"]):
                return True

    # 🔴 BLOQUEOS
    for b in st.session_state.bloqueos:
        if b["fecha"] == fecha and b["muelle"] == muelle:
            if not (fin <= b["inicio"] or ini >= b["fin"]):
                return True

    return False#
# ================= FILTROS DEFAULT =================
if "filtro_muelle" not in st.session_state:
    st.session_state.filtro_muelle = "Todos"

filtro_muelle = st.session_state.filtro_muelle

# ================= FASE 3 ================= 
if pagina == "📅 Fase 3 - Simulación":

    st.title("📅 Simulación")

    # ================= TABLA =================
    st.divider()
    st.header("📋 Gestión de citas")

    ocultar_tabla = st.checkbox("Ocultar citas confirmadas en tabla", value=True)

    if st.session_state.confirmadas:

        if ocultar_tabla:
            st.info("Tabla oculta — activa el checkbox para editar o eliminar")

        else:
            df_tabla = pd.DataFrame(st.session_state.confirmadas)
            st.dataframe(df_tabla[["id", "title"]], use_container_width=True)

            id_delete = st.number_input("ID", min_value=1, step=1)

            if st.button("Eliminar cita"):

                antes = len(st.session_state.confirmadas)

                st.session_state.confirmadas = [
                    c for c in st.session_state.confirmadas
                    if int(c["id"]) != id_delete
                ]

                if len(st.session_state.confirmadas) < antes:
                    for i, c in enumerate(st.session_state.confirmadas, start=1):
                        c["id"] = i

                    guardar_datos()
                    st.rerun()

            if st.button("Eliminar TODAS las citas"):
                st.session_state.confirmadas = []
                guardar_datos()
                st.rerun()

    # ================= CONFIG =================
    st.divider()
    st.header("⚙️ Configuración")

    if "fecha_vista" not in st.session_state:
        st.session_state.fecha_vista = datetime.today().date()

    f1, f2, f3, f4 = st.columns(4)

    filtro_muelle = f1.selectbox("Muelle", ["Todos"] + MUELLES)
    filtro_material = f2.selectbox("Material", ["Todos"] + list(CATALOGO.keys()))
    vista = f3.selectbox("Vista", ["timeGridWeek", "timeGridDay"])

    st.session_state.fecha_vista = f4.date_input(
        "Fecha vista",
        value=st.session_state.fecha_vista
    )

    # ================= SIMULACIÓN =================
    if st.button("Ejecutar Simulación"):

        # ✅ JORNADA OPERATIVA FIJA PARA TODOS LOS MUELLES
        JORNADA_INICIO = time(6, 0)
        JORNADA_FIN = time(22, 0)

        def obtener_franja(fecha_str, muelle):
            f = next(
                (x for x in st.session_state.franjas
                 if x["fecha"] == fecha_str and x["muelle"] == muelle),
                None
            )
            if f:
                return f
            return {"inicio": JORNADA_INICIO, "fin": JORNADA_FIN}

        st.session_state.no_programadas = []
        estrategia = "Normal"

        ordenadas = sorted(
            st.session_state.necesidades,
            key=lambda x: x["duracion"]
        )

        # -------- ASIGNACIÓN BASE (SOLO EN SU MUELLE) --------
        for nec in ordenadas:

            fecha_str = nec["fecha"]
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            dur = nec["duracion"]
            muelle = nec["muelle"]

            asignado = False

            franja = obtener_franja(fecha_str, muelle)
            inicio_dt = datetime.combine(fecha_dt, franja["inicio"])
            fin_franja = datetime.combine(fecha_dt, franja["fin"])

            while inicio_dt + timedelta(minutes=dur) <= fin_franja:

                fin_dt = inicio_dt + timedelta(minutes=dur)

                if not conflicto(fecha_str, inicio_dt.time(), fin_dt.time(), muelle):

                    st.session_state.confirmadas.append({
                        "id": len(st.session_state.confirmadas) + 1,
                        "title": nec["material"],
                        "start": inicio_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                        "end": fin_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                        "fecha": fecha_str,
                        "inicio": inicio_dt.time(),
                        "fin": fin_dt.time(),
                        "muelle": muelle
                    })

                    asignado = True
                    break

                inicio_dt += timedelta(minutes=5)

            if not asignado:
                st.session_state.no_programadas.append(nec)

        # -------- BALANCEO POR HORA DE FINALIZACIÓN (NIVELAR M1 vs CONT Y TERMINAR MÁS TEMPRANO) --------
        # ✅ Reglas:
        # - Si M2 tiene citas: Contingencia solo puede operar desde fin_m2
        # - Si M2 NO tiene nada: Contingencia puede operar desde 06:00 (balance M1 vs Cont)
        # - Respeta SIEMPRE bloqueos/franjas/citas (conflicto y conflicto_excluyendo)
        # - Balanceo bidireccional: puede mover M1 -> Cont o Cont -> M1 si reduce el FIN MÁXIMO del sistema (makespan)
        muelle_m1 = "Muelle 1"
        muelle_m2 = "Muelle 2"
        muelle_cont = "Contingencia"

        fechas_unicas = list(set([c["fecha"] for c in st.session_state.confirmadas] + [n["fecha"] for n in st.session_state.no_programadas]))

        for fecha_str in fechas_unicas:

            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()

            def citas_muelle(muelle):
                return sorted(
                    [c for c in st.session_state.confirmadas if c["fecha"] == fecha_str and c["muelle"] == muelle],
                    key=lambda x: x["inicio"]
                )

            def ultima_hora(muelle):
                horas = [c["fin"] for c in citas_muelle(muelle)]
                return max(horas) if horas else None

            # ✅ base Contingencia según escenario (M2 manda)
            fin_m2 = ultima_hora(muelle_m2)
            base_cont_dt = datetime.combine(fecha_dt, fin_m2) if fin_m2 else datetime.combine(fecha_dt, time(6, 0))

            # ---- conflicto local que EXCLUYE una cita (para poder reubicarla sin chocar consigo misma) ----
            def conflicto_excluyendo(fecha, ini, fin, muelle, excluir_id):

                # FRANJA (si existe); si no, jornada por defecto
                fr_ok = False
                for f in st.session_state.franjas:
                    if f["fecha"] == fecha and f["muelle"] == muelle:
                        fr_ok = True
                        if ini < f["inicio"] or fin > f["fin"]:
                            return True
                        break
                if not fr_ok:
                    if ini < time(6, 0) or fin > time(22, 0):
                        return True

                # CITAS (excepto la que estoy moviendo)
                for c in st.session_state.confirmadas:
                    if c["fecha"] == fecha and c["muelle"] == muelle and int(c["id"]) != int(excluir_id):
                        if not (fin <= c["inicio"] or ini >= c["fin"]):
                            return True

                # BLOQUEOS
                for b in st.session_state.bloqueos:
                    if b["fecha"] == fecha and b["muelle"] == muelle:
                        if not (fin <= b["inicio"] or ini >= b["fin"]):
                            return True

                return False

            # ✅ buscar el PRIMER slot factible (desde un inicio_base) para reubicar una cita
            def primer_slot_disponible_excluyendo(muelle, inicio_base_dt, duracion_min, excluir_id):

                franja = obtener_franja(fecha_str, muelle)

                inicio_dt = max(datetime.combine(fecha_dt, franja["inicio"]), inicio_base_dt)
                fin_franja = datetime.combine(fecha_dt, franja["fin"])

                while inicio_dt + timedelta(minutes=duracion_min) <= fin_franja:

                    fin_dt = inicio_dt + timedelta(minutes=duracion_min)

                    if not conflicto_excluyendo(fecha_str, inicio_dt.time(), fin_dt.time(), muelle, excluir_id):
                        return inicio_dt, fin_dt

                    inicio_dt += timedelta(minutes=5)

                return None, None

            # ✅ 0) Si hay NO_PROGRAMADAS de M1, intentar programarlas en CONT o M1 con criterio de "terminar más temprano"
            #     (CONT solo desde base_cont_dt)
            pendientes = [n for n in st.session_state.no_programadas if n["fecha"] == fecha_str and n["muelle"] == muelle_m1]
            pendientes = sorted(pendientes, key=lambda x: x["duracion"])
            rescatadas = []

            for nec in pendientes:

                dur = nec["duracion"]

                # intentos: primero M1 (si cabe), luego Cont (si cabe desde base)
                mejores = []

                # intento M1
                ini1, fin1 = primer_slot_disponible_excluyendo(muelle_m1, datetime.combine(fecha_dt, time(6, 0)), dur, excluir_id=-999999)
                if ini1 is not None:
                    fin_m1_actual = ultima_hora(muelle_m1)
                    fin_cont_actual = ultima_hora(muelle_cont)
                    fin_m1_nuevo = fin1.time() if (not fin_m1_actual or fin1.time() > fin_m1_actual) else fin_m1_actual
                    max_fin = max([x for x in [fin_m1_nuevo, fin_cont_actual] if x] + [time(0, 0)])
                    mejores.append(("Muelle 1", ini1, fin1, max_fin))

                # intento Cont
                inic, finc = primer_slot_disponible_excluyendo(muelle_cont, base_cont_dt, dur, excluir_id=-999999)
                if inic is not None:
                    fin_m1_actual = ultima_hora(muelle_m1)
                    fin_cont_actual = ultima_hora(muelle_cont)
                    fin_cont_nuevo = finc.time() if (not fin_cont_actual or finc.time() > fin_cont_actual) else fin_cont_actual
                    max_fin = max([x for x in [fin_m1_actual, fin_cont_nuevo] if x] + [time(0, 0)])
                    mejores.append(("Contingencia", inic, finc, max_fin))

                if not mejores:
                    continue

                # elegir opción que minimiza el max(fin_m1, fin_cont)
                mejores.sort(key=lambda x: (x[3].hour, x[3].minute))
                mu_sel, ini_sel, fin_sel, _ = mejores[0]

                st.session_state.confirmadas.append({
                    "id": len(st.session_state.confirmadas) + 1,
                    "title": nec["material"],
                    "start": ini_sel.strftime("%Y-%m-%dT%H:%M:%S"),
                    "end": fin_sel.strftime("%Y-%m-%dT%H:%M:%S"),
                    "fecha": fecha_str,
                    "inicio": ini_sel.time(),
                    "fin": fin_sel.time(),
                    "muelle": mu_sel
                })
                rescatadas.append(nec)

            if rescatadas:
                st.session_state.no_programadas = [n for n in st.session_state.no_programadas if n not in rescatadas]

            # ✅ 1) BALANCEO BIDIRECCIONAL POR MAKESPAN
            # Mover la última cita del muelle que termina más tarde hacia el otro muelle,
            # aceptando SOLO si reduce el max(fin_m1, fin_cont). Repetir hasta no mejorar.
            mejora = True
            while mejora:

                fin_m1 = ultima_hora(muelle_m1)
                fin_cont = ultima_hora(muelle_cont)

                # si uno está vacío, igual sigue intentando (para adelantar el máximo)
                fin_max_actual = max([x for x in [fin_m1, fin_cont] if x] + [time(0, 0)])

                # decidir cuál muelle está "más tarde"
                # si cont no tiene nada, intenta mover desde m1 -> cont (si ayuda)
                # si m1 no tiene nada, intenta mover desde cont -> m1 (si ayuda)
                if fin_cont and (not fin_m1 or fin_cont > fin_m1):
                    origen = muelle_cont
                    destino = muelle_m1
                    inicio_base_dest = datetime.combine(fecha_dt, time(6, 0))  # M1 desde 06:00
                else:
                    origen = muelle_m1
                    destino = muelle_cont
                    inicio_base_dest = base_cont_dt  # CONT desde fin_m2 o 06:00

                citas_origen = sorted(citas_muelle(origen), key=lambda x: x["fin"], reverse=True)
                if not citas_origen:
                    break

                c = citas_origen[0]

                duracion = int(
                    (
                        datetime.combine(fecha_dt, c["fin"]) -
                        datetime.combine(fecha_dt, c["inicio"])
                    ).total_seconds() / 60
                )

                ini_new, fin_new = primer_slot_disponible_excluyendo(destino, inicio_base_dest, duracion, excluir_id=c["id"])
                if ini_new is None:
                    mejora = False
                    break

                # ✅ calcular fin del ORIGEN después de sacar esa cita (SIN None)
                fins_restantes = [
                    x["fin"] for x in citas_muelle(origen)
                    if int(x["id"]) != int(c["id"])
                ]
                fin_origen_nuevo = max(fins_restantes) if fins_restantes else None

                fin_destino_actual = ultima_hora(destino)
                fin_destino_nuevo = fin_new.time() if (not fin_destino_actual or fin_new.time() > fin_destino_actual) else fin_destino_actual

                # max entre M1 y CONT después del movimiento
                if origen == muelle_m1:
                    fin_m1_new = fin_origen_nuevo
                    fin_cont_new = fin_destino_nuevo
                else:
                    fin_cont_new = fin_origen_nuevo
                    fin_m1_new = fin_destino_nuevo

                fin_max_nuevo = max([x for x in [fin_m1_new, fin_cont_new] if x] + [time(0, 0)])

                # aceptar solo si reduce la hora máxima de terminación
                if fin_max_nuevo < fin_max_actual:

                    c["muelle"] = destino
                    c["inicio"] = ini_new.time()
                    c["fin"] = fin_new.time()
                    c["start"] = ini_new.strftime("%Y-%m-%dT%H:%M:%S")
                    c["end"] = fin_new.strftime("%Y-%m-%dT%H:%M:%S")

                else:
                    mejora = False

        st.session_state.necesidades = []
        guardar_datos()
        st.rerun()
# ================= REPROGRAMACIÓN =================
    if st.session_state.no_programadas:

        st.error("No caben en capacidad — puedes reprogramar")

        mReprog = st.selectbox("Muelle destino", MUELLES)
        fecha_reprog = st.date_input("Nueva fecha")

        if st.button("Reprogramar todo"):

            pendientes = st.session_state.no_programadas.copy()
            st.session_state.no_programadas = []

            for nec in pendientes:

                dur = nec["duracion"]
                muelle = mReprog

                inicio_dt = datetime.combine(fecha_reprog, time(6, 0))
                fin_franja = datetime.combine(fecha_reprog, time(22, 0))
                fecha_str = fecha_reprog.strftime("%Y-%m-%d")

                while inicio_dt + timedelta(minutes=dur) <= fin_franja:

                    fin_dt = inicio_dt + timedelta(minutes=dur)

                    if not conflicto(fecha_str, inicio_dt.time(), fin_dt.time(), muelle):

                        st.session_state.confirmadas.append({
                            "id": len(st.session_state.confirmadas) + 1,
                            "title": nec["material"],
                            "start": inicio_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                            "end": fin_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                            "fecha": fecha_str,
                            "inicio": inicio_dt.time(),
                            "fin": fin_dt.time(),
                            "muelle": muelle
                        })
                        break

                    inicio_dt += timedelta(minutes=5)

            guardar_datos()
            st.rerun()

    # ================= CALENDARIO =================
    st.divider()
    st.header("📅 Calendario")

    eventos = []

    for c in st.session_state.confirmadas:
        if filtro_muelle != "Todos" and c["muelle"] != filtro_muelle:
            continue

        eventos.append({
            "id": c["id"],
            "title": f"🆔{c['id']} | {c['title']} | {c['muelle']}",
            "start": c["start"],
            "end": c["end"],
            "color": "green"
        })

    for b in st.session_state.bloqueos:
        if filtro_muelle != "Todos" and b["muelle"] != filtro_muelle:
            continue

        fecha_dt = datetime.strptime(b["fecha"], "%Y-%m-%d")

        eventos.append({
            "title": f"🚫 {b['motivo']} • {b['muelle']}",
            "start": datetime.combine(fecha_dt, b["inicio"]).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": datetime.combine(fecha_dt, b["fin"]).strftime("%Y-%m-%dT%H:%M:%S"),
            "color": "red"
        })

    for f in st.session_state.franjas:
        if filtro_muelle != "Todos" and f["muelle"] != filtro_muelle:
            continue

        fecha_dt = datetime.strptime(f["fecha"], "%Y-%m-%d")

        eventos.append({
            "title": f"⛔ Fuera horario • {f['muelle']}",
            "start": datetime.combine(fecha_dt, time(0, 0)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": datetime.combine(fecha_dt, f["inicio"]).strftime("%Y-%m-%dT%H:%M:%S"),
            "backgroundColor": "#E0E0E0",
            "display": "block"
        })

        eventos.append({
            "title": f"⛔ Fuera horario • {f['muelle']}",
            "start": datetime.combine(fecha_dt, f["fin"]).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": datetime.combine(fecha_dt, time(23, 59)).strftime("%Y-%m-%dT%H:%M:%S"),
            "backgroundColor": "#E0E0E0",
            "display": "block"
        })

    calendar(
        events=eventos,
        options={
            "initialView": vista,
            "initialDate": st.session_state.fecha_vista.strftime("%Y-%m-%d"),
            "timeZone": "local",
            "slotMinTime": "06:00:00",
            "slotMaxTime": "22:00:00",
            "editable": True,
            "allDaySlot": False,
            "nowIndicator": True
        }
    )
# ================= FASE 4 =================
if pagina == "📊 Fase 4 - Indicadores":

    st.title("📊 Indicadores Operativos")

    # 🔹 Estado persistente del reporte
    if "reporte_generado" not in st.session_state:
        st.session_state.reporte_generado = False

    # 🔹 Botón que activa el reporte
    if st.button("📊 Generar reporte diario"):
        st.session_state.reporte_generado = True

    # 🔹 Todo el bloque del reporte va dentro de esta condición
    if st.session_state.reporte_generado:


        from datetime import datetime, time
        import pandas as pd
        import plotly.express as px

        JORNADA_INICIO = time(6,0)
        JORNADA_FIN = time(22,0)

        fechas = sorted(list(set(c["fecha"] for c in st.session_state.confirmadas)))

        data = {}

        for fecha_str in fechas:

            fecha_dt = datetime.strptime(fecha_str,"%Y-%m-%d")

            citas_dia = [
                c for c in st.session_state.confirmadas
                if c["fecha"] == fecha_str
            ]

            jornada_min = (
                datetime.combine(fecha_dt,JORNADA_FIN) -
                datetime.combine(fecha_dt,JORNADA_INICIO)
            ).total_seconds()/60

            # ================= MUELLE 1 =================
            m1 = sorted(
                [c for c in citas_dia if c["muelle"]=="Muelle 1"],
                key=lambda x:x["inicio"]
            )

            if m1:
                ini = m1[0]["inicio"]
                fin = max(c["fin"] for c in m1)
                op = (datetime.combine(fecha_dt,fin) -
                      datetime.combine(fecha_dt,ini)).total_seconds()/60
            else:
                op = 0

            ocio = jornada_min - op
            util = op / jornada_min if jornada_min > 0 else 0

            data.setdefault("Muelle 1", {})[(fecha_str,"Tiempo Op")] = round(op/60,2)
            data.setdefault("Muelle 1", {})[(fecha_str,"Tiempo Oc")] = round(ocio/60,2)
            data.setdefault("Muelle 1", {})[(fecha_str,"% Util")] = util

            # ================= MUELLE 2 + CONTINGENCIA =================
            linea = sorted(
                [c for c in citas_dia if c["muelle"] in ["Muelle 2","Contingencia"]],
                key=lambda x:x["inicio"]
            )

            if linea:
                ini = linea[0]["inicio"]
                fin = max(c["fin"] for c in linea)
                op = (datetime.combine(fecha_dt,fin) -
                      datetime.combine(fecha_dt,ini)).total_seconds()/60
            else:
                op = 0

            ocio = jornada_min - op
            util = op / jornada_min if jornada_min > 0 else 0

            data.setdefault("Muelle 2", {})[(fecha_str,"Tiempo Op")] = round(op/60,2)
            data.setdefault("Muelle 2", {})[(fecha_str,"Tiempo Oc")] = round(ocio/60,2)
            data.setdefault("Muelle 2", {})[(fecha_str,"% Util")] = util

        df = pd.DataFrame(data).T

        # ================= ORDEN COLUMNAS =================
        columnas_ordenadas = []
        for fecha in fechas:
            columnas_ordenadas += [
                (fecha,"Tiempo Op"),
                (fecha,"Tiempo Oc"),
                (fecha,"% Util")
            ]

        df = df[columnas_ordenadas]

        # ================= TOTAL =================
        fila_total = {}
        for col in df.columns:
            if col[1] == "% Util":
                fila_total[col] = df[col].mean()
            else:
                fila_total[col] = df[col].sum()

        df.loc["TOTAL"] = fila_total

        # ================= ALERTAS =================
        alertas = []
        for fecha in fechas:
            util_m2 = df.loc["Muelle 2"][(fecha,"% Util")]
            if util_m2 >= 0.9:
                alertas.append(f"🚨 {fecha} saturación en Muelle 2")

        if alertas:
            st.error(" | ".join(alertas))
        else:
            st.success("Sin saturaciones críticas 👍")

        # ================= REPORTE CALENDARIO =================
        st.subheader("📅 Reporte tipo calendario")

        def color_util(val):
            if isinstance(val,(int,float)):
                if val >= 0.85:
                    return "background-color:#ffb3b3"
                elif val >= 0.65:
                    return "background-color:#fff2cc"
                else:
                    return "background-color:#ccffcc"
            return ""

        styled = (
            df.style
            .format({col: "{:.1%}" for col in df.columns if col[1]=="% Util"})
            .applymap(
                color_util,
                subset=pd.IndexSlice[:, df.columns.get_level_values(1)=="% Util"]
            )
        )

        st.dataframe(styled, use_container_width=True)

        # ================= GRAFICAS OPERATIVAS =================
        st.markdown("## 📊 Gráficas Operativas por Muelle")

        df_plot = df.copy().drop("TOTAL", errors="ignore")

        for muelle in df_plot.index:

            st.markdown(f"### 🚚 {muelle}")

            fechas_plot, util_plot, op_plot, oc_plot = [],[],[],[]

            for fecha in fechas:
                fechas_plot.append(fecha)
                util_plot.append(df_plot.loc[muelle][(fecha,"% Util")])
                op_plot.append(df_plot.loc[muelle][(fecha,"Tiempo Op")])
                oc_plot.append(df_plot.loc[muelle][(fecha,"Tiempo Oc")])

            fig_util = px.line(
                x=fechas_plot,
                y=util_plot,
                markers=True,
                title=f"Utilización {muelle}"
            )
            fig_util.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_util,use_container_width=True)

            df_bar = pd.DataFrame({
                "Fecha": fechas_plot,
                "Operativo": op_plot,
                "Ocio": oc_plot
            })

            fig_bar = px.bar(
                df_bar,
                x="Fecha",
                y=["Operativo","Ocio"],
                barmode="group",
                title=f"Tiempo Operativo vs Ocio — {muelle}"
            )

            st.plotly_chart(fig_bar,use_container_width=True)

        # ================= KPI OEE LOGÍSTICO =================
        st.divider()
        st.subheader("⚙️ KPI OEE Logístico")

        oee_data = {}
        resumen_fin_operacion = {}

        for fecha_str in fechas:

            fecha_dt = datetime.strptime(fecha_str,"%Y-%m-%d")

            jornada_min = (
                datetime.combine(fecha_dt,JORNADA_FIN) -
                datetime.combine(fecha_dt,JORNADA_INICIO)
            ).total_seconds()/60

            # ================= DEFINICIÓN DE LÍNEAS =================
            lineas = {
                "Muelle 1": ["Muelle 1"],
                "Muelle 2 + Contingencia": ["Muelle 2","Contingencia"]
            }

            for nombre_linea, muelles_asociados in lineas.items():

                # ================= CITAS =================
                citas = [
                    c for c in st.session_state.confirmadas
                    if c["fecha"] == fecha_str and
                    c["muelle"] in muelles_asociados
                ]

                if citas:
                    ini = min(c["inicio"] for c in citas)
                    fin = max(c["fin"] for c in citas)

                    op = (
                        datetime.combine(fecha_dt,fin) -
                        datetime.combine(fecha_dt,ini)
                    ).total_seconds()/60

                    hora_fin_operacion = fin.strftime("%H:%M")

                else:
                    op = 0
                    hora_fin_operacion = "Sin operación"

                # Guardamos hora fin por día
                resumen_fin_operacion.setdefault(fecha_str,{})
                resumen_fin_operacion[fecha_str][nombre_linea] = hora_fin_operacion

                # ================= BLOQUEOS =================
                if "bloqueos" in st.session_state:
                    bloqueos = [
                        b for b in st.session_state.bloqueos
                        if b["fecha"] == fecha_str and
                        b["muelle"] in muelles_asociados
                    ]
                else:
                    bloqueos = []

                tiempo_bloq = sum(
                    (
                        datetime.combine(fecha_dt,b["fin"]) -
                        datetime.combine(fecha_dt,b["inicio"])
                    ).total_seconds()/60
                    for b in bloqueos
                )

                # ================= CÁLCULOS OEE =================
                disponible = max(jornada_min - tiempo_bloq, 0)

                disponibilidad = disponible / jornada_min if jornada_min > 0 else 0
                rendimiento = op / disponible if disponible > 0 else 0
                utilizacion = op / jornada_min if jornada_min > 0 else 0

                oee = disponibilidad * rendimiento * utilizacion

                oee_data.setdefault(nombre_linea,{})[(fecha_str,"Disponibilidad")] = disponibilidad
                oee_data.setdefault(nombre_linea,{})[(fecha_str,"Rendimiento")] = rendimiento
                oee_data.setdefault(nombre_linea,{})[(fecha_str,"Utilización")] = utilizacion
                oee_data.setdefault(nombre_linea,{})[(fecha_str,"OEE")] = oee

        df_oee = pd.DataFrame(oee_data).T

        col_ord = []
        for fecha in fechas:
            col_ord += [
                (fecha,"Disponibilidad"),
                (fecha,"Rendimiento"),
                (fecha,"Utilización"),
                (fecha,"OEE")
            ]

        df_oee = df_oee[col_ord]

        def color_oee(v):
            if isinstance(v,(int,float)):
                if v >= 0.75:
                    return "background-color:#c6efce"
                elif v >= 0.5:
                    return "background-color:#fff2cc"
                else:
                    return "background-color:#ffc7ce"
            return ""

        styled_oee = df_oee.style.format("{:.1%}").applymap(color_oee)

        st.dataframe(styled_oee, use_container_width=True)

        # ================= FINALIZACIÓN OPERATIVA (GUARDADO + HISTÓRICO) =================
        st.divider()
        st.subheader("🕓 Finalización Operativa Diaria")

        # 🔹 Inicializar almacenamiento si no existe
        if "finalizaciones" not in st.session_state:
            st.session_state.finalizaciones = {}

        # 🔹 Selector de fecha
        fecha_sel = st.selectbox(
            "Seleccionar fecha",
            fechas
        )

        fecha_dt = datetime.strptime(fecha_sel,"%Y-%m-%d")

        citas_dia = [
            c for c in st.session_state.confirmadas
            if c["fecha"] == fecha_sel
        ]

        if citas_dia:
            hora_teorica = max(c["fin"] for c in citas_dia)
            hora_teorica_str = hora_teorica.strftime("%H:%M")
        else:
            hora_teorica = None
            hora_teorica_str = "Sin operación"

        # ================= MOSTRAR FINAL TEÓRICO =================
        st.metric("Final Teórico", hora_teorica_str)

        # ================= FORMULARIO (EVITA RELOAD AUTOMÁTICO) =================
        with st.form(key=f"form_finalizacion_{fecha_sel}"):

            hora_real = st.time_input(
                "Final Real",
                key=f"hora_real_{fecha_sel}"
            )

            guardar = st.form_submit_button("💾 Guardar")

            if guardar and hora_teorica:

                hora_teorica_dt = datetime.combine(fecha_dt,hora_teorica)
                hora_real_dt = datetime.combine(fecha_dt,hora_real)

                desviacion_min = (
                    hora_real_dt - hora_teorica_dt
                ).total_seconds()/60

                st.session_state.finalizaciones[fecha_sel] = {
                    "Final Teórico": hora_teorica_str,
                    "Final Real": hora_real.strftime("%H:%M"),
                    "Desviación (min)": round(desviacion_min,1)
                }

                st.success("Registro guardado correctamente ✅")

        # ================= MOSTRAR INDICADOR SOLO SI YA EXISTE REGISTRO =================
        if fecha_sel in st.session_state.finalizaciones:

            desviacion_min = st.session_state.finalizaciones[fecha_sel]["Desviación (min)"]

            if desviacion_min <= 0:
                color = "#d4edda"
                texto = "🟢 Operación dentro o mejor que lo simulado"
            elif desviacion_min <= 60:
                color = "#fff3cd"
                texto = "🟡 Ligera desviación operacional"
            else:
                color = "#f8d7da"
                texto = "🔴 Desviación crítica operativa"

            st.markdown(
                f"""
                <div style="
                    background-color:{color};
                    padding:15px;
                    border-radius:10px;
                    font-weight:bold;
                    text-align:center;
                ">
                    {texto}
                </div>
                """,
                unsafe_allow_html=True
            )

        # ================= TABLA HISTÓRICA =================
        if st.session_state.finalizaciones:

            st.markdown("### 📊 Histórico Finalización Operativa")

            df_final = pd.DataFrame(st.session_state.finalizaciones).T
            df_final = df_final.sort_index()

            def color_hist(v):
                if isinstance(v,(int,float)):
                    if v <= 0:
                        return "background-color:#c6efce"
                    elif v <= 60:
                        return "background-color:#fff2cc"
                    else:
                        return "background-color:#ffc7ce"
                return ""

            styled_hist = (
                df_final.style
                .applymap(color_hist, subset=["Desviación (min)"])
            )

            st.dataframe(styled_hist, use_container_width=True)
        # ================= EXPORTAR =================
        df_export=df.copy()
        df_export.to_excel("reporte_operacion.xlsx")

        with open("reporte_operacion.xlsx","rb") as f:
            st.download_button(
                "📥 Descargar Excel",
                data=f,
                file_name="reporte_operacion.xlsx"
            )