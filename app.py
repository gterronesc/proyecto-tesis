"""
app.py
======
Interfaz de usuario (Streamlit). Reemplaza al front-end Angular de la v4,
segun lo definido en el resumen v5. Corre en el mismo proceso Python que
la logica del sistema (Modulo 1 y Modulo 2, via services/ia_predictor.py).

Correr con:  streamlit run app.py
"""

import os

import streamlit as st

# IMPORTANTE: esto tiene que ir ANTES de importar services.registro_service,
# porque ese modulo lee las credenciales de MySQL de las variables de
# entorno en el momento en que se importa. En Streamlit Community Cloud,
# las credenciales se configuran en el panel "Secrets" (no en el codigo),
# y aqui simplemente las copiamos a variables de entorno para que
# registro_service.py las encuentre igual que en local con XAMPP.
try:
    for _clave in ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_SSL_CA"):
        if _clave in st.secrets:
            os.environ[_clave] = str(st.secrets[_clave])
except Exception:
    # En local, si no existe .streamlit/secrets.toml, st.secrets tira error.
    # No pasa nada: registro_service.py cae en los defaults de XAMPP.
    pass

from services.metrado_service import EntradaMetrado, ALTURA_MURO_DEFECTO_M
from services.ia_predictor import obtener_metrado
from services.registro_service import guardar_registro, inicializar_base_datos

st.set_page_config(page_title="Estimador de materiales - Vivienda Piura", page_icon="🏗️")

# Crea la base de datos y la tabla 'registros_uso' si todavia no existen.
# @st.cache_resource hace que esto corra una sola vez (no en cada recarga
# de la pagina). Si falla (por ejemplo, credenciales no configuradas todavia
# en Secrets), no rompe la app: solo se mostrara un aviso.
@st.cache_resource
def _preparar_base_datos():
    try:
        inicializar_base_datos()
        return True
    except Exception as e:
        return str(e)

_resultado_init = _preparar_base_datos()
if _resultado_init is not True:
    st.warning(
        "No se pudo preparar la base de datos automaticamente. "
        "La app funcionara igual, pero no se guardaran los registros de uso. "
        f"Detalle: {_resultado_init}"
    )

st.title("🏗️ Estimador de materiales para vivienda")
st.caption("Sistema web con IA · Viviendas de 1 piso · Piura, 2026")

