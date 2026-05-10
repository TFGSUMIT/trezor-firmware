# This file is part of the Trezor project.
#
# Copyright (C) SatoshiLabs and contributors
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the License along with this library.
# If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>.

"""Prodtest ``tropic-*`` command tests.

These tests run against a dedicated prodtest emulator with its own Tropic model
(the ``tropic_prodtest`` fixture), rather than the shared session emulator. The
fixture starts the Tropic model automatically — nothing has to be launched by
hand. The general pattern is:

  1. start the emulator + Tropic model (entering the context manager),
  2. issue ``tropic-*`` commands via ``session.client``,
  3. leave the context so the Tropic model flushes its final state, then
  4. (optionally) assert on ``session.state()``.

The tests seed the Tropic model with the default device-test config
(``tests/tropic_model/config.yml``), which represents an already-paired device.
Commands that need a fresh/unpaired chip (``tropic-pair``), device-specific
certificates, or hardware the model does not emulate faithfully (the TRNG, which
the model drives from a constant, and firmware update) are intentionally not
covered here.
"""

from __future__ import annotations

import pytest

from trezorlib.prodtest.prodtest_client import Cmd, ProdtestCommand

from .tropic_utils import TropicProdtest

# ECC-key and user-data slots populated by the default Tropic model config,
# used to check what ``tropic-erase-all-slots`` clears.
_ECC_KEY_SLOT = 0
_USER_DATA_SLOTS = (3, 4, 6)
# Arbitrary non-default sensors config: 8 hex digits = big-endian uint32.
_SENSORS_CONFIG_VALUE = "0000000F"


# --- info / read-only commands ---------------------------------------------


@pytest.mark.requires_command(Cmd.TROPIC_GET_CHIP_ID)
def test_tropic_get_chip_id(tropic_prodtest: TropicProdtest) -> None:
    """The Tropic model answers a chip-ID query with non-empty data."""
    with tropic_prodtest() as session:
        response = session.client.command_ok(ProdtestCommand(Cmd.TROPIC_GET_CHIP_ID))

    assert response.args, "tropic-get-chip-id returned no chip ID"


@pytest.mark.requires_command(Cmd.TROPIC_GET_RISCV_FW_VERSION)
def test_tropic_get_riscv_fw_version(tropic_prodtest: TropicProdtest) -> None:
    """The Tropic model reports its RISC-V firmware version."""
    with tropic_prodtest() as session:
        response = session.client.command_ok(
            ProdtestCommand(Cmd.TROPIC_GET_RISCV_FW_VERSION)
        )

    assert response.args, "tropic-get-riscv-fw-version returned no version"


@pytest.mark.requires_command(Cmd.TROPIC_GET_SPECT_FW_VERSION)
def test_tropic_get_spect_fw_version(tropic_prodtest: TropicProdtest) -> None:
    """The Tropic model reports its SPECT firmware version."""
    with tropic_prodtest() as session:
        response = session.client.command_ok(
            ProdtestCommand(Cmd.TROPIC_GET_SPECT_FW_VERSION)
        )

    assert response.args, "tropic-get-spect-fw-version returned no version"


@pytest.mark.requires_command(Cmd.TROPIC_LOCK_CHECK)
def test_tropic_lock_check(tropic_prodtest: TropicProdtest) -> None:
    """A fresh device (no pairing pubkey in MCU flash) reports as not locked.

    ``lock-check`` returns ``NO`` as soon as the MCU has no stored Tropic public
    key, which is the case for a freshly started emulator — the pairing process
    was never run against it.
    """
    with tropic_prodtest() as session:
        response = session.client.command_ok(ProdtestCommand(Cmd.TROPIC_LOCK_CHECK))

    assert response.args == "NO"


@pytest.mark.requires_command(Cmd.TROPIC_READ_CONFIGS)
def test_tropic_read_configs(tropic_prodtest: TropicProdtest) -> None:
    """Reading the whole I/R configuration over a privileged session succeeds."""
    with tropic_prodtest() as session:
        session.client.command_ok(ProdtestCommand(Cmd.TROPIC_READ_CONFIGS))


@pytest.mark.requires_command(Cmd.TROPIC_READ_SENSORS)
def test_tropic_read_sensors(tropic_prodtest: TropicProdtest) -> None:
    """Reading the sensors config returns the default all-enabled value."""
    with tropic_prodtest() as session:
        response = session.client.command_ok(ProdtestCommand(Cmd.TROPIC_READ_SENSORS))

    assert response.args == "0x00000000"


# --- self-test / diagnostic commands ---------------------------------------

