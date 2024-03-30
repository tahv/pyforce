"""Test suite for the commands module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pyforce

if TYPE_CHECKING:
    from conftest import ClientFactory, FileFactory, UserFactory


def test_get_user_returns_expected_user(server: str, user_factory: UserFactory) -> None:
    """It returns the expected `User` instance."""
    user_factory("foo")
    connection = pyforce.Connection(port=server)
    user = pyforce.get_user(connection, "foo")
    assert isinstance(user, pyforce.User)
    assert user.name == "foo"


def test_get_user_raise_user_not_found(server: str) -> None:
    """It raises an error when user does not exists."""
    connection = pyforce.Connection(port=server)
    with pytest.raises(pyforce.UserNotFoundError):
        pyforce.get_user(connection, "foo")


def test_get_client_returns_expected_client(
    server: str,
    client_factory: ClientFactory,
) -> None:
    """It returns the expected `Client` instance."""
    client_factory("foo")
    connection = pyforce.Connection(port=server)
    user = pyforce.get_client(connection, "foo")
    assert isinstance(user, pyforce.Client)
    assert user.name == "foo"


def test_get_client_raise_client_not_found(server: str) -> None:
    """It raises an error when client does not exists."""
    connection = pyforce.Connection(port=server)
    with pytest.raises(pyforce.ClientNotFoundError):
        pyforce.get_client(connection, "foo")


def test_get_change_return_expected_changelist(
    server: str,
    client: pyforce.Client,
) -> None:
    """It returns a Change instance of expected change."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    change_info = pyforce.create_changelist(connection, "Foo")

    change = pyforce.get_change(connection, change_info.change)
    assert isinstance(change, pyforce.Change)
    assert change.change == change_info.change


def test_get_change_raise_change_not_found(
    server: str,
    client: pyforce.Client,
) -> None:
    """It raises an error when change does not exists."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    with pytest.raises(pyforce.ChangeUnknownError):
        pyforce.get_change(connection, 123)


def test_create_changelist_return_change_info(
    server: str,
    client: pyforce.Client,
) -> None:
    """It create a new changelist and return it."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    info = pyforce.create_changelist(connection, "Foo Bar")
    assert isinstance(info, pyforce.ChangeInfo)
    assert info.description.strip() == "Foo Bar"


def test_create_changelist_return_correct_change(
    server: str,
    client: pyforce.Client,
) -> None:
    """When multiple changelists already exists, it return the correct one."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    pyforce.create_changelist(connection, "Foo")
    info = pyforce.create_changelist(connection, "Bar")
    assert info.description.strip() == "Bar"


def test_create_changelist_return_existing_changelist(
    server: str,
    client: pyforce.Client,
) -> None:
    """The changelist is actually created on the server."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    info = pyforce.create_changelist(connection, "Foo")
    change = pyforce.get_change(connection, info.change)
    assert change.change == info.change
    assert change.description == info.description


def test_create_changelist_contain_no_files(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It does not includes files from default changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="foo")
    pyforce.add(connection, [str(file)])
    info = pyforce.create_changelist(connection, "Foo")
    change = pyforce.get_change(connection, info.change)
    assert change.files == []


# TODO: test_changes


def test_add_return_added_file(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It returns the added files."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="foo")
    messages, infos = pyforce.add(connection, [str(file)])
    assert not messages
    assert len(infos) == 1
    assert isinstance(infos[0], pyforce.ActionInfo)
    assert infos[0].client_file == str(file)


def test_add_empty_file_return_addinfo(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It returns info object with correct information."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="")
    messages, _ = pyforce.add(connection, [str(file)])
    assert len(messages) == 1
    assert isinstance(messages[0], pyforce.ActionMessage)
    assert messages[0].message == "empty, assuming text."


def test_add_to_changelist(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It open file for add in specified changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)

    change_info = pyforce.create_changelist(connection, "Foo")

    file = file_factory(root=client.root, content="foobar")
    _, infos = pyforce.add(connection, [str(file)], changelist=change_info.change)

    change = pyforce.get_change(connection, change_info.change)
    assert infos[0].depot_file == change.files[0]


def test_add_preview_does_not_add_file_to_changelist(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """Running add in preview mode does not add file to changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    change_info = pyforce.create_changelist(connection, "Foo")

    pyforce.add(
        connection,
        [str(file_factory(root=client.root, content="foobar"))],
        changelist=change_info.change,
        preview=True,
    )

    change = pyforce.get_change(connection, change_info.change)
    assert change.files == []


def test_edit_return_edited_files(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It returns the edited files."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])
    messages, infos = pyforce.edit(connection, [str(file)])

    assert not messages
    assert len(infos) == 1
    assert isinstance(infos[0], pyforce.ActionInfo)
    assert infos[0].client_file == str(file)


def test_edit_add_file_to_changelist(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It open file for edit in specified changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)

    file = file_factory(root=client.root, content="foo")
    change_info = pyforce.create_changelist(connection, "Foo")

    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])
    _, infos = pyforce.edit(connection, [str(file)], changelist=change_info.change)

    change = pyforce.get_change(connection, change_info.change)
    assert infos[0].depot_file == change.files[0]


def test_edit_preview_does_not_add_file_to_changelist(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """Running edit in preview mode does not open file to changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)

    change_info = pyforce.create_changelist(connection, "Foo")

    file = file_factory(root=client.root, content="foo")
    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])

    pyforce.edit(connection, [str(file)], changelist=change_info.change, preview=True)

    change = pyforce.get_change(connection, change_info.change)
    assert change.files == []


