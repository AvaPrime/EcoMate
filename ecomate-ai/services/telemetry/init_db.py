#!/usr/bin/env python3
"""
Database initialization script for enhanced telemetry system.
This script creates the necessary tables for time-series data storage,
dynamic baselines, and alert management.
"""

import asyncio
import asyncpg
import os
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', 5432)),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', 'password'),
    'database': os.getenv('PGDATABASE', 'ecomate')
}

# SQL statements for table creation
CREATE_TABLES_SQL = [
    # Enable TimescaleDB extension (if available)
    """
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    """,
    
    # Telemetry data table (time-series)
    """
    CREATE TABLE IF NOT EXISTS telemetry_data (
        id BIGSERIAL PRIMARY KEY,
        system_id VARCHAR(255) NOT NULL,
        metric_type VARCHAR(100) NOT NULL,
        value DOUBLE PRECISION NOT NULL,
        unit VARCHAR(50),
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        quality_flags JSONB DEFAULT '{}',
        source VARCHAR(100),
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        -- Indexes for efficient querying
        INDEX idx_telemetry_system_time (system_id, timestamp DESC),
        INDEX idx_telemetry_metric_time (metric_type, timestamp DESC),
        INDEX idx_telemetry_system_metric (system_id, metric_type),
        INDEX idx_telemetry_timestamp (timestamp DESC)
    );
    """,
    
    # Convert to hypertable for TimescaleDB (if extension is available)
    """
    SELECT create_hypertable('telemetry_data', 'timestamp', 
                           chunk_time_interval => INTERVAL '1 day',
                           if_not_exists => TRUE);
    """,
    
    # Baseline configurations table
    """
    CREATE TABLE IF NOT EXISTS baseline_configs (
        id BIGSERIAL PRIMARY KEY,
        system_id VARCHAR(255) NOT NULL,
        metric_type VARCHAR(100) NOT NULL,
        calculation_method VARCHAR(50) NOT NULL DEFAULT 'rolling_mean',
        window_size_hours INTEGER NOT NULL DEFAULT 24,
        min_data_points INTEGER NOT NULL DEFAULT 10,
        outlier_threshold DOUBLE PRECISION DEFAULT 3.0,
        update_frequency_minutes INTEGER NOT NULL DEFAULT 60,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        -- Unique constraint
        UNIQUE(system_id, metric_type),
        
        -- Indexes
        INDEX idx_baseline_config_system (system_id),
        INDEX idx_baseline_config_active (is_active)
    );
    """,
    
    # Dynamic baselines table
    """
    CREATE TABLE IF NOT EXISTS dynamic_baselines (
        id BIGSERIAL PRIMARY KEY,
        system_id VARCHAR(255) NOT NULL,
        metric_type VARCHAR(100) NOT NULL,
        baseline_value DOUBLE PRECISION NOT NULL,
        std_deviation DOUBLE PRECISION,
        confidence_interval_lower DOUBLE PRECISION,
        confidence_interval_upper DOUBLE PRECISION,
        data_points_used INTEGER NOT NULL,
        calculation_window_start TIMESTAMPTZ NOT NULL,
        calculation_window_end TIMESTAMPTZ NOT NULL,
        calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}',
        
        -- Indexes
        INDEX idx_baseline_system_metric (system_id, metric_type),
        INDEX idx_baseline_calculated (calculated_at DESC),
        INDEX idx_baseline_expires (expires_at)
    );
    """,
    
    # Alert rules table
    """
    CREATE TABLE IF NOT EXISTS alert_rules (
        id BIGSERIAL PRIMARY KEY,
        system_id VARCHAR(255) NOT NULL,
        metric_type VARCHAR(100) NOT NULL,
        rule_name VARCHAR(255) NOT NULL,
        condition_type VARCHAR(50) NOT NULL, -- 'threshold', 'deviation', 'trend'
        threshold_value DOUBLE PRECISION,
        deviation_multiplier DOUBLE PRECISION DEFAULT 2.0,
        severity VARCHAR(20) NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        notification_channels JSONB DEFAULT '[]',
        cooldown_minutes INTEGER DEFAULT 30,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        -- Indexes
        INDEX idx_alert_rules_system (system_id),
        INDEX idx_alert_rules_active (is_active),
        INDEX idx_alert_rules_metric (metric_type)
    );
    """,
    
    # Alerts table
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id BIGSERIAL PRIMARY KEY,
        system_id VARCHAR(255) NOT NULL,
        metric_type VARCHAR(100) NOT NULL,
        alert_rule_id BIGINT REFERENCES alert_rules(id),
        severity VARCHAR(20) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'acknowledged', 'resolved'
        title VARCHAR(500) NOT NULL,
        description TEXT,
        current_value DOUBLE PRECISION NOT NULL,
        baseline_value DOUBLE PRECISION,
        threshold_value DOUBLE PRECISION,
        deviation_amount DOUBLE PRECISION,
        triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        acknowledged_at TIMESTAMPTZ,
        resolved_at TIMESTAMPTZ,
        acknowledged_by VARCHAR(255),
        resolved_by VARCHAR(255),
        metadata JSONB DEFAULT '{}',
        
        -- Indexes
        INDEX idx_alerts_system (system_id),
        INDEX idx_alerts_status (status),
        INDEX idx_alerts_severity (severity),
        INDEX idx_alerts_triggered (triggered_at DESC),
        INDEX idx_alerts_system_active (system_id, status) WHERE status = 'active'
    );
    """,
    
    # Create updated_at trigger function
    """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """,
    
    # Add updated_at triggers
    """
    DROP TRIGGER IF EXISTS update_baseline_configs_updated_at ON baseline_configs;
    CREATE TRIGGER update_baseline_configs_updated_at
        BEFORE UPDATE ON baseline_configs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """,
    
    """
    DROP TRIGGER IF EXISTS update_alert_rules_updated_at ON alert_rules;
    CREATE TRIGGER update_alert_rules_updated_at
        BEFORE UPDATE ON alert_rules
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
]

