"""
Prometheus metrics for AI Translation Service
"""
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client.registry import REGISTRY
import time

# Translation-related metrics
translation_requests_total = Counter(
    'translation_requests_total', 
    'Total number of translation requests',
    ['status', 'user_id', 'file_type']
)

translation_request_duration = Histogram(
    'translation_request_duration_seconds',
    'Duration of translation requests',
    ['user_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

active_translations = Gauge(
    'active_translations',
    'Number of currently active translation processes'
)

translation_queue_size = Gauge(
    'translation_queue_size',
    'Size of the translation queue'
)

api_key_usage = Counter(
    'api_key_usage_total',
    'Total usage of API keys',
    ['api_key_id', 'model']
)

api_key_rate_limit = Counter(
    'api_key_rate_limit_total',
    'Number of rate limit events per API key',
    ['api_key_id']
)

# Database metrics
database_connection_errors = Counter(
    'database_connection_errors_total',
    'Total number of database connection errors'
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Duration of database queries',
    ['query_type', 'table']
)

# System metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Business metrics
successful_translations = Counter(
    'translation_requests_success_total',
    'Total number of successful translations'
)

failed_translations = Counter(
    'translation_requests_failure_total',
    'Total number of failed translations'
)

user_document_count = Counter(
    'user_document_total',
    'Total number of documents processed per user',
    ['user_id']
)

# Security metrics
authentication_failures = Counter(
    'auth_failure_total',
    'Total number of authentication failures',
    ['user_id', 'reason']
)

rate_limit_events = Counter(
    'rate_limit_events_total',
    'Total number of rate limit events',
    ['endpoint', 'user_id']
)

# File upload metrics
file_upload_size = Histogram(
    'file_upload_size_bytes',
    'Size of uploaded files',
    ['file_type'],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600]  # 1KB, 10KB, 100KB, 1MB, 10MB, 100MB
)

file_upload_duration = Histogram(
    'file_upload_duration_seconds',
    'Time taken to upload files',
    ['file_type']
)

def register_metrics():
    """Register all metrics with the instrumentator"""
    instrumentator = Instrumentator(
        excluded_handlers=["/metrics", "/health", "/docs", "/redoc"]
    )
    
    # Add default metrics
    instrumentator.add(metrics.request_size(
        should_include_handler=lambda h: h not in ["/metrics", "/health"],
        should_include_method=lambda m: m != "OPTIONS",
    ))
    
    instrumentator.add(metrics.response_size(
        should_include_handler=lambda h: h not in ["/metrics", "/health"],
        should_include_method=lambda m: m != "OPTIONS",
    ))
    
    instrumentator.add(metrics.latency(
        should_include_handler=lambda h: h not in ["/metrics", "/health"],
        should_include_method=lambda m: m != "OPTIONS",
    ))
    
    instrumentator.add(metrics.requests(
        should_include_handler=lambda h: h not in ["/metrics", "/health"],
        should_include_method=lambda m: m != "OPTIONS",
    ))
    
    return instrumentator

def increment_translation_request(user_id: str, file_type: str, status: str = "pending"):
    """Increment translation request counter"""
    translation_requests_total.labels(status=status, user_id=user_id, file_type=file_type).inc()

def observe_translation_duration(user_id: str, duration: float):
    """Observe translation request duration"""
    translation_request_duration.labels(user_id=user_id).observe(duration)

def increment_successful_translation(user_id: str):
    """Increment successful translation counter"""
    successful_translations.inc()
    translation_requests_total.labels(status="success", user_id=user_id, file_type="document").inc()

def increment_failed_translation(user_id: str, file_type: str = "document"):
    """Increment failed translation counter"""
    failed_translations.inc()
    translation_requests_total.labels(status="failure", user_id=user_id, file_type=file_type).inc()

def increment_auth_failure(user_id: str, reason: str):
    """Increment authentication failure counter"""
    authentication_failures.labels(user_id=user_id, reason=reason).inc()

def increment_rate_limit(endpoint: str, user_id: str = "anonymous"):
    """Increment rate limit counter"""
    rate_limit_events.labels(endpoint=endpoint, user_id=user_id).inc()
    api_key_rate_limit.labels(api_key_id=user_id).inc()

def observe_file_upload(size: int, file_type: str, duration: float):
    """Observe file upload metrics"""
    file_upload_size.labels(file_type=file_type).observe(size)
    file_upload_duration.labels(file_type=file_type).observe(duration)

def get_application_metrics():
    """Get application-specific metrics"""
    return REGISTRY