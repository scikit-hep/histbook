Axis descriptors
================

Each dimension of a :py:class:`Hist <histbook.hist.Hist>` is specified by an :py:class:`Axis <histbook.axis.Axis>` object. There are three main categories (abstract classes): :py:class:`GroupAxis <histbook.axis.GroupAxis>`, :py:class:`FixedAxis <histbook.axis.FixedAxis>`, and :py:class:`ProfileAxis <histbook.axis.ProfileAxis>`.

.. autoclass:: histbook.axis.Axis
.. autoclass:: histbook.axis.GroupAxis
.. autoclass:: histbook.axis.FixedAxis
.. autoclass:: histbook.axis.ProfileAxis

.. inheritance-diagram:: histbook.axis.groupby histbook.axis.groupbin histbook.axis.bin histbook.axis.intbin histbook.axis.split histbook.axis.cut histbook.axis.profile
   :parts: 1

Concrete Axis types
-------------------

The following are intended for use in :py:class:`Hist <histbook.hist.Hist>` constructors.

.. autoclass:: histbook.axis.groupby
   :members: 
   :inherited-members: 

.. autoclass:: histbook.axis.groupbin
   :members: 
   :inherited-members: 

.. autoclass:: histbook.axis.bin
   :members: 
   :inherited-members: 

.. autoclass:: histbook.axis.intbin
   :members: 
   :inherited-members: 

.. autoclass:: histbook.axis.split
   :members: 
   :inherited-members: 

.. autoclass:: histbook.axis.cut
   :members: 
   :inherited-members: 

.. autoclass:: histbook.axis.profile
   :members: 
   :inherited-members: 
