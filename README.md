# pcd-rlcd

Parallel constrained decoding for structured extraction and classification on Apple Silicon.

`pcd-rlcd` extracts the core inference engine from the original Parallel Constrained Decoding project and makes it available as a small, reusable Python package.

It evaluates multiple schema fields in parallel instead of generating a complete JSON document token by token. This is useful for classification, decision routing, structured extraction, and other workloads where fields have bounded candidate values.

## Features

- Parallel evaluation of multiple structured fields
- Enum and boolean schema fields
- Constrained candidate selection
- Programmatic JSON assembly
- Field-level confidence scores
- Top-choice probability telemetry
- MLX backend for Apple Silicon
- Torch backend support
- Configurable language model through `MODEL_ID`
- Typed Python package
- Benchmark utilities

## Requirements

- Python 3.10+
- Apple Silicon Mac for the MLX backend
- macOS 14 or later recommended
- A model supported by the selected inference backend

The package defaults to:

```text
mlx-community//Qwen2.5-1.5B-Instruct
```

The example configuration uses:

```text
mlx-community/Qwen2.5-0.5B-Instruct-4bit
```

You can select a different model with the `MODEL_ID` environment variable.

## Installation

Using `uv`:

```bash
uv add pcd-rlcd
```

Using `pip`:

```bash
pip install pcd-rlcd
```

To install directly from the repository:

```bash
git clone <repository-url>
cd <repository-directory>

uv sync
```

## Quickstart

```python
from pcd_rlcd.schema import StructuredSchema
from pcd_rlcd.engine import run_parallel_generation


schema_definition = {
    "fraud_risk": {
        "type": "enum",
        "choices": ["LOW", "ELEVATED", "SUSPICIOUS", "CRITICAL"],
        "description": "Risk assessment tier for incoming transaction",
    },
    "block_account": {
        "type": "boolean",
        "description": "Whether immediate account restriction is required",
    },
    "recommended_action": {
        "type": "enum",
        "choices": [
            "ALLOW",
            "STEP_UP_2FA",
            "TEMPORARY_HOLD",
            "TERMINATE_SESSION",
        ],
        "description": "Immediate mitigation action",
    },
}


def main():
    schema = StructuredSchema(schema_definition)

    context = """
    User ID: usr_9921
    Location: Lagos, Nigeria (usual: Seattle, USA)
    Device: Unknown Linux Chromium browser
    Action: Wire transfer $49,500 to offshore escrow
    Prior velocity: 0 transfers in 90 days
    """

    result = run_parallel_generation(context, schema)

    print(f"Elapsed time: {result['elapsed_ms']} ms")
    print(f"Sequential passes: {result['sequential_forward_passes']}")
    print(f"Parsed JSON: {result['parsed_json']}")


if __name__ == "__main__":
    main()
```

Example output:

```text
Elapsed time: 146.88 ms
Sequential passes: 1
Parsed JSON: {
    'fraud_risk': {'value': 'SUSPICIOUS', 'prob': 0.8131},
    'block_account': {'value': True, 'prob': 0.6637},
    'recommended_action': {
        'value': 'TEMPORARY_HOLD',
        'prob': 0.6054
    }
}
```

## Model Configuration

Set `MODEL_ID` before running your application:

```bash
export MODEL_ID=mlx-community/Qwen2.5-0.5B-Instruct-4bit
```

For example:

```bash
MODEL_ID=mlx-community/Qwen2.5-0.5B-Instruct-4bit python example.py
```

If `MODEL_ID` is not set, the engine uses:

```text
mlx-community/Qwen2.5-1.5B-Instruct
```

The selected model must be compatible with the active inference backend.

## Defining Schemas

Schemas are created with `StructuredSchema`. Each field includes:

- `type`: either `enum` or `boolean`
- `description`: semantic guidance for the model
- `choices`: allowed values for enum fields

### Enum fields

```python
{
    "priority": {
        "type": "enum",
        "choices": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "description": "Urgency of the incident",
    }
}
```

### Boolean fields

```python
{
    "requires_review": {
        "type": "boolean",
        "description": "Whether the result requires manual review",
    }
}
```

### Combined schema

