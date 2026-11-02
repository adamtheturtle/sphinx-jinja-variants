|Build Status| |PyPI|

sphinx-source-variants
======================

Render Sphinx compositions with temporary Jinja bindings and a prepared RST source.

.. code-block:: console

   $ pip install sphinx-source-variants

Use ``render_source_variant`` from a custom Sphinx directive.
It inherits the selected context's existing values, prepares the source once for standard ``include-section`` directives, runs your rendering callback, and restores the original bindings.
Your code chooses variants, content preparation, validation, and presentation.

See the `Python API <https://github.com/adamtheturtle/sphinx-source-variants/blob/main/API.rst>`_ and the `platform example <https://github.com/adamtheturtle/sphinx-source-variants/tree/main/sample/source>`_.
To contribute, see the `contributor guide <https://github.com/adamtheturtle/sphinx-source-variants/blob/main/CONTRIBUTING.rst>`_.

.. |Build Status| image:: https://github.com/adamtheturtle/sphinx-source-variants/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/sphinx-source-variants/actions
.. |PyPI| image:: https://badge.fury.io/py/sphinx-source-variants.svg
   :target: https://badge.fury.io/py/sphinx-source-variants
