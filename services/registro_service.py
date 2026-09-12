"""
registro_service.py
====================
Guarda en MySQL cada vez que alguien usa el sistema. Funciona tanto con
MySQL local (XAMPP) como con MySQL en la nube (ej. Aiven), que suele exigir
conexion SSL.

Variables de entorno (todas opcionales, con default a XAMPP local):
    DB_HOST      -> localhost (XAMPP) o el host que te da Aiven
    DB_PORT      -> 3306 (XAMPP) o el puerto que te da Aiven (ej. 12345)
    DB_USER      -> root (XAMPP) o "avnadmin" (Aiven)
    DB_PASSWORD  -> "" (XAMPP) o la clave que te da Aiven
    DB_NAME      -> proyecto_tesis
    DB_SSL_CA    -> ruta al certificado .pem (solo necesario para MySQL en
                    la nube tipo Aiven; en XAMPP local se deja vacio)
"""

import os
from datetime import datetime

import mysql.connector
from mysql.connector import Error as MySQLError

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "proyecto_tesis"),
}

# Si hay un certificado SSL configurado (tipico de MySQL en la nube como
# Aiven), se agrega a la config de conexion.
_SSL_CA = os.environ.get("DB_SSL_CA", "").strip()
if _SSL_CA:
    DB_CONFIG["ssl_ca"] = _SSL_CA
    DB_CONFIG["ssl_verify_cert"] = True

MATERIALES = [
    "cemento_bolsas",
    "arena_gruesa_m3",
    "arena_fina_m3",
    "piedra_grande_m3",
    "piedra_chancada_m3",
    "acero_corrugado_kg",
    "ladrillo_und",
]

_CREATE_DATABASE_SQL = f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS registros_uso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,

    distrito VARCHAR(50) DEFAULT 'Piura',
    tipo_losa VARCHAR(50) DEFAULT 'Aligerada',
    n_pisos INT DEFAULT 1,
    sistema_constructivo VARCHAR(50) DEFAULT 'Albanileria confinada',

    area_construida_m2 FLOAT NOT NULL,
    n_ambientes INT,
    altura_muro_m FLOAT,
    n_banos INT,
    forma_terreno VARCHAR(30),
    tarrajeo_exterior TINYINT(1),

    perimetro_m FLOAT,
    area_muros_m2 FLOAT,

    cemento_bolsas_teorico     FLOAT, cemento_bolsas_pct_ajuste     FLOAT, cemento_bolsas_final     FLOAT,
    arena_gruesa_m3_teorico    FLOAT, arena_gruesa_m3_pct_ajuste    FLOAT, arena_gruesa_m3_final    FLOAT,
    arena_fina_m3_teorico      FLOAT, arena_fina_m3_pct_ajuste      FLOAT, arena_fina_m3_final      FLOAT,
    piedra_grande_m3_teorico   FLOAT, piedra_grande_m3_pct_ajuste   FLOAT, piedra_grande_m3_final   FLOAT,
    piedra_chancada_m3_teorico FLOAT, piedra_chancada_m3_pct_ajuste FLOAT, piedra_chancada_m3_final FLOAT,
    acero_corrugado_kg_teorico FLOAT, acero_corrugado_kg_pct_ajuste FLOAT, acero_corrugado_kg_final FLOAT,
    ladrillo_und_teorico       FLOAT, ladrillo_und_pct_ajuste       FLOAT, ladrillo_und_final       FLOAT,

    modelo_usado VARCHAR(50),
    ml_disponible TINYINT(1),

    valor_real_registrado TINYINT(1) DEFAULT 0,
    codigo_familia VARCHAR(20)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def _conectar(con_base_datos: bool = True):
    config = dict(DB_CONFIG)
    if not con_base_datos:
        config.pop("database")
    return mysql.connector.connect(**config)


def inicializar_base_datos():
    conn = _conectar(con_base_datos=False)
    cur = conn.cursor()
    cur.execute(_CREATE_DATABASE_SQL)
    conn.commit()
    cur.close()
    conn.close()

    conn = _conectar(con_base_datos=True)
    cur = conn.cursor()
    cur.execute(_CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Base de datos '{DB_CONFIG['database']}' y tabla 'registros_uso' listas.")


def guardar_registro(entrada, resultado: dict, codigo_familia: str = None) -> bool:
    columnas = ["fecha_hora", "area_construida_m2", "n_ambientes", "altura_muro_m",
                "n_banos", "forma_terreno", "tarrajeo_exterior", "perimetro_m",
                "area_muros_m2", "modelo_usado", "ml_disponible", "codigo_familia"]
    valores = [
        datetime.now(), entrada.area_construida_m2, entrada.n_ambientes,
        entrada.altura_muro_m, entrada.n_banos, entrada.forma_terreno,
        int(entrada.tarrajeo_exterior), resultado["perimetro_m"],
        resultado["area_muros_m2"], resultado["modelo_usado"],
        int(resultado["ml_disponible"]), codigo_familia,
    ]

    for mat in MATERIALES:
        columnas += [f"{mat}_teorico", f"{mat}_pct_ajuste", f"{mat}_final"]
        valores += [
            resultado["teorico"][mat],
            resultado["pct_ajuste"][mat],
            resultado["final"][mat],
        ]

    placeholders = ", ".join(["%s"] * len(valores))
    columnas_sql = ", ".join(columnas)
    sql = f"INSERT INTO registros_uso ({columnas_sql}) VALUES ({placeholders})"

    try:
        conn = _conectar()
        cur = conn.cursor()
        cur.execute(sql, valores)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except MySQLError as e:
        print(f"[registro_service] No se pudo guardar el registro: {e}")
        return False


if __name__ == "__main__":
    inicializar_base_datos()
