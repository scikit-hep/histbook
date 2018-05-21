histbook
========

.. inclusion-marker-1-do-not-remove

Versitile, high-performance histogram toolkit for Numpy.

.. inclusion-marker-1-5-do-not-remove

A histogram is a way to visualize the distribution of a dataset via aggregation: rather than plotting data points individually, we count how many fall within a set of abutting intervals and plot those totals. The resulting plot approximates the distribution from which the data were derived (`see Wikipedia for details <https://en.wikipedia.org/wiki/Histogram>`__).

The **histbook** package defines, fills, and visualizes histograms of Numpy data. Its capabilities extend considerably beyond the `numpy.histogram <https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html>`_ function included in Numpy, as it was designed to serve the needs of particle physicists. Particle physicists have been analyzing data with histograms for decades and have strict requirements on a histogramming package:

- It must be able to declare an empty histogram as a container to be filled, iteratively or in parallel, allowing results to be combined from multiple sources.
- It must be able to fill many histograms in a single pass over huge datasets.
- The data analyst must be able to access bin contents programmatically, not just visually.
- It must create "profile plots" (average of one variable, binned in another) in addition to plain histograms.

**histbook** implements the define-fill-visualize cycle established by `CERN HBOOK <http://cds.cern.ch/record/307945/files/>`_ in the 1970's, but in a new way: there is only one histogram class, ``Hist``, an n-dimensional hypercube of aggregated data, from which one and two-dimensional views may be projected. A histogram ``Book`` combines many histograms into an object that may be filled and combined as a single unit.

Finally, each axis of a ``Hist`` is actually a symbolic expression that histbook optimizes to minimize passes over the data. For example, if many histograms contain a subexpression "``pt*sinh(eta)``", this subexpression will be computed only once per ``Book``. The data analyst can therefore copy-paste or generate hundreds of variations on a basic histogram without worrying about inefficiency. This is especially relevant for data selections, such as "``pt > 50``", which can be used as a 2-bin axis in the n-dimensional hypercube instead of creating histograms with and without the selection manually.

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
- `ROOT <https://root.cern/>`__ to analyze histograms in a complete statistical toolkit
- `uproot <https://pypi.org/project/uproot/>`_ to access ROOT files without the full ROOT framework

.. inclusion-marker-3-do-not-remove

Getting started
---------------

Install histbook, pandas, uproot, and your choice of vega or vegascope (above).

.. code-block:: bash

    pip install histbook pandas uproot vega --user

Then start a Jupyter notebook (vega) or Python prompt (vegascope),

.. code-block:: python

    from histbook import *
    import numpy
    import vega       # or vegascope

and create a canvas to draw `Vega-Lite <https://vega.github.io/vega-lite/>`_ graphics.

.. code-block:: python

    from vega import VegaLite as canvas                    # for vega in Jupyter
    import vegascope; canvas = vegascope.LocalCanvas()     # for vegascope

Let's start by histogramming a simple array of data.

.. code-block:: python

    array = numpy.random.normal(0, 1, 1000000)
    histogram = Hist(bin("data", 10, -5, 5))
    histogram.fill(data=array)
    histogram.step("data").to(canvas)

.. image:: docs/source/intro-1.png




.. inclusion-marker-4-do-not-remove

.. inclusion-marker-5-do-not-remove
