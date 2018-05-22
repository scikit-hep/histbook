histbook
========

.. inclusion-marker-1-do-not-remove

Versitile, high-performance histogram toolkit for Numpy.

.. inclusion-marker-1-5-do-not-remove

A histogram is a way to visualize the distribution of a dataset via aggregation: rather than plotting data points individually, we count how many fall within a set of abutting intervals and plot those totals. The resulting chart is an approximate view of the distribution from which the data were derived (`see Wikipedia for details <https://en.wikipedia.org/wiki/Histogram>`__).

The **histbook** package defines, fills, and visualizes histograms of Numpy data. Its capabilities extend considerably beyond the `numpy.histogram <https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html>`__ function included in Numpy, as it was designed to serve the needs of particle physicists. Particle physicists have been analyzing data with histograms for decades and have strict requirements on histogramming:

- One must be able to declare an empty histogram as a container to be filled, iteratively or in parallel, and then combine results from multiple sources. An interface that skips directly from data to plot or tries to guess bin edges on the fly is not sufficient.
- It must be possible to fill many histograms in a single pass over the data, as datasets may be huge and I/O-bound.
- Data analysts must be able to access bin contents programmatically, not just visually. They will be performing statistical analyses on the contents.
- It should be possible to make "profile plots" (average one variable, binned in another) in addition to plain histograms.
- The data may be weighted, including negative weights.

`CERN HBOOK <http://cds.cern.ch/record/307945/files/>`__ was created in the 1970's to address the above. Since then, histogramming packages developed for particle physicists (`PAW <http://paw.web.cern.ch/paw/>`__, `mn_fit <https://community.linuxmint.com/software/view/mn-fit>`__, `Jas3 <http://jas.freehep.org/jas3/>`__, `HippoDraw <http://www.slac.stanford.edu/grp/ek/hippodraw/>`__, `AIDA <http://aida.freehep.org/doc/v3.0/UsersGuide.html>`__, `YODA <https://yoda.hepforge.org/>`__, `ROOT <https://root.cern/>`__) have provided the same capabilities. histbook, deliberately echoing the name, does so for Numpy.

However, histbook has a more streamlined interface that allows users to be "lazy" without giving up performance. Instead of a suite of histogram and profile classes, histbook has a single n-dimensional histogram class, ``Hist``. Different histograms and profiles are latent within this ``Hist``, allowing data exploration after the time-consuming filling stage. Many ``Hist`` objects can be filled at once by binding them into a ``Book``.

It's usually easier to write analysis scripts as a list of mathematical expressions, which suggests separate passes over the data, but it's much faster to execute them as a single pass. To bridge this gap, histbook takes axis specifications as *symbolic expressions* to collect in a single pass with no duplication of reading or processing. For example, if you wish to plot "``pt``", "``eta``", and "``pt*sinh(eta)``" and they're in the same ``Book``, the ``pt`` array will be read once, the ``eta`` array will be read once, and they'll be reused to compute ``pt*sinh(eta)`` (using Numpy ufuncs). If any histograms in the same ``Book`` apply cuts like "``-10 <= pt*sinh(eta) < 10``", the subexpression array will be retained for that. If not, it will be deleted to minimize the memory footprint.

Thus, you can write your analysis as hundreds of mathematical expressions, without worrying about coding for performance, using a single syntax for any dimensionality. You can combine all of your histograms in a ``Book`` so that you have only one object to fill as you iterate through data. Since the filled distributions are n-dimensional, you can change your mind about how you want to plot them after the filling stage.

histbook lets you plot interactively with `Vega-Lite <https://vega.github.io/vega-lite/>`__, dump tables of numbers into `Pandas DataFrames <https://pandas.pydata.org/pandas-docs/stable/dsintro.html>`__, and export histograms to `ROOT <https://root.cern/>`__ format.

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

Tutorial
========

**Table of contents:**

* `Getting started <#getting-started>`__
* `Axis constructors <#axis-constructors>`__

  - `groupby <#groupby>`__
  - `groupbin <#groupbin>`__
  - `bin <#bin>`__
  - `intbin <#intbin>`__
  - `split <#split>`__
  - `cut <#cut>`__
  - `profile <#profile>`__

