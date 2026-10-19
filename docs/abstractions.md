# Abstractions

This page shows the main types in the code. For the flow of a scan, refer to [Design](design.md).

| Type | Module | Description |
| --- | --- | --- |
| `LLMSpec` | `agentic_security.http_spec` | A parsed HTTP request template. It sends one prompt with `probe()`. Refer to [HTTP spec](http_spec.md). |
| `ProbeDataset` | `agentic_security.probe_data.models` | One dataset: the name, the metadata, the prompts, the token count, and the cost. |
| `ImageProbeDataset` | `agentic_security.probe_data.models` | Contains a `ProbeDataset` and one image for each prompt. |
| `Scan` | `agentic_security.primitives.models` | The settings of one scan: spec, budget, datasets, and flags. |
| `ModuleProtocol` | `agentic_security.probe_data.modules.module_protocol` | The interface of a prompt-generator module. Refer to [External modules](external_module.md). |
| `RefusalClassifierPlugin` | `agentic_security.probe_actor.refusal` | The base class of a detector. Refer to [Refusal classifier plugins](refusal_classifier_plugins.md). |
| `RefusalClassifierManager` | `agentic_security.probe_actor.refusal` | Keeps the enabled detectors. `is_refusal()` is `True` if one detector returns `True`. |
| `DetectorRegistry` | `agentic_security.refusal_classifier.registry` | Builds the detectors from the `[detectors]` section. |
| `PromptSelectionInterface` | `agentic_security.probe_data.modules.rl_model` | The interface of a prompt selector. Refer to [RL prompt selection](rl_model.md). |
| `OperatorToolBox` | `agentic_security.probe_actor.operator` | Experimental. Tools for an LLM agent. Refer to [Agent operator](operator.md). |
