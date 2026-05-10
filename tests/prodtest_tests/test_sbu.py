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


@pytest.mark.parametrize("sbu1,sbu2", [("0", "0"), ("1", "0"), ("0", "1"), ("1", "1")])
def test_sbu_set_levels(prodtest_client: ProdtestClient, sbu1: str, sbu2: str) -> None:
    """sbu-set should accept any combination of logical levels 0/1."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.SBU_SET, sbu1, sbu2))


def test_sbu_set_rejects_invalid_level(prodtest_client: ProdtestClient) -> None:
    """sbu-set should reject levels other than 0 or 1."""
    with pytest.raises(ResponseNotOkError):
        prodtest_client.command_ok(ProdtestCommand(Cmd.SBU_SET, "2", "0"))
