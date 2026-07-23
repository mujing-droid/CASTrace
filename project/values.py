"""Portable defaults for paths and experiment-wide constants."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("APT_DATA_ROOT", PROJECT_DIR / "data")).expanduser()
OUTPUT_ROOT = Path(
    os.environ.get("APT_OUTPUT_ROOT", PROJECT_DIR / "output")
).expanduser()
DEFAULT_WINDOWS_NUM = int(os.environ.get("APT_WINDOWS_NUM", "10"))
__all__ = [
    "DATA_ROOT",
    "DEFAULT_WINDOWS_NUM",
    "OUTPUT_ROOT",
    "PROJECT_DIR",
    "all_graph_names",
    "all_poi_names",
    "atlas_save_path",
    "case_study_back_compressed_path",
    "case_study_fd_path",
    "complement_graph_names",
    "depimpact_save_path",
    "dot_file_names",
    "embedding_name_gt",
    "embedding_name_normal",
    "fd_complement_path",
    "file_name_labels",
    "graph_dot_path",
    "graph_dot_path_back",
    "graph_dot_path_back_add_compressed",
    "graph_dot_path_back_compressed",
    "graph_name_bcw_impact",
    "graph_name_forward",
    "graph_path_add_back",
    "graph_path_back_add_sem_compress",
    "graph_path_complement",
    "graph_path_new_back",
    "graph_path_new_origin",
    "large_case_names",
    "large_file_names_dict",
    "log_path_atlas",
    "log_path_depimpact",
    "log_path_my",
    "poi_names_windows_num_dict",
    "forward_graph_output_path",
    "test_data_path",
    "train_data_path",
]


def _directory(root: Path, *parts: str) -> str:
    return str(root.joinpath(*parts)) + os.sep


def _csv_environment(name: str) -> list[str]:
    return [
        item.strip()
        for item in os.environ.get(name, "").split(",")
        if item.strip()
    ]


# Case lists. The command-line entry point derives all_poi_names from config
# when this list is not explicitly supplied through the environment.
all_poi_names = _csv_environment("APT_POI_NAMES")
dot_file_names = _csv_environment("APT_DOT_FILE_NAMES")
complement_graph_names = _csv_environment("APT_COMPLEMENT_GRAPH_NAMES")
large_case_names = _csv_environment("APT_LARGE_CASE_NAMES")
all_graph_names = _csv_environment("APT_GRAPH_NAMES")
large_file_names_dict: dict[str, list[str]] = {}


# Per-case algorithm settings populated from config by the main entry point.
poi_names_windows_num_dict = {
    poi_name: DEFAULT_WINDOWS_NUM for poi_name in all_poi_names
}


# Graph input paths.
graph_path_add_back = _directory(DATA_ROOT, "graph", "back_add")
graph_path_new_back = _directory(DATA_ROOT, "graph", "new_back")
graph_path_new_origin = _directory(DATA_ROOT, "graph", "origin")
graph_path_complement = _directory(DATA_ROOT, "graph", "complement")
graph_path_back_add_sem_compress = _directory(
    DATA_ROOT, "graph", "back_add_sem_compress"
)
case_study_back_compressed_path = _directory(
    DATA_ROOT, "case_study", "back_compressed_graph"
)
graph_dot_path = _directory(DATA_ROOT, "graph", "dot")
graph_dot_path_back = _directory(DATA_ROOT, "graph", "dot", "back")
graph_dot_path_back_compressed = _directory(
    DATA_ROOT, "graph", "dot", "back_compressed"
)
graph_dot_path_back_add_compressed = _directory(
    DATA_ROOT, "graph", "dot", "back_add_compressed"
)


# Generated graph and model paths.
fd_complement_path = _directory(OUTPUT_ROOT, "forward_analysis")
forward_graph_output_path = _directory(OUTPUT_ROOT, "forward_graph")
case_study_fd_path = _directory(OUTPUT_ROOT, "case_study", "fd_data")
depimpact_save_path = _directory(OUTPUT_ROOT, "depimpact")
atlas_save_path = _directory(OUTPUT_ROOT, "atlas", "models")
train_data_path = _directory(DATA_ROOT, "atlas", "train")
test_data_path = _directory(DATA_ROOT, "atlas", "test")


# Log paths.
log_path_my = _directory(OUTPUT_ROOT, "logs", "casuality_analysis")
log_path_depimpact = _directory(OUTPUT_ROOT, "logs", "depimpact")
log_path_atlas = _directory(OUTPUT_ROOT, "logs", "atlas")


# Shared file names.
graph_name_bcw_impact = "bcw_impact_graph.gz"
graph_name_forward = "forward_graph.gz"
embedding_name_normal = "embedding_normal.npy"
embedding_name_gt = "embedding_ground_truth.npy"
file_name_labels = "labels.txt"
