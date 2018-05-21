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
- It must handle weighted data, including negative weights.

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

    pip install histbook pandas vega --user

Then start a Jupyter notebook (vega) or Python prompt (vegascope),

.. code-block:: python

    >>> from histbook import *
    >>> import numpy

and create a canvas to draw `Vega-Lite <https://vega.github.io/vega-lite/>`_ graphics.

.. code-block:: python

    >>> from vega import VegaLite as canvas                    # for vega in Jupyter
    >>> import vegascope; canvas = vegascope.LocalCanvas()     # for vegascope

Let's start by histogramming a simple array of data.

.. code-block:: python

    >>> array = numpy.random.normal(0, 1, 1000000)
    >>> histogram = Hist(bin("data", 10, -5, 5))
    >>> histogram.fill(data=array)
    >>> histogram.step("data").to(canvas)

.. image:: docs/source/intro-1.png

*What just happened here?*

- The first line created a million-element Numpy ``array``.
- The second created a one-dimensional ``histogram``, splitting ``data`` into 10 bins from −5 to 5.
- The third line incremented histogram bins by counting the number of values that lie within each of the 10 subintervals.
- The fourth line projected the hypercube onto steps in the ``data`` axis and passed the Vega-Lite visualization to ``canvas``.

We could also access the data as a table, as a `Pandas DataFrame <https://pandas.pydata.org/pandas-docs/stable/dsintro.html>`__:

.. code-block:: python

    >>> histogram.pandas()

.. code-block::

                   count()  err(count())
    data                                
    [-inf, -5.0)       0.0      0.000000
    [-5.0, -4.0)      33.0      5.744563
    [-4.0, -3.0)    1247.0     35.312887
    [-3.0, -2.0)   21260.0    145.808093
    [-2.0, -1.0)  136067.0    368.872607
    [-1.0, 0.0)   341355.0    584.255937
    [0.0, 1.0)    341143.0    584.074482
    [1.0, 2.0)    136072.0    368.879384
    [2.0, 3.0)     21474.0    146.540097
    [3.0, 4.0)      1320.0     36.331804
    [4.0, 5.0)        29.0      5.385165
    [5.0, inf)         0.0      0.000000
    {NaN}              0.0      0.000000

including underflow (``[-inf, -5.0)``), overflow (``[5.0, inf)``), and nanflow (``{NaN}``), the number of values that escape the [-5, 5) range (none in this case). In the absence of weights, the error in the count is the square root of the count.

This example was deliberately simple. We can extend the binning to two dimensions and use expressions in the axis labels, rather than simple names:

.. code-block:: python

    >>> hist = Hist(bin("sqrt(x**2 + y**2)", 10, 0, 1), bin("atan2(y, x)", 10, 0, 1))
    >>> hist.fill(x=numpy.random.normal(0, 1, 1000000), y=numpy.random.normal(0, 1, 1000000))
    >>> beside(hist.step("sqrt(y**2 + x**2)"), hist.step("atan2(y,x)")).to(canvas)

.. image:: docs/source/intro-2.png

Note that I defined the first axis as ``sqrt(x**2 + y**2)`` and then accessed it as ``sqrt(y**2 + x**2)`` (x and y are reversed). The text between quotation marks is not 

.. code-block:: python

    >>> import math
    >>> r = lambda x, y: math.sqrt(x**2 + y**2)
    >>> phi = lambda y, x: math.atan2(y, x)
    >>> beside(hist.step(r), hist.step(phi)).to(canvas)

.. inclusion-marker-4-do-not-remove

.. inclusion-marker-5-do-not-remove
