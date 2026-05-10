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


def test_log_filter_set(prodtest_client: ProdtestClient) -> None:
    """log-filter should accept a filter string."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.LOG_FILTER, "*"))


def test_log_filter_requires_argument(prodtest_client: ProdtestClient) -> None:
    """log-filter with no filter string should be rejected."""
    with pytest.raises(ResponseNotOkError):
        prodtest_client.command_ok(ProdtestCommand(Cmd.LOG_FILTER))
