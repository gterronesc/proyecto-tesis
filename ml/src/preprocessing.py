"""
preprocessing.py
=================
Lee el dataset crudo (Excel, ml/data/raw/dataset_materiales.xlsx), calcula el
metrado TEORICO (Modulo 1) para cada caso con los mismos inputs que registro
esa vivienda, y arma el dataset PROCESADO con:
    - features: area, altura, n_banos, forma_terreno (ratio), tarrajeo (0/1),
                perimetro, area_muros
    - targets:  % de desviacion real vs teorico, uno por cada material

Ese dataset procesado es el que usa train.py para entrenar el Modulo 2.
"""

import os
import sys

import pandas as pd

# Permite importar services.metrado_service desde ml/src sin instalar el paquete
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.metrado_service import EntradaMetrado, calcular_metrado, RATIO_FORMA  # noqa: E402

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "dataset_materiales.xlsx")
PROCESSED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "dataset_procesado.csv")

MATERIALES = [
    "cemento_bolsas",
    "arena_gruesa_m3",
    "arena_fina_m3",
    "piedra_grande_m3",
    "piedra_chancada_m3",
    "acero_corrugado_kg",
    "ladrillo_und",
]


def _tarrajeo_a_bool(valor: str) -> bool:
    return str(valor).strip().lower() in ("si", "sí", "true", "1")


def cargar_dataset_crudo(path: str = RAW_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Dataset")
    # limpieza basica: quitar espacios/saltos de linea en texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    df = df.dropna(subset=["vivienda_id"]).reset_index(drop=True)
    return df


def calcular_features_y_targets(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for _, r in df.iterrows():
        entrada = EntradaMetrado(
            area_construida_m2=float(r["area_construida_m2"]),
            n_ambientes=0,  # no usado por calcular_metrado, se deja en 0
            altura_muro_m=float(r["Altura"]),
            n_banos=int(float(r["N° de baños"])),
            forma_terreno=r["Forma del terreno"],
            tarrajeo_exterior=_tarrajeo_a_bool(r["Tarrajeo"]),
        )
        teorico = calcular_metrado(entrada)

        fila = {
            "vivienda_id": r["vivienda_id"],
            "area_construida_m2": entrada.area_construida_m2,
            "altura_muro_m": entrada.altura_muro_m,
            "n_banos": entrada.n_banos,
            "forma_terreno_ratio": RATIO_FORMA[entrada.forma_terreno],
            "tarrajeo_exterior": int(entrada.tarrajeo_exterior),
            "perimetro_m": teorico.perimetro_m,
            "area_muros_m2": teorico.area_muros_m2,
        }

        teorico_dict = {
            "cemento_bolsas": teorico.cemento_bolsas,
            "arena_gruesa_m3": teorico.arena_gruesa_m3,
            "arena_fina_m3": teorico.arena_fina_m3,
            "piedra_grande_m3": teorico.piedra_grande_m3,
            "piedra_chancada_m3": teorico.piedra_chancada_m3,
            "acero_corrugado_kg": teorico.acero_corrugado_kg,
            "ladrillo_und": teorico.ladrillo_und,
        }

        for mat in MATERIALES:
            real = float(r[mat])
            teo = teorico_dict[mat]
            fila[f"{mat}_teorico"] = teo
            fila[f"{mat}_real"] = real
            # % de desviacion: (real - teorico) / teorico
            fila[f"{mat}_pct_desviacion"] = (real - teo) / teo if teo != 0 else 0.0

        filas.append(fila)

    return pd.DataFrame(filas)


def main():
    df_crudo = cargar_dataset_crudo()
    df_proc = calcular_features_y_targets(df_crudo)
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df_proc.to_csv(PROCESSED_PATH, index=False)
    print(f"Dataset procesado guardado en: {PROCESSED_PATH}")
    print(f"Filas: {len(df_proc)}")
    print(df_proc.filter(like="pct_desviacion").describe())


if __name__ == "__main__":
    main()
