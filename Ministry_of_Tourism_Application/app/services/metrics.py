"""
Prometheus metrics for MoD Core
"""
import time
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from typing import Optional

# Create custom registry for clean metrics
registry = CollectorRegistry()

# API Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# Business Metrics
tourists_total = Gauge(
    'tourists_total',
    'Total number of tourists currently monitored',
    registry=registry
)

active_alerts = Gauge(
    'active_alerts_total',
    'Number of active alerts by type',
    ['alert_type'],
    registry=registry
)

sos_incidents_24h = Gauge(
    'sos_incidents_24h_total',
    'SOS incidents in the last 24 hours',
    registry=registry
)

# Database Metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=registry
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation'],
    registry=registry
)

# Geofencing Metrics
geofence_hits_total = Counter(
    'geofence_hits_total',
    'Total geofence violations',
    ['geofence_type', 'severity'],
    registry=registry
)

near_red_zone_total = Gauge(
    'near_red_zone_total',
    'Number of tourists currently near red zones',
    registry=registry
)

# Device Metrics
# Police Stream Metrics
stream_clients_connected = Gauge(
    'stream_clients_connected',
    'Number of connected SSE clients',
    registry=registry
)

stream_events_sent = Counter(
    'stream_events_sent_total',
    'Total events sent via SSE',
    ['event_type'],
    registry=registry
)

# Case Management Metrics
open_cases_total = Gauge(
    'open_cases_total',
    'Number of currently open cases',
    registry=registry
)

cases_responded_24h = Gauge(
    'cases_responded_24h_total',
    'Cases responded to in last 24 hours',
    registry=registry
)

# Alert Lifecycle Metrics
alerts_created_total = Counter(
    'alerts_created_total',
    'Total alerts created',
    ['alert_type', 'priority'],
    registry=registry
)

alerts_acknowledged_total = Counter(
    'alerts_acknowledged_total',
    'Total alerts acknowledged',
    ['alert_type'],
    registry=registry
)

# System Health Metrics
system_uptime_seconds = Gauge(
    'system_uptime_seconds',
    'System uptime in seconds',
    registry=registry
)

memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['type'],
    registry=registry
)


def setup_metrics():
    """Initialize metrics collection."""
    import psutil
    import os
    
    # Set initial system metrics
    process = psutil.Process(os.getpid())
    memory_usage_bytes.labels(type='rss').set(process.memory_info().rss)
    memory_usage_bytes.labels(type='vms').set(process.memory_info().vms)


def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """Track API request metrics."""
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()
    
    api_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_alert_created(alert_type: str, priority: str):
    """Track alert creation."""
    alerts_created_total.labels(
        alert_type=alert_type,
        priority=priority
    ).inc()


def track_alert_acknowledged(alert_type: str):
    """Track alert acknowledgment."""
    alerts_acknowledged_total.labels(alert_type=alert_type).inc()


def track_geofence_hit(geofence_type: str, severity: int):
    """Track geofence violations."""
    geofence_hits_total.labels(
        geofence_type=geofence_type,
        severity=str(severity)
    ).inc()




def track_stream_event(event_type: str):
    """Track SSE stream events."""
    stream_events_sent.labels(event_type=event_type).inc()


def update_tourist_count(count: int):
    """Update total tourist count."""
    tourists_total.set(count)


def update_active_alerts(alert_type: str, count: int):
    """Update active alerts count by type."""
    active_alerts.labels(alert_type=alert_type).set(count)



def update_near_red_zone_count(count: int):
    """Update near red zone count."""
    near_red_zone_total.set(count)


def update_open_cases_count(count: int):
    """Update open cases count."""
    open_cases_total.set(count)


def update_stream_clients(count: int):
    """Update connected stream clients count."""
    stream_clients_connected.set(count)


def get_metrics() -> str:
    """Get metrics in Prometheus format."""
    return generate_latest(registry).decode('utf-8')


class MetricsMiddleware:
    """Middleware to automatically track request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                method = scope["method"]
                path = scope["path"]
                status_code = message["status"]
                
                track_request(method, path, status_code, duration)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
