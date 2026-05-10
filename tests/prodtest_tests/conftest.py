from __future__ import annotations

import os
import tempfile
import typing as t
from contextlib import contextmanager
from pathlib import Path

import pytest

from trezorlib._internal.emulator import TropicModel
from trezorlib.prodtest.prodtest_client import Cmd, ProdtestClient, ProdtestCommand
from trezorlib.prodtest.prodtest_emulator import (
    DEFAULT_TROPIC_MODEL_CONFIGFILE,
    find_free_port,
    get_prodtest_emulator,
)
from trezorlib.prodtest.prodtest_transport import VcpUdpTransport

from .tropic_utils import TropicProdtest, TropicSession

# UDP base port for the dedicated Tropic test emulator. Kept clear of the shared
# session emulator (21324) and the default Tropic model port (28992). Tropic
# tests run one at a time and tear their emulator down, so a fixed base is safe.
_TROPIC_EMULATOR_UDP_BASE_PORT = 31324


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--prodtest-model",
        action="store",
        default=os.environ.get("TREZOR_MODEL"),
        help="Prodtest model to run tests against (e.g. t3w1, t3t1). "
        "Can also be set via the TREZOR_MODEL environment variable. "
        "If omitted, the 'latest' emulator build is used.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_command(*names): skip the test unless the device reports all "
        "the given commands in its 'help' listing. Use for model-specific "
        "commands (touch, RGB LED, telemetry, ...).",
    )


@pytest.fixture(scope="session")
def available_commands(prodtest_client: ProdtestClient) -> set[str]:
    """The set of command names the device reports via ``help``.

    This is the device's own view of which commands are compiled in, so it
    stays correct as commands are added or gated per model. ``test_help``
    separately asserts that this set matches what each model is expected to
    expose.
    """
    resp = prodtest_client.command_ok(ProdtestCommand(Cmd.HELP))
    # Each trace line is " <name> - <info>"; extract the command name.
    assert resp.traces is not None
    return {
        line.split()[0]
        for line in resp.traces
        if line.strip() and not line.startswith("Available")
    }


@pytest.fixture(autouse=True)
def skip_if_command_unavailable(
    request: pytest.FixtureRequest, available_commands: set[str]
) -> None:
    """Skip a test whose ``requires_command`` marker names an absent command.

    Model-specific commands are only compiled into some builds. A test declares
    what it needs with ``@pytest.mark.requires_command(Cmd.TOUCH_VERSION)`` and
    is skipped wherever the device doesn't offer it.
    """
    marker = request.node.get_closest_marker("requires_command")
    if marker is None:
        return

    missing = set(marker.args) - available_commands
    if missing:
        pytest.skip(f"command(s) not available on this device: {sorted(missing)}")


@pytest.fixture
def tropic_prodtest(
    request: pytest.FixtureRequest,
) -> TropicProdtest:
    """Factory for a dedicated prodtest emulator with its own Tropic model.

    Each call starts a fresh ``model_server`` seeded with a config (the
    device-test default, or *tropic_model_configfile* if given), starts a
    prodtest emulator pointed at it, yields a :class:`TropicSession`, and tears
    both down on exit. Following the emulator refactor, the model is a standalone
    process (like ``CoreEmulator`` + the device-test ``tropic_model_port``
    fixture): the emulator only receives its TCP port.

    The model dumps its final state on shutdown (SIGINT), so inspect it *after*
    the ``with`` block::

        def test_pair(tropic_prodtest):
            with tropic_prodtest() as tp:
                tp.client.command_ok(ProdtestCommand(Cmd.TROPIC_PAIR))
            assert tp.state().pairing_key_state(0) == "written"

    This is separate from the shared session emulator used by the other tests:
    inspecting Tropic state requires stopping the model, which a shared,
    session-scoped emulator cannot offer.
    """
    model = request.config.getoption("prodtest_model") or None

    @contextmanager
    def _factory(
        *, tropic_model_configfile: str | Path | None = None
    ) -> t.Iterator[TropicSession]:
        config = Path(tropic_model_configfile or DEFAULT_TROPIC_MODEL_CONFIGFILE)
        # Not auto-deleted: the model's output YAML must outlive this block so
        # ``session.state()`` can read it after the model has been stopped.
        model_dir = tempfile.mkdtemp(prefix="prodtest_tropic_model_")
        tropic_model = TropicModel(
            profile_dir=model_dir,
            configfile=config,
            port=find_free_port(),
        )
        tropic_model.start()
        try:
            emu = get_prodtest_emulator(
                model=model,
                port=_TROPIC_EMULATOR_UDP_BASE_PORT,
                tropic_model_port=tropic_model.port,
            )
            emu.start()
            client = ProdtestClient(transport=VcpUdpTransport(port=emu.vcp_port))
            session = TropicSession(client, tropic_model)
            try:
                yield session
            finally:
                client.close()
                emu.stop()
        finally:
            # Stop the model after the emulator so it flushes its final state.
            tropic_model.stop()

    return _factory


@pytest.fixture(scope="session")
def prodtest_client(
    request: pytest.FixtureRequest,
) -> t.Generator[ProdtestClient, None, None]:
    """Start a prodtest emulator and yield a connected client.

    The model is resolved in order:
      1. --prodtest-model CLI option
      2. TREZOR_MODEL environment variable
      3. 'latest' symlink under core/build-xtask/artifacts/latest/prodtest-emu
    """
    model = request.config.getoption("prodtest_model") or None

    emu = get_prodtest_emulator(model=model)
    with emu:
        client = ProdtestClient(transport=VcpUdpTransport(port=emu.vcp_port))
        # Eagerly resolve the model so any unknown-model error surfaces at startup.
        _ = client.model
        yield client
        client.close()
