"""Evaluation helpers."""

__all__ = ["Benchmark", "Metrics"]


def __getattr__(name):
    if name == "Benchmark":
        from .benchmark import Benchmark
        return Benchmark
    if name == "Metrics":
        from .metrics import Metrics
        return Metrics
    raise AttributeError(name)
