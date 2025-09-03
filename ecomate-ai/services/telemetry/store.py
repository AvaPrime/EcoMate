from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import asyncpg
import numpy as np
from contextlib import asynccontextmanager
import logging
from .models import (
    TelemetryData, DynamicBaseline, BaselineConfig, Alert, AlertRule,
    TelemetryQuery, TelemetryResponse, BaselineResponse, AlertResponse,
    AlertSeverity, AlertStatus
)

logger = logging.getLogger(__name__)

class TelemetryStore:
    """Time series data store for telemetry data with dynamic baseline management."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool and create tables."""
        self._pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        await self._create_tables()
        logger.info("TelemetryStore initialized successfully")
    
    async def close(self):
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("TelemetryStore closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self._pool:
            raise RuntimeError("TelemetryStore not initialized")
        
        async with self._pool.acquire() as conn:
            yield conn
    
    async def _create_tables(self):
        """Create necessary tables for telemetry data storage."""
        async with self.get_connection() as conn:
            # Enable TimescaleDB extension if available
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
                logger.info("TimescaleDB extension enabled")
            except Exception as e:
                logger.warning(f"TimescaleDB not available, using regular PostgreSQL: {e}")
            
            # Create telemetry_data table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_data (
                    id SERIAL PRIMARY KEY,
                    system_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    unit VARCHAR(50),
                    quality_score DOUBLE PRECISION DEFAULT 1.0,
                    source VARCHAR(100) DEFAULT 'api',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create hypertable if TimescaleDB is available
            try:
                await conn.execute("""
                    SELECT create_hypertable('telemetry_data', 'timestamp', 
                                           chunk_time_interval => INTERVAL '1 day',
                                           if_not_exists => TRUE);
                """)
                logger.info("Created TimescaleDB hypertable for telemetry_data")
            except Exception as e:
                logger.info(f"Using regular table for telemetry_data: {e}")
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_system_time 
                ON telemetry_data (system_id, timestamp DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_metric_time 
                ON telemetry_data (metric_type, timestamp DESC);
            """)
            
            # Create baseline_configs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS baseline_configs (
                    id SERIAL PRIMARY KEY,
                    system_id VARCHAR(255) NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    window_size INTEGER DEFAULT 60,
                    update_frequency INTEGER DEFAULT 300,
                    min_samples INTEGER DEFAULT 10,
                    outlier_threshold DOUBLE PRECISION DEFAULT 3.0,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(system_id, metric_type)
                );
            """)
            
            # Create dynamic_baselines table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dynamic_baselines (
                    id SERIAL PRIMARY KEY,
                    system_id VARCHAR(255) NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    mean_value DOUBLE PRECISION NOT NULL,
                    std_deviation DOUBLE PRECISION NOT NULL,
                    min_value DOUBLE PRECISION NOT NULL,
                    max_value DOUBLE PRECISION NOT NULL,
                    sample_count INTEGER NOT NULL,
                    confidence_interval DOUBLE PRECISION DEFAULT 0.95,
                    last_updated TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(system_id, metric_type)
                );
            """)
            
            # Create alert_rules table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id SERIAL PRIMARY KEY,
                    system_id VARCHAR(255) NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    rule_name VARCHAR(255) NOT NULL,
                    condition VARCHAR(100) NOT NULL,
                    threshold_value DOUBLE PRECISION,
                    baseline_multiplier DOUBLE PRECISION,
                    severity VARCHAR(20) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    cooldown_minutes INTEGER DEFAULT 15,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    system_id VARCHAR(255) NOT NULL,
                    rule_id INTEGER REFERENCES alert_rules(id),
                    metric_type VARCHAR(100) NOT NULL,
                    alert_message TEXT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    triggered_value DOUBLE PRECISION NOT NULL,
                    baseline_value DOUBLE PRECISION,
                    threshold_value DOUBLE PRECISION,
                    triggered_at TIMESTAMPTZ DEFAULT NOW(),
                    acknowledged_at TIMESTAMPTZ,
                    resolved_at TIMESTAMPTZ,
                    acknowledged_by VARCHAR(255),
                    resolution_notes TEXT
                );
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_system_status 
                ON alerts (system_id, status, triggered_at DESC);
            """)
    
    async def store_telemetry_batch(self, data_points: List[TelemetryData]) -> bool:
        """Store multiple telemetry data points efficiently."""
        if not data_points:
            return True
        
        async with self.get_connection() as conn:
            try:
                # Prepare batch insert
                values = [
                    (dp.system_id, dp.timestamp, dp.metric_type, dp.value, 
                     dp.unit, dp.quality_score, dp.source)
                    for dp in data_points
                ]
                
                await conn.executemany("""
                    INSERT INTO telemetry_data 
                    (system_id, timestamp, metric_type, value, unit, quality_score, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, values)
                
                logger.info(f"Stored {len(data_points)} telemetry data points")
                return True
            except Exception as e:
                logger.error(f"Failed to store telemetry batch: {e}")
                return False
    
    async def query_telemetry(self, query: TelemetryQuery) -> TelemetryResponse:
        """Query telemetry data with filtering and aggregation."""
        async with self.get_connection() as conn:
            # Build query conditions
            conditions = ["system_id = $1"]
            params = [query.system_id]
            param_count = 1
            
            if query.metric_types:
                param_count += 1
                conditions.append(f"metric_type = ANY(${param_count})")
                params.append(query.metric_types)
            
            if query.start_time:
                param_count += 1
                conditions.append(f"timestamp >= ${param_count}")
                params.append(query.start_time)
            
            if query.end_time:
                param_count += 1
                conditions.append(f"timestamp <= ${param_count}")
                params.append(query.end_time)
            
            where_clause = " AND ".join(conditions)
            
            # Build aggregation query if needed
            if query.aggregation and query.interval:
                select_clause = f"""
                    time_bucket('{query.interval}', timestamp) as timestamp,
                    metric_type,
                    {query.aggregation}(value) as value
                """
                group_clause = "GROUP BY time_bucket('{query.interval}', timestamp), metric_type"
            else:
                select_clause = "timestamp, metric_type, value, unit, quality_score, source"
                group_clause = ""
            
            # Execute query
            sql = f"""
                SELECT {select_clause}
                FROM telemetry_data 
                WHERE {where_clause}
                {group_clause}
                ORDER BY timestamp DESC
                LIMIT {query.limit}
            """
            
            start_time = datetime.utcnow()
            rows = await conn.fetch(sql, *params)
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Convert to TelemetryData objects
            data = []
            for row in rows:
                if query.aggregation:
                    data.append(TelemetryData(
                        system_id=query.system_id,
                        timestamp=row['timestamp'],
                        metric_type=row['metric_type'],
                        value=row['value']
                    ))
                else:
                    data.append(TelemetryData(
                        system_id=query.system_id,
                        timestamp=row['timestamp'],
                        metric_type=row['metric_type'],
                        value=row['value'],
                        unit=row.get('unit'),
                        quality_score=row.get('quality_score', 1.0),
                        source=row.get('source', 'api')
                    ))
            
            return TelemetryResponse(
                system_id=query.system_id,
                data=data,
                total_count=len(data),
                has_more=len(data) == query.limit,
                query_time_ms=query_time
            )
    
    async def calculate_dynamic_baseline(self, system_id: str, metric_type: str, 
                                       config: Optional[BaselineConfig] = None) -> Optional[DynamicBaseline]:
        """Calculate dynamic baseline for a metric using recent data."""
        if not config:
            config = await self.get_baseline_config(system_id, metric_type)
            if not config:
                # Create default config
                config = BaselineConfig(system_id=system_id, metric_type=metric_type)
                await self.save_baseline_config(config)
        
        async with self.get_connection() as conn:
            # Get recent data points
            rows = await conn.fetch("""
                SELECT value FROM telemetry_data 
                WHERE system_id = $1 AND metric_type = $2 
                  AND quality_score >= 0.8
                  AND timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC 
                LIMIT $3
            """, system_id, metric_type, config.window_size)
            
            if len(rows) < config.min_samples:
                logger.warning(f"Insufficient data for baseline calculation: {len(rows)} < {config.min_samples}")
                return None
            
            values = np.array([row['value'] for row in rows])
            
            # Remove outliers using z-score
            z_scores = np.abs((values - np.mean(values)) / np.std(values))
            filtered_values = values[z_scores < config.outlier_threshold]
            
            if len(filtered_values) < config.min_samples:
                logger.warning(f"Too many outliers removed, using original data")
                filtered_values = values
            
            # Calculate statistics
            baseline = DynamicBaseline(
                system_id=system_id,
                metric_type=metric_type,
                mean_value=float(np.mean(filtered_values)),
                std_deviation=float(np.std(filtered_values)),
                min_value=float(np.min(filtered_values)),
                max_value=float(np.max(filtered_values)),
                sample_count=len(filtered_values),
                last_updated=datetime.utcnow()
            )
            
            # Save baseline
            await self.save_dynamic_baseline(baseline)
            return baseline
    
    async def save_dynamic_baseline(self, baseline: DynamicBaseline) -> bool:
        """Save or update dynamic baseline."""
        async with self.get_connection() as conn:
            try:
                await conn.execute("""
                    INSERT INTO dynamic_baselines 
                    (system_id, metric_type, mean_value, std_deviation, min_value, 
                     max_value, sample_count, confidence_interval, last_updated)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (system_id, metric_type) 
                    DO UPDATE SET 
                        mean_value = EXCLUDED.mean_value,
                        std_deviation = EXCLUDED.std_deviation,
                        min_value = EXCLUDED.min_value,
                        max_value = EXCLUDED.max_value,
                        sample_count = EXCLUDED.sample_count,
                        confidence_interval = EXCLUDED.confidence_interval,
                        last_updated = EXCLUDED.last_updated
                """, baseline.system_id, baseline.metric_type, baseline.mean_value,
                baseline.std_deviation, baseline.min_value, baseline.max_value,
                baseline.sample_count, baseline.confidence_interval, baseline.last_updated)
                return True
            except Exception as e:
                logger.error(f"Failed to save baseline: {e}")
                return False
    
    async def get_dynamic_baseline(self, system_id: str, metric_type: str) -> Optional[DynamicBaseline]:
        """Get current dynamic baseline for a metric."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM dynamic_baselines 
                WHERE system_id = $1 AND metric_type = $2
            """, system_id, metric_type)
            
            if row:
                return DynamicBaseline(**dict(row))
            return None
    
    async def get_system_baselines(self, system_id: str) -> BaselineResponse:
        """Get all baselines for a system."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM dynamic_baselines 
                WHERE system_id = $1
                ORDER BY metric_type
            """, system_id)
            
            baselines = [DynamicBaseline(**dict(row)) for row in rows]
            last_updated = max([b.last_updated for b in baselines]) if baselines else datetime.utcnow()
            
            return BaselineResponse(
                system_id=system_id,
                baselines=baselines,
                last_updated=last_updated
            )
    
    async def save_baseline_config(self, config: BaselineConfig) -> bool:
        """Save baseline configuration."""
        async with self.get_connection() as conn:
            try:
                await conn.execute("""
                    INSERT INTO baseline_configs 
                    (system_id, metric_type, window_size, update_frequency, min_samples, 
                     outlier_threshold, enabled)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (system_id, metric_type) 
                    DO UPDATE SET 
                        window_size = EXCLUDED.window_size,
                        update_frequency = EXCLUDED.update_frequency,
                        min_samples = EXCLUDED.min_samples,
                        outlier_threshold = EXCLUDED.outlier_threshold,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                """, config.system_id, config.metric_type, config.window_size,
                config.update_frequency, config.min_samples, config.outlier_threshold,
                config.enabled)
                return True
            except Exception as e:
                logger.error(f"Failed to save baseline config: {e}")
                return False
    
    async def get_baseline_config(self, system_id: str, metric_type: str) -> Optional[BaselineConfig]:
        """Get baseline configuration."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM baseline_configs 
                WHERE system_id = $1 AND metric_type = $2
            """, system_id, metric_type)
            
            if row:
                return BaselineConfig(**dict(row))
            return None
    
    async def save_alert_rule(self, rule: AlertRule) -> int:
        """Save alert rule and return its ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                INSERT INTO alert_rules 
                (system_id, metric_type, rule_name, condition, threshold_value, 
                 baseline_multiplier, severity, enabled, cooldown_minutes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, rule.system_id, rule.metric_type, rule.rule_name, rule.condition,
            rule.threshold_value, rule.baseline_multiplier, rule.severity.value,
            rule.enabled, rule.cooldown_minutes)
            
            return row['id']
    
    async def save_alert(self, alert: Alert) -> int:
        """Save alert and return its ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                INSERT INTO alerts 
                (system_id, rule_id, metric_type, alert_message, severity, status,
                 triggered_value, baseline_value, threshold_value)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, alert.system_id, alert.rule_id, alert.metric_type, alert.alert_message,
            alert.severity.value, alert.status.value, alert.triggered_value,
            alert.baseline_value, alert.threshold_value)
            
            return row['id']
    
    async def get_active_alerts(self, system_id: str) -> AlertResponse:
        """Get active alerts for a system."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT a.*, ar.rule_name, ar.condition 
                FROM alerts a
                JOIN alert_rules ar ON a.rule_id = ar.id
                WHERE a.system_id = $1 AND a.status = 'active'
                ORDER BY a.triggered_at DESC
            """, system_id)
            
            alerts = []
            for row in rows:
                alert_dict = dict(row)
                # Remove extra fields from join
                alert_dict.pop('rule_name', None)
                alert_dict.pop('condition', None)
                alerts.append(Alert(**alert_dict))
            
            total_count = len(alerts)
            critical_count = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
            
            return AlertResponse(
                alerts=alerts,
                total_count=total_count,
                active_count=total_count,
                critical_count=critical_count
            )
    
    async def update_baselines_for_system(self, system_id: str) -> Dict[str, bool]:
        """Update all baselines for a system based on recent data."""
        async with self.get_connection() as conn:
            # Get distinct metric types for the system
            rows = await conn.fetch("""
                SELECT DISTINCT metric_type FROM telemetry_data 
                WHERE system_id = $1 
                  AND timestamp >= NOW() - INTERVAL '24 hours'
            """, system_id)
            
            results = {}
            for row in rows:
                metric_type = row['metric_type']
                try:
                    baseline = await self.calculate_dynamic_baseline(system_id, metric_type)
                    results[metric_type] = baseline is not None
                except Exception as e:
                    logger.error(f"Failed to update baseline for {metric_type}: {e}")
                    results[metric_type] = False
            
            return results

# Global store instance
_store: Optional[TelemetryStore] = None

async def get_telemetry_store() -> TelemetryStore:
    """Get global telemetry store instance."""
    global _store
    if _store is None:
        # This should be configured from environment variables
        connection_string = "postgresql://user:password@localhost:5432/ecomate"
        _store = TelemetryStore(connection_string)
        await _store.initialize()
    return _store

async def close_telemetry_store():
    """Close global telemetry store."""
    global _store
    if _store:
        await _store.close()
        _store = None