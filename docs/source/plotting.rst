Plotting
========

The plotting interface is fluent, meaning that the graphical content of the plot is configured by a chain of method calls. Steps along this chain (including the :py:class:`Hist <histbook.hist.Hist>` itself) are :py:class:`PlottingChain <histbook.vega.PlottingChain>` objects and the last one is :py:class:`Plotable <histbook.vega.Plotable>`.

.. autoclass:: histbook.vega.PlottingChain
   :members: 
   :inherited-members:

.. autoclass:: histbook.vega.Plotable
   :members: 
   :inherited-members:

.. inheritance-diagram:: histbook.vega.overlay histbook.vega.beside histbook.vega.below
   :parts: 1
   :top-classes: histbook.vega.Combination

.. autoclass:: histbook.vega.Combination
   :members: 
   :inherited-members:

.. autoclass:: histbook.vega.overlay
   :members: 
   :inherited-members:

.. autoclass:: histbook.vega.beside
   :members: 
   :inherited-members:

.. autoclass:: histbook.vega.below
   :members: 
   :inherited-members:
