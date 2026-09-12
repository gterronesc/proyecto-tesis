"""
evaluate.py
===========
Carga el modelo entrenado (modelo_v1.pkl) y el dataset procesado completo,
y reporta el error (MAE del % de desviacion, y el error final en unidades
reales de cada material) para revisar que tan bien esta funcionando el
Modulo 2 antes de usarlo en la app.
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

PROCESSED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "dataset_procesado.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "modelo_v1.pkl")


def main():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"No existe {MODEL_PATH}. Corre primero: python train.py")

    paquete = joblib.load(MODEL_PATH)
    modelo = paquete["modelo"]
    features = paquete["features"]
    materiales = paquete["materiales"]

    df = pd.read_csv(PROCESSED_PATH)
    X = df[features]
    targets = [f"{m}_pct_desviacion" for m in materiales]
    y_real_pct = df[targets]

    y_pred_pct = pd.DataFrame(modelo.predict(X), columns=targets, index=df.index)

    print(f"{'material':<20}{'MAE % desviacion':>20}{'MAE unidades reales':>24}")
    for m in materiales:
        col = f"{m}_pct_desviacion"
        mae_pct = mean_absolute_error(y_real_pct[col], y_pred_pct[col])

        teorico = df[f"{m}_teorico"]
        real = df[f"{m}_real"]
        estimado = teorico * (1 + y_pred_pct[col])
        mae_unidades = mean_absolute_error(real, estimado)

        print(f"{m:<20}{mae_pct:>20.3f}{mae_unidades:>24.2f}")

    print(
        "\nMAE % desviacion = que tan lejos, en promedio, esta el % predicho "
        "del % real (0.10 = 10 puntos porcentuales de error).\n"
        "MAE unidades reales = error promedio del metrado final (teorico + "
        "ajuste del modelo) contra la cantidad real, en la unidad de cada "
        "material (bolsas, m3, kg, und)."
    )


if __name__ == "__main__":
    main()
