"""Pyforce models."""

from __future__ import annotations

import pathlib
import shlex
from dataclasses import dataclass
from typing import Any, Iterable, List, Literal, Mapping, NamedTuple, Union, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from pyforce.utils import (
    MessageLevel,
    PerforceDateTime,
    PerforceDict,
    PerforceTimestamp,
    StrEnum,
    extract_indexed_values,
)

__all__ = [
    "UserType",
    "AuthMethod",
    "User",
    "View",
    "ClientType",
    "ClientOptions",
    "SubmitOptions",
    "Client",
    "ChangeStatus",
    "ChangeType",
    "Change",
    "ChangeInfo",
    "Action",
    "ActionMessage",
    "ActionInfo",
    "Revision",
    "Sync",
    "OtherOpen",
    "HeadInfo",
    "FStat",
]


class PyforceModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __repr_args__(self) -> Iterable[tuple[str | None, Any]]:
        """Filter out extras."""
        extra = self.__pydantic_extra__
        if not extra:
            return super().__repr_args__()
        return (
            (key, val) for (key, val) in super().__repr_args__() if key not in extra
        )


class UserType(StrEnum):
    """Types of user enum."""

    STANDARD = "standard"
    OPERATOR = "operator"
    SERVICE = "service"


class AuthMethod(StrEnum):
    """User authentication enum."""

    PERFORCE = "perforce"
    LDAP = "ldap"


class User(PyforceModel):
    """A Perforce user specification."""

    access: PerforceDateTime = Field(alias="Access", repr=False)
    """The date and time this user last ran a Helix Server command."""

    auth_method: AuthMethod = Field(alias="AuthMethod", repr=False)
    email: str = Field(alias="Email")
    full_name: str = Field(alias="FullName")
    type: UserType = Field(alias="Type")

    update: PerforceDateTime = Field(alias="Update", repr=False)
    """The date and time this user was last updated."""

    name: str = Field(alias="User")


class SubmitOptions(StrEnum):
    """Options to govern the default behavior of ``p4 submit``."""

    SUBMIT_UNCHANGED = "submitunchanged"
    SUBMIT_UNCHANGED_AND_REOPEN = "submitunchanged+reopen"
    REVERT_UNCHANGED = "revertunchanged"
    REVERT_UNCHANGED_AND_REOPEN = "revertunchanged+reopen"
    LEAVE_UNCHANGED = "leaveunchanged"
    LEAVE_UNCHANGED_AND_REOPEN = "leaveunchanged+reopen"


class ClientType(StrEnum):
    """Types of client workspace."""

    STANDARD = "writeable"
    OPERATOR = "readonly"
    SERVICE = "partitioned"


class View(NamedTuple):
    """A perforce `View specification`_."""

    left: str
    right: str

    @staticmethod
    def from_string(string: str) -> View:
        """New instance from a view string.

        Example:
            >>> View.from_string("//depot/foo/... //ws/bar/...")
            View(left='//depot/foo/...', right='//ws/bar/...')
        """
        return View(*shlex.split(string))


@dataclass
class ClientOptions:
    """A set of switches that control particular `Client options`_.

    .. _Client options:
        https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_client.html#Options2
    """

    allwrite: bool
    clobber: bool
    compress: bool
    locked: bool
    modtime: bool
    rmdir: bool

    @classmethod
    def from_string(cls, string: str) -> ClientOptions:
        """Instanciate class from an option line returned by p4."""
        data = set(string.split())
        return cls(
            allwrite="allwrite" in data,
            clobber="clobber" in data,
            compress="compress" in data,
            locked="locked" in data,
            modtime="modtime" in data,
            rmdir="rmdir" in data,
        )

    def __str__(self) -> str:
        options = [
            "allwrite" if self.allwrite else "noallwrite",
            "clobber" if self.clobber else "noclobber",
            "compress" if self.compress else "nocompress",
            "locked" if self.locked else "nolocked",
            "modtime" if self.modtime else "nomodtime",
            "rmdir" if self.rmdir else "normdir",
        ]
        return " ".join(options)


