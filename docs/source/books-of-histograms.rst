Books of histograms
===================

Histograms can be collected into "books," both as a user convenience (fill all histograms in a book with a single call to ``fill``) and for performance (avoid multiple passes over the data or repeated calculations).

Books of histograms behave like dicts, with access to individual histograms through square brackets (``__getitem__`` and ``__setitem__``).

.. autoclass:: histbook.book.Book
   :members: 
   :inherited-members: 
