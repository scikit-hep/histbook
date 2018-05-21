histbook
========

.. inclusion-marker-1-do-not-remove

Versitile, high-performance histogram toolkit for Numpy.

.. inclusion-marker-1-5-do-not-remove

A histogram is a way to visualize the distribution of a dataset via aggregation: rather than plotting data points individually, we count how many fall within a set of abutting intervals and plot those totals. The resulting plot approximates the distribution from which the data were derived (`see Wikipedia for details <https://en.wikipedia.org/wiki/Histogram>`__).

The **histbook** package defines, fills, and visualizes histograms of Numpy data. Its capabilities extend considerably beyond the `numpy.histogram <https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html>`__ function included in Numpy, as it was designed to serve the needs of particle physicists. Particle physicists have been analyzing data with histograms for decades and have strict requirements on a histogramming package:

- It must be able to declare an empty histogram as a container to be filled, iteratively or in parallel, allowing results to be combined from multiple sources.
- It must be able to fill many histograms in a single pass over huge datasets.
- The data analyst must be able to access bin contents programmatically, not just visually.
- It must create "profile plots" (average of one variable, binned in another) in addition to plain histograms.
- It must handle weighted data, including negative weights.

**histbook** implements the define-fill-visualize cycle established by `CERN HBOOK <http://cds.cern.ch/record/307945/files/>`__ in the 1970's, but in a new way: there is only one histogram class, ``Hist``, an n-dimensional hypercube of aggregated data, from which one and two-dimensional views may be projected. A histogram ``Book`` combines many histograms into an object that may be filled and combined as a single unit.

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

- `Python <http://docs.python-guide.org/en/latest/starting/installation/>`__ (2.7+, 3.4+)
- `Numpy <https://scipy.org/install.html>`__ (1.8.0+)
- `meta <https://pypi.org/project/meta/>`__

Recommended dependencies:
=========================

- `Pandas <https://pandas.pydata.org/>`__ for more convenient programmatic access to bin contents
- `vega <https://pypi.org/project/vega/>`__ to view plots in a Jupyter notebook or `vegascope <https://pypi.org/project/vegascope/>`__ to view them in a browser window without Jupyter.
- `ROOT <https://root.cern/>`__ to analyze histograms in a complete statistical toolkit
- `uproot <https://pypi.org/project/uproot/>`__ to access ROOT files without the full ROOT framework

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

and create a canvas to draw `Vega-Lite <https://vega.github.io/vega-lite/>`__ graphics.

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

including underflow (``[-inf, -5.0)``), overflow (``[5.0, inf)``), and nanflow (``{NaN}``), the number of values that escape the [-5, 5) range (none in this case). In the absence of weights, the error in the count is the square root of the count (approximation of `Poisson statistics <https://en.wikipedia.org/wiki/Poisson_distribution>`__).

This example was deliberately simple. We can extend the binning to two dimensions and use expressions in the axis labels, rather than simple names:

.. code-block:: python

    >>> import math
    >>> hist = Hist(bin("sqrt(x**2 + y**2)", 5, 0, 1), bin("atan2(y, x)", 3, -math.pi, math.pi))
    >>> hist.fill(x=numpy.random.normal(0, 1, 1000000), y=numpy.random.normal(0, 1, 1000000))
    >>> beside(hist.step("sqrt(y**2 + x**2)"), hist.step("atan2(y,x)")).to(canvas)

.. image:: docs/source/intro-2.png

Note that I defined the first axis as ``sqrt(x**2 + y**2)`` and then accessed it as ``sqrt(y**2 + x**2)`` (x and y are reversed). The text between quotation marks is not a label that must be matched exactly, it's a symbolic expression that is matched algebraically. They could even be entered as Python functions because the language is a declarative subset of Python (functions that return one output for each input in an array).

.. code-block:: python

    >>> import math
    >>> r = lambda x, y: math.sqrt(x**2 + y**2)
    >>> phi = lambda y, x: math.atan2(y, x)
    >>> beside(hist.step(r), hist.step(phi)).to(canvas)

The data contained in ``hist`` is two-dimensional, which you can see by printing it as a Pandas table. (Pandas pretty-prints the nested indexes.)

.. code-block:: python

    >>> hist.pandas()

