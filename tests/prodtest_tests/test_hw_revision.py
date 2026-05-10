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


def test_hw_revision_is_byte(prodtest_client: ProdtestClient) -> None:
    """hw-revision should return an integer in the 0-255 range."""
    resp = prodtest_client.command_ok(ProdtestCommand(Cmd.HW_REVISION))
    assert resp.args.isdigit()
    assert 0 <= int(resp.args) <= 255


def test_hw_revision_rejects_args(prodtest_client: ProdtestClient) -> None:
    """hw-revision takes no arguments."""
    with pytest.raises(ResponseNotOkError):
        prodtest_client.command_ok(ProdtestCommand(Cmd.HW_REVISION, "extra"))
