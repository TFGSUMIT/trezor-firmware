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


@pytest.mark.requires_command(Cmd.HAPTIC_TEST)
def test_haptic_test_runs(prodtest_client: ProdtestClient) -> None:
    """haptic-test should run a short feedback pulse and succeed."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.HAPTIC_TEST, "1"))


@pytest.mark.requires_command(Cmd.HAPTIC_TEST)
def test_haptic_test_rejects_bad_amplitude(prodtest_client: ProdtestClient) -> None:
    """haptic-test should reject an amplitude above 100."""
    with pytest.raises(ResponseNotOkError):
        prodtest_client.command_ok(ProdtestCommand(Cmd.HAPTIC_TEST, "1", "101"))
