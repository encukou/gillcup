Introduction
============

Gillcup is a 2D animation library.

It is intended for both scripted and interactive animations:
in the former, the entire animation is known ahead of time, and rendered
as fast as possible; the latter is gnerally tied to a system clock, and can be
influenced by user input.

The Gillcup core is only concerned with animations; it's not tied to
any particular graphics library.
The gillcup_graphics_ package includes a more accessible demo and a tutorial.


Version warning
---------------

This is version 0.2. The API **will** change significantly in version 0.3.
Please make sure you specify ``gillcup < 0.3`` in your setup/requirements file.


The Project
-----------

Gillcup is a MIT-licensed, `Github-hosted <https://github.com/encukou/gillcup>`_
project striving to uphold best practices of the Python craft, from PEP8_ to
`semantic versioning`_.
Please report any bugs, style issues and suggestions on the `bug tracker`_!

.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _semantic versioning: http://semver.org/
.. _bug tracker: https://github.com/encukou/gillcup/issues
.. _gillcup_graphics: http://gillcup-graphics.readthedocs.org/