```python
from pcd_rlcd.schema import StructuredSchema


schema = StructuredSchema(
    {
        "priority": {
            "type": "enum",
            "choices": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "description": "Urgency of the incident",
        },
        "requires_review": {
            "type": "boolean",
            "description": "Whether manual review is required",
        },
        "department": {
            "type": "enum",
            "choices": [
                "BILLING",
                "INFRASTRUCTURE",
                "SECURITY",
                "PRODUCT_SUPPORT",
            ],
            "description": "Department responsible for handling the issue",
        },
    }
)
```

## Result Format

`run_parallel_generation` returns a dictionary containing the structured result and execution telemetry.

```python
{
    "mode": "parallel_constrained_calibrated",
    "elapsed_ms": 146.88,
    "prefill_ms": 100.42,
    "suffix_eval_ms": 42.17,
    "sequential_forward_passes": 1,
    "is_valid_json": True,
    "schema_match": True,
    "parsed_json": {
        "priority": {
            "value": "HIGH",
            "prob": 0.91,
        },
        "requires_review": {
            "value": True,
            "prob": 0.84,
        },
        "department": {
            "value": "SECURITY",
            "prob": 0.96,
        },
    },
    "field_telemetry": {
        "priority": {
            "value": "HIGH",
            "confidence": 0.91,
            "cardinality": 4,
            "top_choices": [
                {
                    "choice": "HIGH",
                    "probability": 0.91,
                },
                {
                    "choice": "CRITICAL",
                    "probability": 0.06,
                },
            ],
        }
    },
}
```

The exact timing fields depend on the selected backend, model, hardware, and input.

## How It Works

Traditional structured generation produces JSON autoregressively:

```text
"context" -> "{" -> "\"field\"" -> ":" -> "\"value\"" -> ...
```

Each generated token requires another model evaluation. As the output grows, the number of sequential evaluations also grows.

Parallel constrained decoding uses a different strategy:

1. The input context and schema descriptions are prefetched once.
2. The resulting key-value cache is shared across schema fields.
3. Each field is evaluated against only its valid candidate values.
4. Candidate probabilities are normalized within each field.
5. The selected values are assembled programmatically.
6. The final structure is guaranteed to match the requested schema.

This approach is especially useful when fields contain bounded values such as enums, labels, routing decisions, or booleans.

## Package Structure

```text
.
├── pyproject.toml
├── README.md
├── requirements.txt
├── uv.lock
└── src
    └── pcd_rlcd
        ├── __init__.py
        ├── benchmark.py
        ├── engine.py
        ├── engine_mlx.py
        ├── engine_torch.py
        ├── prompt_builder.py
        ├── py.typed
        └── schema.py
```

### Main modules

- `schema.py` — schema definitions and field metadata
- `engine.py` — public engine interface
- `engine_mlx.py` — MLX-based inference implementation
- `engine_torch.py` — PyTorch-based inference implementation
- `prompt_builder.py` — prompt construction utilities
- `benchmark.py` — benchmark and comparison utilities

## Running Benchmarks

The package includes benchmark utilities for comparing parallel constrained decoding with autoregressive generation.

Run the benchmark module with:

```bash
python -m pcd_rlcd.benchmark
```

Benchmark results depend on:

- Model size and quantization
- Apple Silicon generation
- Available memory
- Input length
- Number of fields
- Number of candidate choices
- Backend configuration

Use benchmark results as hardware- and model-specific measurements rather than universal performance guarantees.

## Choosing Candidate Values

Enum fields work best when:

- The candidate set is known in advance
- Each choice is semantically distinct
- Values are reasonably short
- The model can infer the correct choice from the context

For example:

```python
{
    "severity": {
        "type": "enum",
        "choices": ["INFO", "WARNING", "ERROR", "CRITICAL"],
        "description": "Operational severity of the event",
    }
}
```

For open-ended text generation, use a conventional autoregressive generation approach instead.

## Limitations

- The engine is designed for bounded structured decisions, not arbitrary JSON generation.
- Results are model predictions and should be validated against application-specific requirements.
- Confidence values represent model probabilities over the candidate set; they are not guaranteed to be calibrated for every domain.
- Performance varies significantly between models, devices, and backends.
- MLX execution requires compatible Apple Silicon hardware.
- The available schema field types are currently limited to the types supported by the package implementation.

## Relationship to the Original Project

This package extracts and refactors the reusable core of the original Parallel Constrained Decoding implementation into an independently installable Python package.

The original project demonstrated parallel constrained decoding for Apple Silicon using MLX. `pcd-rlcd` focuses on making the core schema and inference functionality easier to install and use from other Python applications.

## License

Apache License 2.0.