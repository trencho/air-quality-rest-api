from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

from definitions import METRICS_PATH

# Deferred (app-factory) init. Instruments request count/latency — grouped by Flask
# endpoint to avoid high-cardinality labels from path params — and serves METRICS_PATH.
metrics = PrometheusMetrics.for_app_factory(path=METRICS_PATH, group_by="endpoint")


def init_metrics(app: Flask) -> None:
    metrics.init_app(app)
