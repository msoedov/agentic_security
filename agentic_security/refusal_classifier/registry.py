"""Config-driven registry for refusal classifiers and leak detectors.

The registry maps a plugin *name* to a zero-argument *factory* that builds a
detector. A detector is any object exposing ``is_refusal(response) -> bool``
(the :class:`~agentic_security.probe_actor.refusal.RefusalClassifierPlugin`
contract). This lets users enable, disable, or add custom detectors through the
``[detectors]`` section of ``agentic_security.toml`` instead of editing source.

Built-in names registered here: ``pii`` and ``sandbox_escape``. The phrase-based
``default`` classifier and the ML ``ml_classifier`` are registered by
:mod:`agentic_security.probe_actor.refusal` to avoid importing the trained model
eagerly.

Example configuration::

    [detectors]
    default = true          # phrase-based refusal classifier
    ml_classifier = true    # ML one-class SVM refusal classifier
    pii = true              # enable the PII / credential leak detector
    sandbox_escape = false  # keep the sandbox-escape detector off

    [detectors.infra_fingerprint]
    class = "my_package.detectors:InfraFingerprintDetector"
    enabled = true

    [detectors.infra_fingerprint.options]
    threshold = 3
"""

from __future__ import annotations

import importlib
from collections import OrderedDict
from collections.abc import Callable, Mapping
from typing import Protocol, runtime_checkable

from agentic_security.logutils import logger

__all__ = [
    "Detector",
    "DetectorFactory",
    "DetectorRegistry",
    "load_plugin_class",
    "registry",
]


@runtime_checkable
class Detector(Protocol):
    """Structural type for detector and refusal-classifier plugins."""

    def is_refusal(self, response: str) -> bool: ...


DetectorFactory = Callable[[], Detector]


def load_plugin_class(path: str) -> Callable[..., Detector]:
    """Import a detector class from a dotted path.

    Args:
        path: Import path in either ``"package.module:ClassName"`` or
            ``"package.module.ClassName"`` form.

    Returns:
        The referenced class (or any callable that builds a detector).

    Raises:
        ValueError: If ``path`` is not a valid ``module``/``attribute`` pair.
        ImportError: If the module or attribute cannot be imported.
        TypeError: If the resolved attribute is not callable.
    """
    if ":" in path:
        module_name, _, attribute = path.partition(":")
    else:
        module_name, _, attribute = path.rpartition(".")

    if not module_name or not attribute:
        raise ValueError(
            f"Invalid detector class path {path!r}; "
            "expected 'package.module:ClassName'."
        )

    module = importlib.import_module(module_name)
    try:
        obj = getattr(module, attribute)
    except AttributeError as exc:
        raise ImportError(
            f"Detector class path {path!r} is invalid: "
            f"module {module_name!r} has no attribute {attribute!r}."
        ) from exc

    if not callable(obj):
        raise TypeError(f"Detector class path {path!r} does not resolve to a callable.")
    return obj


class DetectorRegistry:
    """Registry of named detector factories with config-driven assembly.

    Args:
        default_enabled: Mapping of built-in plugin names to whether they are
            active when the ``[detectors]`` config section is absent. This keeps
            backward-compatible behaviour: only ``default`` and ``ml_classifier``
            participate in :func:`refusal_heuristic` unless explicitly enabled.
    """

    def __init__(self, default_enabled: Mapping[str, bool] | None = None):
        self._factories: OrderedDict[str, DetectorFactory] = OrderedDict()
        self._default_enabled: dict[str, bool] = dict(default_enabled or {})

    def register(
        self,
        name: str,
        factory: DetectorFactory,
        *,
        default_enabled: bool | None = None,
    ) -> None:
        """Register (or override) a detector factory.

        Args:
            name: Unique plugin name used as the ``[detectors]`` config key.
            factory: Zero-argument callable returning a detector instance.
            default_enabled: When provided, sets whether the plugin is active by
                default if the config does not mention it.
        """
        if not callable(factory):
            raise TypeError(f"Detector factory for {name!r} must be callable.")
        self._factories[name] = factory
        if default_enabled is not None:
            self._default_enabled[name] = default_enabled

    def unregister(self, name: str) -> None:
        """Remove a registered plugin if present."""
        self._factories.pop(name, None)
        self._default_enabled.pop(name, None)

    def is_registered(self, name: str) -> bool:
        """Return True if ``name`` is registered."""
        return name in self._factories

    def available(self) -> list[str]:
        """Return the names of all registered plugins."""
        return list(self._factories)

    def build_from_config(
        self, config: Mapping[str, object] | None = None
    ) -> OrderedDict[str, Detector]:
        """Build the enabled detectors described by a ``[detectors]`` config.

        Args:
            config: The parsed ``[detectors]`` table. ``None`` or an empty
                mapping yields the built-in defaults.

        Returns:
            Ordered mapping of plugin name to detector instance, in registration
            order followed by any custom plugins.

        Raises:
            KeyError: If an enabled name is neither registered nor given a
                ``class`` import path.
            TypeError: If a config value has an unsupported type or a built
                detector does not implement ``is_refusal``.
        """
        config = config or {}
        enabled: OrderedDict[str, bool] = OrderedDict(self._default_enabled)

        for name, spec in config.items():
            if isinstance(spec, bool):
                if not self.is_registered(name):
                    raise KeyError(
                        f"Unknown detector {name!r}; register it or provide a "
                        "'class' import path."
                    )
                enabled[name] = spec
            elif isinstance(spec, Mapping):
                class_path = spec.get("class")
                if class_path is not None:
                    options = dict(spec.get("options") or {})
                    self.register(name, self._factory_from_path(class_path, options))
                elif not self.is_registered(name):
                    raise KeyError(
                        f"Unknown detector {name!r}; provide a 'class' import path."
                    )
                enabled[name] = bool(spec.get("enabled", True))
            else:
                raise TypeError(
                    f"Detector config for {name!r} must be a bool or a table, "
                    f"got {type(spec).__name__}."
                )

        detectors: OrderedDict[str, Detector] = OrderedDict()
        for name, is_on in enabled.items():
            if not is_on:
                continue
            detector = self._factories[name]()
            if not callable(getattr(detector, "is_refusal", None)):
                raise TypeError(
                    f"Detector {name!r} does not implement is_refusal(response)."
                )
            detectors[name] = detector
            logger.debug(f"Detector plugin enabled: {name}")
        return detectors

    @staticmethod
    def _factory_from_path(class_path: str, options: dict) -> DetectorFactory:
        cls = load_plugin_class(class_path)
        return lambda: cls(**options)


def _build_pii_detector() -> Detector:
    from agentic_security.refusal_classifier.pii_detector import PIIDetector

    return PIIDetector()


def _build_sandbox_escape_detector() -> Detector:
    from agentic_security.refusal_classifier.sandbox_escape_detector import (
        SandboxEscapeDetector,
    )

    return SandboxEscapeDetector()


# Global registry. ``default`` and ``ml_classifier`` are registered by
# agentic_security.probe_actor.refusal so the trained model is not imported here.
# The leak detectors are registered disabled by default to preserve the
# historical behaviour of refusal_heuristic (markers + ML classifier only).
registry = DetectorRegistry()
registry.register("pii", _build_pii_detector, default_enabled=False)
registry.register(
    "sandbox_escape", _build_sandbox_escape_detector, default_enabled=False
)
