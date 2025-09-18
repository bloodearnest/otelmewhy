import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, export
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


def setup_tracing(server, worker):
    """Set up otel provider and exporters."""

    # do not export backend telemetry initially for pedagological purposes
    if "DISABLE_BACKEND_TELEMETRY" in os.environ:
        return

    # Create a resource with service information
    resource = Resource.create({ "service.name": "memes.backend"})
    # this is global to this python process
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Manually configure exporters based on env var value
    traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", "").lower()
    if traces_exporter == "console":
        console_exporter = export.ConsoleSpanExporter()
        provider.add_span_processor(export.SimpleSpanProcessor(console_exporter))
        server.log.info(f"Set up console exporter for worker {worker.pid}")
    elif traces_exporter == "otlp":
        otlp_exporter = OTLPSpanExporter()
        provider.add_span_processor(export.BatchSpanProcessor(otlp_exporter))
        server.log.info(f"Set up OTLP exporter for worker {worker.pid}")
