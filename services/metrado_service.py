"""
Modulo 1 - Reglas fijas (RNE / practica constructiva peruana - CAPECO)
======================================================================
Calcula el metrado TEORICO de materiales para una vivienda de 1 piso en
Piura, con sistema constructivo de albanileria confinada y losa aligerada.
Es un calculo deterministico (sin aprendizaje). El resultado de este modulo
es luego corregido por el Modulo 2 (ML) con el % de desviacion aprendido.

IMPORTANTE:
Los coeficientes de dosificacion usados aqui son valores estandar de uso
comun en la construccion peruana (proporciones cemento:arena:piedra,
recubrimientos de acero minimo, rendimiento de ladrillo por m2, etc.).
NO reemplazan un calculo estructural con planos reales. Deben ser
revisados y validados con el asesor antes de la sustentacion.

Constantes fijas del sistema (seccion 7.1 del proyecto):
    - Distrito: Piura
    - Tipo de losa: Aligerada
    - N de pisos: 1
    - Sistema constructivo: Albanileria confinada
"""

from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Constantes fijas del sistema (no editables por el usuario)
# ---------------------------------------------------------------------------
DISTRITO_FIJO = "Piura"
TIPO_LOSA_FIJO = "Aligerada"
N_PISOS_FIJO = 1
SISTEMA_CONSTRUCTIVO_FIJO = "Albanileria confinada"

FormaTerreno = Literal["Cuadrado (1:1)", "Rectangular (1:1.5)", "Alargado (1:2)"]

RATIO_FORMA = {
    "Cuadrado (1:1)": 1.0,
    "Rectangular (1:1.5)": 1.5,
    "Alargado (1:2)": 2.0,
}

# ---------------------------------------------------------------------------
# Coeficientes de dosificacion (valores estandar CAPECO / practica local)
# ---------------------------------------------------------------------------

# Cimiento corrido: concreto ciclopeo 1:10 + 30% piedra grande (P.G.)
CIMIENTO_ANCHO_M = 0.40
CIMIENTO_ALTO_M = 0.80
CIMIENTO_PORC_PIEDRA_GRANDE = 0.30
CIMIENTO_CEMENTO_BOL_M3 = 4.30
CIMIENTO_ARENA_GRUESA_M3_M3 = 0.90

# Sobrecimiento: concreto 1:8 + 25% piedra mediana (P.M.)
SOBRECIMIENTO_ANCHO_M = 0.15
SOBRECIMIENTO_ALTO_M = 0.30
SOBRECIMIENTO_PORC_PIEDRA_MEDIANA = 0.25
SOBRECIMIENTO_CEMENTO_BOL_M3 = 5.90
SOBRECIMIENTO_ARENA_GRUESA_M3_M3 = 0.85

# Columnas y vigas de confinamiento: concreto 1:2:3 (cemento:arena:piedra chancada)
CONCRETO_ESTRUCTURAL_CEMENTO_BOL_M3 = 9.73
CONCRETO_ESTRUCTURAL_ARENA_GRUESA_M3_M3 = 0.52
CONCRETO_ESTRUCTURAL_PIEDRA_CHANCADA_M3_M3 = 0.53
FACTOR_VOL_CONFINAMIENTO_M3_POR_M2 = 0.028

# Losa aligerada (h=0.20m): concreto 1:2:3, ladrillo hueco 30x30x15 y acero de viguetas
LOSA_ESPESOR_M = 0.20
LOSA_CONCRETO_M3_POR_M2 = 0.13
LOSA_LADRILLO_UND_POR_M2 = 8.0
LOSA_ACERO_KG_POR_M2 = 3.80

# Muros de albanileria (ladrillo King Kong, soga, junta 1.5cm)
LADRILLO_UND_POR_M2_MURO = 39.0
ALTURA_MURO_DEFECTO_M = 2.60

# Tarrajeo (interior + exterior): mezcla cemento:arena fina 1:5
TARRAJEO_CEMENTO_BOL_M2 = 0.13
TARRAJEO_ARENA_FINA_M3_M2 = 0.018
FACTOR_AREA_TARRAJEO_POR_M2_MURO = 1.6

# Acero minimo en columnas y vigas de confinamiento (independiente del acero de losa)
ACERO_COLUMNAS_VIGAS_KG_POR_M2 = 5.20

# Partida adicional por bano (impermeabilizacion, tarrajeo extra, instalaciones)
CEMENTO_BOL_POR_BANO_EXTRA = 3.5
ARENA_FINA_M3_POR_BANO_EXTRA = 0.25
LADRILLO_UND_POR_BANO_EXTRA = 60

# Desperdicio estandar aplicado al final (acero y ladrillo)
FACTOR_DESPERDICIO_ACERO = 1.07
FACTOR_DESPERDICIO_LADRILLO = 1.05