class Client(PyforceModel):
    """A Perforce client workspace specification."""

    access: PerforceDateTime = Field(alias="Access", repr=False)
    """The date and time that the workspace was last used in any way."""

    name: str = Field(alias="Client")
    description: str = Field(alias="Description", repr=False)

    host: str = Field(alias="Host")
    """The name of the workstation on which this workspace resides."""

    options: ClientOptions = Field(alias="Options", repr=False)

    owner: str = Field(alias="Owner")
    """The name of the user who owns the workspace."""

    root: pathlib.Path = Field(alias="Root")
    """Workspace root directory on the local host

    All the file in `views` are relative to this directory.
    """

    stream: Union[str, None] = Field(alias="Stream", default=None)
    submit_options: SubmitOptions = Field(alias="SubmitOptions", repr=False)
    type: ClientType = Field(alias="Type")

    update: PerforceDateTime = Field(alias="Update", repr=False)
    """The date the workspace specification was last modified."""

    views: List[View]
    """Specifies the mappings between files in the depot and files in the workspace."""

    @field_validator("options", mode="before")
    @classmethod
    def _validate_options(cls, v: str) -> ClientOptions:
        return ClientOptions.from_string(v)

    @model_validator(mode="before")
    @classmethod
    def _prepare_views(cls, data: dict[str, object]) -> dict[str, object]:
        data["views"] = [
            View.from_string(cast(str, v))
            for v in extract_indexed_values(data, prefix="View")
        ]
        return data


class ChangeStatus(StrEnum):
    """Types of changelist status."""

    PENDING = "pending"
    SHELVED = "shelved"
    SUBMITTED = "submitted"
    # TODO: NEW = "new" ?


class ChangeType(StrEnum):
    """Types of changelist."""

    RESTRICTED = "restricted"
    PUBLIC = "public"


class Change(PyforceModel):
    """A Perforce changelist specification.

    Command:
        `p4 change`_
    """

    change: int = Field(alias="Change")
    client: str = Field(alias="Client")

    date: PerforceDateTime = Field(alias="Date")
    """Date the changelist was last modified."""

    description: str = Field(alias="Description", repr=False)
    status: ChangeStatus = Field(alias="Status")
    type: ChangeType = Field(alias="Type")

    user: str = Field(alias="User")
    """Name of the change owner."""

    files: List[str] = Field(repr=False)
    """The list of files being submitted in this changelist."""

    shelve_access: Union[PerforceDateTime, None] = Field(
        alias="shelveAccess",
        default=None,
    )
    shelve_update: Union[PerforceDateTime, None] = Field(
        alias="shelveUpdate",
        default=None,
    )

    @model_validator(mode="before")
    @classmethod
    def _prepare_files(cls, data: dict[str, object]) -> dict[str, object]:
        data["files"] = extract_indexed_values(data, prefix="Files")
        return data


class ChangeInfo(PyforceModel):
    """A Perforce changelist.

    Compared to a `Change`, this model does not contain the files in the changelist.

    Command:
        `p4 changes`_
    """

    change: int = Field(alias="change")
    client: str = Field(alias="client")

    date: PerforceTimestamp = Field(alias="time")
    """Date the changelist was last modified."""

    description: str = Field(alias="desc", repr=False)
    status: ChangeStatus = Field(alias="status")
    type: ChangeType = Field(alias="changeType")

    user: str = Field(alias="user")
    """Name of the change owner."""


class Action(StrEnum):
    """A file action."""

    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    BRANCH = "branch"
    MOVE_ADD = "move/add"
    MOVE_DELETE = "move/delete"
    INTEGRATE = "integrate"
    IMPORT = "import"
    PURGE = "purge"
    ARCHIVE = "archive"


@dataclass(frozen=True)
class ActionMessage:
    """Information on a file during an action operation.

    Actions can be, for example, ``add``, ``edit`` or ``remove``.

    Notable messages:
        - "can't add (already opened for edit)"
        - "can't add existing file"
        - "empty, assuming text."
        - "also opened by user@client"
    """

    path: str
    message: str
    level: MessageLevel

    @classmethod
    def from_info_data(cls, data: PerforceDict) -> ActionMessage:
        """Create instance from an 'info' dict of an action command."""
        path, _, message = data["data"].rpartition(" - ")
        level = MessageLevel(int(data["level"]))
        return cls(
            path=path.strip(),
            message=message.strip(),
            level=level,
        )


