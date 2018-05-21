histbook
========

.. inclusion-marker-1-do-not-remove

Histogram toolkit for Numpy.

.. inclusion-marker-1-5-do-not-remove

A histogram is a way to visualize the distribution of a dataset via aggregation: rather than plotting data points individually, we count how many fall within a set of abutting intervals and plot those counts. The resulting plot approximates the distribution from which the data were derived (`see Wikipedia <https://en.wikipedia.org/wiki/Histogram>`_ for details).

The **histbook** package defines, fills, and visualizes histograms of Numpy data. Its capabilities extend considerably beyond the ```numpy.histogram`` <https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html>`_ function included in Numpy, as it was designed to serve the needs of particle physicists. Physicists have been analyzing data with histograms for decades (see `CERN HBOOK <http://cds.cern.ch/record/307945/files/>`_, `PAW <http://paw.web.cern.ch/paw/>`_, `mn_fit <https://community.linuxmint.com/software/view/mn-fit>`_, `HippoDraw <http://www.slac.stanford.edu/grp/ek/hippodraw/>`_, `AIDA <http://aida.freehep.org/doc/v3.0/UsersGuide.html>`_, `YODA <https://yoda.hepforge.org/>`_, `ROOT <https://root.cern/>`_) and must be able to

- declare empty histograms and fill them iteratively or in parallel, combining results from multiple sources;
- fill many histograms in a single pass over the data;
- analyze the bin contents programmatically, not only graphically;
- visualize "profile plots" (average of one variable binned in another) as well as histograms.

histbook implements the familiar define-fill-visualize in a new way: there is only one histogram class, ``Hist``, an n-dimensional hypercube of aggregated data with convenient selection and projection routines to view one and two-dimensional distributions. Histograms can be collected into a ``Book`` that can be filled and combined as a single unit. Each axis of a ``Hist`` is a symbolic expression that histbook organizes and executes in an optimized way across all of the histograms in a ``Book``.

.. inclusion-marker-2-do-not-remove

Installation
============

Install histbook like any other Python package:

.. code-block:: bash

    pip install histbook --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

Strict dependencies:
====================

- `Python <http://docs.python-guide.org/en/latest/starting/installation/>`_ (2.7+, 3.4+)
- `Numpy <https://scipy.org/install.html>`_ (1.8.0+)
- `meta <https://pypi.org/project/meta/>`_

Recommended dependencies:
=========================

- `Pandas <https://pandas.pydata.org/>`_ for more convenient programmatic access to bin contents
- `vega <https://pypi.org/project/vega/>`_ to view plots in a Jupyter notebook or `vegascope <https://pypi.org/project/vegascope/>`_ to view them in a browser window without Jupyter.
- `ROOT <https://root.cern/>`_ to analyze histograms in a complete statistical toolkit
- `uproot <https://pypi.org/project/uproot/>`_ to access ROOT files without the full ROOT framework

.. inclusion-marker-3-do-not-remove

Getting started
---------------

Install histbook, pandas, uproot, and your choice of vega or vegascope (above).

.. code-block:: bash

    pip install histbook pandas uproot vega --user

Then start a Jupyter notebook (vega) or Python prompt (vegascope),

.. code-block:: python

    >>> from histbook import *
    >>> import numpy
    >>> import vega       # or vegascope

and create a canvas to draw [Vega-Lite](https://vega.github.io/vega-lite/) graphics.

.. code-block:: python

    >>> from vega import VegaLite as canvas                 # for vega
    >>> import vegascope; canvas = vegascope.LocalCanvas()  # for vegascope

Let's start by histogramming a simple array of data.

.. code-block:: python

    >>> array = numpy.random.normal(0, 1, 1000000)
    >>> histogram = Hist(bin("data", 10, -5, 5))
    >>> histogram.fill(data=array)
    >>> histogram.step("data").to(canvas)

.. image:: docs/source/intro-1.png

