gillcup.actions
===============

Although arbitrary callables can be scheduled on a Gillcup
:class:`~gillcup.Clock`, one frequently schedules objects that are specifically
made for this purpose.
Using :class:`gillcup.Action` allows one to chain actions together in various
ways, allowing the developer to create complex effects.

.. autoclass:: gillcup.Action

    .. automethod:: gillcup.Action.chain
    .. attribute:: gillcup.Action.chain_triggered

        Set to true when this Action is finished, i.e. its chained actions have
        been triggered.

    Subclassable methods:

        .. automethod:: gillcup.Action.__call__

    Methods useful for subclassing:

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