* `Weighted data <#weighted-data>`__
* `Books of histograms <#books-of-histograms>`__
* `Manipulation methods <#manipulation-methods>`__

  - `select <#select>`__
  - `project <#project>`__
  - `drop <#drop>`__
  - `rebin, rebinby <#rebin-rebinby>`__

* `Tabular output <#tabular-output>`__

  - `table <#table>`__
  - `fraction <#fraction>`__
  - `pandas <#pandas>`__

* `Plotting methods <#plotting-methods>`__

  - `bar <#bar>`__
  - `step <#step>`__
  - `area <#area>`__
  - `line <#line>`__
  - `marker <#marker>`__
  - `stack <#stack>`__
  - `overlay <#overlay>`__
  - `beside <#beside>`__
  - `below <#below>`__

* `Exporting to ROOT <#exporting-to-root>`__

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

including underflow (``[-inf, -5.0)``), overflow (``[5.0, inf)``), and nanflow (``{NaN}``). In the absence of weights, the error in the count is the square root of the count (approximation of `Poisson statistics <https://en.wikipedia.org/wiki/Poisson_distribution>`__; histbook makes the same statistical assumptions as ROOT).

This example was deliberately simple. We can extend the binning to two dimensions and use expressions in the axis labels, rather than simple names:

.. code-block:: python

    >>> import math
    >>> hist = Hist(bin("sqrt(x**2 + y**2)", 5, 0, 1),
    ...             bin("atan2(y, x)", 3, -math.pi, math.pi))
    >>> hist.fill(x=numpy.random.normal(0, 1, 1000000),
    ...           y=numpy.random.normal(0, 1, 1000000))
    >>> beside(hist.step("sqrt(y**2 + x**2)"), hist.step("atan2(y,x)")).to(canvas)

.. image:: docs/source/intro-2.png

Note that I defined the first axis as ``sqrt(x**2 + y**2)`` and then accessed it as ``sqrt(y**2 + x**2)`` (x and y are reversed). The text between quotation marks is not a label that must be matched exactly, it's a symbolic expression that is matched algebraically. They could even be entered as Python functions because the language is a declarative subset of Python (functions that return one output for each input in an array).

.. code-block:: python

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

The ``stack`` method draws them cumulatively, though it only works with ``area`` (filled) rendering.

.. code-block:: python

    >>> hist.stack("atan2(y, x)").area("sqrt(x**2+y**2)").to(canvas)

.. image:: docs/source/intro-4.png

The underflow, overflow, and nanflow curves are empty. Let's exclude them with a post-aggregation selection. You can select at any bin boundary of any axis, as long as the inequalities match (e.g. ``<=`` for left edges and ``<`` for right edges for an axis with ``closedlow=True``).

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

Notice that the three subfigures are labeled by their ``atan2(y, x)`` bins. This "trellis plot" formed with ``beside`` and ``below`` separated data just as ``overlay`` and ``stack`` separated data. Using all but one together, we could visualize four dimensions at once:

.. code-block:: python

    >>> import random
    >>> labels = "one", "two", "three"
    >>> hist = Hist(groupby("a"),                     # categorical axis: distinct strings are bins
    ...             cut("b > 1"),                     # cut axis: two bins (pass and fail)
    ...             split("c", (-3, 0, 1, 2, 3)),     # non-uniformly split the data
    ...             bin("d", 50, -3, 3))              # uniform bins, conventional histogram
    >>> hist.fill(a=[random.choice(labels) for i in range(1000000)],
    ...           b=numpy.random.normal(0, 1, 1000000),
    ...           c=numpy.random.normal(0, 1, 1000000),
    ...           d=numpy.random.normal(0, 1, 1000000))
    >>> hist.beside("a").below("b > 1").overlay("c").step("d").to(canvas)

.. image:: docs/source/intro-8.png

In the above, only the last line does any drawing. The syntax is deliberately succinct to encourage interactive exploration. For instance, you can quickly switch from plotting "``c``" side-by-side with "``b > 1``" as bars:

.. code-block:: python

    >>> hist.beside("c").bar("b > 1").to(canvas)

.. image:: docs/source/intro-9.png

to plotting "``b > 1``" side-by-side with "``c``" as bars:

.. code-block:: python

    >>> hist.beside("b > 1").bar("c").to(canvas)

