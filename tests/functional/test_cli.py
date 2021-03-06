# Copyright 2020 Lynn Root
"""Functional tests for the CLI and implicitly interrogate/visit.py."""

import os

import pytest

from click import testing

from interrogate import cli


HERE = os.path.abspath(os.path.join(os.path.abspath(__file__), os.path.pardir))
SAMPLE_DIR = os.path.join(HERE, "sample")
FIXTURES = os.path.join(HERE, "fixtures")


@pytest.fixture
def runner():
    """Click fixture runner"""
    return testing.CliRunner()


def test_run_no_paths(runner, monkeypatch, tmpdir):
    """Assume current working directory if no paths are given."""
    monkeypatch.setattr(os, "getcwd", lambda: SAMPLE_DIR)

    result = runner.invoke(cli.main, [])

    assert "actual: 46.2%" in result.output
    assert 1 == result.exit_code


@pytest.mark.parametrize(
    "flags,exp_result,exp_exit_code",
    (
        # no flags
        ([], 46.2, 1),
        # ignore init module
        (["-I"], 46.0, 1),
        # ignore module docs
        (["-M"], 45.7, 1),
        # ignore semiprivate docs
        (["-s"], 46.7, 1),
        # ignore private docs
        (["-p"], 47.8, 1),
        # ignore magic method docs
        (["-m"], 45.8, 1),
        # ignore init method docs
        (["-i"], 44.9, 1),
        # ignore regex
        (["-r", "^get$"], 45.8, 1),
        # whitelist regex
        (["-w", "^get$"], 50.0, 1),
        # exclude file
        (["-e", os.path.join(SAMPLE_DIR, "partial.py")], 53.1, 1),
        # fail under
        (["-f", "40"], 46.2, 0),
    ),
)
def test_run_shortflags(flags, exp_result, exp_exit_code, runner):
    """Test CLI with single short flags"""
    cli_inputs = flags + [SAMPLE_DIR]
    result = runner.invoke(cli.main, cli_inputs)

    exp_partial_output = "actual: {:.1f}%".format(exp_result)
    assert exp_partial_output in result.output
    assert exp_exit_code == result.exit_code


@pytest.mark.parametrize(
    "flags,exp_result,exp_exit_code",
    (
        (["--ignore-init-module"], 46.0, 1),
        (["--ignore-module"], 45.7, 1),
        (["--ignore-semiprivate"], 46.7, 1),
        (["--ignore-private"], 47.8, 1),
        (["--ignore-magic"], 45.8, 1),
        (["--ignore-init-method"], 44.9, 1),
        (["--ignore-regex", "^get$"], 45.8, 1),
        (["--whitelist-regex", "^get$"], 50.0, 1),
        (["--exclude", os.path.join(SAMPLE_DIR, "partial.py")], 53.1, 1),
        (["--fail-under", "40"], 46.2, 0),
    ),
)
def test_run_longflags(flags, exp_result, exp_exit_code, runner):
    """Test CLI with single long flags"""
    cli_inputs = flags + [SAMPLE_DIR]
    result = runner.invoke(cli.main, cli_inputs)

    exp_partial_output = "actual: {:.1f}%".format(exp_result)
    assert exp_partial_output in result.output
    assert exp_exit_code == result.exit_code


@pytest.mark.parametrize(
    "flags,exp_result,exp_exit_code",
    (
        (["-i", "-I", "-r" "^method_foo$"], 45.5, 1),
        (["-s", "-p", "-M"], 48.5, 1),
        (["-m", "-f", "45"], 45.8, 0),
    ),
)
def test_run_multiple_flags(flags, exp_result, exp_exit_code, runner):
    """Test CLI with a hodge-podge of flags"""
    cli_inputs = flags + [SAMPLE_DIR]
    result = runner.invoke(cli.main, cli_inputs)

    exp_partial_output = "actual: {:.1f}%".format(exp_result)
    assert exp_partial_output in result.output
    assert exp_exit_code == result.exit_code


@pytest.mark.parametrize("quiet", (True, False))
def test_generate_badge(quiet, runner):
    """Test expected SVG output when creating a status badge."""
    expected_output_path = os.path.join(FIXTURES, "expected_badge.svg")
    with open(expected_output_path, "r") as f:
        expected_output = f.read()

    with runner.isolated_filesystem() as tmpdir:
        expected_path = os.path.join(tmpdir, "interrogate_badge.svg")
        cli_inputs = [
            "--fail-under",
            0,
            "--generate-badge",
            tmpdir,
            SAMPLE_DIR,
        ]
        if quiet:
            cli_inputs.append("--quiet")

        result = runner.invoke(cli.main, cli_inputs)
        assert 0 == result.exit_code
        if quiet:
            assert "" == result.output
        else:
            assert expected_path in result.output

        with open(expected_path, "r") as f:
            actual_output = f.read()

        assert expected_output == actual_output
