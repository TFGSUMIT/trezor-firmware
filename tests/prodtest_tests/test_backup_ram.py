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

from trezorlib.prodtest.prodtest_client import Cmd, ProdtestClient, ProdtestCommand


@pytest.mark.requires_command(Cmd.BACKUP_RAM_LIST)
def test_backup_ram_list(prodtest_client: ProdtestClient) -> None:
    """backup-ram-list should initialize backup RAM and succeed (even if empty)."""
    prodtest_client.command_ok(ProdtestCommand(Cmd.BACKUP_RAM_LIST))
