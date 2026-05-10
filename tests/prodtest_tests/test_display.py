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

import pytest

from trezorlib.prodtest.prodtest_client import (
    Cmd,
    ProdtestClient,
    ProdtestCommand,
    ResponseNotOkError,
)


def test_display_border(prodtest_client: ProdtestClient) -> None:
    """display-border should succeed with no arguments."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.DISPLAY_BORDER))


def test_display_text(prodtest_client: ProdtestClient) -> None:
    """display-text should succeed rendering the given text."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.DISPLAY_TEXT, "prodtest"))


def test_display_bars(prodtest_client: ProdtestClient) -> None:
    """display-bars should succeed rendering a valid RGBW color pattern."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.DISPLAY_BARS, "RGBW"))


def test_display_set_backlight(prodtest_client: ProdtestClient) -> None:
    """display-set-backlight should accept a level in the 0-255 range."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.DISPLAY_SET_BACKLIGHT, "128"))


def test_display_set_backlight_rejects_out_of_range(
    prodtest_client: ProdtestClient,
) -> None:
    """A backlight level above 255 should be rejected."""
    with pytest.raises(ResponseNotOkError):
        prodtest_client.command_ok(ProdtestCommand(Cmd.DISPLAY_SET_BACKLIGHT, "256"))
