"""
train.py
========
Entrena el Modulo 2: un modelo que aprende el % de desviacion entre el
metrado teorico (Modulo 1) y la cantidad real, para cada uno de los 7
materiales. Usa RandomForestRegressor (scikit-learn) envuelto en
MultiOutputRegressor para predecir los 7 porcentajes a la vez.

Nota: el resumen del proyecto menciona Random Forest / XGBoost. Aqui se usa
Random Forest porque viene con scikit-learn (sin dependencias extra) y con
un dataset de ~60 casos es mas estable que XGBoost, que tiende a sobreajustar
con tan pocos datos. Si luego el dataset crece bastante, cambiar a XGBoost
es un cambio de una sola linea (ver comentario en get_modelo()).
"""

import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor

PROCESSED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "dataset_procesado.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "modelo_v1.pkl")

FEATURES = [
    "area_construida_m2",
    "altura_muro_m",
    "n_banos",
    "forma_terreno_ratio",
    "tarrajeo_exterior",
    "perimetro_m",
    "area_muros_m2",
]

MATERIALES = [
    "cemento_bolsas",
    "arena_gruesa_m3",
    "arena_fina_m3",
    "piedra_grande_m3",
    "piedra_chancada_m3",
    "acero_corrugado_kg",
    "ladrillo_und",
]

TARGETS = [f"{m}_pct_desviacion" for m in MATERIALES]


def get_modelo():
    """
    Modelo base. Para cambiar a XGBoost (si el dataset crece):
        from xgboost import XGBRegressor
        base = XGBRegressor(n_estimators=200, max_depth=4, random_state=42)
    """
    base = RandomForestRegressor(
        n_estimators=200,
        max_depth=5,
        min_samples_leaf=2,
        random_state=42,
    )
    return MultiOutputRegressor(base)


def main():
    if not os.path.exists(PROCESSED_PATH):
        raise FileNotFoundError(
            f"No existe {PROCESSED_PATH}. Corre primero: python preprocessing.py"
        )

    df = pd.read_csv(PROCESSED_PATH)
    X = df[FEATURES]
    y = df[TARGETS]

    # Con ~60 casos el test set queda muy chico; se usa igual para tener una
    # referencia, pero el numero real de validacion para la tesis deberia
    # crecer conforme el dataset crezca (ver seccion 9 del resumen).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    modelo = get_modelo()
    modelo.fit(X_train, y_train)

    train_score = modelo.score(X_train, y_train)
    test_score = modelo.score(X_test, y_test)
    print(f"R2 en train: {train_score:.3f}")
    print(f"R2 en test:  {test_score:.3f}")
    if len(X_test) < 5:
        print(
            "Aviso: el test set tiene muy pocos casos "
            f"({len(X_test)}). El R2 de test no es confiable todavia; "
            "sirve solo como referencia hasta tener mas datos reales."
        )

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "features": FEATURES,
            "materiales": MATERIALES,
        },
        MODEL_PATH,
    )
    print(f"Modelo guardado en: {MODEL_PATH}")


if __name__ == "__main__":
    main()
