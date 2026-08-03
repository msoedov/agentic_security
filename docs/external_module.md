# External modules

The dynamic module contract is documented in [module.md](module.md).

Import the structural interface with:

```python
from agentic_security.probe_data.modules import ModuleProtocol
```

Implementations do not need to inherit from a concrete base class. They only need the attributes and `apply()` method described by `ModuleProtocol`, which keeps third-party modules decoupled from Agentic Security internals.
