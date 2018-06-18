#!/usr/bin/env python

# Copyright (c) 2018, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import collections
import functools
import sys

import numpy

import histbook.calc.spark
import histbook.fill
import histbook.hist
import histbook.util

class Book(collections.MutableMapping, histbook.fill.Fillable):
    """
    A collection of histograms (:py:class:`Hist <histbook.hist.Hist>`) that can be filled with a single ``fill`` call.

    Behaves like a dict (item assignment, ``keys``, ``values``).
    """

    def __init__(self, hists={}, **more):
        u"""
        Parameters
        ----------
        hists : dict of str \u2192 :py:class:`Hist <histbook.hist.Hist>`
            initial histograms

        **more : dict of str \u2192 :py:class:`Hist <histbook.hist.Hist>`
            more initial histograms
        """
        self._fields = None
        self._hists = collections.OrderedDict()
        for n, x in hists.items():
            self._hists[n] = x
        for n, x in more.items():
            self._hists[n] = x

    def __repr__(self):
        return "Book({0} histogram{1})".format(len(self), "" if len(self) == 1 else "s")

    def __str__(self):
        return "Book({" + ",\n      ".join("{0}: {1}".format(repr(n), repr(x)) for n, x in self.items()) + "})"

    def __len__(self):
        return len(self._hists)

    def __contains__(self, name):
        return name in self._hists

    def __getitem__(self, name):
        return self._hists[name]

    def __setitem__(self, name, value):
        if isinstance(value, Book):
            for n, x in value.items():
                self._hists[name + "/" + n] = x.copyonfill()
                self._fields = None
        elif isinstance(value, histbook.hist.Hist):
            self._hists[name] = value.copyonfill()
            self._fields = None
        else:
            raise TypeError("histogram books can only be filled with histograms or other histogram books, not {0}".format(type(value)))

    def __delitem__(self, name):
        del self._hists[name]

    def __iter__(self):
        if sys.version_info[0] < 3:
            return self._hists.iterkeys()
        else:
            return self._hists.keys()

    def keys(self):
        return self._hists.keys()

    def values(self):
        return self._hists.values()

    @property
    def _goals(self):
        return functools.reduce(set.union, (x._goals for x in self.values()))

    def _streamline(self, i, instructions):
        self._destination = []
        for i, x in enumerate(self._hists.values()):
            self._destination.append(x._destination[0])
            x._streamline(i, instructions)
        return instructions

    def fill(self, arrays=None, **more):
        u"""
        Fill the histogram: identify bins for independent variables, increase their counts by ``1`` or ``weight``, and increment any profile (dependent variable) means and errors in the means.

        All arrays must have the same length (one-dimensional shape). Numbers are treated as one-element arrays.

        All histograms in the book are filled with the same inputs.

        Parameters
        ----------
        arrays : dict \u2192 Numpy array or number
            field values to use in the calculation of independent and dependent variables (axes)

        **more : dict \u2192 Numpy array or number
            more field values
        """

        if histbook.calc.spark.isspark(arrays, more):
            # special SparkSQL
            threads = [threading.Thread(target=histbook.calc.spark.fillspark(x, arrays)) for x in self._hists.values()]
            for x in self._hists.values():
                x._prefill()
            for x in threads:
                x.start()
            for x in threads:
                x.join()

        else:
            # standard Numpy
            if arrays is None:
                arrays = more
            elif len(more) == 0:
                pass
            else:
                arrays = histbook.util.ChainedDict(arrays, more)

            for x in self._hists.values():
                x._prefill()
            length = self._fill(arrays)
            for x in self._hists.values():
                x._postfill(arrays, length)

    def cleared(self):
        """Return a copy with all bins in all histograms set to zero."""
        out = Book()
        for n, x in other.items():
            out[n] = x.cleared()
        return out

    def clear(self):
        """Effectively reset all bins in all histograms to zero."""
        for x in self._hists.values():
            x.clear()

    def __add__(self, other):
        if not isinstance(other, Book):
            raise TypeError("histogram Books can only be added to other histogram Books")

        out = Book(self._hists)
        for n, x in other.items():
            if n in out:
                out[n] += x
            else:
                out[n] = x

        return out

    def __iadd__(self, other):
        if not isinstance(other, Book):
            raise TypeError("histogram Books can only be added to other histogram Books")

        for n, x in other.items():
            if n in self:
                self[n] += x
            else:
                self[n] = x

        return self

    def __mul__(self, value):
        out = Book()
        for n, x in self._hists.items():
            out[n] = x.__mul__(value)
        return out

    def __rmul__(self, value):
        return self.__mul__(value)

    def __imul__(self, value):
        for x in self._hists.values():
            x.__imul__(value)
        return self

    @staticmethod
    def group(by="source", **books):
        """
        Combine histograms, maintaining their distinctiveness by adding a new categorical axis to each.

        To combine histograms by adding bins, just use the ``+`` operator.

        Parameters
        ----------
        by : string
            name of the new axis (must not already exist)

        **books : :py:class:`Book <histbook.hist.Book>`
            books to combine (histograms with the same names must have the same axes)
        """
        if any(not isinstance(x, Book) for x in books.values()):
            raise TypeError("only histogram Books can be grouped")
        out = Book()
        for n in functools.reduce(set.union, (set(x.keys()) for x in books.values())):
            out._hists[n] = histbook.hist.Hist.group(by=by, **dict((name, book[n]) for name, book in books.items() if n in book.keys()))
        return out
