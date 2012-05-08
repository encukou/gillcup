gillcup.actions
===============

.. automodule:: gillcup.actions

.. autoclass:: gillcup.Action

    .. automethod:: gillcup.Action.chain
    .. attribute:: gillcup.Action.chain_triggered

        Set to true when this Action is finished, i.e. its chained actions have
        been triggered.

    Overridable methods:

        .. automethod:: gillcup.Action.__call__

    Methods useful for subclasses:

        .. automethod:: gillcup.Action.expire
        .. automethod:: gillcup.Action.trigger_chain
        .. automethod:: gillcup.Action.coerce

.. _action-building-blocks:

Building blocks for complex actions
-----------------------------------

.. autoclass:: gillcup.actions.FunctionCaller
.. autoclass:: gillcup.actions.Delay
.. autoclass:: gillcup.actions.Sequence
.. autoclass:: gillcup.actions.Parallel
.. autoclass:: gillcup.actions.Process
.. autoclass:: gillcup.actions.process_generator
