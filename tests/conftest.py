import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import lib.io as io
import lib.game_files as game_files
import lib.constants as const


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def paths():
    return game_files.build_paths(const.INPUT_DIR)


@pytest.fixture(scope="session")
def en():
    return io.load_json(os.path.join(const.INPUT_DIR, const.LANGUAGE_FILES["en"]))


@pytest.fixture(scope="session")
def table(paths):
    cache = {}
    def load(key):
        if key not in cache:
            cache[key] = io.load_json(paths[key])
        return cache[key]
    return load


@pytest.fixture(scope="session")
def source():
    def read(rel_path):
        with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
            return f.read()
    return read


@pytest.fixture(scope="session")
def report():
    def fail_if_any(what, problems):
        if not problems:
            return
        if isinstance(problems, dict):
            lines = []
            for key, values in sorted(problems.items()):
                values = sorted(map(str, values))
                more = f" (+{len(values) - 3} more)" if len(values) > 3 else ""
                lines.append(f"  {key}: {', '.join(values[:3])}{more}")
        else:
            lines = [f"  {p}" for p in sorted(map(str, problems))]
        pytest.fail(f"{what}:\n" + "\n".join(lines), pytrace=False)
    return fail_if_any
