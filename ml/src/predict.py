"""
predict.py
==========
Punto de entrada del Modulo 2 para USO EN PRODUCCION (llamado desde
services/ia_predictor.py con import directo, sin HTTP).

Dado un metrado teorico (Modulo 1) y los datos del formulario, predice el
% de ajuste por material y devuelve tanto el % de ajuste como el metrado
FINAL corregido (para trazabilidad completa).
"""

import os

import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "modelo_v1.pkl")
MODELO_NOMBRE = "modelo_v1"  # identificador de trazabilidad (punto 7)

_paquete_cache = None


def _cargar_modelo():
    global _paquete_cache
    if _paquete_cache is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"No existe {MODEL_PATH}. Corre primero: python train.py"
            )
        _paquete_cache = joblib.load(MODEL_PATH)
    return _paquete_cache


def predecir_ajuste(features: dict) -> dict:
    """
    features debe traer las mismas keys usadas en train.py (FEATURES):
        area_construida_m2, altura_muro_m, n_banos, forma_terreno_ratio,
        tarrajeo_exterior (0/1), perimetro_m, area_muros_m2

    Devuelve un dict {material: pct_ajuste} , ej: {"cemento_bolsas": 0.12, ...}
    """
    paquete = _cargar_modelo()
    modelo = paquete["modelo"]
    columnas = paquete["features"]
    materiales = paquete["materiales"]

    X = pd.DataFrame([[features[c] for c in columnas]], columns=columnas)
    pred = modelo.predict(X)[0]

    return {mat: float(p) for mat, p in zip(materiales, pred)}


def calcular_todo(metrado_teorico, features: dict) -> dict:
    """
    Version con trazabilidad completa (punto 7): devuelve, para cada
    material, el valor teorico, el % de ajuste que aplico el Modulo 2, y
    el valor final. Tambien indica que modelo se uso.

    Devuelve:
    {
        "cemento_bolsas": {"teorico": .., "pct_ajuste": .., "final": ..},
        ...
        "modelo_usado": "modelo_v1",
    }
    """
    ajustes = predecir_ajuste(features)

    teorico_dict = {
        "cemento_bolsas": metrado_teorico.cemento_bolsas,
        "arena_gruesa_m3": metrado_teorico.arena_gruesa_m3,
        "arena_fina_m3": metrado_teorico.arena_fina_m3,
        "piedra_grande_m3": metrado_teorico.piedra_grande_m3,
        "piedra_chancada_m3": metrado_teorico.piedra_chancada_m3,
        "acero_corrugado_kg": metrado_teorico.acero_corrugado_kg,
        "ladrillo_und": metrado_teorico.ladrillo_und,
    }

    resultado = {"modelo_usado": MODELO_NOMBRE}
    for material, valor_teorico in teorico_dict.items():
        pct = ajustes.get(material, 0.0)
        resultado[material] = {
            "teorico": valor_teorico,
            "pct_ajuste": round(pct, 4),
            "final": round(valor_teorico * (1 + pct), 2),
        }
    return resultado


def calcular_metrado_final(metrado_teorico, features: dict) -> dict:
    """
    Compatibilidad hacia atras: solo el metrado final (sin el detalle de
    trazabilidad). Usa calcular_todo() internamente.
    """
    completo = calcular_todo(metrado_teorico, features)
    return {k: v["final"] for k, v in completo.items() if k != "modelo_usado"}
