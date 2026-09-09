"""Unit tests for the pure playback-state logic in pyflow.playback
(TASK-047, Stage 8, Recording & Playback) -- position/pause/speed
advancement, with no rendering or window involved at all. The rendering
integration itself (`play()`, keyboard wiring) needs a real window and
is covered by `tests/integration/test_playback_cli.py` instead, the same
split `tests/unit/test_rendering.py`/`tests/integration/
test_interactive_window.py` already establish.
"""

from __future__ import annotations

from pyflow.playback import (
    MAX_SPEED,
    MIN_SPEED,
    PlaybackState,
    advance_playback_position,
    decrease_speed,
    frame_index_from_fraction,
    increase_speed,
    seek_relative,
    seek_to,
    toggle_pause,
)


def test_advance_playback_position_moves_forward_by_speed() -> None:
    state = PlaybackState(position=0.0, paused=False, speed=1.0)

    index = advance_playback_position(state, max_index=10)

    assert index == 1
    assert state.position == 1.0


def test_advance_playback_position_does_nothing_while_paused() -> None:
    state = PlaybackState(position=3.0, paused=True, speed=1.0)

    index = advance_playback_position(state, max_index=10)

    assert index == 3
    assert state.position == 3.0


def test_advance_playback_position_clamps_at_the_end_rather_than_looping() -> None:
    state = PlaybackState(position=9.0, paused=False, speed=5.0)

    index = advance_playback_position(state, max_index=10)

    assert index == 10
    assert state.position == 10.0

    # Stays clamped on the next call too, rather than overshooting further.
    index = advance_playback_position(state, max_index=10)
    assert index == 10


def test_advance_playback_position_clamps_at_zero_for_a_negative_speed() -> None:
    state = PlaybackState(position=1.0, paused=False, speed=-5.0)

    index = advance_playback_position(state, max_index=10)

    assert index == 0
    assert state.position == 0.0


def test_advance_playback_position_floors_a_fractional_speed() -> None:
    state = PlaybackState(position=0.0, paused=False, speed=0.5)

    first = advance_playback_position(state, max_index=10)
    second = advance_playback_position(state, max_index=10)

    assert first == 0  # position 0.5, floored
    assert second == 1  # position 1.0


def test_toggle_pause_flips_the_flag() -> None:
    state = PlaybackState(paused=False)

    toggle_pause(state)
    assert state.paused is True

    toggle_pause(state)
    assert state.paused is False


def test_increase_speed_doubles_and_clamps_at_max() -> None:
    state = PlaybackState(speed=1.0)

    increase_speed(state)
    assert state.speed == 2.0

    state.speed = MAX_SPEED
    increase_speed(state)
    assert state.speed == MAX_SPEED  # does not exceed the ceiling


def test_decrease_speed_halves_and_clamps_at_min() -> None:
    state = PlaybackState(speed=1.0)

    decrease_speed(state)
    assert state.speed == 0.5

    state.speed = MIN_SPEED
    decrease_speed(state)
    assert state.speed == MIN_SPEED  # does not go below the floor


# -- live scrub (TASK-048, Stage 8 reopening) -----------------------------


def test_seek_relative_moves_by_exactly_one_frame_regardless_of_speed() -> None:
    """Left/Right always step one frame -- `state.speed` (which governs
    ordinary playback advancement) must have no bearing on a keyboard
    seek.
    """
    state = PlaybackState(position=5.0, speed=8.0)

    index = seek_relative(state, 1, max_index=10)
    assert index == 6
    assert state.position == 6.0

    index = seek_relative(state, -1, max_index=10)
    assert index == 5


def test_seek_relative_clamps_at_both_ends() -> None:
    state = PlaybackState(position=0.0)
    assert seek_relative(state, -1, max_index=10) == 0

    state = PlaybackState(position=10.0)
    assert seek_relative(state, 1, max_index=10) == 10


def test_seek_to_jumps_directly_to_an_absolute_frame() -> None:
    state = PlaybackState(position=3.0)

    index = seek_to(state, 7, max_index=10)

    assert index == 7
    assert state.position == 7.0


def test_seek_to_clamps_an_out_of_range_target() -> None:
    state = PlaybackState(position=3.0)

    assert seek_to(state, -5, max_index=10) == 0
    assert seek_to(state, 999, max_index=10) == 10


def test_frame_index_from_fraction_maps_the_full_range() -> None:
    assert frame_index_from_fraction(0.0, max_index=10) == 0
    assert frame_index_from_fraction(1.0, max_index=10) == 10
    assert frame_index_from_fraction(0.5, max_index=10) == 5


def test_frame_index_from_fraction_clamps_outside_zero_to_one() -> None:
    """A drag that overshoots the bar's own extent (the cursor moves past
    either end while still held) should clamp to that end, not
    extrapolate past it.
    """
    assert frame_index_from_fraction(-0.5, max_index=10) == 0
    assert frame_index_from_fraction(1.5, max_index=10) == 10


def test_playback_state_defaults_to_not_dragging() -> None:
    assert PlaybackState().dragging is False
