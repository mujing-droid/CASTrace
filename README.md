# CASTrace

**Integrating Causal Knowledge Analysis and Sequential Learning for APT Attack Investigation**

CASTrace is a provenance-based attack investigation framework for identifying
compact, attack-relevant components from large system audit graphs. It combines
POI-centered causal influence analysis with process-centric sequence learning
to reduce dependency explosion, false negatives, and false positives during
Advanced Persistent Threat (APT) investigation.

## Overview

Given a point-of-interest (POI) event and a provenance graph, CASTrace is
designed to:

1. Reduce redundant and irrelevant graph elements.
2. Build a POI backtracking dependency graph.
3. Extract temporal, data-flow, rarity, and topology features.
4. Compute and propagate dependency influence from the POI.
5. Select highly influenced entry nodes and construct a POI Strong Dependency
   Influence Graph (POIsdiG).
6. Extract process-centric chronological event sequences.
7. Identify anomalous sequences and generate a Critical Component Graph (CCG).


## Repository status

The current code snapshot provides the following components:

| Component | Main implementation | Status |
| --- | --- | --- |
| Graph serialization and preprocessing | `project/basic_funcs/graph_process.py` | Available |
| Causal feature extraction and dependency propagation | `project/basic_funcs/casuality.py` | Available |
| POI-centered causal-analysis pipeline | `project/casuality_analysis.py` | Available |
| Process-centric sequence extraction | `project/basic_funcs/sequenceExtraction.py` | Available |
| BERT sequence embedding helpers | `project/basic_funcs/embedding.py` | Available |
| DEPIMPACT comparison code | `project/depimpact.py` | Experimental |
| ATLAS comparison and LSTM code | `project/atlas.py`, `project/atlas_methods.py` | Experimental |
| OC-SVM training and inference described in the paper | — | Not included |
| Fully automated POIsdiG-to-CCG workflow | — | Partial |

The default command-line entry point runs the causal-analysis portion of the
pipeline. Reproducing the complete paper workflow requires the missing anomaly
model stage, the original preprocessed datasets, model assets, and experiment
parameters.

## Repository structure

```text
.
├── project/
│   ├── casuality_analysis.py       # Main causal-analysis entry point
│   ├── depimpact.py                # DEPIMPACT-style baseline experiments
│   ├── atlas.py                    # ATLAS/LSTM experiments
│   ├── atlas_methods.py            # ATLAS graph and sequence helpers
│   ├── values.py                   # Portable data and output paths
│   ├── config.example.json         # Experiment configuration template
│   └── basic_funcs/
│       ├── graph_process.py        # Graph I/O, reduction, and traversal
│       ├── casuality.py            # Features, weights, and propagation
│       ├── sequenceExtraction.py   # Event-sequence construction
│       ├── embedding.py            # BERT embedding helpers
│       ├── file_process.py         # Data serialization utilities
│       ├── get_config.py           # Configuration loading and validation
│       ├── tools.py                # Looping and logging helpers
│       └── lstm_model.py           # LSTM utilities
├── requirements.txt
└── README.md
```

The misspelling `casuality` is retained in file and function names for
compatibility with the existing code.

## Requirements

- Python 3.10 or later
- Linux is recommended for experiments on kernel audit provenance
- Sufficient memory for the selected provenance graph

Core causal-analysis dependencies are listed in `requirements.txt`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional modules require additional packages:

```bash
# BERT embedding helpers
python -m pip install torch transformers

# ATLAS/LSTM experiments
python -m pip install tensorflow imbalanced-learn
```

Pretrained model files are not downloaded automatically. Pass a local model
directory to the embedding helpers.

## Data preparation

The datasets and pretrained model assets are not distributed in this
repository. The paper evaluates 15 attacks using more than 150 million audit
records: 10 simulated attacks and 5 attacks from the
[DARPA Transparent Computing Engagement 3](https://github.com/darpa-i2o/Transparent-Computing/blob/master/README-E3.md)
dataset. Users are responsible for obtaining the data under its applicable
terms and converting it to the graph schema below.

CASTrace expects gzip-compressed, pickled NetworkX `MultiDiGraph` objects.
Only load graph files from trusted sources because Python pickle files may
execute code during deserialization.

Each node must have a `type` attribute:

```python
graph.add_node("process-node", type="process")
graph.add_node("file-node", type="file")
graph.add_node("socket-node", type="socket")
```

Each event edge must provide these attributes:

```python
graph.add_edge(
    "source-node",
    "target-node",
    key=0,
    type="write",
    start_time=1000,
    end_time=1001,
    data_amount=512,
)
```

Required edge attributes:

| Attribute | Description |
| --- | --- |
| `type` | Event operation, such as `read`, `write`, `execve`, or `sendto` |
| `start_time` | Event start timestamp |
| `end_time` | Event end timestamp |
| `data_amount` | Data volume associated with the event |

By default, input data is read from `project/data`. Set `APT_DATA_ROOT` to use
another location. Generated files are written to `project/output`; set
`APT_OUTPUT_ROOT` to override it.

The main entry point reads graphs from:

```text
project/data/
└── graph/
    ├── back_add/
    │   └── <case-name>.gz
    └── dot/
        └── back/
            └── <case-name>.gz
```

Cases listed in `metadata.dot_file_names` use `graph/dot/back`; all other cases
use `graph/back_add`.

## Configuration

Create the local experiment configuration:

```bash
cp project/config.example.json project/config.json
```

Configuration schema:

```json
{
  "ground_truth": {
    "case1": [
      ["source-node", "target-node"]
    ]
  },
  "poi_events": {
    "case1": ["source-node", "target-node", 0]
  },
  "windows": {
    "case1": 10
  },
  "metadata": {
    "dot_file_names": []
  }
}
```

- `ground_truth` contains critical event pairs used for evaluation.
- `poi_events` contains `(source, target, edge_key)` for each POI.
- `windows` controls temporal segmentation during rarity calculation.
- The POI edge key must match the key stored in the `MultiDiGraph`.

You may select another configuration file with `--config` or the `APT_CONFIG`
environment variable.

## Usage

Run every case defined in the configuration:

```bash
python -m project.casuality_analysis --config project/config.json
```

Run one or more selected cases:

```bash
python -m project.casuality_analysis \
  --config project/config.json \
  --poi case1 \
  --poi case2
```

Mirror console output to the configured log directory:

```bash
python -m project.casuality_analysis \
  --config project/config.json \
  --log
```

The command reports graph sizes, entry-point selection statistics, TP/FN/FP
counts, and execution time for each case. Optional intermediate graphs and
feature arrays can be saved by calling the analysis functions with
`need_save=True`.

## Results reported in the paper

On the 15 evaluated attacks, the paper reports the following average graph
sizes:

| Method or stage | Average edges | Average FP | Average FN |
| --- | ---: | ---: | ---: |
| Original POI dependency graph | 227,589.00 | — | — |
| Reduced graph | 68,605.67 | 68,593.20 | 0 |
| DEPIMPACT | 1,209.00 | 1,196.87 | 0.33 |
| ATLAS | 1,426.07 | 1,415.80 | 2.20 |
| CASTrace POIsdiG | 170.67 | 158.20 | 0 |
| CASTrace CCG | 97.53 | 85.07 | 0 |

These values are results reported by the paper, not results produced
automatically by the current repository snapshot.

The reported evaluation used Ubuntu 20.04 LTS, an Intel Xeon Gold 5218 CPU at
2.30 GHz, and 128 GB of memory. Runtime and memory consumption will vary with
the graph size, hardware, software versions, and preprocessing choices.

