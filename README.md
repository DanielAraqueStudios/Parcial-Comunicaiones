# Network Discovery Project

![NMAP Scan](nmap_scan_image.png)

## Project Description

This project implements a comprehensive network discovery system using ping commands to scan university networks and store the results in a PostgreSQL database. The system captures network statistics including packet loss, latency, and host availability.

## Files in this Project

### 1. network_discovery_db.py
**Main Python Script**
- Performs network discovery using ping commands
- Scans IP ranges (default: 192.168.137.0/24 - university network)
- Stores ping results in PostgreSQL database
- Captures metrics: packets sent/received, latency, TTL, timestamp
- Multi-threaded scanning for improved performance
- Comprehensive error handling and logging

**Key Features:**
- Network range scanning with configurable CIDR
- Real-time progress monitoring
- Database connection management
- Latency analysis and statistics
- Cross-platform ping support (Windows/Linux)

### 2. database_schema.sql
**Database Schema Definition**
- Creates PostgreSQL table structure for ping results
- Defines all required fields with appropriate data types
- Includes optimized indexes for query performance
- Sets up constraints and default values

**Table Structure:**
- `id`: Serial primary key
- `ip_address`: INET type for IP addresses
- `packets_sent`: Integer (default: 1)
- `packets_received`: Integer 
- `packet_loss_percentage`: Decimal(5,2)
- `latency_ms`: Decimal(10,3) for latency in milliseconds
- `is_active`: Boolean flag for host status
- `scan_timestamp`: Timestamp of the scan
- `response_time`: Decimal(10,3) for response time
- `ttl`: Integer for Time To Live value

### 3. requirements_network.txt
**Python Dependencies**
- Lists all required Python packages
- `psycopg2-binary`: PostgreSQL adapter for Python
- `ipaddress`: IP address manipulation library

## Installation and Setup

1. **Install Python Dependencies:**
   ```bash
   pip install -r requirements_network.txt
   ```

2. **Setup PostgreSQL Database:**
   ```bash
   psql -U postgres -f database_schema.sql
   ```

3. **Configure Database Connection:**
   Edit the database configuration in `network_discovery_db.py`:
   ```python
   db_config = {
       'host': 'localhost',
       'database': 'network_discovery',
       'user': 'postgres',
       'password': 'your_password',
       'port': 5432
   }
   ```

## Usage

**Run Network Discovery:**
```bash
python network_discovery_db.py
```

**Query Results by IP Segment (Class C):**
```sql
SELECT 
    SUBSTRING(ip_address::text FROM '^(\d+\.\d+\.\d+)\.') as segment,
    AVG(latency_ms) as avg_latency_ms,
    COUNT(*) as total_hosts
FROM ping_results 
WHERE latency_ms IS NOT NULL
GROUP BY SUBSTRING(ip_address::text FROM '^(\d+\.\d+\.\d+)\.')
ORDER BY segment;
```

**Find Latency for Specific IP Pattern (e.g., code 7004185 = .185):**
```sql
SELECT 
    AVG(latency_ms) as avg_latency_ms
FROM ping_results 
WHERE ip_address::text LIKE '%.185'
AND latency_ms IS NOT NULL;
```

## Network Analysis Features

- **Host Discovery**: Identify active hosts in network ranges
- **Latency Measurement**: Capture response times in milliseconds
- **Packet Loss Analysis**: Track connection reliability
- **Temporal Tracking**: Monitor network changes over time
- **Segment Analysis**: Group results by IP Class C segments

## Technical Specifications

- **Target Network**: 192.168.137.0/24 (university network)
- **Ping Parameters**: Single packet per host (-n 1 on Windows, -c 1 on Linux)
- **Timeout**: 3 seconds per ping
- **Concurrency**: Multi-threaded execution (configurable workers)
- **Database**: PostgreSQL with optimized schema
- **Logging**: Comprehensive logging to file and console

## Author

Network Discovery System for University Network Analysis
Code: 7004185