def test_delete_return_deleted_files(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It returns the edited files."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])
    messages, infos = pyforce.delete(connection, [str(file)])

    assert not messages
    assert len(infos) == 1
    assert isinstance(infos[0], pyforce.ActionInfo)
    assert infos[0].client_file == str(file)


def test_delete_add_file_to_changelist(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It open file for deletion to specified changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)

    file = file_factory(root=client.root, content="foo")
    change_info = pyforce.create_changelist(connection, "Foo")

    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])
    _, infos = pyforce.delete(connection, [str(file)], changelist=change_info.change)

    change = pyforce.get_change(connection, change_info.change)
    assert infos[0].depot_file == change.files[0]


def test_delete_preview_does_not_add_file_to_changelist(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """Running delete in preview mode does not open file to changelist."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)

    change_info = pyforce.create_changelist(connection, "Foo")

    file = file_factory(root=client.root, content="foo")
    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])

    pyforce.delete(connection, [str(file)], changelist=change_info.change, preview=True)

    change = pyforce.get_change(connection, change_info.change)
    assert change.files == []


def test_sync_return_synced_files(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """It sync files and return them."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])
    pyforce.p4(connection, ["sync", "-f", f"{file}#0"])

    synced_files = pyforce.sync(connection, [str(file)])

    assert len(synced_files) == 1
    assert isinstance(synced_files[0], pyforce.Sync)
    assert synced_files[0].client_file == str(file)
    assert synced_files[0].revision == 1


def test_sync_skip_up_to_date_file(
    server: str,
    file_factory: FileFactory,
    client: pyforce.Client,
) -> None:
    """Is skip up to date files without raising error."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    file = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(file)])
    pyforce.p4(connection, ["submit", "-d", "Added Foo", str(file)])

    synced_files = pyforce.sync(connection, [str(file)])
    assert len(synced_files) == 0


def test_fstat_return_fstat_instance(
    server: str,
    client: pyforce.Client,
    file_factory: FileFactory,
) -> None:
    """It return expected object type."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    path = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(path)])
    pyforce.p4(connection, ["submit", "-d", "Foo", str(path)])

    fstats = list(pyforce.fstat(connection, [str(path)], include_deleted=False))
    assert isinstance(fstats[0], pyforce.FStat)


def test_fstat_return_remote_file(
    server: str,
    client: pyforce.Client,
    file_factory: FileFactory,
) -> None:
    """It list remote file."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    path = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(path)])
    pyforce.p4(connection, ["submit", "-d", "Foo", str(path)])

    fstats = list(pyforce.fstat(connection, [str(path)], include_deleted=False))
    assert len(fstats) == 1
    assert fstats[0].client_file == str(path)
    assert fstats[0].head
    assert fstats[0].head.revision  # NOTE: check is in depot
    assert fstats[0].have_rev  # NOTE: check is client


def test_fstat_return_deleted_file(
    server: str,
    client: pyforce.Client,
    file_factory: FileFactory,
) -> None:
    """It list deleted file if include_deleted is True."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    path = file_factory(root=client.root, content="foo")

    pyforce.add(connection, [str(path)])
    pyforce.p4(connection, ["submit", "-d", "Adding foo", str(path)])
    pyforce.p4(connection, ["delete", str(path)])
    pyforce.p4(connection, ["submit", "-d", "Deleting Foo", str(path)])

    fstats = list(pyforce.fstat(connection, [str(path)], include_deleted=True))
    assert len(fstats) == 1
    assert fstats[0].client_file == str(path)


def test_fstat_ignore_local_file(
    server: str,
    client: pyforce.Client,
    file_factory: FileFactory,
) -> None:
    """It ignore local files."""
    connection = pyforce.Connection(port=server, user=client.owner, client=client.name)
    path = file_factory(root=client.root, content="foo")

    fstats = list(pyforce.fstat(connection, [str(path)], include_deleted=False))
    assert len(fstats) == 0


# TODO: test_get_revisions
