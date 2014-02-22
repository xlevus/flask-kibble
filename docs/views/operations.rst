.. _views/operations:

Operations
==========

Operations are a views that perform simple no-input actions against
model instances.


Delete
------
Deletes the instance.

.. module:: flask_kibble

.. autoclass:: Delete
   :members:

Custom Operations
-----------------
Custom operations can be defined by subclassing
:class:`~flask_kibble.Operation` and implementing, at the very least,
:attr:`~flask_kibble.Operation.run`.

.. autoclass:: Operation
   :members:


