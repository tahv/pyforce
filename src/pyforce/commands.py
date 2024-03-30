"""Pyforce commands."""

from __future__ import annotations

import marshal
import re
import subprocess
from typing import Iterator

from pyforce.exceptions import (
    AuthenticationError,
    ChangeUnknownError,
    ClientNotFoundError,
    CommandExecutionError,
    ConnectionExpiredError,
    UserNotFoundError,
)
from pyforce.models import (
    ActionInfo,
    ActionMessage,
    Change,
    ChangeInfo,
    ChangeStatus,
    Client,
    FStat,
    Revision,
    Sync,
    User,
)
from pyforce.utils import (
    Connection,
    MarshalCode,
    MessageSeverity,
    PerforceDict,
    extract_indexed_values,
    log,
)

# TODO: submit_changelist
# TODO: edit_changelist
# TODO: move: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_move.html
# TODO: opened

__all__ = [
    "get_user",
    "get_client",
    "get_change",
    "get_revisions",
    "create_changelist",
    "add",
    "edit",
    "delete",
    "sync",
    "login",
    "fstat",
    "p4",
]


def get_user(connection: Connection, user: str) -> User:
    """Get user specification.

    Command:
        `p4 user`_.

    Args:
        connection: Perforce connection.
        user: Perforce username.
    """
    data = p4(connection, ["user", "-o", user])[0]
    if "Update" not in data:
        msg = f"User {user!r} does not exists"
        raise UserNotFoundError(msg)
    return User(**data)  # type: ignore[arg-type]


def get_client(connection: Connection, client: str) -> Client:
    """Get client workspace specification.

    Command:
        `p4 client`_.

    Args:
        connection: Perforce connection.
        client: Perforce client name.
    """
    data = p4(connection, ["client", "-o", client])[0]
    if "Update" not in data:
        msg = f"Client {client!r} does not exists"
        raise ClientNotFoundError(msg)
    return Client(**data)  # type: ignore[arg-type]


def get_change(connection: Connection, change: int) -> Change:
    """Get changelist specification.

    Command:
        `p4 change`_.

    Args:
        connection: Perforce connection.
        change: The changelist number.

    Raises:
        ChangeUnknownError: ``change`` not found.
    """
    try:
        data = p4(connection, ["change", "-o", str(change)])[0]
    except CommandExecutionError as error:
        if error.data["data"].strip() == f"Change {change} unknown.":
            raise ChangeUnknownError(change) from error
        raise
    return Change(**data)  # type: ignore[arg-type]


def create_changelist(connection: Connection, description: str) -> ChangeInfo:
    """Create and return a new changelist.

    Command:
        `p4 change`_.

    Args:
        connection: Perforce connection.
        description: Changelist description.
    """
    data = p4(connection, ["change", "-o"])[0]
    data["Description"] = description
    _ = extract_indexed_values(data, "Files")
    p4(connection, ["change", "-i"], stdin=data)

    data = p4(connection, ["changes", "--me", "-m", "1", "-l"])[0]
    return ChangeInfo(**data)  # type: ignore[arg-type]


def changes(
    connection: Connection,
    user: str | None = None,
    *,
    status: ChangeStatus | None = None,
    long_output: bool = False,
) -> Iterator[ChangeInfo]:
    """Iter submitted and pending changelists.

    Command:
        `p4 changes`_.

    Args:
        connection: Perforce connection.
        user: List only changes made from that user.
        status: List only changes with the specified status.
        long_output: List long output, with full text of each changelist description.
    """
    command = ["changes"]
    if user:
        command += ["-u", user]
    if status:
        command += ["-s", str(status)]
    if long_output:
        command += ["-l"]

    for data in p4(connection, command):
        yield ChangeInfo(**data)  # type: ignore[arg-type]


def add(
    connection: Connection,
    filespecs: list[str],
    *,
    changelist: int | None = None,
    preview: bool = False,
) -> tuple[list[ActionMessage], list[ActionInfo]]:
    """Open ``filespecs`` in client workspace for **addition** to the depot.

    Command:
        `p4 add`_.

    Args:
        connection: Perforce connection.
        filespecs: A list of `File specifications`_.
        changelist: Open the files within the specified changelist. If not set,
            the files are linked to the default changelist.
        preview: Preview which files would be opened for add, without actually
            changing any files or metadata.

    Returns:
        `ActionInfo` and `ActionMessage` objects. `ActionInfo` are only included if
        something unexpected happened during the operation.
    """
    command = ["add"]
    if changelist:
        command += ["-c", str(changelist)]
    if preview:
        command += ["-n"]
    command += filespecs

    messages: list[ActionMessage] = []
    infos: list[ActionInfo] = []
    for data in p4(connection, command):
        if data["code"] == MarshalCode.INFO:
            messages.append(ActionMessage.from_info_data(data))
        else:
            infos.append(ActionInfo(**data))  # type: ignore[arg-type]
    return messages, infos


def edit(
    connection: Connection,
    filespecs: list[str],
    *,
    changelist: int | None = None,
    preview: bool = False,
) -> tuple[list[ActionMessage], list[ActionInfo]]:
    """Open ``filespecs`` in client workspace for **edit**.

    Command:
        `p4 edit`_.

    Args:
        connection: Perforce connection.
        filespecs: A list of `File specifications`_.
        changelist: Open the files within the specified changelist. If not set,
            the files are linked to the default changelist.
        preview: Preview the result of the operation, without actually changing
            any files or metadata.

    Returns:
        `ActionInfo` and `ActionMessage` objects. `ActionInfo` are only included if
        something unexpected happened during the operation.
    """
    command = ["edit"]
    if changelist:
        command += ["-c", str(changelist)]
    if preview:
        command += ["-n"]
    command += filespecs

    messages: list[ActionMessage] = []
    infos: list[ActionInfo] = []
    for data in p4(connection, command):
        if data["code"] == MarshalCode.INFO:
            messages.append(ActionMessage.from_info_data(data))
        else:
            infos.append(ActionInfo(**data))  # type: ignore[arg-type]
    return messages, infos


def delete(
    connection: Connection,
    filespecs: list[str],
    *,
    changelist: int | None = None,
    preview: bool = False,
) -> tuple[list[ActionMessage], list[ActionInfo]]:
    """Open ``filespecs`` in client workspace for **deletion** from the depo.

    Command:
        `p4 delete`_.

    Args:
        connection: Perforce connection.
        filespecs: A list of `File specifications`_.
        changelist: Open the files within the specified changelist. If not set,
            the files are linked to the default changelist.
        preview: Preview the result of the operation, without actually changing
            any files or metadata.

    Returns:
        `ActionInfo` and `ActionMessage` objects. `ActionInfo` are only included if
        something unexpected happened during the operation.
    """
    # TODO: investigate '-v' and '-k' options
    command = ["delete"]
    if changelist:
        command += ["-c", str(changelist)]
    if preview:
        command += ["-n"]
    command += filespecs

    messages: list[ActionMessage] = []
    infos: list[ActionInfo] = []
    for data in p4(connection, command):
        if data["code"] == MarshalCode.INFO:
            messages.append(ActionMessage.from_info_data(data))
        else:
            infos.append(ActionInfo(**data))  # type: ignore[arg-type]
    return messages, infos


def fstat(
    connection: Connection,
    filespecs: list[str],
    *,
    include_deleted: bool = False,
) -> Iterator[FStat]:
    """List files information.

    Local files (not in depot and not opened for ``add``) are not included.

    Command:
        `p4 fstat`_.

    Args:
        connection: Perforce connection.
        filespecs: A list of `File specifications`_.
        include_deleted: Include files with a head action of ``delete`` or
            ``move/delete``.
    """
    # NOTE: not using: '-Ol': include 'fileSize' and 'digest' fields.
    command = ["fstat"]
    if not include_deleted:
        command += ["-F", "^headAction=delete ^headAction=move/delete"]
    command += filespecs

    local_paths = set()  # TODO: not doing anything with local paths at the moment
    for data in p4(connection, command, max_severity=MessageSeverity.WARNING):
        if data["code"] == "error":
            path, _, message = data["data"].rpartition(" - ")
            path, message = path.strip(), message.strip()
            if message == "no such file(s).":
                local_paths.add(path)
            else:
                raise CommandExecutionError(data["data"], command=command, data=data)
        else:
            yield FStat(**data)  # type: ignore[arg-type]


def get_revisions(
    connection: Connection,
    filespecs: list[str],
    *,
    long_output: bool = False,
) -> Iterator[list[Revision]]:
    """List **all** revisions of files matching ``filespecs``.

    Command:
        `p4 filelog`_.

    Args:
        connection: Perforce Connection.
        filespecs: A list of `File specifications`_.
        long_output: List long output, with full text of each changelist description.

    Warning:
        The lists are not intentionally sorted despite being *naturally* sorted by
        descending revision (highest to lowset) due to how `p4 filelog`_ data are
        processed. This behavior could change in the future, the order is not
        guaranteed.
    """
    # NOTE: Most fields ends with the rev number, like 'foo1', other indicate a
    # relationship, like 'bar0,1'
    regex = re.compile(r"([a-zA-Z]+)([0-9]+)(?:,([0-9]+))?")

    command = ["filelog"]
    if long_output:
        command += ["-l"]
    command += filespecs

    for data in p4(connection, command):
        revisions: dict[int, dict[str, str]] = {}
        shared: dict[str, str] = {}

        for key, value in data.items():
            match = regex.match(key)

            if match:
                prefix: str = match.group(1)
                index = int(match.group(2))
                suffix = "" if match.group(3) is None else int(match.group(3))
                revisions.setdefault(index, {})[f"{prefix}{suffix}"] = value
            else:
                shared[key] = value

        yield [Revision(**rev, **shared) for rev in revisions.values()]  # type: ignore[arg-type]


