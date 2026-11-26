import os
import lib.game_files as game_files
import lib.constants as const


def test_every_registered_table_exists(paths, report):
    report("Missing input tables", [p for p in paths.values() if not os.path.isfile(p)])


def test_every_language_file_exists(report):
    report("Missing language files", [f for f in const.LANGUAGE_FILES.values() if not os.path.isfile(os.path.join(const.INPUT_DIR, f))])


def test_every_filename_constant_is_in_build_paths(paths, report):
    constants = {v for k, v in vars(game_files).items() if k.isupper() and isinstance(v, str)}
    registered = {os.path.relpath(p, const.INPUT_DIR) for p in paths.values()}
    report("game_files constants missing from build_paths", constants - registered)
