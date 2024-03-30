"""Pyforce utils."""

from __future__ import annotations

import datetime
import itertools
import logging
import sys
from enum import Enum, IntEnum
from typing import Dict, Final, NamedTuple

from pydantic import BeforeValidator, PlainSerializer
from typing_extensions import Annotated, TypeVar

if sys.version_info < (3, 11):

    class StrEnum(str, Enum):
        """Enum where members are also (and must be) stings."""
else:
    from enum import StrEnum


__all__ = [
    "PerforceDict",
    "Connection",
    "MessageSeverity",
    "MarshalCode",
]

log: Final = logging.getLogger("pyforce")

PerforceDict = Dict[str, str]

R = TypeVar("R")


class Connection(NamedTuple):
    """Perforce connection informations."""

    port: str
    """Perforce host and port (``P4PORT``)."""

    user: str | None = None
    """Helix server username (``P4USER``)."""

    client: str | None = None
    """Client workspace name (``P4CLIENT``)."""


class MarshalCode(StrEnum):
    """Values of the ``code`` field from a marshaled P4 response.

    The output dictionary from ``p4 -G`` must have a ``code`` field.
    """

    STAT = "stat"
    """Means 'status' and is the default status."""

    ERROR = "error"
    """An error has occured.

    The full error message is contained in the 'data' field.
    """

    INFO = "info"
    """There was some feedback from the command.

    The message is contained in the 'data' field.
    """


class MessageSeverity(IntEnum):
    """Perforce message severity levels."""

    EMPTY = 0
    """No Error."""

    INFO = 1
    """Informational message, something good happened."""

    WARNING = 2
    """Warning message, something not good happened."""

    FAILED = 3
    """Command failed, user did something wrong."""

    FATAL = 4
    """System broken, severe error, cannot continue."""


class MessageLevel(IntEnum):
    """Perforce generic 'level' codes, as described in `P4.Message`_.

    .. _P4.Message:
        https://www.perforce.com/manuals/p4python/Content/P4Python/python.p4_message.html
    """

    NONE = 0
    """Miscellaneous."""

    USAGE = 0x01
    """Request is not consistent with dox."""

    UNKNOWN = 0x02
    """Using unknown entity."""

    CONTEXT = 0x03
    """Using entity in the wrong context."""

    ILLEGAL = 0x04
    """You do not have permission to perform this action."""

    NOTYET = 0x05
    """An issue needs to be fixed before you can perform this action."""

    PROTECT = 0x06
    """Protections prevented operation."""

    EMPTY = 0x11
    """Action returned empty results."""

    FAULT = 0x21
    """Inexplicable program fault."""

    CLIENT = 0x22
    """Client side program errors."""

    ADMIN = 0x23
    """Server administrative action required."""

    CONFIG = 0x24
    """Client configuration is inadequate."""

    UPGRADE = 0x25
    """Client or server too old to interact."""

    COMM = 0x26
    """Communications error."""

    TOOBIG = 0x27
    """Too big to handle."""


PERFORCE_DATE_FORMAT = "%Y/%m/%d %H:%M:%S"


def perforce_date_to_datetime(string: str) -> datetime.datetime:
    utc = datetime.timezone.utc
    return datetime.datetime.strptime(string, PERFORCE_DATE_FORMAT).replace(tzinfo=utc)


def perforce_timestamp_to_datetime(time: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(int(time), tz=datetime.timezone.utc)


def perforce_datetime_to_timestamp(date: datetime.datetime) -> str:
    return str(round(date.timestamp()))


def datetime_to_perforce_date(date: datetime.datetime) -> str:
    return date.strftime(PERFORCE_DATE_FORMAT)


PerforceDateTime = Annotated[
    datetime.datetime,
    BeforeValidator(perforce_date_to_datetime),
    PlainSerializer(datetime_to_perforce_date),
]


PerforceTimestamp = Annotated[
    datetime.datetime,
    BeforeValidator(perforce_timestamp_to_datetime),
    PlainSerializer(perforce_datetime_to_timestamp),
]


def extract_indexed_values(data: dict[str, R], prefix: str) -> list[R]:
    """Pop indexed keys, in `data` to list of value.

    Args:
        data: dict to pop process.
        prefix: Indexed key prefix. For example, the keys in
            `{'Files0': "//depot/foo", 'Files1': "//depot/bar"}` have the prefix
            `Files`.
    """
    result: list[R] = []
    counter = itertools.count()

    while True:
        index = next(counter)
        value: R | None = data.pop(f"{prefix}{index}", None)
        if value is None:
            break
        result.append(value)

    return result
