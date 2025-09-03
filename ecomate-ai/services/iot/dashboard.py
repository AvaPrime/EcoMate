"""
IoT Dashboard

Real-time dashboard for IoT data visualization, monitoring, and analytics
with interactive charts, widgets, and customizable layouts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .models import (
    ChartType, Dashboard, DashboardWidget, IoTMessage, WidgetType, Chart, DataQuery
)


logger = logging.getLogger(__name__)


class IoTDashboard:
    """
    Real-time IoT dashboard for data visualization and monitoring.
    
    Provides interactive charts, widgets, alerts, and customizable
    dashboard layouts for IoT device monitoring and analytics.
    """
    
    def __init__(self):
        # Dashboard storage
        self.dashboards: Dict[str, Dashboard] = {}
        self.widgets: Dict[str, DashboardWidget] = {}
        self.charts: Dict[str, Chart] = {}
        
        # Real-time data streams
        self.data_streams: Dict[str, List[Dict[str, Any]]] = {}
        self.stream_subscribers: Dict[str, Set[str]] = {}  # stream_id -> dashboard_ids
        
        # Dashboard statistics
        self.stats = {
            "dashboards_created": 0,
            "widgets_created": 0,
            "charts_created": 0,
            "data_points_processed": 0,
            "real_time_updates": 0,
            "active_subscriptions": 0
        }
        
        # Data aggregation cache
        self.aggregation_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Setup default dashboards
        asyncio.create_task(self._setup_default_dashboards())
        
        # Start background tasks
        asyncio.create_task(self._data_aggregation_worker())
        asyncio.create_task(self._cache_cleanup_worker())
        
        logger.info("IoT Dashboard initialized")
    
    # Dashboard Management
    async def create_dashboard(
        self,
        name: str,
        description: str = "",
        layout: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Dashboard:
        """
        Create a new dashboard.
        
        Args:
            name: Dashboard name
            description: Dashboard description
            layout: Dashboard layout configuration
            tags: Dashboard tags
        
        Returns:
            Created dashboard
        """
        try:
            dashboard_id = str(uuid4())
            
            dashboard = Dashboard(
                dashboard_id=dashboard_id,
                name=name,
                description=description,
                widgets=[],
                layout=layout or {"type": "grid", "columns": 12},
                tags=tags or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_public=False,
                refresh_interval=30
            )
            
            self.dashboards[dashboard_id] = dashboard
            self.stats["dashboards_created"] += 1
            
            logger.info(f"Dashboard '{name}' created with ID {dashboard_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            raise
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """
        Get a dashboard by ID.
        
        Args:
            dashboard_id: Dashboard ID
        
        Returns:
            Dashboard if found, None otherwise
        """
        return self.dashboards.get(dashboard_id)
    
    async def update_dashboard(
        self,
        dashboard_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            updates: Updates to apply
        
        Returns:
            True if successful, False otherwise
        """
        try:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(dashboard, key):
                    setattr(dashboard, key, value)
            
            dashboard.updated_at = datetime.utcnow()
            
            logger.info(f"Dashboard {dashboard_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update dashboard {dashboard_id}: {e}")
            return False
    
    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """
        Delete a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if dashboard_id in self.dashboards:
                # Remove dashboard widgets
                dashboard = self.dashboards[dashboard_id]
                for widget_id in dashboard.widgets:
                    await self.delete_widget(widget_id)
                
                # Remove dashboard
                del self.dashboards[dashboard_id]
                
                # Clean up subscriptions
                for stream_id, subscribers in self.stream_subscribers.items():
                    subscribers.discard(dashboard_id)
                
                logger.info(f"Dashboard {dashboard_id} deleted")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete dashboard {dashboard_id}: {e}")
            return False
    
    async def list_dashboards(
        self,
        tags: List[str] = None,
        public_only: bool = False
    ) -> List[Dashboard]:
        """
        List dashboards with optional filtering.
        
        Args:
            tags: Filter by tags
            public_only: Only return public dashboards
        
        Returns:
            List of dashboards
        """
        try:
            dashboards = list(self.dashboards.values())
            
            # Apply filters
            if public_only:
                dashboards = [d for d in dashboards if d.is_public]
            
            if tags:
                dashboards = [
                    d for d in dashboards
                    if any(tag in d.tags for tag in tags)
                ]
            
            # Sort by creation date (newest first)
            dashboards.sort(key=lambda x: x.created_at, reverse=True)
            
            return dashboards
            
        except Exception as e:
            logger.error(f"Failed to list dashboards: {e}")
            return []
    
    # Widget Management
    async def create_widget(
        self,
        dashboard_id: str,
        widget_type: WidgetType,
        title: str,
        config: Dict[str, Any],
        position: Dict[str, int] = None
    ) -> Optional[DashboardWidget]:
        """
        Create a new widget.
        
        Args:
            dashboard_id: Dashboard ID to add widget to
            widget_type: Type of widget
            title: Widget title
            config: Widget configuration
            position: Widget position and size
        
        Returns:
            Created widget if successful, None otherwise
        """
        try:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                logger.error(f"Dashboard {dashboard_id} not found")
                return None
            
            widget_id = str(uuid4())
            
            widget = DashboardWidget(
                widget_id=widget_id,
                widget_type=widget_type,
                title=title,
                config=config,
                position=position or {"x": 0, "y": 0, "width": 6, "height": 4},
                data_source="",
                refresh_interval=30,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store widget
            self.widgets[widget_id] = widget
            
            # Add to dashboard
            dashboard.widgets.append(widget_id)
            dashboard.updated_at = datetime.utcnow()
            
            self.stats["widgets_created"] += 1
            
            logger.info(f"Widget '{title}' created with ID {widget_id}")
            return widget
            
        except Exception as e:
            logger.error(f"Failed to create widget: {e}")
            return None
    
    async def get_widget(self, widget_id: str) -> Optional[DashboardWidget]:
        """
        Get a widget by ID.
        
        Args:
            widget_id: Widget ID
        
        Returns:
            Widget if found, None otherwise
        """
        return self.widgets.get(widget_id)
    
    async def update_widget(
        self,
        widget_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a widget.
        
        Args:
            widget_id: Widget ID
            updates: Updates to apply
        
        Returns:
            True if successful, False otherwise
        """
        try:
            widget = self.widgets.get(widget_id)
            if not widget:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(widget, key):
                    setattr(widget, key, value)
            
            widget.updated_at = datetime.utcnow()
            
            logger.info(f"Widget {widget_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update widget {widget_id}: {e}")
            return False
    
    async def delete_widget(self, widget_id: str) -> bool:
        """
        Delete a widget.
        
        Args:
            widget_id: Widget ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if widget_id in self.widgets:
                # Remove from dashboards
                for dashboard in self.dashboards.values():
                    if widget_id in dashboard.widgets:
                        dashboard.widgets.remove(widget_id)
                        dashboard.updated_at = datetime.utcnow()
                
                # Remove widget
                del self.widgets[widget_id]
                
                logger.info(f"Widget {widget_id} deleted")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete widget {widget_id}: {e}")
            return False
    
    # Chart Management
    async def create_chart(
        self,
        chart_type: ChartType,
        title: str,
        data_query: DataQuery,
        config: Dict[str, Any] = None
    ) -> Chart:
        """
        Create a new chart.
        
        Args:
            chart_type: Type of chart
            title: Chart title
            data_query: Data query for the chart
            config: Chart configuration
        
        Returns:
            Created chart
        """
        try:
            chart_id = str(uuid4())
            
            chart = Chart(
                chart_id=chart_id,
                chart_type=chart_type,
                title=title,
                data_query=data_query,
                config=config or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.charts[chart_id] = chart
            self.stats["charts_created"] += 1
            
            logger.info(f"Chart '{title}' created with ID {chart_id}")
            return chart
            
        except Exception as e:
            logger.error(f"Failed to create chart: {e}")
            raise
    
    async def get_chart_data(
        self,
        chart_id: str,
        time_range: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get data for a chart.
        
        Args:
            chart_id: Chart ID
            time_range: Optional time range filter
        
        Returns:
            Chart data
        """
        try:
            chart = self.charts.get(chart_id)
            if not chart:
                return {}
            
            # Execute data query
            data = await self._execute_data_query(chart.data_query, time_range)
            
            # Format data based on chart type
            formatted_data = await self._format_chart_data(chart.chart_type, data)
            
            return {
                "chart_id": chart_id,
                "chart_type": chart.chart_type.value,
                "title": chart.title,
                "data": formatted_data,
                "config": chart.config,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get chart data for {chart_id}: {e}")
            return {}
    
    # Real-time Data Streaming
    async def process_real_time_data(self, message: IoTMessage) -> None:
        """
        Process real-time IoT data for dashboard updates.
        
        Args:
            message: IoT message to process
        """
        try:
            # Extract data points
            data_points = await self._extract_data_points(message)
            
            # Update data streams
            for stream_id, data_point in data_points.items():
                if stream_id not in self.data_streams:
                    self.data_streams[stream_id] = []
                
                self.data_streams[stream_id].append(data_point)
                
                # Keep only recent data (last 1000 points)
                if len(self.data_streams[stream_id]) > 1000:
                    self.data_streams[stream_id] = self.data_streams[stream_id][-1000:]
                
                self.stats["data_points_processed"] += 1
            
            # Notify subscribers
            await self._notify_subscribers(data_points)
            
        except Exception as e:
            logger.error(f"Failed to process real-time data: {e}")
    
    async def subscribe_to_stream(
        self,
        dashboard_id: str,
        stream_id: str
    ) -> bool:
        """
        Subscribe a dashboard to a data stream.
        
        Args:
            dashboard_id: Dashboard ID
            stream_id: Stream ID to subscribe to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if stream_id not in self.stream_subscribers:
                self.stream_subscribers[stream_id] = set()
            
            self.stream_subscribers[stream_id].add(dashboard_id)
            self.stats["active_subscriptions"] += 1
            
            logger.info(f"Dashboard {dashboard_id} subscribed to stream {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to stream: {e}")
            return False
    
    async def unsubscribe_from_stream(
        self,
        dashboard_id: str,
        stream_id: str
    ) -> bool:
        """
        Unsubscribe a dashboard from a data stream.
        
        Args:
            dashboard_id: Dashboard ID
            stream_id: Stream ID to unsubscribe from
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if stream_id in self.stream_subscribers:
                self.stream_subscribers[stream_id].discard(dashboard_id)
                
                if not self.stream_subscribers[stream_id]:
                    del self.stream_subscribers[stream_id]
                
                self.stats["active_subscriptions"] -= 1
                
                logger.info(f"Dashboard {dashboard_id} unsubscribed from stream {stream_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from stream: {e}")
            return False
    
    # Data Analytics
    async def get_device_analytics(
        self,
        device_id: str,
        time_range: Dict[str, datetime],
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific device.
        
        Args:
            device_id: Device ID
            time_range: Time range for analytics
            metrics: Specific metrics to include
        
        Returns:
            Device analytics data
        """
        try:
            # Get device data from streams
            device_streams = {
                stream_id: data for stream_id, data in self.data_streams.items()
                if stream_id.startswith(f"{device_id}:")
            }
            
            analytics = {
                "device_id": device_id,
                "time_range": {
                    "start": time_range["start"].isoformat(),
                    "end": time_range["end"].isoformat()
                },
                "metrics": {},
                "summary": {},
                "trends": {}
            }
            
            # Calculate metrics for each stream
            for stream_id, data_points in device_streams.items():
                metric_name = stream_id.split(":", 1)[1]  # Remove device_id prefix
                
                if metrics and metric_name not in metrics:
                    continue
                
                # Filter data by time range
                filtered_data = [
                    point for point in data_points
                    if time_range["start"] <= point["timestamp"] <= time_range["end"]
                ]
                
                if filtered_data:
                    values = [point["value"] for point in filtered_data if isinstance(point["value"], (int, float))]
                    
                    if values:
                        analytics["metrics"][metric_name] = {
                            "count": len(values),
                            "min": min(values),
                            "max": max(values),
                            "avg": sum(values) / len(values),
                            "latest": values[-1],
                            "data_points": filtered_data[-100:]  # Last 100 points
                        }
            
            # Calculate summary statistics
            analytics["summary"] = await self._calculate_device_summary(device_id, analytics["metrics"])
            
            # Calculate trends
            analytics["trends"] = await self._calculate_trends(analytics["metrics"])
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get device analytics: {e}")
            return {}
    
    async def get_system_analytics(
        self,
        time_range: Dict[str, datetime]
    ) -> Dict[str, Any]:
        """
        Get system-wide analytics.
        
        Args:
            time_range: Time range for analytics
        
        Returns:
            System analytics data
        """
        try:
            analytics = {
                "time_range": {
                    "start": time_range["start"].isoformat(),
                    "end": time_range["end"].isoformat()
                },
                "overview": {
                    "total_devices": len(set(
                        stream_id.split(":")[0] for stream_id in self.data_streams.keys()
                    )),
                    "total_streams": len(self.data_streams),
                    "total_dashboards": len(self.dashboards),
                    "total_widgets": len(self.widgets),
                    "active_subscriptions": self.stats["active_subscriptions"]
                },
                "activity": {},
                "performance": {},
                "top_devices": []
            }
            
            # Calculate activity metrics
            total_data_points = 0
            active_devices = set()
            
            for stream_id, data_points in self.data_streams.items():
                device_id = stream_id.split(":")[0]
                
                # Filter by time range
                filtered_points = [
                    point for point in data_points
                    if time_range["start"] <= point["timestamp"] <= time_range["end"]
                ]
                
                if filtered_points:
                    total_data_points += len(filtered_points)
                    active_devices.add(device_id)
            
            analytics["activity"] = {
                "total_data_points": total_data_points,
                "active_devices": len(active_devices),
                "avg_points_per_device": total_data_points / len(active_devices) if active_devices else 0
            }
            
            # Calculate performance metrics
            analytics["performance"] = {
                "data_processing_rate": self.stats["data_points_processed"] / 3600,  # per hour
                "real_time_updates": self.stats["real_time_updates"],
                "cache_hit_rate": await self._calculate_cache_hit_rate()
            }
            
            # Get top devices by activity
            device_activity = {}
            for stream_id, data_points in self.data_streams.items():
                device_id = stream_id.split(":")[0]
                if device_id not in device_activity:
                    device_activity[device_id] = 0
                
                filtered_points = [
                    point for point in data_points
                    if time_range["start"] <= point["timestamp"] <= time_range["end"]
                ]
                device_activity[device_id] += len(filtered_points)
            
            analytics["top_devices"] = [
                {"device_id": device_id, "data_points": count}
                for device_id, count in sorted(
                    device_activity.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            ]
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get system analytics: {e}")
            return {}
    
    # Dashboard Statistics
    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics.
        
        Returns:
            Dashboard statistics
        """
        try:
            return {
                "dashboards": {
                    "total": len(self.dashboards),
                    "public": len([d for d in self.dashboards.values() if d.is_public]),
                    "private": len([d for d in self.dashboards.values() if not d.is_public])
                },
                "widgets": {
                    "total": len(self.widgets),
                    "by_type": await self._get_widget_type_counts()
                },
                "charts": {
                    "total": len(self.charts),
                    "by_type": await self._get_chart_type_counts()
                },
                "data_streams": {
                    "total": len(self.data_streams),
                    "total_data_points": sum(len(stream) for stream in self.data_streams.values()),
                    "active_subscriptions": self.stats["active_subscriptions"]
                },
                **self.stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard statistics: {e}")
            return {}
    
    # Private Helper Methods
    async def _setup_default_dashboards(self) -> None:
        """
        Setup default dashboards.
        """
        try:
            # System Overview Dashboard
            system_dashboard = await self.create_dashboard(
                "System Overview",
                "Real-time system monitoring and device status",
                {"type": "grid", "columns": 12},
                ["system", "overview"]
            )
            
            # Add system widgets
            await self.create_widget(
                system_dashboard.dashboard_id,
                WidgetType.METRIC,
                "Active Devices",
                {
                    "metric": "active_devices",
                    "format": "number",
                    "color": "blue"
                },
                {"x": 0, "y": 0, "width": 3, "height": 2}
            )
            
            await self.create_widget(
                system_dashboard.dashboard_id,
                WidgetType.CHART,
                "Data Points Over Time",
                {
                    "chart_type": "line",
                    "data_source": "system_data_points",
                    "time_range": "1h"
                },
                {"x": 3, "y": 0, "width": 9, "height": 4}
            )
            
            # Device Status Dashboard
            device_dashboard = await self.create_dashboard(
                "Device Status",
                "Individual device monitoring and alerts",
                {"type": "grid", "columns": 12},
                ["devices", "status"]
            )
            
            # Add device widgets
            await self.create_widget(
                device_dashboard.dashboard_id,
                WidgetType.TABLE,
                "Device List",
                {
                    "columns": ["device_id", "status", "last_seen", "battery"],
                    "sortable": True,
                    "filterable": True
                },
                {"x": 0, "y": 0, "width": 12, "height": 6}
            )
            
            logger.info("Default dashboards created")
            
        except Exception as e:
            logger.error(f"Failed to setup default dashboards: {e}")
    
    async def _execute_data_query(
        self,
        query: DataQuery,
        time_range: Optional[Dict[str, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a data query.
        
        Args:
            query: Data query to execute
            time_range: Optional time range filter
        
        Returns:
            Query results
        """
        try:
            # Check cache first
            cache_key = f"{query.query_id}:{time_range}"
            if cache_key in self.aggregation_cache:
                cache_entry = self.aggregation_cache[cache_key]
                if datetime.utcnow() - cache_entry["timestamp"] < timedelta(seconds=self.cache_ttl):
                    return cache_entry["data"]
            
            # Execute query based on type
            if query.data_source.startswith("device:"):
                device_id = query.data_source.split(":", 1)[1]
                results = await self._query_device_data(device_id, query, time_range)
            elif query.data_source == "system":
                results = await self._query_system_data(query, time_range)
            else:
                # Custom data source
                results = await self._query_custom_data(query, time_range)
            
            # Cache results
            self.aggregation_cache[cache_key] = {
                "data": results,
                "timestamp": datetime.utcnow()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute data query: {e}")
            return []
    
    async def _query_device_data(
        self,
        device_id: str,
        query: DataQuery,
        time_range: Optional[Dict[str, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query data for a specific device.
        
        Args:
            device_id: Device ID
            query: Data query
            time_range: Time range filter
        
        Returns:
            Query results
        """
        results = []
        
        try:
            # Get device streams
            device_streams = {
                stream_id: data for stream_id, data in self.data_streams.items()
                if stream_id.startswith(f"{device_id}:")
            }
            
            # Apply filters
            for stream_id, data_points in device_streams.items():
                filtered_data = data_points
                
                # Time range filter
                if time_range:
                    filtered_data = [
                        point for point in filtered_data
                        if time_range["start"] <= point["timestamp"] <= time_range["end"]
                    ]
                
                # Field filters
                if query.filters:
                    for field, filter_value in query.filters.items():
                        filtered_data = [
                            point for point in filtered_data
                            if point.get(field) == filter_value
                        ]
                
                results.extend(filtered_data)
            
            # Apply aggregation
            if query.aggregation:
                results = await self._apply_aggregation(results, query.aggregation)
            
            # Apply sorting
            if query.sort_by:
                reverse = query.sort_order == "desc"
                results.sort(key=lambda x: x.get(query.sort_by, 0), reverse=reverse)
            
            # Apply limit
            if query.limit:
                results = results[:query.limit]
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query device data: {e}")
            return []
    
    async def _query_system_data(
        self,
        query: DataQuery,
        time_range: Optional[Dict[str, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query system-wide data.
        
        Args:
            query: Data query
            time_range: Time range filter
        
        Returns:
            Query results
        """
        try:
            # Generate system metrics
            now = datetime.utcnow()
            
            results = [
                {
                    "timestamp": now,
                    "metric": "active_devices",
                    "value": len(set(
                        stream_id.split(":")[0] for stream_id in self.data_streams.keys()
                    ))
                },
                {
                    "timestamp": now,
                    "metric": "total_data_points",
                    "value": sum(len(stream) for stream in self.data_streams.values())
                },
                {
                    "timestamp": now,
                    "metric": "active_dashboards",
                    "value": len(self.dashboards)
                },
                {
                    "timestamp": now,
                    "metric": "active_subscriptions",
                    "value": self.stats["active_subscriptions"]
                }
            ]
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query system data: {e}")
            return []
    
    async def _query_custom_data(
        self,
        query: DataQuery,
        time_range: Optional[Dict[str, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query custom data source.
        
        Args:
            query: Data query
            time_range: Time range filter
        
        Returns:
            Query results
        """
        # Placeholder for custom data source queries
        return []
    
    async def _apply_aggregation(
        self,
        data: List[Dict[str, Any]],
        aggregation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply aggregation to data.
        
        Args:
            data: Data to aggregate
            aggregation: Aggregation configuration
        
        Returns:
            Aggregated data
        """
        try:
            agg_type = aggregation.get("type", "none")
            group_by = aggregation.get("group_by")
            
            if agg_type == "none":
                return data
            
            # Group data if needed
            if group_by:
                groups = {}
                for item in data:
                    key = item.get(group_by, "unknown")
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(item)
                
                # Apply aggregation to each group
                results = []
                for group_key, group_data in groups.items():
                    agg_result = await self._calculate_aggregation(group_data, agg_type)
                    agg_result[group_by] = group_key
                    results.append(agg_result)
                
                return results
            else:
                # Apply aggregation to entire dataset
                return [await self._calculate_aggregation(data, agg_type)]
            
        except Exception as e:
            logger.error(f"Failed to apply aggregation: {e}")
            return data
    
    async def _calculate_aggregation(
        self,
        data: List[Dict[str, Any]],
        agg_type: str
    ) -> Dict[str, Any]:
        """
        Calculate aggregation for a dataset.
        
        Args:
            data: Data to aggregate
            agg_type: Type of aggregation
        
        Returns:
            Aggregated result
        """
        if not data:
            return {}
        
        # Extract numeric values
        values = []
        for item in data:
            value = item.get("value")
            if isinstance(value, (int, float)):
                values.append(value)
        
        if not values:
            return {"count": len(data)}
        
        result = {
            "count": len(data),
            "timestamp": data[-1].get("timestamp", datetime.utcnow())
        }
        
        if agg_type == "sum":
            result["value"] = sum(values)
        elif agg_type == "avg":
            result["value"] = sum(values) / len(values)
        elif agg_type == "min":
            result["value"] = min(values)
        elif agg_type == "max":
            result["value"] = max(values)
        elif agg_type == "count":
            result["value"] = len(values)
        
        return result
    
    async def _format_chart_data(
        self,
        chart_type: ChartType,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format data for specific chart type.
        
        Args:
            chart_type: Type of chart
            data: Raw data
        
        Returns:
            Formatted chart data
        """
        try:
            if chart_type == ChartType.LINE:
                return {
                    "labels": [item.get("timestamp", "").isoformat() if hasattr(item.get("timestamp", ""), "isoformat") else str(item.get("timestamp", "")) for item in data],
                    "datasets": [{
                        "label": "Value",
                        "data": [item.get("value", 0) for item in data],
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    }]
                }
            
            elif chart_type == ChartType.BAR:
                return {
                    "labels": [item.get("label", str(i)) for i, item in enumerate(data)],
                    "datasets": [{
                        "label": "Value",
                        "data": [item.get("value", 0) for item in data],
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "borderWidth": 1
                    }]
                }
            
            elif chart_type == ChartType.PIE:
                return {
                    "labels": [item.get("label", str(i)) for i, item in enumerate(data)],
                    "datasets": [{
                        "data": [item.get("value", 0) for item in data],
                        "backgroundColor": [
                            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
                            "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
                        ]
                    }]
                }
            
            elif chart_type == ChartType.GAUGE:
                latest_value = data[-1].get("value", 0) if data else 0
                return {
                    "value": latest_value,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "low": 30,
                        "medium": 70,
                        "high": 90
                    }
                }
            
            elif chart_type == ChartType.HEATMAP:
                # Group data by x and y coordinates
                heatmap_data = []
                for item in data:
                    heatmap_data.append({
                        "x": item.get("x", 0),
                        "y": item.get("y", 0),
                        "v": item.get("value", 0)
                    })
                
                return {"data": heatmap_data}
            
            else:
                # Default format
                return {"data": data}
            
        except Exception as e:
            logger.error(f"Failed to format chart data: {e}")
            return {"data": data}
    
    async def _extract_data_points(self, message: IoTMessage) -> Dict[str, Dict[str, Any]]:
        """
        Extract data points from an IoT message.
        
        Args:
            message: IoT message
        
        Returns:
            Dictionary of stream_id -> data_point
        """
        data_points = {}
        
        try:
            # Extract from payload
            for key, value in message.payload.items():
                stream_id = f"{message.device_id}:{key}"
                data_points[stream_id] = {
                    "timestamp": message.timestamp,
                    "value": value,
                    "device_id": message.device_id,
                    "metric": key,
                    "message_id": message.message_id
                }
            
            # Extract from sensor readings
            if message.sensor_readings:
                for reading in message.sensor_readings:
                    stream_id = f"{message.device_id}:{reading.sensor_type}"
                    data_points[stream_id] = {
                        "timestamp": reading.timestamp,
                        "value": reading.value,
                        "device_id": message.device_id,
                        "metric": reading.sensor_type,
                        "unit": reading.unit,
                        "quality": reading.quality,
                        "message_id": message.message_id
                    }
            
            return data_points
            
        except Exception as e:
            logger.error(f"Failed to extract data points: {e}")
            return {}
    
    async def _notify_subscribers(self, data_points: Dict[str, Dict[str, Any]]) -> None:
        """
        Notify dashboard subscribers of new data.
        
        Args:
            data_points: New data points
        """
        try:
            for stream_id, data_point in data_points.items():
                if stream_id in self.stream_subscribers:
                    subscribers = self.stream_subscribers[stream_id]
                    
                    for dashboard_id in subscribers:
                        # In a real implementation, this would send WebSocket updates
                        # to connected dashboard clients
                        logger.debug(f"Notifying dashboard {dashboard_id} of update to {stream_id}")
                        self.stats["real_time_updates"] += 1
            
        except Exception as e:
            logger.error(f"Failed to notify subscribers: {e}")
    
    async def _calculate_device_summary(
        self,
        device_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for a device.
        
        Args:
            device_id: Device ID
            metrics: Device metrics
        
        Returns:
            Summary statistics
        """
        try:
            summary = {
                "total_metrics": len(metrics),
                "health_score": 0.0,
                "status": "unknown",
                "last_activity": None
            }
            
            if metrics:
                # Calculate health score based on data quality and recency
                total_score = 0
                metric_count = 0
                latest_timestamp = None
                
                for metric_name, metric_data in metrics.items():
                    # Data quality score (based on count and consistency)
                    quality_score = min(1.0, metric_data["count"] / 100)  # Normalize to 100 points
                    
                    # Recency score (based on latest data)
                    if metric_data.get("data_points"):
                        latest_point = metric_data["data_points"][-1]
                        point_timestamp = latest_point["timestamp"]
                        
                        if latest_timestamp is None or point_timestamp > latest_timestamp:
                            latest_timestamp = point_timestamp
                        
                        # Calculate recency score (1.0 for data within last hour)
                        time_diff = (datetime.utcnow() - point_timestamp).total_seconds()
                        recency_score = max(0.0, 1.0 - (time_diff / 3600))  # Decay over 1 hour
                    else:
                        recency_score = 0.0
                    
                    total_score += (quality_score + recency_score) / 2
                    metric_count += 1
                
                if metric_count > 0:
                    summary["health_score"] = total_score / metric_count
                
                summary["last_activity"] = latest_timestamp.isoformat() if latest_timestamp else None
                
                # Determine status based on health score
                if summary["health_score"] >= 0.8:
                    summary["status"] = "healthy"
                elif summary["health_score"] >= 0.5:
                    summary["status"] = "warning"
                else:
                    summary["status"] = "critical"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to calculate device summary: {e}")
            return {"total_metrics": 0, "health_score": 0.0, "status": "error"}
    
    async def _calculate_trends(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate trends for metrics.
        
        Args:
            metrics: Metrics data
        
        Returns:
            Trend analysis
        """
        trends = {}
        
        try:
            for metric_name, metric_data in metrics.items():
                data_points = metric_data.get("data_points", [])
                
                if len(data_points) >= 2:
                    # Calculate simple trend (slope of linear regression)
                    values = [point["value"] for point in data_points if isinstance(point["value"], (int, float))]
                    
                    if len(values) >= 2:
                        # Simple linear trend calculation
                        n = len(values)
                        x_values = list(range(n))
                        
                        sum_x = sum(x_values)
                        sum_y = sum(values)
                        sum_xy = sum(x * y for x, y in zip(x_values, values))
                        sum_x2 = sum(x * x for x in x_values)
                        
                        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                        
                        trends[metric_name] = {
                            "direction": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
                            "slope": slope,
                            "change_rate": abs(slope),
                            "confidence": min(1.0, len(values) / 10)  # Higher confidence with more data points
                        }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {}
    
    async def _calculate_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Cache hit rate as a percentage
        """
        # Placeholder implementation
        return 0.85  # 85% hit rate
    
    async def _get_widget_type_counts(self) -> Dict[str, int]:
        """
        Get count of widgets by type.
        
        Returns:
            Widget type counts
        """
        counts = {}
        for widget in self.widgets.values():
            widget_type = widget.widget_type.value
            counts[widget_type] = counts.get(widget_type, 0) + 1
        return counts
    
    async def _get_chart_type_counts(self) -> Dict[str, int]:
        """
        Get count of charts by type.
        
        Returns:
            Chart type counts
        """
        counts = {}
        for chart in self.charts.values():
            chart_type = chart.chart_type.value
            counts[chart_type] = counts.get(chart_type, 0) + 1
        return counts
    
    # Background Workers
    async def _data_aggregation_worker(self) -> None:
        """
        Background worker for data aggregation.
        """
        while True:
            try:
                # Perform periodic data aggregation
                await self._aggregate_historical_data()
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Data aggregation worker error: {e}")
                await asyncio.sleep(60)
    
    async def _aggregate_historical_data(self) -> None:
        """
        Aggregate historical data for performance.
        """
        try:
            # Placeholder for historical data aggregation
            # In production, this would create hourly/daily aggregates
            # to improve query performance for large time ranges
            pass
            
        except Exception as e:
            logger.error(f"Historical data aggregation error: {e}")
    
    async def _cache_cleanup_worker(self) -> None:
        """
        Background worker for cache cleanup.
        """
        while True:
            try:
                # Clean up expired cache entries
                now = datetime.utcnow()
                expired_keys = [
                    key for key, entry in self.aggregation_cache.items()
                    if now - entry["timestamp"] > timedelta(seconds=self.cache_ttl)
                ]
                
                for key in expired_keys:
                    del self.aggregation_cache[key]
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                await asyncio.sleep(600)  # Run every 10 minutes
                
            except Exception as e:
                logger.error(f"Cache cleanup worker error: {e}")
                await asyncio.sleep(300)