.. image:: docs/source/intro-10.png

or rather, as an area:

.. code-block:: python

    >>> hist.beside("b > 1").area("c").to(canvas)

.. image:: docs/source/intro-11.png

We see the same trend in different ways. Whatever axes are not mentioned are summed over: imagine a hypercube whose shadows you project onto the graphical elements of bars, areas, lines, overlays, and trellises.

Axis constructors
-----------------

groupby
"""""""

``Hist.groupby(expr)``

Groups values computed from ``expr`` by uniqueness, usually strings or integers.

groupbin
""""""""

``Hist.groupbin(expr, binwidth, origin=0, nanflow=True, closedlow=True)``

Groups by binned numbers: a sparse histogram. The ``binwidth`` determines the granularity of binning with an ``origin`` to let the bins offset from zero. If ``nanflow`` is ``True``, "not a number" values will fill a single bin; if ``False``, they will be ignored. If ``closedlow`` is ``True``, intervals will include their infimum (leftmost) point; otherwise they'll include their supremum (rightmost) point.

bin
"""

``Hist.bin(expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True)``

Uniformly and densely splits a dimension into ``numbins`` from ``low`` to ``high``. If ``underflow`` and/or ``overflow`` are ``True``, values below or above this range go into their own bins; if ``False``, they are ignored (similar to ``nanflow``).

intbin
""""""

``Hist.intbin(expr, min, max, underflow=True, overflow=True)``

Splits a dimension by integers from ``min`` (inclusive) to ``max`` (inclusive). "Not a number" is not a possible value for integers.

split
"""""

``Hist.split(expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True)``

Splits a dimension into the regions between ``edges``, which can be non-uniformly spaced. Without underflow, overflow, or nanflow bins, there are one fewer bins than edges.

