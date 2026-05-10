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

from __future__ import annotations

import typing as t

import pytest

from trezorlib.prodtest.prodtest_client import (
    Cmd,
    ProdtestClient,
    ProdtestCommand,
    ResponseNotOkError,
)


@pytest.fixture(autouse=True)
def _restore_rgbled(
    prodtest_client: ProdtestClient, available_commands: set[str]
) -> t.Iterator[None]:
    """Leave the RGB LED as it was on entry (off) after each test.

    These tests share the session emulator, and — with tests running in random
    order — must not leave the LED lit for whatever runs next. The prodtest main
    loop turns the LED off and disables automatic control once its start-up
    animation finishes, so ``off`` is the state tests see on entry. There is no
    command to read the current color, so we reset to off (0, 0, 0) to match it.
    """
    yield
    if Cmd.RGBLED_SET in available_commands:
        prodtest_client.command_ok(ProdtestCommand(Cmd.RGBLED_SET, "0", "0", "0"))


@pytest.mark.requires_command(Cmd.RGBLED_SET)
def test_rgbled_set(prodtest_client: ProdtestClient) -> None:
    """rgbled-set should accept an R/G/B triple in the 0-255 range."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.RGBLED_SET, "0", "255", "0"))


@pytest.mark.requires_command(Cmd.RGBLED_SET)
def test_rgbled_set_rejects_out_of_range(prodtest_client: ProdtestClient) -> None:
    """rgbled-set should reject a channel value above 255."""
    with pytest.raises(ResponseNotOkError):
        prodtest_client.command_ok(ProdtestCommand(Cmd.RGBLED_SET, "256", "0", "0"))


@pytest.mark.requires_command(Cmd.RGBLED_EFFECT_START, Cmd.RGBLED_EFFECT_STOP)
def test_rgbled_effect_start_stop(prodtest_client: ProdtestClient) -> None:
    """An RGB LED effect should start and stop successfully."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.RGBLED_EFFECT_START, "0"))
    prodtest_client.command_ok(ProdtestCommand(Cmd.RGBLED_EFFECT_STOP))