# ---------------------------------------------------------------------------
# 7.1 Campos fijos del sistema (no editables) - solo informativos en pantalla
# ---------------------------------------------------------------------------
with st.expander("Condiciones fijas del sistema (no editables)", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Distrito", "Piura")
    col2.metric("Tipo de losa", "Aligerada")
    col3.metric("N° de pisos", "1")
    col4.metric("Sistema constructivo", "Albañilería confinada")

st.divider()

# ---------------------------------------------------------------------------
# 7.2 Variables de entrada actuales + 7.3 Nuevos campos propuestos
# ---------------------------------------------------------------------------
st.subheader("Datos de la vivienda")

with st.form("formulario_vivienda"):
    col_izq, col_der = st.columns(2)

    with col_izq:
        area = st.number_input(
            "Área construida (m²)", min_value=30.0, max_value=150.0, value=60.0, step=1.0,
            help="Rango permitido: 30 - 150 m²",
        )
        n_ambientes = st.number_input(
            "N° de ambientes", min_value=1, max_value=6, value=4, step=1,
        )
        altura = st.selectbox(
            "Altura de piso a techo (m)", options=[2.40, 2.60, 2.80],
            index=[2.40, 2.60, 2.80].index(ALTURA_MURO_DEFECTO_M),
        )

    with col_der:
        n_banos = st.selectbox("N° de baños", options=[1, 2, 3], index=0)
        forma_terreno = st.selectbox(
            "Forma del terreno",
            options=["Cuadrado (1:1)", "Rectangular (1:1.5)", "Alargado (1:2)"],
            index=1,
        )
        tarrajeo = st.radio("Tarrajeo exterior", options=["Sí", "No"], horizontal=True)

    enviado = st.form_submit_button("Calcular materiales", use_container_width=True)

# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------
if enviado:
    entrada = EntradaMetrado(
        area_construida_m2=area,
        n_ambientes=int(n_ambientes),
        altura_muro_m=altura,
        n_banos=int(n_banos),
        forma_terreno=forma_terreno,
        tarrajeo_exterior=(tarrajeo == "Sí"),
    )

    resultado = obtener_metrado(entrada)

    # Registro en MySQL para el analisis posterior (pre-test/post-test).
    # "Best effort": si la base de datos no esta disponible, se avisa pero
    # no se interrumpe el resultado que ya se calculo.
    guardado_ok = guardar_registro(entrada, resultado)
    if not guardado_ok:
        st.info(
            "⚠️ El resultado se calculó bien, pero no se pudo guardar en la "
            "base de datos (¿está prendido MySQL/XAMPP?). Este cálculo no "
            "quedará registrado para el análisis posterior."
        )

    if not resultado["ml_disponible"]:
        st.warning(
            "El modelo del Módulo 2 (modelo_v1.pkl) todavía no existe. "
            "Corre `python ml/src/train.py` primero. Mientras tanto se "
            "muestra solo el metrado teórico del Módulo 1."
        )

    st.subheader("Resultado")

    etiquetas = {
        "cemento_bolsas": ("Cemento", "bolsas"),
        "arena_gruesa_m3": ("Arena gruesa", "m³"),
        "arena_fina_m3": ("Arena fina", "m³"),
        "piedra_grande_m3": ("Piedra grande (cimientos)", "m³"),
        "piedra_chancada_m3": ("Piedra chancada", "m³"),
        "acero_corrugado_kg": ("Acero corrugado", "kg"),
        "ladrillo_und": ("Ladrillo", "und"),
    }

    filas = []
    for clave, (nombre, unidad) in etiquetas.items():
        pct = resultado["pct_ajuste"][clave]
        filas.append({
            "Material": nombre,
            "Teórico (Módulo 1)": f'{resultado["teorico"][clave]:,.2f} {unidad}',
            "% ajuste (Módulo 2)": f'{pct*100:+.1f}%',
            "Final (con ajuste IA)": f'{resultado["final"][clave]:,.2f} {unidad}',
        })

    st.table(filas)

    with st.expander("Detalles de cálculo"):
        st.write(f"Perímetro estimado: {resultado['perimetro_m']} m")
        st.write(f"Área de muros: {resultado['area_muros_m2']} m²")
        st.write(f"Modelo usado (Módulo 2): {resultado['modelo_usado'] or 'no disponible'}")
        st.caption(
            "El metrado teórico usa reglas fijas (dosificación RNE/CAPECO). "
            "El metrado final aplica el % de desviación aprendido por el "
            "Módulo 2 a partir de los casos reales del dataset."
        )

st.divider()

# ---------------------------------------------------------------------------
# Panel de verificacion (temporal): muestra los ultimos registros guardados
# en MySQL, solo para confirmar que la conexion a la base de datos funciona.
# Se puede borrar este bloque despues sin afectar el resto de la app.
# ---------------------------------------------------------------------------
with st.expander("🔍 Ver últimos registros guardados en la base de datos"):
    try:
        import pandas as pd
        import mysql.connector
        from services.registro_service import DB_CONFIG

        conn = mysql.connector.connect(**DB_CONFIG)
        df_registros = pd.read_sql(
            "SELECT id, fecha_hora, area_construida_m2, n_ambientes, modelo_usado "
            "FROM registros_uso ORDER BY id DESC LIMIT 30",
            conn,
        )
        conn.close()

        if df_registros.empty:
            st.info("Todavía no hay registros guardados.")
        else:
            st.dataframe(df_registros, use_container_width=True)

        st.divider()

        # Descarga del historial COMPLETO (todas las columnas, todos los
        # registros), no solo la vista previa de arriba. Se genera al
        # tocar el boton, para no traer toda la tabla en cada recarga.
        if st.button("📥 Preparar descarga de TODOS los registros (CSV completo)"):
            conn = mysql.connector.connect(**DB_CONFIG)
            df_completo = pd.read_sql(
                "SELECT * FROM registros_uso ORDER BY id ASC", conn
            )
            conn.close()

            csv_bytes = df_completo.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                label=f"Descargar CSV completo ({len(df_completo)} registros)",
                data=csv_bytes,
                file_name="registros_uso_completo.csv",
                mime="text/csv",
            )
    except Exception as e:
        st.error(f"No se pudo leer la base de datos: {e}")

st.caption(
    "Proyecto de investigación · Cabrera Cabrera, H. y Terrones Campos, G. "
    
)
