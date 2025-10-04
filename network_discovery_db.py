#!/usr/bin/env python3
"""
Script de Descubrimiento de Red Universitaria
Descubre hosts en la red de la universidad usando ping y almacena los resultados en PostgreSQL
Autor: Sistema de Descubrimiento de Red
Fecha: 2025-10-04
"""

import subprocess
import ipaddress
import time
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_discovery.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NetworkDiscovery:
    def __init__(self, db_config):
        """
        Inicializa el descubridor de red con configuración de base de datos
        
        Args:
            db_config (dict): Configuración de conexión a PostgreSQL
        """
        self.db_config = db_config
        self.connection = None
        self.lock = threading.Lock()
        
    def connect_database(self):
        """Establece conexión con la base de datos PostgreSQL"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            logger.info("Conexión a base de datos establecida exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            return False
    
    def create_table_if_not_exists(self):
        """Crea la tabla ping_results si no existe"""
        try:
            cursor = self.connection.cursor()
            create_table_sql = """
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
                ttl INTEGER NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_ip_address ON ping_results(ip_address);
            CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON ping_results(scan_timestamp);
            CREATE INDEX IF NOT EXISTS idx_is_active ON ping_results(is_active);
            """
            cursor.execute(create_table_sql)
            cursor.close()
            logger.info("Tabla ping_results verificada/creada")
            return True
        except Exception as e:
            logger.error(f"Error creando tabla: {e}")
            return False
    
    def ping_host(self, ip_address):
        """
        Ejecuta ping a una dirección IP específica y extrae estadísticas
        
        Args:
            ip_address (str): Dirección IP a hacer ping
            
        Returns:
            dict: Resultado del ping con estadísticas
        """
        result = {
            'ip_address': ip_address,
            'packets_sent': 1,
            'packets_received': 0,
            'packet_loss_percentage': 100.0,
            'latency_ms': None,
            'is_active': False,
            'response_time': None,
            'ttl': None,
            'scan_timestamp': datetime.now()
        }
        
        try:
            # Comando ping para Windows
            if os.name == 'nt':
                cmd = ['ping', '-n', '1', '-w', '3000', ip_address]
            else:
                # Comando ping para Linux/Unix
                cmd = ['ping', '-c', '1', '-W', '3', ip_address]
            
            # Ejecutar ping
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if process.returncode == 0:
                result['is_active'] = True
                result['packets_received'] = 1
                result['packet_loss_percentage'] = 0.0
                
                # Extraer latencia del output
                output = process.stdout
                
                if os.name == 'nt':
                    # Parsing para Windows
                    time_match = re.search(r'tiempo[<=\s]*(\d+)ms', output, re.IGNORECASE)
                    ttl_match = re.search(r'TTL=(\d+)', output)
                else:
                    # Parsing para Linux/Unix
                    time_match = re.search(r'time=(\d+\.?\d*)ms', output)
                    ttl_match = re.search(r'ttl=(\d+)', output)
                
                if time_match:
                    latency = float(time_match.group(1))
                    result['latency_ms'] = latency
                    result['response_time'] = latency
                
                if ttl_match:
                    result['ttl'] = int(ttl_match.group(1))
                
                logger.info(f"✓ {ip_address} - ACTIVO (latencia: {result['latency_ms']}ms)")
            else:
                logger.info(f"✗ {ip_address} - INACTIVO")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠ {ip_address} - TIMEOUT")
        except Exception as e:
            logger.error(f"✗ {ip_address} - ERROR: {e}")
            
        return result
    
    def save_ping_result(self, ping_result):
        """
        Guarda el resultado del ping en la base de datos
        
        Args:
            ping_result (dict): Resultado del ping a guardar
        """
        try:
            with self.lock:
                cursor = self.connection.cursor()
                
                insert_sql = """
                INSERT INTO ping_results (
                    ip_address, packets_sent, packets_received, 
                    packet_loss_percentage, latency_ms, is_active,
                    scan_timestamp, response_time, ttl
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                cursor.execute(insert_sql, (
                    ping_result['ip_address'],
                    ping_result['packets_sent'],
                    ping_result['packets_received'],
                    ping_result['packet_loss_percentage'],
                    ping_result['latency_ms'],
                    ping_result['is_active'],
                    ping_result['scan_timestamp'],
                    ping_result['response_time'],
                    ping_result['ttl']
                ))
                
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error guardando resultado para {ping_result['ip_address']}: {e}")
    
    def scan_network_range(self, network_cidr="192.168.137.0/24", max_workers=50):
        """
        Escanea un rango completo de red usando ping
        
        Args:
            network_cidr (str): Red en formato CIDR (ej: 192.168.137.0/24)
            max_workers (int): Número máximo de threads concurrentes
        """
        logger.info(f"Iniciando escaneo de red: {network_cidr}")
        
        try:
            network = ipaddress.IPv4Network(network_cidr, strict=False)
            total_hosts = sum(1 for _ in network.hosts())
            scanned_hosts = 0
            active_hosts = 0
            
            logger.info(f"Total de hosts a escanear: {total_hosts}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar trabajos de ping
                future_to_ip = {
                    executor.submit(self.ping_host, str(ip)): str(ip) 
                    for ip in network.hosts()
                }
                
                # Procesar resultados conforme van llegando
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        ping_result = future.result()
                        self.save_ping_result(ping_result)
                        
                        scanned_hosts += 1
                        if ping_result['is_active']:
                            active_hosts += 1
                        
                        # Mostrar progreso cada 10 hosts
                        if scanned_hosts % 10 == 0:
                            progress = (scanned_hosts / total_hosts) * 100
                            logger.info(f"Progreso: {progress:.1f}% ({scanned_hosts}/{total_hosts}) - Activos: {active_hosts}")
                            
                    except Exception as e:
                        logger.error(f"Error procesando {ip}: {e}")
            
            logger.info(f"Escaneo completado: {active_hosts}/{total_hosts} hosts activos")
            return {
                'total_hosts': total_hosts,
                'scanned_hosts': scanned_hosts,
                'active_hosts': active_hosts,
                'success_rate': (scanned_hosts / total_hosts) * 100
            }
            
        except Exception as e:
            logger.error(f"Error durante el escaneo de red: {e}")
            return None
    
    def get_scan_summary(self):
        """Obtiene un resumen de los resultados del último escaneo"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            summary_sql = """
            SELECT 
                COUNT(*) as total_scanned,
                COUNT(*) FILTER (WHERE is_active = true) as active_hosts,
                COUNT(*) FILTER (WHERE is_active = false) as inactive_hosts,
                AVG(latency_ms) FILTER (WHERE latency_ms IS NOT NULL) as avg_latency,
                MIN(latency_ms) FILTER (WHERE latency_ms IS NOT NULL) as min_latency,
                MAX(latency_ms) FILTER (WHERE latency_ms IS NOT NULL) as max_latency,
                MAX(scan_timestamp) as last_scan
            FROM ping_results 
            WHERE scan_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            """
            
            cursor.execute(summary_sql)
            summary = cursor.fetchone()
            cursor.close()
            
            return dict(summary) if summary else None
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            return None
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("Conexión a base de datos cerrada")

def main():
    """Función principal del script"""
    
    # Configuración de la base de datos PostgreSQL
    db_config = {
        'host': 'localhost',
        'database': 'network_discovery',
        'user': 'postgres',
        'password': 'password',  # Cambiar por la contraseña real
        'port': 5432
    }
    
    # Crear instancia del descubridor
    discovery = NetworkDiscovery(db_config)
    
    try:
        # Conectar a la base de datos
        if not discovery.connect_database():
            logger.error("No se pudo conectar a la base de datos. Terminando...")
            return
        
        # Crear tabla si no existe
        if not discovery.create_table_if_not_exists():
            logger.error("No se pudo crear/verificar la tabla. Terminando...")
            return
        
        # Escanear la red de la universidad
        logger.info("=" * 60)
        logger.info("INICIANDO DESCUBRIMIENTO DE RED UNIVERSITARIA")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Ejecutar escaneo
        results = discovery.scan_network_range("192.168.137.0/24")
        
        end_time = time.time()
        scan_duration = end_time - start_time
        
        if results:
            logger.info("=" * 60)
            logger.info("RESUMEN DEL ESCANEO")
            logger.info("=" * 60)
            logger.info(f"Tiempo total: {scan_duration:.2f} segundos")
            logger.info(f"Hosts totales: {results['total_hosts']}")
            logger.info(f"Hosts escaneados: {results['scanned_hosts']}")
            logger.info(f"Hosts activos: {results['active_hosts']}")
            logger.info(f"Tasa de éxito: {results['success_rate']:.1f}%")
            
            # Obtener resumen detallado de la base de datos
            summary = discovery.get_scan_summary()
            if summary:
                logger.info("=" * 60)
                logger.info("ESTADÍSTICAS DETALLADAS")
                logger.info("=" * 60)
                logger.info(f"Latencia promedio: {summary['avg_latency']:.2f}ms" if summary['avg_latency'] else "Latencia promedio: N/A")
                logger.info(f"Latencia mínima: {summary['min_latency']:.2f}ms" if summary['min_latency'] else "Latencia mínima: N/A")
                logger.info(f"Latencia máxima: {summary['max_latency']:.2f}ms" if summary['max_latency'] else "Latencia máxima: N/A")
        
    except KeyboardInterrupt:
        logger.info("Escaneo interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
    finally:
        discovery.close_connection()
        logger.info("Script finalizado")

if __name__ == "__main__":
    main()