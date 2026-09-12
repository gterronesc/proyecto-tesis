-- =============================================================
-- database.sql
-- Sistema web con IA para estimar materiales - vivienda Piura 2026
-- Crea la base de datos y la tabla donde se registra cada uso del
-- sistema (parametros ingresados, metrado teorico, % de ajuste del
-- Modulo 2, metrado final y modelo usado).
--
-- Uso:
--   - phpMyAdmin: pestaña "SQL", pegar todo este archivo y ejecutar.
--   - Consola: mysql -u root -p < database.sql
--
-- Nota: esto es equivalente a correr "python -m services.registro_service"
-- desde el proyecto; usa el que te resulte mas comodo, no hace falta
-- correr ambos.
-- =============================================================

CREATE DATABASE IF NOT EXISTS proyecto_tesis
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE proyecto_tesis;

CREATE TABLE IF NOT EXISTS registros_uso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,

    -- 7.1 Constantes fijas del sistema (se guardan igual, por trazabilidad)
    distrito VARCHAR(50) DEFAULT 'Piura',
    tipo_losa VARCHAR(50) DEFAULT 'Aligerada',
    n_pisos INT DEFAULT 1,
    sistema_constructivo VARCHAR(50) DEFAULT 'Albanileria confinada',

    -- 7.2 / 7.3 Parametros de entrada (formulario)
    area_construida_m2 FLOAT NOT NULL,
    n_ambientes INT,
    altura_muro_m FLOAT,
    n_banos INT,
    forma_terreno VARCHAR(30),
    tarrajeo_exterior TINYINT(1),

    -- Geometria derivada (Modulo 1)
    perimetro_m FLOAT,
    area_muros_m2 FLOAT,

    -- Cemento: teorico (Modulo 1), % ajuste (Modulo 2), final
    cemento_bolsas_teorico     FLOAT,
    cemento_bolsas_pct_ajuste  FLOAT,
    cemento_bolsas_final       FLOAT,

    -- Arena gruesa
    arena_gruesa_m3_teorico    FLOAT,
    arena_gruesa_m3_pct_ajuste FLOAT,
    arena_gruesa_m3_final      FLOAT,

    -- Arena fina
    arena_fina_m3_teorico      FLOAT,
    arena_fina_m3_pct_ajuste   FLOAT,
    arena_fina_m3_final        FLOAT,

    -- Piedra grande
    piedra_grande_m3_teorico     FLOAT,
    piedra_grande_m3_pct_ajuste  FLOAT,
    piedra_grande_m3_final       FLOAT,

    -- Piedra chancada
    piedra_chancada_m3_teorico    FLOAT,
    piedra_chancada_m3_pct_ajuste FLOAT,
    piedra_chancada_m3_final      FLOAT,

    -- Acero corrugado
    acero_corrugado_kg_teorico     FLOAT,
    acero_corrugado_kg_pct_ajuste  FLOAT,
    acero_corrugado_kg_final       FLOAT,

    -- Ladrillo
    ladrillo_und_teorico     FLOAT,
    ladrillo_und_pct_ajuste  FLOAT,
    ladrillo_und_final       FLOAT,

    -- Trazabilidad (punto 7)
    modelo_usado VARCHAR(50),
    ml_disponible TINYINT(1),

    -- Para el pre-test/post-test con las 30 familias:
    -- valor_real_registrado se marca en 1 cuando alguien complete a mano
    -- el valor que realmente se uso en obra (para poder calcular el PME).
    -- codigo_familia es un codigo ANONIMO (ej. "F-07"), nunca nombre/DNI.
    valor_real_registrado TINYINT(1) DEFAULT 0,
    codigo_familia VARCHAR(20)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================
-- Tabla adicional: pretest_o1
-- Guarda el valor REAL que reporto cada familia/maestro de obra
-- (el calculo tradicional, SIN el sistema). Se llena a mano o con un
-- formulario aparte, una fila por familia, y se cruza con
-- registros_uso usando codigo_familia.
-- =============================================================
USE proyecto_tesis;

CREATE TABLE IF NOT EXISTS pretest_o1 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_familia VARCHAR(20) NOT NULL UNIQUE,
    fecha_hora DATETIME NOT NULL,
    fuente_calculo VARCHAR(50) DEFAULT 'maestro de obra',  -- o 'familia'

    cemento_bolsas_real       FLOAT,
    arena_gruesa_m3_real      FLOAT,
    arena_fina_m3_real        FLOAT,
    piedra_grande_m3_real     FLOAT,
    piedra_chancada_m3_real   FLOAT,
    acero_corrugado_kg_real   FLOAT,
    ladrillo_und_real         FLOAT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