# ---------------------------------------------------------------------------
# Calibracion empirica (NUEVO)
# ---------------------------------------------------------------------------
# Los coeficientes de dosificacion de arriba son valores estandar de CAPECO,
# pero no estaban ajustados a los 30 casos reales del dataset de Piura. Estos
# factores corrigen esa brecha: cada uno es la MEDIANA de (valor_real /
# valor_teorico) calculada sobre los 30 casos de ml/data/raw/dataset_materiales.xlsx
# (ver ml/src/preprocessing.py). Se uso la mediana en vez del promedio porque
# es mas robusta a casos atipicos (algunos casos sinteticos, algunos con
# fuentes de datos heterogeneas).
#
# IMPORTANTE: estos factores deben RECALCULARSE cada vez que el dataset
# crezca con casos reales nuevos (especialmente cuando se reemplacen los 3
# casos sinteticos por casos de INFOBRAS). Para recalcularlos: correr
# ml/src/preprocessing.py con estos factores en 1.0, y sacar la mediana de
# la columna "{material}_real" / "{material}_teorico" del CSV resultante.
FACTOR_CALIBRACION = {
    "cemento_bolsas": 1.808,
    "arena_gruesa_m3": 1.195,
    "arena_fina_m3": 1.019,
    "piedra_grande_m3": 1.828,
    "piedra_chancada_m3": 1.946,
    "acero_corrugado_kg": 1.511,
    "ladrillo_und": 1.020,
}


@dataclass
class EntradaMetrado:
    """Campos que llena el usuario en el formulario (Streamlit)."""
    area_construida_m2: float
    n_ambientes: int
    altura_muro_m: float = ALTURA_MURO_DEFECTO_M
    n_banos: int = 1
    forma_terreno: FormaTerreno = "Rectangular (1:1.5)"
    tarrajeo_exterior: bool = True


@dataclass
class MetradoTeorico:
    """Salida del Modulo 1: metrado teorico antes del ajuste del Modulo 2."""
    cemento_bolsas: float
    arena_gruesa_m3: float
    arena_fina_m3: float
    piedra_grande_m3: float
    piedra_chancada_m3: float
    acero_corrugado_kg: float
    ladrillo_und: float
    perimetro_m: float
    area_muros_m2: float


def _calcular_perimetro(area_m2: float, forma_terreno: FormaTerreno) -> float:
    """
    Deriva ancho y largo a partir del area y el ratio de forma elegido,
    y devuelve el perimetro. area = ancho * largo ; largo = ratio * ancho
    """
    ratio = RATIO_FORMA[forma_terreno]
    ancho = (area_m2 / ratio) ** 0.5
    largo = ancho * ratio
    return 2 * (ancho + largo)


