# histbook

Histogram library with better separation between aggregation and plotting.

## Motivation and introduction

The name deliberately draws from [CERN HBOOK](http://cds.cern.ch/record/307945/files/), a histogramming library developed for particle physics in the 1970's. Descendants and libraries based on HBOOK, including [PAW](http://paw.web.cern.ch/paw/), [mn_fit](https://community.linuxmint.com/software/view/mn-fit), [HippoDraw](http://www.slac.stanford.edu/grp/ek/hippodraw/), [ROOT](https://root.cern/), [AIDA](http://aida.freehep.org/doc/v3.0/UsersGuide.html), and [YODA](https://yoda.hepforge.org/) have a three-step API not shared by histogramming functions developed outside of particle physics. These are:

   1. Define ("book") the bin widths and ranges of all your histograms.
   2. Increment ("fill") them with a large dataset.
   3. Visualize ("plot") them.

The advantage of an explicit "booking" step allows step 2 to be performed in parallel and in one pass— essential for the scale of problems in particle physics. With explicit bins, histograms are simple [monoids](https://fsharpforfunandprofit.com/posts/monoids-without-tears/) that can be combined by addition ([hadd](https://root.cern.ch/how/how-merge-histogram-files) in ROOT).

histbook takes this separation further by making the booking step independent of how the histograms might eventually be plotted. HBOOK and its descendants define one, two, and sometimes three-dimensional histograms because this is the highest dimensionality that can be visualized by humans. However, it's often useful to aggregate data along more dimensions, some categorically (pass/fail, unique strings), some sparsely, some with regular bin widths, some irregularly. Today, particle physicists manage this with arrays of histograms or naming conventions because the current frameworks only organize counters along one, two, or three dimensions.

histbook's booking step divides an arbitrary-dimensional parameter space into bins and creates an n-dimensional "fill" function. Collections of histograms can be further consolidated into a single "book." The result of filling does not produce a plot but a table of numbers that could be viewed as a [Numpy record array](https://docs.scipy.org/doc/numpy/user/basics.rec.html) or a [Pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe). It can also be plotted in many different ways:

   * as a single distribution,
   * stacked by category,
   * overlaid,
   * as a trellis of side-by-side plots, etc.

In addition, post-aggregation analysis can be performed:

   * plot subsets of the data, as long as the threshold coincides with a bin edge,
   * compute ratios or fractions (e.g. trigger efficiency) with propagated uncertainties,
   * apply complex weighting schemes, including negative weights,
   * "profile plots" of one dimension by viewing it along another, etc.

## Implementation

histbook is written in Python, using Numpy record arrays for storage. They are [Numba-aware](http://numba.pydata.org/), meaning that they can be used in JIT-compiled Python functions for speed. Plots are presented in [Vega-Lite](https://vega.github.io/vega-lite/), a JSON grammar for visualization that render inline in [Jupyter notebooks](http://jupyter.org/) or anywhere through [VegaScope](https://github.com/diana-hep/vegascope). Projections of a filled histogram book can also be converted to [PyROOT](https://root.cern.ch/pyroot) histograms for ROOT.

## Disclaimer/timeline

By the way, none of the above exists as of this writing (May 7, 2018); it's a scope of work. Now I need to make all of the above true. (Should be doable in less than 3 weeks: end of May.)