cut
"""

``Hist.cut(expr)``

Splits a boolean dimension into true ("pass") and false ("fail"). This differs from ``split`` with one edge because it can include boolean logic (and/or/not).

profile
"""""""

``Hist.profile(expr)``

Collects statistics to view the mean and error in the mean of ``expr`` in bins of the other dimensions (same statistical treatment as ROOT).

For example, we can profile "``y``" and "``z``" or as many distributions as we want in a single ``Hist`` object.

.. code-block:: python

    >>> x = numpy.random.normal(0, 1, 10000)
    >>> y = x**2 + numpy.random.normal(0, 5, 10000)
    >>> z = -x**3 + numpy.random.normal(0, 5, 10000)

    >>> h = Hist(bin("x", 100, -5, 5), profile("y"), profile("z"))
    >>> h.fill(x=x, y=y, z=z)
    >>> beside(h.marker("x", "y"), h.marker("x", "z")).to(canvas)

.. image:: docs/source/intro-12.png

.. code-block:: python

    >>> h.select("-1 <= x < 1").pandas("y", "z")

.. code-block::

                  count()  err(count())         y    err(y)         z    err(z)
    x                                                                          
    [-1.0, -0.9)    243.0     15.588457  1.104575  0.319523  1.135648  0.301416
    [-0.9, -0.8)    275.0     16.583124  0.775029  0.312829  0.485808  0.302074
    [-0.8, -0.7)    317.0     17.804494  0.505641  0.300481  0.427452  0.274324
    [-0.7, -0.6)    315.0     17.748239  0.358800  0.268928  0.823575  0.288089
    [-0.6, -0.5)    351.0     18.734994  0.691492  0.262019 -0.081257  0.265111
    [-0.5, -0.4)    359.0     18.947295  0.116491  0.263602  0.171423  0.273736
    [-0.4, -0.3)    359.0     18.947295  0.349983  0.256635 -0.107522  0.262714
    [-0.3, -0.2)    392.0     19.798990  0.060286  0.257601  0.203810  0.252574
    [-0.2, -0.1)    369.0     19.209373  0.207661  0.246779  0.355550  0.268741
    [-0.1, 0.0)     388.0     19.697716  0.111659  0.258635  0.223001  0.265828
    [0.0, 0.1)      382.0     19.544820  0.348179  0.243986  0.292852  0.249558
    [0.1, 0.2)      378.0     19.442222  0.332284  0.273607 -0.277728  0.248078
    [0.2, 0.3)      401.0     20.024984  0.100446  0.241673 -0.052257  0.258555
    [0.3, 0.4)      386.0     19.646883  0.356500  0.246703 -0.014357  0.251480
    [0.4, 0.5)      369.0     19.209373  0.421627  0.258498 -0.073345  0.261555
    [0.5, 0.6)      355.0     18.841444 -0.060199  0.259124 -0.383521  0.255889
    [0.6, 0.7)      335.0     18.303005  0.560394  0.272651 -0.239575  0.287837
    [0.7, 0.8)      298.0     17.262677  0.499264  0.264333 -0.453906  0.282144
    [0.8, 0.9)      291.0     17.058722  1.449089  0.293750 -0.920633  0.306683
    [0.9, 1.0)      267.0     16.340135  1.085551  0.287038 -1.120942  0.304403

Although each non-profile axis multiplies the number of bins and therefore its memory use, profiles merely add to the number of bins. In fact, they share some statistics, making it 33% (unweighted) to 50% (weighted) more efficient to combine profiles with the same binning. Perhaps more importantly, it's an organizational aid.

Weighted data
-------------

In addition to bins, histograms take a ``weight`` parameter to compute weights for each input value. A value with weight 2 is roughly equivalent to having two values with all other attributes being equal (for counts, sums, and means, but not standard deviations). Weights may be zero or even negative.

For example: without weights, counts are integers and the effective counts (used for weighted profiles) are equal to the counts.

.. code-block:: python

    >>> x = numpy.random.normal(0, 1, 10000)
    >>> y = x**2 + numpy.random.normal(0, 5, 10000)

    >>> h = Hist(bin("x", 100, -5, 5), profile("y"))
    >>> h.fill(x=x, y=y)
    >>> h.select("-0.5 <= x < 0.5").pandas("y", effcount=True)

.. code-block::

                  count()  err(count())  effcount()         y    err(y)
    x                                                                  
    [-0.5, -0.4)    381.0     19.519221       381.0  0.124497  0.251414
    [-0.4, -0.3)    388.0     19.697716       388.0  0.215915  0.241851
    [-0.3, -0.2)    376.0     19.390719       376.0 -0.029105  0.252925
    [-0.2, -0.1)    410.0     20.248457       410.0 -0.128061  0.249327
    [-0.1, 0.0)     392.0     19.798990       392.0  0.199057  0.250275
    [0.0, 0.1)      398.0     19.949937       398.0 -0.081793  0.242204
    [0.1, 0.2)      401.0     20.024984       401.0 -0.144345  0.258108
    [0.2, 0.3)      397.0     19.924859       397.0  0.083175  0.251312
    [0.3, 0.4)      381.0     19.519221       381.0  0.065216  0.248393
    [0.4, 0.5)      341.0     18.466185       341.0  0.349919  0.267243

Below, we make the weights normal-distributed with a mean of 1 and a standard deviation of 4 (many of them are negative, but the average is 1). The counts are no longer integers, errors in the count are much larger, effective counts much smaller, and it affects the profile central values and errors.

.. code-block:: python

    >>> h = Hist(bin("x", 100, -5, 5), profile("y"), weight="w")
    >>> h.fill(x=x, y=y, w=numpy.random.normal(1, 4, 10000))
    >>> h.select("-0.5 <= x < 0.5").pandas("y", effcount=True)

.. code-block::

                     count()  err(count())  effcount()         y    err(y)
    x                                                                     
    [-0.5, -0.4)  310.641444     83.340859   13.893218 -0.405683  1.690065
    [-0.4, -0.3)  425.941704     84.217430   25.579754  0.184349  0.836336
    [-0.3, -0.2)  375.066116     82.471825   20.682568 -0.608185  1.064126
    [-0.2, -0.1)  382.807263     82.146862   21.715927 -1.597008  1.126224
    [-0.1, 0.0)   286.163241     87.789195   10.625407  0.713485  1.790242
    [0.0, 0.1)    390.969763     83.196893   22.083714  0.068378  1.082724
    [0.1, 0.2)    307.430278     84.485770   13.241163  0.444630  1.355545
    [0.2, 0.3)    366.041800     81.623699   20.110776  0.085841  1.464471
    [0.3, 0.4)    342.713428     74.441222   21.195090 -0.193052  0.993808
    [0.4, 0.5)    444.800092     77.272327   33.134601  0.011396  0.839200

Books of histograms
-------------------

A histogram ``Book`` acts like a Python dictionary, mapping string names to ``Hist`` objects. It provides the convenience of having only one object to ``fill`` (important in a complicated parallelization scheme), but also optimizes the calculation of those histograms to avoid unnecessary passes over the data.

.. code-block:: python

    >>> book = Book()
    >>> for w in 0.1, 0.5, 0.9:
    ...     book["w %g" % w] = Hist(bin("w*left + (1-w)*right", 100, -5, 5), defs={"w": w})

    >>> left = numpy.random.normal(-1, 1, 1000000)
    >>> right = numpy.random.normal(1, 1, 1000000)
    >>> book.fill(left=left, right=right)            # one "fill" for all histograms

    >>> overlay(book["w 0.1"].step(),
    ...         book["w 0.5"].step(),
    ...         book["w 0.9"].step()).to(canvas)

.. image:: docs/source/intro-13.png

In the above, we created three similar histograms, differing only in how to weight two subexpressions. The use of ``defs`` for substituting constants (or any expression) makes it easier to generate many histograms in a loop.

Note that the number of bins (memory use) scales as

.. pull-quote::

    (B :sub:`1` × ... B × :sub:`n` × (P :sub:`1` + ... + P :sub:`m`)) :sub:`1` + ... + (B :sub:`1` × ... B × :sub:`n` × (P :sub:`1` + ... + P :sub:`m`)) :sub:`k`

where B :sub:`i` is the number of bins in non-profile axis i, P :sub:`i` is the number of bins in profile axis i, and the whole expression is repeated for each histogram k in a book. That is, books add memory use, non-profile axes multiply, and profile axes add within the non-profile axes.

Manipulation methods
--------------------

select
""""""

``Hist.select(expr, tolerance=1e-12)``

Select a set of bins with a boolean ``expr``, returning a new ``Hist``. Cut boundaries may be approximate (within ``tolerance``), but the inequalities must be exact.

For example, if the low edge of each bin is closed, attempting to cut above it without including it is an error, as is attempting to cut below it with including it:

.. code-block:: python

    >>> h = Hist(bin("x", 100, -5, 5, closedlow=True))
    >>> h.select("x <= 0")

.. code-block::

    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "histbook/proj.py", line 230, in select
        return self._select(expr, tolerance)
      File "histbook/proj.py", line 328, in _select
        raise ValueError("no axis can select {0} (axis {1} has the wrong inequality; low edges are {2})"
                         .format(repr(str(expr)), wrongcmpaxis, "closed" if wrongcmpaxis.closedlow else
                         "open"))
    ValueError: no axis can select 'x <= 0' (axis bin('x', 100, -5.0, 5.0) has the wrong inequality;
                low edges are closed)

whereas

.. code-block:: python

    >>> h.select("x < 0")
    Hist(bin('x', 50, -5.0, 0.0, overflow=False, nanflow=False))

Any selection other than "``x == nan``" eliminates the nanflow because every comparison with "not a number" should yield ``False``. (So technically, "``x == nan``" shouldn't work— this deviation from strict IEEE behavior is for convenience.)

Selections can never select a partial bin, so filling a histogram and then selecting from it should yield exactly the same result as filtering the data before filling.

Categorical ``groupby`` axes can be selected with Python's ``in`` operator and constant sets (necessary because there are no comparators for categorical data other than ``==``, ``!=``, and ``in``).

.. code-block:: python

    >>> h = Hist(groupby("c"))
    >>> h.fill(c=["one", "two", "two", "three", "three", "three"])
    >>> h.pandas()

.. code-block::

           count()  err(count())
    c                           
    one        1.0      1.000000
    three      3.0      1.732051
    two        2.0      1.414214

.. code-block:: python

    >>> h.select("c in {'one', 'two'}").pandas()

.. code-block::

         count()  err(count())
    c                         
    one      1.0      1.000000
    two      2.0      1.414214

project
"""""""

``Hist.project(*axis)``

Reduces the number of non-profile axes to the provided set, ``*axis``, by summing over all other non-profile axes.

All internal data are sums that are properly combined by summing. For instance, histograms are represented by a count (unweighted) or a sum of weights and squared-weights (weighted), and profiles are represented by a sum of the quantity times weight and a sum of the squared-quantity times weight.

drop
""""

