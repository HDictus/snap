"""Module providing utility functions for the tests"""

import json
import shutil
import tempfile
from contextlib import contextmanager
from distutils.dir_util import copy_tree
from pathlib import Path

import libsonata
import pytest

from bluepysnap.circuit import Circuit
from bluepysnap.nodes import NodePopulation, Nodes

TEST_DIR = Path(__file__).resolve().parent
TEST_DATA_DIR = TEST_DIR / "data"

skip_if_libsonata_0_1_16 = pytest.mark.skipif(
    libsonata.version == "0.1.16", reason="Disabled with libsonata 0.1.16"
)


@contextmanager
def setup_tempdir(cleanup=True):
    temp_dir = str(Path(tempfile.mkdtemp()).resolve())
    try:
        yield temp_dir
    finally:
        if cleanup:
            shutil.rmtree(temp_dir)


@contextmanager
def copy_test_data(config="circuit_config.json"):
    """Copies test/data circuit to a temp directory.

    We don't all data every time but considering this is a copy into a temp dir, it should be fine.
    Returns:
        yields a path to the copy of the config file
    """
    with setup_tempdir() as tmp_dir:
        copy_tree(str(TEST_DATA_DIR), tmp_dir)
        copied_path = Path(tmp_dir)
        yield copied_path, copied_path / config


@contextmanager
def copy_config(config="circuit_config.json"):
    """Copies config to a temp directory.

    Returns:
        yields a path to the copy of the config file
    """
    with setup_tempdir() as tmp_dir:
        output = Path(tmp_dir, config)
        shutil.copy(str(TEST_DATA_DIR / config), str(output))
        yield output


@contextmanager
def edit_config(config_path):
    """Context manager within which you can edit a circuit config. Edits are saved on the context
    manager leave.

    Args:
        config_path (Path): path to config

    Returns:
        Yields a json dict instance of the config_path. This instance will be saved as the config.
    """
    with config_path.open("r") as f:
        config = json.load(f)
    try:
        yield config
    finally:
        with config_path.open("w") as f:
            f.write(json.dumps(config))


def create_node_population(filepath, pop_name, circuit=None, node_sets=None, pop_type=None):
    """Creates a node population.
    Args:
        filepath (str): path to the node file.
        pop_name (str): population name inside the file.
        circuit (Mock/Circuit): either a real circuit or a Mock containing the nodes.
        node_sets: (Mock/NodeSets): either a real node_sets or a mocked node_sets.
        pop_type (str): optional population type.
    Returns:
        NodePopulation: return a node population.
    """
    node_pop_config = {
        "nodes_file": filepath,
        "node_types_file": None,
        "populations": {pop_name: {}},
    }

    if pop_type is not None:
        node_pop_config["populations"][pop_name]["type"] = pop_type

    with copy_test_data() as (_, config_path):
        with edit_config(config_path) as config:
            config["networks"]["nodes"] = [node_pop_config]

        if circuit is None:
            circuit = Circuit(config_path)

    if node_sets is not None:
        circuit.node_sets = node_sets

    node_pop = NodePopulation(circuit, pop_name)
    circuit.nodes = Nodes(circuit)
    return node_pop