def sync(connection: Connection, filespecs: list[str]) -> list[Sync]:
    """Update ``filespecs`` to the client workspace.

    Args:
        connection: Perforce Connection.
        filespecs: A list of `File specifications`_.
    """
    # TODO: parallel as an option
    command = ["sync", *filespecs]
    output = p4(connection, command, max_severity=MessageSeverity.WARNING)

    result: list = []
    for data in output:
        if data["code"] == MarshalCode.ERROR:
            _, _, message = data["data"].rpartition(" - ")
            message = message.strip()
            if message == "file(s) up-to-date.":
                log.debug(data["data"].strip())
                continue
            raise CommandExecutionError(message, command=command, data=data)

        if data["code"] == MarshalCode.INFO:
            log.info(data["data"].strip())
            continue

        # NOTE: The first item contain info about total file count and size.
        if not result and "totalFileCount" in data:
            total_files = int(data.pop("totalFileCount", 0))
            total_bytes = int(data.pop("totalFileSize", 0))
            log.info("Synced %s files (%s bytes)", total_files, total_bytes)

        result.append(Sync(**data))  # type: ignore[arg-type]

    return result


def login(connection: Connection, password: str) -> None:
    """Login to Perforce Server.

    Raises:
        AuthenticationError: Failed to login.
    """
    command = ["p4", "-p", connection.port]
    if connection.user:
        command += ["-u", connection.user]
    command += ["login"]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _, stderr = process.communicate(password.encode())

    if stderr:
        raise AuthenticationError(stderr.decode().strip())


def p4(
    connection: Connection,
    command: list[str],
    stdin: PerforceDict | None = None,
    max_severity: MessageSeverity = MessageSeverity.EMPTY,
) -> list[PerforceDict]:
    """Run a ``p4`` command and return its output.

    This function uses `marshal` (using ``p4 -G``) to load stdout and dump stdin.

    Args:
        connection: The connection to execute the command with.
        command: A ``p4`` command to execute, with arguments.
        stdin: Write a dict to the standard input file using `marshal.dump`.
        max_severity: Raises an exception if the output error severity is above
            that threshold.

    Returns:
        The command output.

    Raises:
        CommandExecutionError: An error occured during command execution.
        ConnectionExpiredError: Connection to server expired, password is required.
            You can use the `login` function.
    """
    args = ["p4", "-G", "-p", connection.port]
    if connection.user:
        args += ["-u", connection.user]
    if connection.client:
        args += ["-c", connection.client]
    args += command

    log.debug("Running: '%s'", " ".join(args))

    result: list[PerforceDict] = []
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE if stdin else None,
        stderr=subprocess.PIPE,
    )
    with process:
        if stdin:
            assert process.stdin is not None  # noqa: S101
            marshal.dump(stdin, process.stdin, 0)  # NOTE: perforce require version 0
        else:
            assert process.stdout is not None  # noqa: S101
            while True:
                try:
                    out: dict[bytes, bytes | int] = marshal.load(process.stdout)  # noqa: S302
                except EOFError:
                    break

                # NOTE: Some rare values, like user FullName, can be encoded
                # differently, and decoding them with 'latin-1' give us a result
                # that seem to match what P4V does.
                data = {
                    key.decode(): val.decode("latin-1")
                    if isinstance(val, bytes)
                    else str(val)
                    for key, val in out.items()
                }

                if (
                    data.get("code") == MarshalCode.ERROR
                    and int(data["severity"]) > max_severity
                ):
                    message = str(data["data"].strip())

                    if message == "Perforce password (P4PASSWD) invalid or unset.":
                        message = "Perforce connection expired, password is required"
                        raise ConnectionExpiredError(message)

                    raise CommandExecutionError(message, command=args, data=data)

                result.append(data)

        _, stderr = process.communicate()
        if stderr:
            message = stderr.decode()
            raise CommandExecutionError(message, command=args)

    return result
