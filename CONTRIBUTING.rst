Contributing
============

Contributions are always welcome.
Either simply reporting bugs or feature suggestions under 'issues' or by making pull-requests.


How to develop
~~~~~~~~~~~~~~

In order to start working on the project:

* Clone the repository
* Create and activate a virtual environment
* Install the package in editable mode, together with the optional development dependencies:

  .. code-block::

     pip install -e .[dev]


Linting and Formatting
~~~~~~~~~~~~~~~~~~~~~~

Ruff is used for code checking and formatting.
It is configured from `pyproject.toml`.
Checking and formatting will be verified in CI.

Run formatting and check on the entire project with:

.. code-block:: bash

   ruff format
   ruff check [--fix] [--unsafe-fix]

For ``ruff check``, consider either `fix` option to let it fix issues it sees.


Releases
~~~~~~~~

In order to make a new release, do the following:

* Update the version tag in ``src/pyqtconsole/__init__.py``

  * The version string should resemble: ``2.3.4``

* Update the ``CHANGES.rst`` file, by replacing the latest section with the new release and add a date
* Commit, push and merge
* Create a new tag on that (merge)commit

  * Tags should resemble: ``v2.3.4``
  * The CI will publish to PyPi automatically (through a 'trusted publisher', configured in PyPi)

* Finally, create a new release on Github for this tag - add the changelog info verbatim
