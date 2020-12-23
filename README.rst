=========
LDS Notes
=========


.. image:: https://img.shields.io/pypi/v/ldsnotes.svg
        :target: https://pypi.python.org/pypi/ldsnotes

.. image:: https://img.shields.io/travis/contagon/ldsnotes.svg
        :target: https://travis-ci.com/contagon/ldsnotes

.. image:: https://readthedocs.org/projects/ldsnotes/badge/?version=latest
        :target: https://ldsnotes.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/contagon/ldsnotes/shield.svg
     :target: https://pyup.io/repos/github/contagon/ldsnotes/
     :alt: Updates



Unofficial Python API to interact with your annotations from churchofjesuschrist.org. 
I reverse engineered a bit of the API to download content/user notes from churchofjesuschrist.org.
Currently can only download notes, working on uploading next.


* Free software: MIT license
* Documentation: https://ldsnotes.readthedocs.io.


Roadmap
--------

* Update Content/Annotation classes to inherit from addict.Dict. Should make upload easier later.
* 2-way sync.
* Make tests (and setup CI with github) using dummy account/notes. 

Handling Highlights
--------------------

The way churchofjesuschrist.org handles where highlights are is a bit difficult to reverse engineer. They save where your highlight is
by counting words - both from the start, and from the end. The difficult part is figuring out what they consider a "word". For example,
a footnote/reference counts as a word, *and a comma after a word with a footnote also counts as one*. This makes things very case by case
to get things right. If you have a problem with a highlight being a few words off, please open an issue with your where your highlight is at.

TL;DR Highlights are hard, open issue if yours are off.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
