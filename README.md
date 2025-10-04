# Proyecto de Descubrimiento de Red

![NMAP Scan](nmap_scan_image.png)

## Descripción del Proyecto

Este proyecto implementa un sistema integral de descubrimiento de red utilizando comandos ping para escanear redes universitarias y almacenar los resultados en una base de datos PostgreSQL. El sistema captura estadísticas de red incluyendo pérdida de paquetes, latencia y disponibilidad de hosts.

## Archivos en este Proyecto

### 1. network_discovery_db.py
**Script Principal de Python**
- Realiza descubrimiento de red usando comandos ping
- Escanea rangos IP (por defecto: 192.168.137.0/24 - red universitaria)
- Almacena resultados de ping en base de datos PostgreSQL
- Captura métricas: paquetes enviados/recibidos, latencia, TTL, timestamp
- Escaneo multi-hilo para mejorar rendimiento
- Manejo integral de errores y logging

**Características Principales:**
- Escaneo de rangos de red con CIDR configurable
- Monitoreo de progreso en tiempo real
- Gestión de conexión a base de datos
- Análisis de latencia y estadísticas
- Soporte multiplataforma para ping (Windows/Linux)

### 2. database_schema.sql
**Definición del Esquema de Base de Datos**
- Crea estructura de tabla PostgreSQL para resultados de ping
- Define todos los campos requeridos con tipos de datos apropiados
- Incluye índices optimizados para rendimiento de consultas
- Establece restricciones y valores por defecto

**Estructura de la Tabla:**
- `id`: Clave primaria serial
- `ip_address`: Tipo INET para direcciones IP
- `packets_sent`: Entero (por defecto: 1)
- `packets_received`: Entero
- `packet_loss_percentage`: Decimal(5,2)
- `latency_ms`: Decimal(10,3) para latencia en milisegundos
- `is_active`: Bandera booleana para estado del host
- `scan_timestamp`: Timestamp del escaneo
- `response_time`: Decimal(10,3) para tiempo de respuesta
- `ttl`: Entero para valor Time To Live

### 3. requirements_network.txt
**Dependencias de Python**
- Lista todos los paquetes Python requeridos
- `psycopg2-binary`: Adaptador PostgreSQL para Python
- `ipaddress`: Librería de manipulación de direcciones IP

## Instalación y Configuración

1. **Instalar Dependencias de Python:**
   ```bash
   pip install -r requirements_network.txt
   ```

2. **Configurar Base de Datos PostgreSQL:**
   ```bash
   psql -U postgres -f database_schema.sql
   ```

3. **Configurar Conexión a Base de Datos:**
   Editar la configuración de base de datos en `network_discovery_db.py`:
   ```python
   db_config = {
       'host': 'localhost',
       'database': 'network_discovery',
       'user': 'postgres',
       'password': 'tu_contraseña',
       'port': 5432
   }
   ```

## Uso

**Ejecutar Descubrimiento de Red:**
```bash
python network_discovery_db.py
```

**Consultar Resultados por Segmento IP (Clase C):**
```sql
SELECT 
    SUBSTRING(ip_address::text FROM '^(\d+\.\d+\.\d+)\.') as segmento,
    AVG(latency_ms) as latencia_promedio_ms,
    COUNT(*) as total_hosts
FROM ping_results 
WHERE latency_ms IS NOT NULL
GROUP BY SUBSTRING(ip_address::text FROM '^(\d+\.\d+\.\d+)\.')
ORDER BY segmento;
```

**Encontrar Latencia para Patrón IP Específico (ej., código 7004185 = .185):**
```sql
SELECT 
    AVG(latency_ms) as latencia_promedio_ms
FROM ping_results 
WHERE ip_address::text LIKE '%.185'
AND latency_ms IS NOT NULL;
```

## Características de Análisis de Red

- **Descubrimiento de Hosts**: Identificar hosts activos en rangos de red
- **Medición de Latencia**: Capturar tiempos de respuesta en milisegundos
- **Análisis de Pérdida de Paquetes**: Rastrear confiabilidad de conexión
- **Seguimiento Temporal**: Monitorear cambios de red a través del tiempo
- **Análisis por Segmentos**: Agrupar resultados por segmentos IP Clase C

## Especificaciones Técnicas

- **Red Objetivo**: 192.168.137.0/24 (red universitaria)
- **Parámetros de Ping**: Un paquete por host (-n 1 en Windows, -c 1 en Linux)
- **Timeout**: 3 segundos por ping
- **Concurrencia**: Ejecución multi-hilo (workers configurables)
- **Base de Datos**: PostgreSQL con esquema optimizado
- **Logging**: Logging integral a archivo y consola

## Autor

Sistema de Descubrimiento de Red para Análisis de Red Universitaria
Código: 7004185