``Hist.drop(*profile)``

Eliminates all profile axes except the provided set, ``*profile``.

If a ``Hist`` were represented as a table, non-profile axes form a compound key but profile axes are simple columns, which may be dropped without affecting any other data.

rebin, rebinby
""""""""""""""

``Hist.rebin(axis, edges)``

``Hist.rebinby(axis, factor)``

Eliminates or sums neighboring bins to reduce the number of bins in an axis to ``edges`` or by a multiplicative ``factor``.

A ``Hist`` with detailed binning in two dimensions can be plotted against one axis with rebinned overlays in the other axis and vice-versa.

Tabular output
--------------

table
"""""

``Hist.table(*profile, count=True, effcount=False, error=True, recarray=True)``

Presents data from the histogram as a Numpy array,

- including any ``profile`` in the list;
- with a total ``count()`` if ``count=True``;
- with the effective ``effcount()`` if ``effcount=True`` (used to calculate weighted profile errors);
- with ``err(count()`` and an error for each profile if ``error=True``;
- as a labeled record array if ``recarray=True``; otherwise, an unlabeled rank-n ndarray.

fraction
""""""""

``Hist.fraction(*cut, count=True, error="clopper-pearson", level=erf(sqrt(0.5)), recarray=True)``

Presents cut fractions (cut efficiencies) as a function of non-profile axes for each ``cut``,

- with the total ``count()`` if ``count=True``;
- using "``clopper-pearson``", "``normal``" (naive binomial), "``wilson``", "``agresti-coull``", "``feldman-cousins``", "``jeffrey``", or "``bayesian-uniform``" errors or no errors if ``errors=None``;
- evaluated at ``level`` confidence levels (``erf(sqrt(0.5))`` is one sigma);
- as a labeled record array if ``recarray=True``; otherwise, an unlabeled rank-n ndarray.

pandas
""""""

``Hist.pandas(*axis, **opts)``

Presents a ``Hist.table`` as a Pandas DataFrame if all ``*axis`` are profiles or ``Hist.fraction`` if all ``*axis`` are cuts.

Plotting methods
----------------

``Hist`` and objects returned by ``PlottingChain.stack``, ``PlottingChain.overlay``, ``PlottingChain.beside``, and ``PlottingChain.below`` are PlottingChains.

bar
"""