# These exercise the Tropic over a session and clean up after themselves; each
# runs against its own fresh model, so we only assert they complete successfully.
_SELF_TEST_COMMANDS = [
    Cmd.TROPIC_BENCHMARK,
    Cmd.TROPIC_STRESS_INIT,
    Cmd.TROPIC_STRESS_SESSION,
    Cmd.TROPIC_STRESS_MAC_AND_DESTROY,
    Cmd.TROPIC_STRESS_TEST,
    Cmd.TROPIC_TEST_MAC_AND_DESTROY,
    Cmd.TROPIC_TEST_RMEM,
    Cmd.TROPIC_TEST_SIGN,
    Cmd.TROPIC_TESTS_CLEANUP,
]


@pytest.mark.parametrize("command", _SELF_TEST_COMMANDS)
def test_tropic_self_tests(
    tropic_prodtest: TropicProdtest,
    available_commands: set[str],
    command: str,
) -> None:
    """Each self-test/diagnostic command runs to completion on the model."""
    if command not in available_commands:
        pytest.skip(f"command not available on this device: {command}")

    with tropic_prodtest() as session:
        session.client.command_ok(ProdtestCommand(command))


# --- state-changing commands (inspected via the model output) --------------


@pytest.mark.requires_command(Cmd.TROPIC_ERASE_ALL_SLOTS)
def test_tropic_erase_all_slots(tropic_prodtest: TropicProdtest) -> None:
    """``erase-all-slots`` clears ECC keys and data slots, keeps pairing keys."""
    with tropic_prodtest() as session:
        session.client.command_ok(ProdtestCommand(Cmd.TROPIC_ERASE_ALL_SLOTS))

    state = session.state()

    # Pairing keys are explicitly preserved.
    assert state.pairing_key_state(1) == "written"
    assert state.pairing_key_state(2) == "written"

    # ECC keys and user-data slots seeded by the config are gone.
    assert not state.ecc_key_is_present(_ECC_KEY_SLOT)
    for slot in _USER_DATA_SLOTS:
        assert state.slot_is_erased(slot), f"slot {slot} not erased"


@pytest.mark.requires_command(Cmd.TROPIC_SET_SENSORS)
def test_tropic_set_sensors(tropic_prodtest: TropicProdtest) -> None:
    """``set-sensors`` writes the requested value into the R-config."""
    with tropic_prodtest() as session:
        session.client.command_ok(
            ProdtestCommand(Cmd.TROPIC_SET_SENSORS, _SENSORS_CONFIG_VALUE)
        )

    state = session.state()
    assert state.r_config.get("cfg_sensors") == int(_SENSORS_CONFIG_VALUE, 16)


@pytest.mark.requires_command(Cmd.TROPIC_TEST_COUNTER)
def test_tropic_test_counter(tropic_prodtest: TropicProdtest) -> None:
    """``test-counter`` initializes the monotonic counters on the model."""
    with tropic_prodtest() as session:
        session.client.command_ok(ProdtestCommand(Cmd.TROPIC_TEST_COUNTER))

    state = session.state()
    assert state.mcounters, "no monotonic counters were initialized"


# The distribution-version slot lock writes, and its always-erased backup slot.
_DISTRIBUTION_VERSION_SLOT = 6
_BACKUP_DISTRIBUTION_VERSION_SLOT = 7


@pytest.mark.requires_command(Cmd.TROPIC_LOCK)
def test_tropic_lock(tropic_prodtest: TropicProdtest) -> None:
    """``tropic-lock`` writes the expected config and distribution version.

    ``lock`` is irreversible, but each Tropic test runs against its own
    throwaway model, so locking it is safe. It rewrites the reversible config to
    the expected "locked" values, writes the distribution version into its slot,
    erases the backup slot, and leaves the pairing keys untouched. We capture a
    fresh (unlocked) model as a baseline to show the reversible config actually
    changed.
    """
    with tropic_prodtest() as baseline_session:
        pass  # fresh model, no commands issued
    baseline = baseline_session.state()

    with tropic_prodtest() as session:
        session.client.command_ok(ProdtestCommand(Cmd.TROPIC_LOCK))
    locked = session.state()

    # The reversible config is rewritten to the locked values.
    assert locked.r_config != baseline.r_config

    # The distribution version is written (4-byte big-endian) and its backup
    # slot is left erased.
    version = locked.slot_value(_DISTRIBUTION_VERSION_SLOT)
    assert version is not None and len(version) == 4
    assert locked.slot_is_erased(_BACKUP_DISTRIBUTION_VERSION_SLOT)

    # Pairing keys survive the lock.
    assert locked.pairing_key_state(1) == "written"
    assert locked.pairing_key_state(2) == "written"
