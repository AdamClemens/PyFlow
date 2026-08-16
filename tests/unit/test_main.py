"""Unit tests for pyflow.__main__ (in-process).

Complements, not replaces, the subprocess-based integration tests
(`tests/integration/test_cli.py`, `test_bootstrap.py`), which verify the
real packaged entry point. Those run as real subprocesses, deliberately,
so coverage.py -- which only instruments the in-process interpreter --
can't see into them; `__main__.py` showed 0% coverage despite genuinely
being exercised. These tests call `main()` directly instead, giving real
coverage without weakening the subprocess tests' own purpose.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from pyflow import __version__
from pyflow.__main__ import main


def test_no_args_prints_version_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    captured = capsys.readouterr()
    assert __version__ in captured.out
    assert "usage:" in captured.out
    assert "-h, --help" in captured.out


def test_run_dispatches_to_bootstrap_with_parsed_args() -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(["run", "--config", "some-config.yaml", "--max-frames", "3"])

    mock_bootstrap.assert_called_once_with(Path("some-config.yaml"), max_frames=3)


def test_run_defaults_to_no_config_and_no_max_frames() -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(["run"])

    mock_bootstrap.assert_called_once_with(None, max_frames=None)