``PlottingChain.bar(axis=None, profile=None, error=False)``

Creates a bar chart Plotable.

step
""""

``PlottingChain.step(axis=None, profile=None, error=False)``

Creates a step chart Plotable.

area
""""

``PlottingChain.area(axis=None, profile=None, error=False)``

Creates an area chart Plotable.

line
""""

``PlottingChain.line(axis=None, profile=None, error=False)``

Creates a line chart Plotable.

marker
""""""

``PlottingChain.marker(axis=None, profile=None, error=True)``

Creates a marker chart (points with error bars) Plotable.

stack
"""""

``PlottingChain.stack(axis)``

Extends the PlottingChain that stacks data along ``axis``.

overlay
"""""""

``PlottingChain.overlay(axis)``

Extends the PlottingChain that overlays data along ``axis``.

``overlay(*plotables)``

Overlays two existing Plotables.

beside
""""""

``PlottingChain.beside(axis)``

Extends the PlottingChain that places data side-by-side along ``axis``.

``beside(*plotables)``

Places two existing Plotables side-by-side.

below
"""""

``PlottingChain.below(axis)``

Extends the PlottingChain that places data above-and-below along ``axis``.

``below(*plotables)``

Places two existing Plotables above-and-below.

Exporting to ROOT
-----------------

``Hist.root(*axis, cache={}, name="", title="")``

Returns a PyROOT histogram projected on ``*axis``.

- If ``cache`` is provided, the resulting object is placed in the cache so that it doesn't disappear after you plot it (due to ROOT's memory management).
- If ``name`` and ``title`` are provided, they are assigned to PyROOT object.

.. inclusion-marker-4-do-not-remove

.. inclusion-marker-5-do-not-remove