# Sample data for testing
SAMPLE_DATA_SQL = [
    # Sample baseline configurations
    """
    INSERT INTO baseline_configs (system_id, metric_type, calculation_method, window_size_hours, min_data_points)
    VALUES 
        ('system_001', 'flow_m3h', 'rolling_mean', 24, 10),
        ('system_001', 'uv_dose_mj_cm2', 'rolling_mean', 24, 10),
        ('system_002', 'flow_m3h', 'rolling_mean', 48, 15),
        ('system_002', 'uv_dose_mj_cm2', 'rolling_mean', 48, 15)
    ON CONFLICT (system_id, metric_type) DO NOTHING;
    """,
    
    # Sample alert rules
    """
    INSERT INTO alert_rules (system_id, metric_type, rule_name, condition_type, deviation_multiplier, severity)
    VALUES 
        ('system_001', 'flow_m3h', 'Low Flow Alert', 'deviation', 2.0, 'high'),
        ('system_001', 'uv_dose_mj_cm2', 'Low UV Dose Alert', 'deviation', 2.0, 'medium'),
        ('system_002', 'flow_m3h', 'Flow Deviation Alert', 'deviation', 1.5, 'medium'),
        ('system_002', 'uv_dose_mj_cm2', 'UV Dose Deviation Alert', 'deviation', 1.5, 'medium')
    ON CONFLICT DO NOTHING;
    """
]

async def create_database_connection() -> asyncpg.Connection:
    """Create a database connection."""
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

async def execute_sql_statements(conn: asyncpg.Connection, statements: list, description: str):
    """Execute a list of SQL statements."""
    logger.info(f"Executing {description}...")
    
    for i, statement in enumerate(statements, 1):
        try:
            # Skip empty statements
            if not statement.strip():
                continue
                
            logger.info(f"Executing statement {i}/{len(statements)}")
            await conn.execute(statement)
            logger.info(f"Statement {i} executed successfully")
            
        except Exception as e:
            # For TimescaleDB-specific operations, log warning but continue
            if "timescaledb" in str(e).lower() or "hypertable" in str(e).lower():
                logger.warning(f"TimescaleDB operation failed (continuing): {e}")
                continue
            else:
                logger.error(f"Failed to execute statement {i}: {e}")
                logger.error(f"Statement: {statement[:200]}...")
                raise
    
    logger.info(f"{description} completed successfully")

async def check_table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    """Check if a table exists."""
    result = await conn.fetchval(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
        table_name
    )
    return result

async def get_table_row_count(conn: asyncpg.Connection, table_name: str) -> int:
    """Get the row count for a table."""
    try:
        result = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        return result
    except Exception:
        return 0

async def verify_installation(conn: asyncpg.Connection):
    """Verify that all tables were created successfully."""
    logger.info("Verifying installation...")
    
    expected_tables = [
        'telemetry_data',
        'baseline_configs', 
        'dynamic_baselines',
        'alert_rules',
        'alerts'
    ]
    
    for table in expected_tables:
        exists = await check_table_exists(conn, table)
        if exists:
            row_count = await get_table_row_count(conn, table)
            logger.info(f"✓ Table '{table}' exists with {row_count} rows")
        else:
            logger.error(f"✗ Table '{table}' does not exist")
            raise Exception(f"Table {table} was not created")
    
    logger.info("Installation verification completed successfully")

async def init_telemetry_database(include_sample_data: bool = True):
    """Initialize the telemetry database with all required tables."""
    conn = None
    try:
        logger.info("Starting telemetry database initialization...")
        
        # Create connection
        conn = await create_database_connection()
        
        # Execute table creation statements
        await execute_sql_statements(conn, CREATE_TABLES_SQL, "table creation")
        
        # Insert sample data if requested
        if include_sample_data:
            await execute_sql_statements(conn, SAMPLE_DATA_SQL, "sample data insertion")
        
        # Verify installation
        await verify_installation(conn)
        
        logger.info("Telemetry database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed")

async def drop_telemetry_tables():
    """Drop all telemetry tables (for cleanup/reset)."""
    conn = None
    try:
        logger.warning("Dropping all telemetry tables...")
        
        conn = await create_database_connection()
        
        drop_statements = [
            "DROP TABLE IF EXISTS alerts CASCADE;",
            "DROP TABLE IF EXISTS alert_rules CASCADE;",
            "DROP TABLE IF EXISTS dynamic_baselines CASCADE;",
            "DROP TABLE IF EXISTS baseline_configs CASCADE;",
            "DROP TABLE IF EXISTS telemetry_data CASCADE;",
            "DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;"
        ]
        
        await execute_sql_statements(conn, drop_statements, "table dropping")
        
        logger.warning("All telemetry tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize telemetry database")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables first")
    parser.add_argument("--no-sample-data", action="store_true", help="Skip sample data insertion")
    
    args = parser.parse_args()
    
    async def main():
        try:
            if args.drop:
                await drop_telemetry_tables()
            
            await init_telemetry_database(include_sample_data=not args.no_sample_data)
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            exit(1)
    
    # Run the initialization
    asyncio.run(main())