.. code-block::

                                                        count()  err(count())
    sqrt(x**2 + y**2) atan2(y, x)                                            
    [-inf, 0.0)       [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)       0.0      0.000000
                      [-1.0471975512, 1.0471975512)         0.0      0.000000
                      [1.0471975512, 3.14159265359)         0.0      0.000000
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    [0.0, 0.2)        [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)    6704.0     81.877958
                      [-1.0471975512, 1.0471975512)      6595.0     81.209605
                      [1.0471975512, 3.14159265359)      6409.0     80.056230
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    [0.2, 0.4)        [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)   19008.0    137.869504
                      [-1.0471975512, 1.0471975512)     19312.0    138.967622
                      [1.0471975512, 3.14159265359)     19137.0    138.336546
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    [0.4, 0.6)        [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)   29266.0    171.073084
                      [-1.0471975512, 1.0471975512)     29163.0    170.771778
                      [1.0471975512, 3.14159265359)     29293.0    171.151979
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    [0.6, 0.8)        [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)   36289.0    190.496719
                      [-1.0471975512, 1.0471975512)     36227.0    190.333917
                      [1.0471975512, 3.14159265359)     36145.0    190.118384
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    [0.8, 1.0)        [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)   39931.0    199.827426
                      [-1.0471975512, 1.0471975512)     39769.0    199.421664
                      [1.0471975512, 3.14159265359)     39752.0    199.379036
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    [1.0, inf)        [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)  202393.0    449.881095
                      [-1.0471975512, 1.0471975512)    202686.0    450.206619
                      [1.0471975512, 3.14159265359)    201921.0    449.356206
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000
    {NaN}             [-inf, -3.14159265359)                0.0      0.000000
                      [-3.14159265359, -1.0471975512)       0.0      0.000000
                      [-1.0471975512, 1.0471975512)         0.0      0.000000
                      [1.0471975512, 3.14159265359)         0.0      0.000000
                      [3.14159265359, inf)                  0.0      0.000000
                      {NaN}                                 0.0      0.000000

With multiple dimensions, we can project it out different ways. The ``overlay`` method draws all the bins of one axis as separate lines in the projection of the other.

.. code-block:: python

    >>> hist.overlay("atan2(y, x)").step("sqrt(x**2+y**2)").to(canvas)

.. image:: docs/source/intro-3.png

The ``stack`` method draws them cumulatively, though it only works with the ``area`` (filled) rendering.

.. code-block:: python

    >>> hist.stack("atan2(y, x)").area("sqrt(x**2+y**2)").to(canvas)

.. image:: docs/source/intro-4.png

The underflow, overflow, and nanflow curves are zero. Let's exclude them with a post-aggregation selection. You can select at any bin boundary of any axis, as long as the inequalities match (e.g. ``<=`` for left edges and ``<`` for right edges for an axis with ``closedlow=True``).

.. code-block:: python

    >>> hist.select("-pi <= atan2(y, x) < pi").stack(phi).area(r).to(canvas)

.. image:: docs/source/intro-5.png

We can also split side-by-side and top-down:

.. code-block:: python

    >>> hist.select("-pi <= atan2(y, x) < pi").beside(phi).line(r).to(canvas)

.. image:: docs/source/intro-6.png

.. code-block:: python

    >>> hist.select("-pi <= atan2(y, x) < pi").below(phi).marker(r, error=False).to(canvas)

.. image:: docs/source/intro-7.png

Notice that the three subfigures are labeled by ``atan2(y, x)`` bin. This "trellis plot" formed with ``beside`` and ``below`` is splitting data just as ``overlay`` and ``stack`` split data. Using all but one together, we could visualize four dimensions at once:

.. code-block:: python

    >>> import random
    >>> labels = "one", "two", "three"
    >>> hist = Hist(groupby("a"),
    ...             cut("b > 1"),
    ...             split("c", (-3, 0, 1, 2, 3)),
    ...             bin("d", 50, -3, 3))
    >>> hist.fill(a=[random.choice(labels) for i in range(1000000)],
    ...           b=numpy.random.normal(0, 1, 1000000),
    ...           c=numpy.random.normal(0, 1, 1000000),
    ...           d=numpy.random.normal(0, 1, 1000000))
    ... 
    >>> hist.beside("a").below("b > 1").overlay("c").step("d").to(canvas)

.. image:: docs/source/intro-8.png

In the above, we created a four-dimensional histogram in which the first axis is categorical: ``one``, ``two``, ``three``, the second axis is a cut: ``b > 1``, the third axis is irregularly split into bins at edges −3, 0, 1, 2, 3, and the last is split into 50 regularly split bins.

Only the last line is involved in drawing. Vega-Lite takes a "`grammar of graphics <https://cfss.uchicago.edu/dataviz_grammar_of_graphics.html>`__" approach to visualization, in which plots are made by matching data attributes with visual facets such as overlay, stack, and placement, instead of manually drawing over drawings. histbook extends this mapping to aggregated bin data.

In practice, you probably won't be making histograms with many dimensions, in part because of the memory use, but also because it becomes cumbersome to visualize. However, many of the "groups of histograms" particle physicists make are actually ``groupby``, ``cut``, or ``split`` dimensions in disguise. histbook puts them on the same footing as regular binning, providing flexibility to delay some decisions until you're ready to plot.

Axis constructors
-----------------

histbook currently recognizes the following axis constructors:

- ``groupby(expr)`` groups by unique Python objects, usually strings or integers
- ``groupbin(expr, binwidth, origin=0, nanflow=True, closedlow=True)``


profile


Books of histograms
-------------------



Manipulation methods
--------------------







Plotting methods
----------------



Tabular output
--------------

fraction, weights



.. inclusion-marker-4-do-not-remove

.. inclusion-marker-5-do-not-remove
