"""
exportar_postest.py
====================
Cruza registros_uso (O2, lo que calculo el sistema) con pretest_o1 (O1, lo
que reporto la familia/maestro de obra a mano), y arma la tabla final lista
para SPSS: % de error por material, PME por familia, y promedio general.

MARGEN_ERROR_ACEPTADO sigue siendo un valor DE EJEMPLO (0.10 = +-10%).
Hay que reemplazarlo por lo que se defina con el asesor antes de usar esto
para el informe final.
"""

import os
import sys

import pandas as pd
import mysql.connector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.registro_service import DB_CONFIG, MATERIALES  # noqa: E402

MARGEN_ERROR_ACEPTADO = 0.10  # PLACEHOLDER - definir con el asesor


def obtener_datos_cruzados() -> pd.DataFrame:
    conn = mysql.connector.connect(**DB_CONFIG)

    columnas_o2 = ", ".join(f"u.{m}_final AS {m}_sistema" for m in MATERIALES)
    columnas_o1 = ", ".join(f"p.{m}_real AS {m}_real" for m in MATERIALES)

    query = f"""
        SELECT u.codigo_familia, u.fecha_hora AS fecha_post_test,
               p.fecha_hora AS fecha_pre_test, p.fuente_calculo,
               {columnas_o2}, {columnas_o1}
        FROM registros_uso u
        INNER JOIN pretest_o1 p ON u.codigo_familia = p.codigo_familia
        WHERE u.codigo_familia IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def calcular_pme(df: pd.DataFrame) -> pd.DataFrame:
    for m in MATERIALES:
        error = (df[f"{m}_sistema"] - df[f"{m}_real"]).abs() / df[f"{m}_real"]
        df[f"{m}_correcto"] = error <= MARGEN_ERROR_ACEPTADO

    cols_correcto = [f"{m}_correcto" for m in MATERIALES]
    df["n_correctos"] = df[cols_correcto].sum(axis=1)
    df["n_total"] = len(MATERIALES)
    df["PME_%"] = (df["n_correctos"] / df["n_total"] * 100).round(1)
    return df


def main():
    df = obtener_datos_cruzados()
    df = calcular_pme(df)
    salida = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "postest_pme.xlsx")
    df.to_excel(salida, index=False)
    print(f"Exportado a: {salida}")
    print(f"PME promedio (todas las familias): {df['PME_%'].mean():.1f}%")


if __name__ == "__main__":
    main()
