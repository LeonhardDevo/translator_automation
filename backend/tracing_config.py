"""
OpenTelemetry tracing configuration for AI Translation Service
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import os

def setup_tracing(service_name: str = "ai-translation-service"):
    """Setup OpenTelemetry tracing"""
    
    # Configure resource attributes
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "development"),
    })
    
    # Initialize tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure exporters (both console and OTLP for Jaeger)
    otlp_exporter = None
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
            insecure=True  # For development; set to False for production with TLS
        )
    except Exception as e:
        print(f"Could not initialize OTLP exporter: {e}")
    
    # Add span processors
    if otlp_exporter:
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Always add console exporter for development
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    return provider

def instrument_application(app):
    """Instrument the FastAPI application with tracing"""
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument requests (for external API calls)
    RequestsInstrumentor().instrument()
    
    # Instrument SQLAlchemy (for database operations)
    # This needs to be called after the engine is created
    # SQLAlchemyInstrumentor().instrument()
    
    # Instrument logging to include trace IDs
    LoggingInstrumentor().instrument()

def get_tracer(name: str):
    """Get a tracer instance"""
    return trace.get_tracer(name)

# Example usage in a translation function
def trace_translation_request(tracer, user_id: str, file_info: dict):
    """Trace a translation request"""
    with tracer.start_as_current_span("translate_document") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("file.name", file_info.get("name", "unknown"))
        span.set_attribute("file.size", file_info.get("size", 0))
        span.set_attribute("file.type", file_info.get("type", "unknown"))
        
        # Simulate work being done
        span.add_event("File upload completed")
        
        with span.start_as_current_span("ai_processing") as ai_span:
            ai_span.set_attribute("model.name", "gemini-pro")
            ai_span.set_attribute("processing.step", "text_extraction")
            # More processing steps...
        
        span.add_event("Translation completed")
        return {"status": "completed", "span_id": span.get_span_context().span_id}