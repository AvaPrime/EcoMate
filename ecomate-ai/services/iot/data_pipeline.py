"""
IoT Data Pipeline

Real-time data processing pipeline for IoT messages with transformation,
validation, routing, and storage capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .models import (
    IoTMessage, MessageType, ProcessingStage, TransformationRule
)


logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Real-time IoT data processing pipeline.
    
    Provides message transformation, validation, routing, aggregation,
    and storage with configurable processing stages and rules.
    """
    
    def __init__(self):
        self.transformation_rules: Dict[str, TransformationRule] = {}
        self.processing_stages: List[ProcessingStage] = []
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.data_validators: Dict[str, Callable] = {}
        self.storage_backends: Dict[str, Any] = {}
        
        # Processing queues
        self.input_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self.processing_queue: asyncio.Queue = asyncio.Queue(maxsize=5000)
        self.output_queue: asyncio.Queue = asyncio.Queue(maxsize=5000)
        
        # Processing statistics
        self.stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "messages_dropped": 0,
            "transformation_count": 0,
            "validation_failures": 0,
            "storage_writes": 0,
            "processing_time_total": 0.0,
            "queue_sizes": {}
        }
        
        # Processing workers
        self.workers: List[asyncio.Task] = []
        self.running = False
        
        # Setup default processing stages
        self._setup_default_stages()
        
        logger.info("Data pipeline initialized")
    
    async def start(self, num_workers: int = 4) -> None:
        """
        Start the data pipeline with specified number of workers.
        
        Args:
            num_workers: Number of processing workers to start
        """
        try:
            self.running = True
            
            # Start processing workers
            for i in range(num_workers):
                worker = asyncio.create_task(self._processing_worker(f"worker-{i}"))
                self.workers.append(worker)
            
            # Start queue monitoring
            asyncio.create_task(self._monitor_queues())
            
            # Start statistics collection
            asyncio.create_task(self._collect_statistics())
            
            logger.info(f"Data pipeline started with {num_workers} workers")
            
        except Exception as e:
            logger.error(f"Failed to start data pipeline: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the data pipeline and all workers.
        """
        try:
            self.running = False
            
            # Cancel all workers
            for worker in self.workers:
                worker.cancel()
            
            # Wait for workers to finish
            if self.workers:
                await asyncio.gather(*self.workers, return_exceptions=True)
            
            self.workers.clear()
            
            logger.info("Data pipeline stopped")
            
        except Exception as e:
            logger.error(f"Error stopping data pipeline: {e}")
    
    # Message Processing
    async def process_message(self, message: IoTMessage) -> bool:
        """
        Add a message to the processing pipeline.
        
        Args:
            message: IoT message to process
        
        Returns:
            True if message was queued successfully, False otherwise
        """
        try:
            # Check queue capacity
            if self.input_queue.full():
                logger.warning("Input queue full, dropping message")
                self.stats["messages_dropped"] += 1
                return False
            
            # Add to input queue
            await self.input_queue.put(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue message for processing: {e}")
            return False
    
    async def process_batch_messages(self, messages: List[IoTMessage]) -> Dict[str, bool]:
        """
        Process multiple messages in batch.
        
        Args:
            messages: List of IoT messages to process
        
        Returns:
            Dictionary mapping message IDs to processing success status
        """
        results = {}
        
        for message in messages:
            results[message.message_id] = await self.process_message(message)
        
        return results
    
    # Transformation Rules
    async def add_transformation_rule(self, rule: TransformationRule) -> bool:
        """
        Add a transformation rule to the pipeline.
        
        Args:
            rule: Transformation rule to add
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.transformation_rules[rule.rule_id] = rule
            logger.info(f"Transformation rule '{rule.name}' added")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add transformation rule: {e}")
            return False
    
    async def remove_transformation_rule(self, rule_id: str) -> bool:
        """
        Remove a transformation rule from the pipeline.
        
        Args:
            rule_id: ID of the rule to remove
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if rule_id in self.transformation_rules:
                del self.transformation_rules[rule_id]
                logger.info(f"Transformation rule {rule_id} removed")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove transformation rule {rule_id}: {e}")
            return False
    
    async def update_transformation_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a transformation rule.
        
        Args:
            rule_id: ID of the rule to update
            updates: Dictionary of updates to apply
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if rule_id in self.transformation_rules:
                rule = self.transformation_rules[rule_id]
                
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                
                rule.updated_at = datetime.utcnow()
                logger.info(f"Transformation rule {rule_id} updated")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update transformation rule {rule_id}: {e}")
            return False
    
    # Message Handlers
    def add_message_handler(
        self,
        message_type: MessageType,
        handler: Callable[[IoTMessage], None]
    ) -> None:
        """
        Add a message handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
        logger.info(f"Message handler added for type {message_type.value}")
    
    def remove_message_handler(
        self,
        message_type: MessageType,
        handler: Callable[[IoTMessage], None]
    ) -> bool:
        """
        Remove a message handler.
        
        Args:
            message_type: Type of message
            handler: Handler function to remove
        
        Returns:
            True if handler was removed, False otherwise
        """
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type].remove(handler)
                logger.info(f"Message handler removed for type {message_type.value}")
                return True
            except ValueError:
                pass
        
        return False
    
    # Data Validation
    def add_data_validator(self, validator_name: str, validator: Callable[[Any], bool]) -> None:
        """
        Add a data validator.
        
        Args:
            validator_name: Name of the validator
            validator: Validator function
        """
        self.data_validators[validator_name] = validator
        logger.info(f"Data validator '{validator_name}' added")
    
    def remove_data_validator(self, validator_name: str) -> bool:
        """
        Remove a data validator.
        
        Args:
            validator_name: Name of the validator to remove
        
        Returns:
            True if validator was removed, False otherwise
        """
        if validator_name in self.data_validators:
            del self.data_validators[validator_name]
            logger.info(f"Data validator '{validator_name}' removed")
            return True
        return False
    
    # Storage Backends
    def add_storage_backend(self, backend_name: str, backend: Any) -> None:
        """
        Add a storage backend.
        
        Args:
            backend_name: Name of the storage backend
            backend: Storage backend instance
        """
        self.storage_backends[backend_name] = backend
        logger.info(f"Storage backend '{backend_name}' added")
    
    def remove_storage_backend(self, backend_name: str) -> bool:
        """
        Remove a storage backend.
        
        Args:
            backend_name: Name of the backend to remove
        
        Returns:
            True if backend was removed, False otherwise
        """
        if backend_name in self.storage_backends:
            del self.storage_backends[backend_name]
            logger.info(f"Storage backend '{backend_name}' removed")
            return True
        return False
    
    # Statistics and Monitoring
    async def get_pipeline_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline statistics.
        
        Returns:
            Dictionary containing pipeline statistics
        """
        try:
            # Calculate processing rate
            processing_rate = 0.0
            if self.stats["processing_time_total"] > 0:
                processing_rate = self.stats["messages_processed"] / self.stats["processing_time_total"]
            
            # Calculate error rate
            total_messages = self.stats["messages_processed"] + self.stats["messages_failed"]
            error_rate = 0.0
            if total_messages > 0:
                error_rate = self.stats["messages_failed"] / total_messages
            
            return {
                "pipeline_status": "running" if self.running else "stopped",
                "active_workers": len([w for w in self.workers if not w.done()]),
                "total_workers": len(self.workers),
                "messages_processed": self.stats["messages_processed"],
                "messages_failed": self.stats["messages_failed"],
                "messages_dropped": self.stats["messages_dropped"],
                "processing_rate_per_second": processing_rate,
                "error_rate": error_rate,
                "transformation_rules": len(self.transformation_rules),
                "message_handlers": sum(len(handlers) for handlers in self.message_handlers.values()),
                "data_validators": len(self.data_validators),
                "storage_backends": len(self.storage_backends),
                "queue_sizes": {
                    "input": self.input_queue.qsize(),
                    "processing": self.processing_queue.qsize(),
                    "output": self.output_queue.qsize()
                },
                **self.stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline statistics: {e}")
            return {}
    
    async def get_transformation_rules(self) -> List[TransformationRule]:
        """
        Get all transformation rules.
        
        Returns:
            List of transformation rules
        """
        return list(self.transformation_rules.values())
    
    # Private Processing Methods
    async def _processing_worker(self, worker_name: str) -> None:
        """
        Main processing worker loop.
        
        Args:
            worker_name: Name of the worker for logging
        """
        logger.info(f"Processing worker {worker_name} started")
        
        while self.running:
            try:
                # Get message from input queue
                try:
                    message = await asyncio.wait_for(
                        self.input_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the message
                start_time = datetime.utcnow()
                success = await self._process_single_message(message)
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update statistics
                if success:
                    self.stats["messages_processed"] += 1
                else:
                    self.stats["messages_failed"] += 1
                
                self.stats["processing_time_total"] += processing_time
                
                # Mark task as done
                self.input_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                self.stats["messages_failed"] += 1
                await asyncio.sleep(1)  # Brief pause on error
        
        logger.info(f"Processing worker {worker_name} stopped")
    
    async def _process_single_message(self, message: IoTMessage) -> bool:
        """
        Process a single message through all pipeline stages.
        
        Args:
            message: Message to process
        
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Stage 1: Validation
            if not await self._validate_message(message):
                logger.warning(f"Message validation failed: {message.message_id}")
                return False
            
            # Stage 2: Transformation
            transformed_message = await self._apply_transformations(message)
            if not transformed_message:
                logger.warning(f"Message transformation failed: {message.message_id}")
                return False
            
            # Stage 3: Enrichment
            enriched_message = await self._enrich_message(transformed_message)
            
            # Stage 4: Routing and Handling
            await self._route_message(enriched_message)
            
            # Stage 5: Storage
            await self._store_message(enriched_message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process message {message.message_id}: {e}")
            return False
    
    async def _validate_message(self, message: IoTMessage) -> bool:
        """
        Validate a message using configured validators.
        
        Args:
            message: Message to validate
        
        Returns:
            True if message is valid, False otherwise
        """
        try:
            # Basic message structure validation
            if not message.device_id or not message.message_id:
                return False
            
            # Check timestamp validity
            now = datetime.utcnow()
            if message.timestamp > now + timedelta(minutes=5):  # Future timestamp
                return False
            if message.timestamp < now - timedelta(days=1):  # Too old
                return False
            
            # Apply custom validators
            for validator_name, validator in self.data_validators.items():
                try:
                    if not validator(message):
                        logger.warning(f"Validation failed: {validator_name} for message {message.message_id}")
                        self.stats["validation_failures"] += 1
                        return False
                except Exception as e:
                    logger.error(f"Validator {validator_name} error: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Message validation error: {e}")
            return False
    
    async def _apply_transformations(self, message: IoTMessage) -> Optional[IoTMessage]:
        """
        Apply transformation rules to a message.
        
        Args:
            message: Message to transform
        
        Returns:
            Transformed message or None if transformation failed
        """
        try:
            transformed_message = message
            
            # Apply applicable transformation rules
            for rule in self.transformation_rules.values():
                if not rule.enabled:
                    continue
                
                # Check if rule applies to this message
                if await self._rule_applies(rule, transformed_message):
                    transformed_message = await self._apply_transformation_rule(
                        rule, transformed_message
                    )
                    
                    if not transformed_message:
                        logger.error(f"Transformation rule {rule.name} failed")
                        return None
                    
                    self.stats["transformation_count"] += 1
            
            return transformed_message
            
        except Exception as e:
            logger.error(f"Transformation error: {e}")
            return None
    
    async def _rule_applies(self, rule: TransformationRule, message: IoTMessage) -> bool:
        """
        Check if a transformation rule applies to a message.
        
        Args:
            rule: Transformation rule
            message: Message to check
        
        Returns:
            True if rule applies, False otherwise
        """
        try:
            # Check device ID filter
            if rule.device_filter and message.device_id not in rule.device_filter:
                return False
            
            # Check message type filter
            if rule.message_type_filter and message.message_type not in rule.message_type_filter:
                return False
            
            # Check condition (simplified evaluation)
            if rule.condition:
                # In production, this would use a proper expression evaluator
                condition = rule.condition.lower()
                
                if "message_type ==" in condition:
                    expected_type = condition.split("==")[1].strip().strip("'\"")
                    return message.message_type.value == expected_type
                
                if "device_id contains" in condition:
                    search_term = condition.split("contains")[1].strip().strip("'\"")
                    return search_term in message.device_id
            
            return True
            
        except Exception as e:
            logger.error(f"Rule condition evaluation error: {e}")
            return False
    
    async def _apply_transformation_rule(
        self,
        rule: TransformationRule,
        message: IoTMessage
    ) -> Optional[IoTMessage]:
        """
        Apply a specific transformation rule to a message.
        
        Args:
            rule: Transformation rule to apply
            message: Message to transform
        
        Returns:
            Transformed message or None if transformation failed
        """
        try:
            # Create a copy of the message for transformation
            transformed_message = IoTMessage(
                device_id=message.device_id,
                message_id=message.message_id,
                message_type=message.message_type,
                timestamp=message.timestamp,
                payload=message.payload.copy(),
                sensor_readings=message.sensor_readings.copy() if message.sensor_readings else [],
                priority=message.priority,
                format=message.format,
                metadata=message.metadata.copy() if message.metadata else {}
            )
            
            # Apply transformations based on rule type
            for transformation in rule.transformations:
                transformation_type = transformation.get("type")
                
                if transformation_type == "field_mapping":
                    await self._apply_field_mapping(transformed_message, transformation)
                elif transformation_type == "unit_conversion":
                    await self._apply_unit_conversion(transformed_message, transformation)
                elif transformation_type == "data_filtering":
                    await self._apply_data_filtering(transformed_message, transformation)
                elif transformation_type == "aggregation":
                    await self._apply_aggregation(transformed_message, transformation)
                elif transformation_type == "normalization":
                    await self._apply_normalization(transformed_message, transformation)
                else:
                    logger.warning(f"Unknown transformation type: {transformation_type}")
            
            return transformed_message
            
        except Exception as e:
            logger.error(f"Transformation rule application error: {e}")
            return None
    
    async def _apply_field_mapping(
        self,
        message: IoTMessage,
        transformation: Dict[str, Any]
    ) -> None:
        """
        Apply field mapping transformation.
        
        Args:
            message: Message to transform
            transformation: Transformation configuration
        """
        try:
            mapping = transformation.get("mapping", {})
            
            for old_field, new_field in mapping.items():
                if old_field in message.payload:
                    message.payload[new_field] = message.payload.pop(old_field)
            
        except Exception as e:
            logger.error(f"Field mapping error: {e}")
    
    async def _apply_unit_conversion(
        self,
        message: IoTMessage,
        transformation: Dict[str, Any]
    ) -> None:
        """
        Apply unit conversion transformation.
        
        Args:
            message: Message to transform
            transformation: Transformation configuration
        """
        try:
            conversions = transformation.get("conversions", {})
            
            for field, conversion in conversions.items():
                if field in message.payload:
                    value = message.payload[field]
                    from_unit = conversion.get("from")
                    to_unit = conversion.get("to")
                    factor = conversion.get("factor", 1.0)
                    
                    # Apply conversion
                    if isinstance(value, (int, float)):
                        message.payload[field] = value * factor
                        
                        # Update metadata to reflect unit change
                        if "units" not in message.metadata:
                            message.metadata["units"] = {}
                        message.metadata["units"][field] = to_unit
            
        except Exception as e:
            logger.error(f"Unit conversion error: {e}")
    
    async def _apply_data_filtering(
        self,
        message: IoTMessage,
        transformation: Dict[str, Any]
    ) -> None:
        """
        Apply data filtering transformation.
        
        Args:
            message: Message to transform
            transformation: Transformation configuration
        """
        try:
            filters = transformation.get("filters", {})
            
            for field, filter_config in filters.items():
                if field in message.payload:
                    value = message.payload[field]
                    
                    # Apply range filter
                    if "min" in filter_config and value < filter_config["min"]:
                        del message.payload[field]
                        continue
                    
                    if "max" in filter_config and value > filter_config["max"]:
                        del message.payload[field]
                        continue
                    
                    # Apply value filter
                    if "allowed_values" in filter_config:
                        if value not in filter_config["allowed_values"]:
                            del message.payload[field]
            
        except Exception as e:
            logger.error(f"Data filtering error: {e}")
    
    async def _apply_aggregation(
        self,
        message: IoTMessage,
        transformation: Dict[str, Any]
    ) -> None:
        """
        Apply aggregation transformation.
        
        Args:
            message: Message to transform
            transformation: Transformation configuration
        """
        try:
            # Placeholder for aggregation logic
            # In production, this would implement various aggregation functions
            aggregations = transformation.get("aggregations", {})
            
            for field, agg_config in aggregations.items():
                agg_type = agg_config.get("type", "avg")
                
                # Simple aggregation example
                if field in message.payload and isinstance(message.payload[field], list):
                    values = message.payload[field]
                    
                    if agg_type == "avg":
                        message.payload[field] = sum(values) / len(values)
                    elif agg_type == "sum":
                        message.payload[field] = sum(values)
                    elif agg_type == "max":
                        message.payload[field] = max(values)
                    elif agg_type == "min":
                        message.payload[field] = min(values)
            
        except Exception as e:
            logger.error(f"Aggregation error: {e}")
    
    async def _apply_normalization(
        self,
        message: IoTMessage,
        transformation: Dict[str, Any]
    ) -> None:
        """
        Apply normalization transformation.
        
        Args:
            message: Message to transform
            transformation: Transformation configuration
        """
        try:
            normalizations = transformation.get("normalizations", {})
            
            for field, norm_config in normalizations.items():
                if field in message.payload:
                    value = message.payload[field]
                    
                    if isinstance(value, (int, float)):
                        min_val = norm_config.get("min", 0)
                        max_val = norm_config.get("max", 100)
                        
                        # Min-max normalization
                        normalized_value = (value - min_val) / (max_val - min_val)
                        message.payload[field] = max(0, min(1, normalized_value))
            
        except Exception as e:
            logger.error(f"Normalization error: {e}")
    
    async def _enrich_message(self, message: IoTMessage) -> IoTMessage:
        """
        Enrich a message with additional context and metadata.
        
        Args:
            message: Message to enrich
        
        Returns:
            Enriched message
        """
        try:
            # Add processing timestamp
            if "processing" not in message.metadata:
                message.metadata["processing"] = {}
            
            message.metadata["processing"]["pipeline_timestamp"] = datetime.utcnow().isoformat()
            message.metadata["processing"]["pipeline_version"] = "1.0"
            
            # Add data quality metrics
            quality_score = await self._calculate_data_quality(message)
            message.metadata["data_quality"] = quality_score
            
            return message
            
        except Exception as e:
            logger.error(f"Message enrichment error: {e}")
            return message
    
    async def _calculate_data_quality(self, message: IoTMessage) -> float:
        """
        Calculate data quality score for a message.
        
        Args:
            message: Message to evaluate
        
        Returns:
            Data quality score between 0.0 and 1.0
        """
        try:
            score = 1.0
            
            # Check for missing required fields
            required_fields = ["device_id", "timestamp"]
            for field in required_fields:
                if not getattr(message, field, None):
                    score -= 0.2
            
            # Check payload completeness
            if not message.payload:
                score -= 0.3
            
            # Check sensor readings quality
            if message.sensor_readings:
                total_readings = len(message.sensor_readings)
                quality_readings = sum(
                    1 for reading in message.sensor_readings
                    if reading.quality is None or reading.quality >= 0.8
                )
                
                if total_readings > 0:
                    reading_quality = quality_readings / total_readings
                    score *= reading_quality
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Data quality calculation error: {e}")
            return 0.5  # Default to medium quality on error
    
    async def _route_message(self, message: IoTMessage) -> None:
        """
        Route a message to appropriate handlers.
        
        Args:
            message: Message to route
        """
        try:
            # Get handlers for message type
            handlers = self.message_handlers.get(message.message_type, [])
            
            # Execute handlers
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Message handler error: {e}")
            
        except Exception as e:
            logger.error(f"Message routing error: {e}")
    
    async def _store_message(self, message: IoTMessage) -> None:
        """
        Store a message using configured storage backends.
        
        Args:
            message: Message to store
        """
        try:
            # Store in all configured backends
            for backend_name, backend in self.storage_backends.items():
                try:
                    if hasattr(backend, 'store_message'):
                        if asyncio.iscoroutinefunction(backend.store_message):
                            await backend.store_message(message)
                        else:
                            backend.store_message(message)
                        
                        self.stats["storage_writes"] += 1
                    
                except Exception as e:
                    logger.error(f"Storage backend {backend_name} error: {e}")
            
        except Exception as e:
            logger.error(f"Message storage error: {e}")
    
    def _setup_default_stages(self) -> None:
        """
        Setup default processing stages.
        """
        self.processing_stages = [
            ProcessingStage.VALIDATION,
            ProcessingStage.TRANSFORMATION,
            ProcessingStage.ENRICHMENT,
            ProcessingStage.ROUTING,
            ProcessingStage.STORAGE
        ]
    
    async def _monitor_queues(self) -> None:
        """
        Monitor queue sizes and health.
        """
        while self.running:
            try:
                self.stats["queue_sizes"] = {
                    "input": self.input_queue.qsize(),
                    "processing": self.processing_queue.qsize(),
                    "output": self.output_queue.qsize()
                }
                
                # Log warnings for full queues
                if self.input_queue.qsize() > self.input_queue.maxsize * 0.8:
                    logger.warning("Input queue is nearly full")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Queue monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _collect_statistics(self) -> None:
        """
        Collect and log pipeline statistics.
        """
        while self.running:
            try:
                stats = await self.get_pipeline_statistics()
                
                # Log statistics periodically
                logger.info(
                    f"Pipeline stats - Processed: {stats['messages_processed']}, "
                    f"Failed: {stats['messages_failed']}, "
                    f"Rate: {stats['processing_rate_per_second']:.2f}/sec, "
                    f"Error Rate: {stats['error_rate']:.3f}"
                )
                
                await asyncio.sleep(60)  # Log every minute
                
            except Exception as e:
                logger.error(f"Statistics collection error: {e}")
                await asyncio.sleep(60)