-- Esquema de base de datos para el descubrimiento de red
-- Tabla para almacenar los resultados del ping

CREATE DATABASE IF NOT EXISTS network_discovery;

USE network_discovery;

CREATE TABLE IF NOT EXISTS ping_results (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    packets_sent INTEGER NOT NULL DEFAULT 1,
    packets_received INTEGER NOT NULL DEFAULT 0,
    packet_loss_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    latency_ms DECIMAL(10,3) NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    scan_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_time DECIMAL(10,3) NULL,
    ttl INTEGER NULL,
    CONSTRAINT unique_ip_scan UNIQUE(ip_address, scan_timestamp)
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_ip_address ON ping_results(ip_address);
CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON ping_results(scan_timestamp);
CREATE INDEX IF NOT EXISTS idx_is_active ON ping_results(is_active);

-- Vista para obtener el último escaneo de cada IP
CREATE OR REPLACE VIEW latest_ping_results AS
SELECT DISTINCT ON (ip_address) 
    ip_address,
    packets_sent,
    packets_received,
    packet_loss_percentage,
    latency_ms,
    is_active,
    scan_timestamp,
    response_time,
    ttl
FROM ping_results
ORDER BY ip_address, scan_timestamp DESC;