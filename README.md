# Pyforce

[![License - MIT][license-badge]][pyforce-license]
[![PyPI - Python Version][python-version-badge]][pyforce-pypi]
[![PyPI - Version][version-badge]][pyforce-pypi]
[![Linter - Ruff][ruff-badge]][ruff-repo]
[![Types - Mypy][mypy-badge]][mypy-repo]
[![CI - Tests][pyforce-workflow-tests-badge]][pyforce-workflow-tests]

Python wrapper for Perforce p4 command-line client.

## Features

- Python wrapper for the `p4` command using [marshal](https://docs.python.org/3/library/marshal.html).
- Built with [Pydantic](https://github.com/pydantic/pydantic).
- Fully typed.
- Built for scripting.

## Installation

```bash
python -m pip install pyforce-p4
```

## Quickstart

```python
import pyforce

connection = pyforce.Connection(host="localhost:1666", user="foo", client="my-client")

# Create a new file in our client
file = "/home/foo/my-client/bar.txt"
fp = open(file, "w")
fp.write("bar")
fp.close()

# Run 'p4 add', open our file for addition to the depot
_, infos = pyforce.add(connection, [file])
print(infos[0])
"""
ActionInfo(
    action='add', 
    client_file='/home/foo/my-client/bar.txt', 
    depot_file='//my-depot/my-stream/bar.txt', 
    file_type='text', 
    work_rev=1
)
"""

# Run 'p4 submit', submitting our local file
pyforce.p4(connection, ["submit", "-d", "Added bar.txt", file])

# Run 'p4 fstat', listing all files in depot
fstats = list(pyforce.fstat(connection, ["//..."]))
print(fstats[0])
"""
FStat(
    client_file='/home/foo/my-client/bar.txt', 
    depot_file='//my-depot/my-stream/bar.txt', 
    head=HeadInfo(
        action=<Action.ADD: 'add'>, 
        change=2, 
        revision=1, 
        file_type='text', 
        time=datetime.datetime(2024, 3, 29, 13, 56, 57, tzinfo=datetime.timezone.utc), 
        mod_time=datetime.datetime(2024, 3, 29, 13, 56, 11, tzinfo=datetime.timezone.utc)
    ), 
    have_rev=1, 
    is_mapped=True, 
    others_open=None
)
"""
```

The goal of Pyforce is not to be exhaustive. 
It focuses on the most common `p4` commands, 
but can execute more complexe commands by using `pyforce.p4`.

For example, Pyforce does not have a function to create a new client workspace, 
but it is possible to create one with `pyforce.p4`.

```python
import pyforce

connection = pyforce.Connection(port="localhost:1666", user="foo")

# Create client
command = ["client", "-o", "-S", "//my-depot/my-stream", "my-client"]
data = pyforce.p4(connection, command)[0]
data["Root"] = "/home/foo/my-client"
pyforce.p4(connection, ["client", "-i"], stdin=data)

# Get created client
client = pyforce.get_client(connection,  "my-client")
print(client)
"""
Client(
    name='my-client', 
    host='5bb1735f73fc', 
    owner='foo', 
    root=PosixPath('/home/foo/my-client'), 
    stream='//my-depot/my-stream', 
    type=<ClientType.STANDARD: 'writeable'>, 
    views=[View(left='//my-depot/my-stream/...', right='//my-client/...')]
)
"""
```

<!--
## Documentation

See [documentation]() for more details.
-->

## Contributing

For guidance on setting up a development environment and contributing to pyforce,
see the [Contributing](https://github.com/tahv/pyforce/blob/main/CONTRIBUTING.md) section.

<!-- Links -->

[license-badge]: https://img.shields.io/github/license/tahv/pyforce?label=License
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
[version-badge]: https://img.shields.io/pypi/v/pyforce-p4?logo=pypi&label=PyPI&logoColor=white
[python-version-badge]: https://img.shields.io/pypi/pyversions/pyforce-p4?logo=python&label=Python&logoColor=white
[mypy-badge]: https://img.shields.io/badge/Types-Mypy-blue.svg
[pyforce-workflow-tests-badge]: https://github.com/tahv/pyforce/actions/workflows/tests.yml/badge.svg

[pyforce-license]: https://github.com/tahv/pyforce/blob/main/LICENSE
[ruff-repo]: https://github.com/astral-sh/ruff
[pyforce-pypi]: https://pypi.org/project/pyforce-p4
[mypy-repo]: https://github.com/python/mypy
[pyforce-workflow-tests]: https://github.com/tahv/pyforce/actions/workflows/tests.yml
