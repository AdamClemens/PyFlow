"""Binds `tests/features/fluid_configuration.feature` (TASK-041) --
Stage 5's first task, moving `numerics.diffusion_coefficient` into a new
`fluid:` section alongside a new `fluid.viscosity`. Lives here, not
`tests/unit/`, because its own last scenario needs a real CLI subprocess
run (`tests/CLAUDE.md`'s own unit/integration split); not a golden demo
either -- no new config file under `examples/golden-demos/`, reusing the
existing Passive Scalar Transport demo's own committed file for the
migration scenario instead of a fixture copy, so a real drift between
that file and the schema is exactly what this scenario would catch.
Supplies its own local steps rather than drawing on
`tests/golden/conftest.py`'s demo-running vocabulary, which a
`conftest.py`'s own directory scoping could not reach from here anyway.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from pyflow.configuration import PyFlowConfig, load_config

scenarios("fluid_configuration.feature")

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _Context:
    config_path: Path
    loaded: PyFlowConfig | None = None
    error: ValueError | None = None
    process: subprocess.CompletedProcess[str] | None = None


# -- Given -------------------------------------------------------------


@given(
    "a configuration file setting fluid.viscosity and fluid.diffusion_coefficient",
    target_fixture="ctx",
)
def _given_both_fluid_fields(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fluid:\n  viscosity: 2.5\n  diffusion_coefficient: 3.5\n")
    return _Context(config_path=config_path)


@given("a configuration file setting only fluid.viscosity", target_fixture="ctx")
def _given_only_viscosity(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fluid:\n  viscosity: 2.5\n")
    return _Context(config_path=config_path)


@given("a configuration file setting numerics.diffusion_coefficient", target_fixture="ctx")
def _given_stale_numerics_field(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("numerics:\n  diffusion_coefficient: 3.5\n")
    return _Context(config_path=config_path)


@given(
    "the Passive Scalar Transport golden demo's own committed configuration file",
    target_fixture="ctx",
)
def _given_the_real_demo_config() -> _Context:
    config_path = _REPO_ROOT / "examples" / "golden-demos" / "passive_scalar_transport.yaml"
    assert config_path.is_file(), f"expected the real demo config at {config_path}"
    return _Context(config_path=config_path)


# -- When ----------------------------------------------------------------


@when("the configuration is loaded")
def _when_loaded(ctx: _Context) -> None:
    try:
        ctx.loaded = load_config(ctx.config_path)
    except ValueError as exc:
        ctx.error = exc


@when("the demo is run through the real CLI as a subprocess")
def _when_run_through_the_cli(ctx: _Context) -> None:
    ctx.process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(ctx.config_path),
            "--backend",
            "offscreen",
            "--max-frames",
            "2",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


# -- Then ------------------------------------------------------------------


@then("both values arrive on the loaded configuration's fluid section")
def _then_both_values_arrive(ctx: _Context) -> None:
    assert ctx.loaded is not None, ctx.error
    assert ctx.loaded.fluid.viscosity == 2.5
    assert ctx.loaded.fluid.diffusion_coefficient == 3.5


@then("fluid.diffusion_coefficient is still its own default value")
def _then_diffusion_coefficient_stays_default(ctx: _Context) -> None:
    assert ctx.loaded is not None, ctx.error
    assert ctx.loaded.fluid.viscosity == 2.5
    assert ctx.loaded.fluid.diffusion_coefficient == PyFlowConfig().fluid.diffusion_coefficient


@then(
    "loading is rejected with a named error saying the field moved to fluid.diffusion_coefficient"
)
def _then_rejected_naming_the_new_home(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the retired field"
    message = str(ctx.error)
    assert "numerics.diffusion_coefficient" in message
    assert "fluid.diffusion_coefficient" in message


@then("the process exits successfully")
def _then_the_process_exits_successfully(ctx: _Context) -> None:
    assert ctx.process is not None
    assert ctx.process.returncode == 0, ctx.process.stderr
