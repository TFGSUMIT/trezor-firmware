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

from trezorlib.prodtest.prodtest_client import Cmd, ProdtestClient, ProdtestCommand


def test_uptime_is_nonnegative_integer(prodtest_client: ProdtestClient) -> None:
    """prodtest-uptime should return a non-negative integer number of milliseconds."""
    resp = prodtest_client.command_ok(ProdtestCommand(Cmd.PRODTEST_UPTIME))
    assert resp.args.isdigit()


def test_uptime_is_monotonic(prodtest_client: ProdtestClient) -> None:
    """prodtest-uptime should not decrease between consecutive calls."""
    first = int(prodtest_client.command_ok(ProdtestCommand(Cmd.PRODTEST_UPTIME)).args)
    second = int(prodtest_client.command_ok(ProdtestCommand(Cmd.PRODTEST_UPTIME)).args)
    assert second >= first
