from agentic_security.cache_config import ensure_cache_dir

ensure_cache_dir()

__all__ = ["SecurityScanner", "ensure_cache_dir"]


def __getattr__(name: str):
    """Load the scanner lazily so lightweight CLI commands have no scan side effects."""
    if name == "SecurityScanner":
        from .lib import SecurityScanner

        globals()[name] = SecurityScanner
        return SecurityScanner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
