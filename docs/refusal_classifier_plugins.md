# Refusal Classifier Plugin System Documentation

The refusal classifier plugin system allows for the creation and use of custom refusal classifiers. This system is designed to be modular and extensible, enabling users to add their own refusal detection logic.

## Overview

The plugin system is based on the `RefusalClassifierPlugin` abstract base class, which defines the interface for all refusal classifier plugins. The `RefusalClassifierManager` is used to register and manage these plugins.

## Creating a Plugin

To create a custom refusal classifier plugin, you must implement the `RefusalClassifierPlugin` abstract base class. This class requires the implementation of the `is_refusal` method, which checks if a response contains a refusal.

```python
from abc import ABC, abstractmethod

class RefusalClassifierPlugin(ABC):
    """Base class for refusal classifier plugins."""

    @abstractmethod
    def is_refusal(self, response: str) -> bool:
        """Check if the response contains a refusal.

        Args:
            response (str): The response from the language model.

        Returns:
            bool: True if the response contains a refusal, False otherwise.
        """
        pass
```

### Example Plugin

Here is an example of a custom refusal classifier plugin that checks for specific phrases:

```python
class CustomRefusalClassifier(RefusalClassifierPlugin):
    def __init__(self, custom_phrases: List[str]):
        self.custom_phrases = custom_phrases

    def is_refusal(self, response: str) -> bool:
        """Check if the response contains any custom refusal phrases.

        Args:
            response (str): The response from the language model.

        Returns:
            bool: True if the response contains a custom refusal phrase, False otherwise.
        """
        return any(phrase in response for phrase in self.custom_phrases)
```

## Registering a Plugin

To register a custom refusal classifier plugin, use the `RefusalClassifierManager`:

```python
from agentic_security.probe_actor.refusal import RefusalClassifierManager

# Initialize the plugin manager
refusal_classifier_manager = RefusalClassifierManager()

# Register the custom plugin
refusal_classifier_manager.register_plugin("custom", CustomRefusalClassifier(custom_phrases=["I can't", "I won't"]))
```

## Using the Plugin System

The `refusal_heuristic` function automatically uses all registered plugins to check for refusals:

```python
from agentic_security.probe_actor.refusal import refusal_heuristic

is_refusal = refusal_heuristic(request_json)
```

## Conclusion

The refusal classifier plugin system provides a flexible and extensible way to add custom refusal detection logic to the Agentic Security project. This documentation serves as a guide to creating, registering, and using custom refusal classifier plugins.
