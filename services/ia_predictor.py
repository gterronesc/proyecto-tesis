"""
ia_predictor.py
================
Puente entre la app de Streamlit y el Modulo 2 (ML). Import directo
(mismo proceso Python), sin HTTP a un ml-service aparte.

app.py solo deberia llamar a obtener_metrado() de este archivo.
"""

import os
import sys

_RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.append(_RAIZ_PROYECTO)

from services.metrado_service import EntradaMetrado, calcular_metrado, RATIO_FORMA  # noqa: E402
from ml.src.predict import calcular_todo  # noqa: E402


def _construir_features(entrada: EntradaMetrado, teorico) -> dict:
    return {
        "area_construida_m2": entrada.area_construida_m2,
        "altura_muro_m": entrada.altura_muro_m,
        "n_banos": entrada.n_banos,
        "forma_terreno_ratio": RATIO_FORMA[entrada.forma_terreno],
        "tarrajeo_exterior": int(entrada.tarrajeo_exterior),
        "perimetro_m": teorico.perimetro_m,
        "area_muros_m2": teorico.area_muros_m2,
    }


def obtener_metrado(entrada: EntradaMetrado) -> dict:
    """
    Punto de entrada unico para app.py.

    Devuelve:
    {
        "teorico": {material: valor, ...},
        "pct_ajuste": {material: pct, ...},   # trazabilidad (punto 7)
        "final": {material: valor, ...},
        "modelo_usado": "modelo_v1",
        "perimetro_m": float,
        "area_muros_m2": float,
        "ml_disponible": bool,
    }
    """
    teorico = calcular_metrado(entrada)
    teorico_dict = {
        "cemento_bolsas": teorico.cemento_bolsas,
        "arena_gruesa_m3": teorico.arena_gruesa_m3,
        "arena_fina_m3": teorico.arena_fina_m3,
        "piedra_grande_m3": teorico.piedra_grande_m3,
        "piedra_chancada_m3": teorico.piedra_chancada_m3,
        "acero_corrugado_kg": teorico.acero_corrugado_kg,
        "ladrillo_und": teorico.ladrillo_und,
    }

    features = _construir_features(entrada, teorico)

    try:
        completo = calcular_todo(teorico, features)
        modelo_usado = completo.pop("modelo_usado")
        pct_ajuste = {mat: v["pct_ajuste"] for mat, v in completo.items()}
        final_dict = {mat: v["final"] for mat, v in completo.items()}
        ml_disponible = True
    except FileNotFoundError:
        pct_ajuste = {mat: 0.0 for mat in teorico_dict}
        final_dict = teorico_dict
        modelo_usado = None
        ml_disponible = False

    return {
        "teorico": teorico_dict,
        "pct_ajuste": pct_ajuste,
        "final": final_dict,
        "modelo_usado": modelo_usado,
        "perimetro_m": teorico.perimetro_m,
        "area_muros_m2": teorico.area_muros_m2,
        "ml_disponible": ml_disponible,
    }