def calcular_metrado(entrada: EntradaMetrado) -> MetradoTeorico:
    """
    Calcula el metrado teorico de materiales (Modulo 1) para una vivienda
    de 1 piso en Piura, albanileria confinada, losa aligerada.
    """
    area = entrada.area_construida_m2
    perimetro = _calcular_perimetro(area, entrada.forma_terreno)
    area_muros = perimetro * entrada.altura_muro_m

    # --- Cimiento corrido (perimetro completo) ---
    vol_cimiento_total = perimetro * CIMIENTO_ANCHO_M * CIMIENTO_ALTO_M
    vol_cimiento_piedra_grande = vol_cimiento_total * CIMIENTO_PORC_PIEDRA_GRANDE
    vol_cimiento_mezcla = vol_cimiento_total - vol_cimiento_piedra_grande
    cemento_cimiento = vol_cimiento_mezcla * CIMIENTO_CEMENTO_BOL_M3
    arena_gruesa_cimiento = vol_cimiento_mezcla * CIMIENTO_ARENA_GRUESA_M3_M3

    # --- Sobrecimiento (perimetro completo) ---
    vol_sobrecim_total = perimetro * SOBRECIMIENTO_ANCHO_M * SOBRECIMIENTO_ALTO_M
    vol_sobrecim_piedra_mediana = vol_sobrecim_total * SOBRECIMIENTO_PORC_PIEDRA_MEDIANA
    vol_sobrecim_mezcla = vol_sobrecim_total - vol_sobrecim_piedra_mediana
    cemento_sobrecim = vol_sobrecim_mezcla * SOBRECIMIENTO_CEMENTO_BOL_M3
    arena_gruesa_sobrecim = vol_sobrecim_mezcla * SOBRECIMIENTO_ARENA_GRUESA_M3_M3
    piedra_chancada_sobrecim = vol_sobrecim_piedra_mediana

    # --- Columnas y vigas de confinamiento (concreto 1:2:3) ---
    vol_confinamiento = area * FACTOR_VOL_CONFINAMIENTO_M3_POR_M2
    cemento_confinamiento = vol_confinamiento * CONCRETO_ESTRUCTURAL_CEMENTO_BOL_M3
    arena_gruesa_confinamiento = vol_confinamiento * CONCRETO_ESTRUCTURAL_ARENA_GRUESA_M3_M3
    piedra_chancada_confinamiento = vol_confinamiento * CONCRETO_ESTRUCTURAL_PIEDRA_CHANCADA_M3_M3
    acero_confinamiento = area * ACERO_COLUMNAS_VIGAS_KG_POR_M2

    # --- Losa aligerada ---
    vol_losa = area * LOSA_CONCRETO_M3_POR_M2
    cemento_losa = vol_losa * CONCRETO_ESTRUCTURAL_CEMENTO_BOL_M3
    arena_gruesa_losa = vol_losa * CONCRETO_ESTRUCTURAL_ARENA_GRUESA_M3_M3
    piedra_chancada_losa = vol_losa * CONCRETO_ESTRUCTURAL_PIEDRA_CHANCADA_M3_M3
    ladrillo_losa = area * LOSA_LADRILLO_UND_POR_M2
    acero_losa = area * LOSA_ACERO_KG_POR_M2

    # --- Muros de albanileria ---
    ladrillo_muros = area_muros * LADRILLO_UND_POR_M2_MURO

    # --- Tarrajeo (solo si el usuario lo marca) ---
    cemento_tarrajeo = 0.0
    arena_fina_tarrajeo = 0.0
    if entrada.tarrajeo_exterior:
        area_tarrajeo = area_muros * FACTOR_AREA_TARRAJEO_POR_M2_MURO
        cemento_tarrajeo = area_tarrajeo * TARRAJEO_CEMENTO_BOL_M2
        arena_fina_tarrajeo = area_tarrajeo * TARRAJEO_ARENA_FINA_M3_M2
    else:
        arena_fina_tarrajeo = 0.05

    # --- Partida adicional por N de banos (mas de 1) ---
    banos_extra = max(entrada.n_banos - 1, 0)
    cemento_banos = banos_extra * CEMENTO_BOL_POR_BANO_EXTRA
    arena_fina_banos = banos_extra * ARENA_FINA_M3_POR_BANO_EXTRA
    ladrillo_banos = banos_extra * LADRILLO_UND_POR_BANO_EXTRA

    # --- Totales ---
    cemento_total = (
        cemento_cimiento + cemento_sobrecim + cemento_confinamiento
        + cemento_losa + cemento_tarrajeo + cemento_banos
    )
    arena_gruesa_total = (
        arena_gruesa_cimiento + arena_gruesa_sobrecim
        + arena_gruesa_confinamiento + arena_gruesa_losa
    )
    arena_fina_total = arena_fina_tarrajeo + arena_fina_banos
    piedra_grande_total = vol_cimiento_piedra_grande
    piedra_chancada_total = (
        piedra_chancada_sobrecim + piedra_chancada_confinamiento + piedra_chancada_losa
    )
    acero_total = (acero_confinamiento + acero_losa) * FACTOR_DESPERDICIO_ACERO
    ladrillo_total = (ladrillo_muros + ladrillo_losa + ladrillo_banos) * FACTOR_DESPERDICIO_LADRILLO

    return MetradoTeorico(
        cemento_bolsas=round(cemento_total * FACTOR_CALIBRACION["cemento_bolsas"], 2),
        arena_gruesa_m3=round(arena_gruesa_total * FACTOR_CALIBRACION["arena_gruesa_m3"], 2),
        arena_fina_m3=round(arena_fina_total * FACTOR_CALIBRACION["arena_fina_m3"], 2),
        piedra_grande_m3=round(piedra_grande_total * FACTOR_CALIBRACION["piedra_grande_m3"], 2),
        piedra_chancada_m3=round(piedra_chancada_total * FACTOR_CALIBRACION["piedra_chancada_m3"], 2),
        acero_corrugado_kg=round(acero_total * FACTOR_CALIBRACION["acero_corrugado_kg"], 2),
        ladrillo_und=round(ladrillo_total * FACTOR_CALIBRACION["ladrillo_und"]),
        perimetro_m=round(perimetro, 2),
        area_muros_m2=round(area_muros, 2),
    )


if __name__ == "__main__":
    ejemplo = EntradaMetrado(
        area_construida_m2=60,
        n_ambientes=4,
        altura_muro_m=2.60,
        n_banos=1,
        forma_terreno="Rectangular (1:1.5)",
        tarrajeo_exterior=True,
    )
    resultado = calcular_metrado(ejemplo)
    print(resultado)