class ActionInfo(PyforceModel):
    """The result of an action operation.

    Actions can be, for example, ``add``, ``edit`` or ``remove``.
    """

    action: str
    client_file: str = Field(alias="clientFile")
    depot_file: str = Field(alias="depotFile")
    file_type: str = Field(alias="type")  # TODO: create object type ? 'binary+F'
    work_rev: int = Field(alias="workRev")
    """Open revision."""


class Revision(PyforceModel):
    """A file revision information."""

    action: Action
    """The operation the file was open for."""

    change: int
    """The number of the submitting changelist."""

    client: str
    depot_file: str = Field(alias="depotFile")
    description: str = Field(alias="desc", repr=False)

    digest: Union[str, None] = Field(default=None, repr=False)
    """MD5 digest of the file. ``None`` if ``action`` is `Action.DELETE`."""

    # TODO: None when action is 'deleted'
    file_size: Union[int, None] = Field(default=None)
    """File length in bytes. ``None`` if ``action`` is `Action.DELETE`."""

    revision: int = Field(alias="rev")
    time: PerforceTimestamp

    # TODO: enum ? https://www.perforce.com/manuals/cmdref/Content/CmdRef/file.types.html
    file_type: str = Field(alias="type")

    user: str
    """The name of the user who submitted the revision."""


class Sync(PyforceModel):
    """The result of a file sync operation."""

    action: str
    client_file: str = Field(alias="clientFile")  # TODO: Could be Path
    depot_file: str = Field(alias="depotFile")
    revision: int = Field(alias="rev")  # TODO: can be None ?

    # TODO: can be None if action is 'delete' or 'move/delete'
    file_size: int = Field(alias="fileSize")


@dataclass(frozen=True)
class OtherOpen:
    """Other Open information."""

    action: Action
    change: Union[int, Literal["default"]]
    user: str
    client: str


class HeadInfo(PyforceModel):
    """Head revision information."""

    action: Action = Field(alias="headAction")
    change: int = Field(alias="headChange")
    revision: int = Field(alias="headRev")
    """Revision number.

    If you used a `Revision specifier`_ in your query, this field is set to the
    specified value. Otherwise, it's the head revision.

    .. _Revision specifier:
        https://www.perforce.com/manuals/cmdref/Content/CmdRef/filespecs.html#Using_revision_specifiers
    """

    file_type: str = Field(alias="headType")
    time: PerforceTimestamp = Field(alias="headTime")
    """Revision **changelist** time."""

    mod_time: PerforceTimestamp = Field(alias="headModTime")
    """Revision modification time.

    The time that the file was last modified on the client before submit.
    """


class FStat(PyforceModel):
    """A file information."""

    client_file: str = Field(alias="clientFile")
    depot_file: str = Field(alias="depotFile")
    head: Union[HeadInfo, None] = Field(alias="head", default=None)

    have_rev: Union[int, None] = Field(alias="haveRev", default=None)
    """Revision last synced to workspace, if on workspace."""

    is_mapped: bool = Field(alias="isMapped", default=False)
    """Is the file is mapped to client workspace."""

    others_open: Union[List[OtherOpen], None] = Field(default=None)

    @field_validator("is_mapped", mode="before")
    @classmethod
    def _validate_is_mapped(cls, v: str | None) -> bool:
        return v == ""

    @model_validator(mode="before")
    @classmethod
    def _prepare_head(cls, data: dict[str, object]) -> dict[str, object]:
        if "headRev" not in data:
            return data

        head_info = {
            "headAction": data.pop("headAction"),
            "headChange": data.pop("headChange"),
            "headRev": data.pop("headRev"),
            "headType": data.pop("headType"),
            "headTime": data.pop("headTime"),
            "headModTime": data.pop("headModTime"),
        }

        charset = data.pop("headCharset", None)
        if charset:
            head_info["headCharset"] = charset

        data["head"] = head_info
        return data

    @model_validator(mode="before")
    @classmethod
    def _prepare_others_open(cls, data: dict[str, object]) -> Mapping[str, object]:
        total = cast("str | None", data.pop("otherOpen", None))
        if total is None:
            return data

        result: list[OtherOpen] = []
        for index in range(int(total)):
            user, _, client = cast(str, data.pop(f"otherOpen{index}")).partition("@")
            other = OtherOpen(
                action=Action(cast(str, data.pop(f"otherAction{index}"))),
                change=int(cast(str, data.pop(f"otherChange{index}"))),
                user=user,
                client=client,
            )
            result.append(other)

        data["others_open"] = result
        return data
