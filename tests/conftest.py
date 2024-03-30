"""Configuration and fixtures."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Iterator, Protocol

import pytest

import pyforce


def create_user(
    connection: pyforce.Connection,
    name: str,
    full_name: str | None = None,
    email: str | None = None,
) -> pyforce.User:
    """Create a new user on perforce server and return it."""
    data = pyforce.p4(connection, ["user", "-o", name])[0]

    if full_name is not None:
        data["FullName"] = full_name
    if email is not None:
        data["Email"] = email

    pyforce.p4(connection, ["user", "-i", "-f"], stdin=data)
    return pyforce.get_user(connection, name)


class UserFactory(Protocol):
    """Create and return a new user."""

    def __call__(self, name: str) -> pyforce.User:  # noqa: D102
        ...


@pytest.fixture()
def user_factory(server: str) -> Iterator[UserFactory]:
    """Factory fixture that create and return a new user."""
    connection = pyforce.Connection(port=server)
    created: list[pyforce.User] = []

    def factory(name: str) -> pyforce.User:
        user = create_user(connection, name)
        created.append(user)
        return user

    yield factory

    for user in created:
        pyforce.p4(connection, ["user", "-d", "-f", user.name])


def create_client(
    connection: pyforce.Connection,
    name: str,
    stream: str | None = None,
    root: Path | None = None,
) -> pyforce.Client:
    """Create a new `Client` on perforce server and return it."""
    command = ["client", "-o"]
    if stream is not None:
        command += ["-S", stream]
    command += [name]

    data = pyforce.p4(connection, command)[0]

    if root is not None:
        data["Root"] = str(root.resolve())

    pyforce.p4(connection, ["client", "-i"], stdin=data)
    return pyforce.get_client(connection, name)


class ClientFactory(Protocol):
    """Create and return a new client."""

    def __call__(self, name: str, stream: str | None = None) -> pyforce.Client:  # noqa: D102
        ...


@pytest.fixture()
def client_factory(server: str) -> Iterator[ClientFactory]:
    """Factory fixture that create and return a new client."""
    connection = pyforce.Connection(port=server)
    created: list[tuple[pyforce.Client, Path]] = []

    def factory(name: str, stream: str | None = None) -> pyforce.Client:
        root = Path(tempfile.mkdtemp(prefix="pyforce-client-"))
        client = create_client(connection, name, stream=stream, root=root)
        created.append((client, root))
        return client

    yield factory

    for client, root in created:
        pyforce.p4(connection, ["client", "-d", "-f", client.name])
        if root.exists():
            shutil.rmtree(root)


@pytest.fixture()
def client(server: str) -> Iterator[pyforce.Client]:
    """Create a client on a mainline stream for the duration of the test.

    This fixture create (and tear-down) a stream depot, a mainline stream and
    a client on that stream.
    """
    connection = pyforce.Connection(port=server)

    depot = f"depot-{uuid.uuid4().hex}"
    data = pyforce.p4(connection, ["depot", "-o", "-t", "stream", depot])[0]
    pyforce.p4(connection, ["depot", "-i"], stdin=data)

    stream = f"//{depot}/stream-{uuid.uuid4().hex}"
    data = pyforce.p4(connection, ["stream", "-o", "-t", "mainline", stream])[0]
    pyforce.p4(connection, ["stream", "-i"], stdin=data)

    client = create_client(
        connection,
        f"client-{uuid.uuid4().hex}",
        stream=stream,
        root=Path(tempfile.mkdtemp(prefix="pyforce-client-")),
    )

    yield client

    pyforce.p4(connection, ["client", "-d", "-f", client.name])
    pyforce.p4(connection, ["stream", "-d", "--obliterate", "-y", stream])
    pyforce.p4(connection, ["obliterate", "-y", f"//{depot}/..."])
    pyforce.p4(connection, ["depot", "-d", depot])
    shutil.rmtree(client.root)


class FileFactory(Protocol):
    """Create and return a new file."""

    def __call__(self, root: Path, prefix: str = "file", content: str = "") -> Path:  # noqa: D102
        ...


@pytest.fixture()
def file_factory() -> FileFactory:
    """Factory fixture that create and return a new file."""

    def factory(root: Path, prefix: str = "file", content: str = "") -> Path:
        path = root / f"{prefix}-{uuid.uuid4().hex}"
        with path.open("w") as fp:
            fp.write(content)
        return path

    return factory


@pytest.fixture(autouse=True, scope="session")
def server() -> Iterator[str]:
    """Create a temporary perforce server for the duration of the test session.

    Yield:
        The server port ('localhost:1666').
    """
    # Backup p4 variables set as env variables, and clear them.
    # This should override all variables that could cause issue with the tests
    # We override 'P4ENVIRON' and 'P4CONFIG' because both files, if set, could
    # overrides environment variables.
    # Predecence for variables:
    # https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_set.html
    backup_env: dict[str, str] = {}
    for key in ("P4CLIENT", "P4PORT", "P4USER", "P4CONFIG", "P4ENVIRO"):
        value = os.environ.pop(key, None)
        if value is not None:
            backup_env[key] = value

    # Run server
    root = Path(tempfile.mkdtemp(prefix="pyforce-server-"))
    port = "localhost:1666"  # default port on localhost
    user = "remote"  # same as p4d default
    timeout = 5  # in seconds

    process = subprocess.Popen(["p4d", "-r", str(root), "-p", port, "-u", user])
    start_time = time.time()

    while True:
        if time.time() > start_time + timeout:
            msg = f"Server initialization timed out after {timeout} seconds"
            raise RuntimeError(msg)

        try:
            subprocess.check_call(["p4", "-p", port, "-u", user, "info"])
        except subprocess.CalledProcessError:
            continue
        else:
            break

    yield port

    # Kill server
    process.kill()
    process.communicate()

    # Restore environment
    for key, value in backup_env.items():
        os.environ[key] = value

    # Delete server root
    if root.exists():
        shutil.rmtree(root)
