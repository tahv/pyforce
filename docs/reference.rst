.. _p4 user: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_user.html
.. _p4 client: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_client.html
.. _p4 change: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_change.html
.. _p4 add: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_add.html
.. _p4 filelog: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_filelog.html
.. _p4 fstat: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_fstat.html
.. _p4 edit: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_edit.html
.. _p4 delete: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_delete.html
.. _p4 changes: https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_changes.html
.. _File specifications: https://www.perforce.com/manuals/cmdref/Content/CmdRef/filespecs.html
.. _View specification: https://www.perforce.com/manuals/cmdref/Content/CmdRef/views.html


API Reference
===============

Commands
--------

.. autofunction:: pyforce.p4
.. autofunction:: pyforce.login

.. autofunction:: pyforce.get_user
.. autofunction:: pyforce.get_client
.. autofunction:: pyforce.get_change
.. autofunction:: pyforce.get_revisions
.. autofunction:: pyforce.create_changelist
.. autofunction:: pyforce.add
.. autofunction:: pyforce.edit
.. autofunction:: pyforce.delete
.. autofunction:: pyforce.sync
.. autofunction:: pyforce.fstat

User
----

.. autopydantic_model:: pyforce.User

.. autoenum:: pyforce.UserType
   :members:

.. autoenum:: pyforce.AuthMethod
   :members:

Client
------

.. autopydantic_model:: pyforce.Client

.. autoclass:: pyforce.View
   :members:

.. autoclass:: pyforce.ClientOptions
   :members:

.. autoenum:: pyforce.ClientType
   :members:

.. autoenum:: pyforce.SubmitOptions
   :members:


Change
------

.. autopydantic_model:: pyforce.Change
.. autopydantic_model:: pyforce.ChangeInfo

.. autoenum:: pyforce.ChangeType
   :members:

.. autoenum:: pyforce.ChangeStatus
   :members:


Action
------

.. autopydantic_model:: pyforce.ActionInfo

.. autoenum:: pyforce.Action
   :members:

.. autoclass:: pyforce.ActionMessage
   :members:

Revision
--------

.. autopydantic_model:: pyforce.Revision

Sync
----

.. autopydantic_model:: pyforce.Sync

FStat
-----

.. autopydantic_model:: pyforce.FStat
.. autopydantic_model:: pyforce.HeadInfo
.. autoclass:: pyforce.OtherOpen

Exceptions
----------

.. autoexception:: pyforce.AuthenticationError
.. autoexception:: pyforce.ConnectionExpiredError
.. autoexception:: pyforce.CommandExecutionError

Other
-----

.. autoclass:: pyforce.Connection
   :members:

.. autoenum:: pyforce.MessageSeverity
   :members:

.. autoenum:: pyforce.MarshalCode
   :members:
