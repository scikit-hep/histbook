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
import fnmatch
import functools
import sys

import numpy

import histbook.calc.spark
import histbook.fill
import histbook.hist
import histbook.util

################################################################ superclass of all books (glorified dict)

class GenericBook(collections.MutableMapping):
    """
    A generic collection of histograms (:py:class:`Hist <histbook.hist.Hist>`) or other ``Books``.

    This generic superclass can't be filled; for a fillable book, use :py:class:`Book <histbook.book.Book>`.

    Behaves like a dict (item assignment, ``keys``, ``values``).
    """

    def __init__(self, hists={}, **more):
        u"""
        Parameters
        ----------
        hists : dict of str \u2192 :py:class:`Hist <histbook.hist.Hist>` or :py:class:`Book <histbook.book.Book>`; or list of :py:class:`Hists <histbook.hist.Hist>` and :py:class:`Books <histbook.book.Book>`
            initial histograms; if list is provided, names will be numbers increasing from zero

        **more : :py:class:`Hists <histbook.hist.Hist>` or :py:class:`Books <histbook.book.Book>`
            more initial histograms
        """
        self._content = collections.OrderedDict()
        self._attachment = {}
        if hasattr(hists, "items"):
            for n, x in hists.items():
                self[n] = x
        else:
            for i, x in enumerate(hists):
                self[str(i)] = x
        for n, x in more.items():
            self[n] = x

    @classmethod
    def fromdicts(cls, content, attachment):
        """Construct a book from its ``content`` and ``attachment`` dicts."""
        out = cls.__new__(cls)
        out._content = collections.OrderedDict()
        for n, x in content.items():
            out[n] = x
        out._attachment = attachment
        return out

    def attach(self, key, value):
        """Add an attachment to the book (changing it in-place and returning it)."""
        self._attachment[key] = value
        return self

    def detach(self, key):
        """Remove an attachment from the book (changing it in-place and returning it)."""
        del self._attachment[key]
        return self

    @property
    def attachment(self):
        """Python dict of attachment metadata."""
        return self._attachment

    def __repr__(self):
        return "<{0} ({1} content{2}{3}) at {4:012x}>".format(self.__class__.__name__, len(self), "" if len(self) == 1 else "s", "" if len(self._attachment) == 0 else " {0} attachment{1}".format(len(self._attachment), "" if len(self._attachment) == 1 else "s"), id(self))

    def __str__(self, indent=",\n      ", first=False):
        return self.__class__.__name__ + "({" + (indent.replace(",", "") if first else "") + indent.join("{0}: {1}".format(repr(n), x.__str__(indent + "      " if isinstance(x, GenericBook) else ", ", True)) for n, x in self.iteritems()) + "})"

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._content == other._content and self._attachment == other._attachment

    def __ne__(self, other):
        return not self.__eq__(other)

    def tojson(self):
        def merge(name, node):
            node["name"] = name
            return node
        out = {"type": self.__class__.__name__, "content": [merge(n, x.tojson()) for n, x in self._content.items()]}
        if len(self._attachment) != 0:
            out["attachment"] = self._attachment
        return out

    @staticmethod
    def fromjson(obj):
        cls = getattr(sys.modules[GenericBook.__module__], obj["type"])
        content = collections.OrderedDict()
        for node in obj["content"]:
            if node["type"] == "Hist":
                content[node["name"]] = histbook.hist.Hist.fromjson(node)
            else:
                content[node["name"]] = GenericBook.fromjson(node)
        return cls.fromdicts(content, obj.get("attachment", {}))

    def __len__(self):
        return len(self._content)

    def __contains__(self, name):
        try:
            self[name]
        except KeyError:
            return False
        else:
            return True

    def _get(self, name):
        attempt = self._content.get(name, None)
        if attempt is not None:
            return attempt
        else:
            try:
                slash = name.index("/")
            except ValueError:
                pass
            else:
                attempt = self._content.get(name[:slash], None)
                if isinstance(attempt, GenericBook):
                    return attempt._get(name[slash + 1:])
        return None

    def _set(self, name, value, path):
        try:
            slash = name.index("/")
        except ValueError:
            self._content[name] = value
        else:
            attempt = self._content.get(name[:slash], None)
            if attempt is None:
                attempt = self._content[name[:slash]] = Book()
            if isinstance(attempt, GenericBook):
                attempt._set(name[slash + 1:], value, path + "/" + name[:slash])
            else:
                raise KeyError("there is no book at {0}".format(repr(path)))
            
    def _del(self, name, path):
        if name in self._content:
            del self._content[name]
        else:
            try:
                slash = name.index("/")
            except ValueError:
                raise KeyError("could not find {0}".format(name if path == "" else path + "/" + name))
            else:
                attempt = self._content.get(name[:slash], None)
                if isinstance(attempt, GenericBook):
                    attempt._del(name[slash + 1:], path + "/" + name[:slash])
                else:
                    raise KeyError("could not find {0}".format(name if path == "" else path + "/" + name))

    def __getitem__(self, name):
        if (sys.version_info[0] <= 2 and not isinstance(name, basestring)) or (sys.version_info[0] >= 3 and not isinstance(name, str)):
            raise TypeError("keys of a {0} must be strings".format(self.__class__.__name__))

        if "*" in name or "?" in name or "[" in name:
            return [x for n, x in self.iteritems(recursive=True) if fnmatch.fnmatchcase(n, name)]
        else:
            out = self._get(name)
            if out is not None:
                return out
            else:
                raise KeyError("could not find {0} and could not interpret it as a wildcard (glob) pattern".format(repr(name)))

    def __setitem__(self, name, value):
        if (sys.version_info[0] <= 2 and not isinstance(name, basestring)) or (sys.version_info[0] >= 3 and not isinstance(name, str)):
            raise TypeError("keys of a {0} must be strings".format(self.__class__.__name__))

        self._set(name, value, "")

    def __delitem__(self, name):
        if (sys.version_info[0] <= 2 and not isinstance(name, basestring)) or (sys.version_info[0] >= 3 and not isinstance(name, str)):
            raise TypeError("keys of a {0} must be strings".format(self.__class__.__name__))

        if "*" in name or "?" in name or "[" in name:
            for n in self.allkeys():
                self._del(n, "")
        else:
            self._del(name, "")

    def _iteritems(self, path, recursive, onlyhist):
        for n, x in self._content.items():
            if not onlyhist or isinstance(x, histbook.hist.Hist):
                yield (n if path is None else path + "/" + n), x

            if recursive and isinstance(x, GenericBook):
                for y in x._iteritems((n if path is None else path + "/" + n), recursive, onlyhist):
                    yield y

    def iteritems(self, recursive=False, onlyhist=False):
        """
        Iterate through path, book-or-histogram pairs.

        Parameters
        ----------
        recursive : bool
            if ``True`` *(default)*, descend into books of books

        onlyhist : bool
            if ``True`` *(not default)*, only return histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        for n, x in self._iteritems(None, recursive, onlyhist):
            yield n, x

    def iterkeys(self, recursive=False, onlyhist=False):
        """
        Iterate through paths.

        Parameters
        ----------
        recursive : bool
            if ``True`` *(default)*, descend into books of books

        onlyhist : bool
            if ``True`` *(not default)*, only return names of histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        for n, x in self.iteritems(recursive=recursive, onlyhist=onlyhist):
            yield n

    def itervalues(self, recursive=False, onlyhist=False):
        """
        Iterate through books and histograms.

        Parameters
        ----------
        recursive : bool
            if ``True`` *(default)*, descend into books of books

        onlyhist : bool
            if ``True`` *(not default)*, only return histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        for n, x in self.iteritems(recursive=recursive, onlyhist=onlyhist):
            yield x

    def items(self, recursive=False, onlyhist=False):
        """
        Return a list of path, book-or-histogram pairs.

        Parameters
        ----------
        recursive : bool
            if ``True`` *(default)*, descend into books of books

        onlyhist : bool
            if ``True`` *(not default)*, only return histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        return list(self.iteritems(recursive=recursive, onlyhist=onlyhist))

    def keys(self, recursive=False, onlyhist=False):
        """
        Return a list of paths.

        Parameters
        ----------
        recursive : bool
            if ``True`` *(default)*, descend into books of books

        onlyhist : bool
            if ``True`` *(not default)*, only return names of histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        return list(self.iterkeys(recursive=recursive, onlyhist=onlyhist))

    def values(self, recursive=False, onlyhist=False):
        """
        Return a list of books and histograms.

        Parameters
        ----------
        recursive : bool
            if ``True`` *(default)*, descend into books of books

        onlyhist : bool
            if ``True`` *(not default)*, only return histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        return list(self.itervalues(recursive=recursive, onlyhist=onlyhist))

    def allitems(self, onlyhist=False):
        """
        Return a recursive list of path, book-or-histogram pairs.

        Parameters
        ----------
        onlyhist : bool
            if ``True`` *(not default)*, only return histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        return self.items(recursive=True, onlyhist=onlyhist)

    def allkeys(self, onlyhist=False):
        """
        Return a recursive list of paths.

        Parameters
        ----------
        onlyhist : bool
            if ``True`` *(not default)*, only return names of histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        return self.keys(recursive=True, onlyhist=onlyhist)

    def allvalues(self, onlyhist=False):
        """
        Return a recursive list of books and histograms.

        Parameters
        ----------
        onlyhist : bool
            if ``True`` *(not default)*, only return histograms (type :py:class:`Hist <histbook.hist.Hist>`), not books
        """
        return self.values(recursive=True, onlyhist=onlyhist)

    def __iter__(self):
        """Same as ``iteritems(recursive=True, onlyhist=True)``."""
        return self.iteritems(recursive=True, onlyhist=True)

    def copy(self):
        """Return an immediate copy of the book of histograms."""
        return self.__class__(dict((n, x.copy()) for n, x in self.items()))

    def copyonfill(self):
        """Return a copy of the book of histograms whose content is copied if filled."""
        return self.__class__(dict((n, x.copyonfill()) for n, x in self.items()))

    def clear(self):
        """Effectively reset all bins of all histograms to zero."""
        for x in self.itervalues(recursive=True, onlyhist=True):
            x.clear()

    def cleared(self):
        """Return a copy with all bins of all histograms set to zero."""
        return self.__class__(dict((n, x.cleared()) for n, x in self.items()))

    def __add__(self, other):
        if not isinstance(other, GenericBook):
            raise TypeError("histogram books can only be added to other histogram books")

        out = self.__class__()
        for n, x in self.iteritems():
            if n not in other:
                out[n] = x
        for n, x in other.iteritems():
            if n not in self:
                out[n] = x
            else:
                out[n] = x + self[n]
        return out

    def __iadd__(self, other):
        if not isinstance(other, GenericBook):
            raise TypeError("histogram books can only be added to other histogram books")

        for n, x in other.iteritems():
            if n not in self:
                self[n] = x
            else:
                self[n] += x
        return self

    def __mul__(self, value):
        out = self.__class__()
        for n, x in self.iteritems():
            out[n] = x.__mul__(value)
        return out

    def __rmul__(self, value):
        return self.__mul__(value)

    def __imul__(self, value):
        for x in self.itervalues():
            x.__imul__(value)
        return self

    @classmethod
    def group(cls, by="source", **books):
        """
        Combine histograms, maintaining their distinctiveness by adding a new categorical axis to each.

        To combine histograms by adding bins, just use the ``+`` operator.

        Parameters
        ----------
        by : string
            name of the new axis (must not already exist)

        **books : :py:class:`Book <histbook.book.Book>`
            books to combine (histograms with the same names must have the same axes)
        """
        if any(not isinstance(x, GenericBook) for x in books.values()):
            raise TypeError("only histogram books can be grouped with other books")
        out = cls()
        for name in functools.reduce(set.union, (set(book.iterkeys()) for book in books.values())):
            nestcls = tuple(set(book[name].__class__ for book in books.values() if name in book))
            if len(nestcls) != 1:
                raise TypeError("books at {0} have different types: {1}".format(repr(name), ", ".join(repr(x) for x in nestcls)))
            out[name] = nestcls[0].group(by=by, **dict((n, book[name]) for n, book in books.items() if name in book))
        return out

################################################################ user-level Book (in the histbook.* namespace)

class Book(GenericBook, histbook.fill.Fillable):
    """
    A collection of histograms (:py:class:`Hist <histbook.hist.Hist>`) or other ``Books`` that can be filled with a single ``fill`` call.

    Behaves like a dict (item assignment, ``keys``, ``values``).
    """

    def __init__(self, hists={}, **more):
        self._fields = None
        super(Book, self).__init__(hists, **more)

    def __setitem__(self, name, value):
        self._fields = None
        super(Book, self).__setitem__(name, value)

    def __delitem__(self, name):
        self._fields = None
        super(Book, self).__delitem__(name)

    @property
    def _goals(self):
        return functools.reduce(set.union, (x._goals for x in self.itervalues(recursive=True, onlyhist=True)))

    def _streamline(self, i, instructions):
        self._destination = []
        for i, x in enumerate(self.itervalues(recursive=True, onlyhist=True)):
            self._destination.append(x._destination[0])
            x._streamline(i, instructions)
        return instructions

    def fill(self, arrays=None, **more):
        u"""
        Fill the histograms: identify bins for independent variables, increase their counts by ``1`` or ``weight``, and increment any profile (dependent variable) means and errors in the means.

        All arrays must have the same length (one-dimensional shape). Numbers are treated as one-element arrays.

        All histograms in the book are filled with the same inputs.

        Parameters
        ----------
        arrays : dict \u2192 Numpy array or number; Spark DataFrame; Pandas DataFrame
            field values to use in the calculation of independent and dependent variables (axes)

        **more : Numpy arrays or numbers
            more field values
        """

        if histbook.calc.spark.isspark(arrays, more):
            # pyspark.DataFrame
            threads = [threading.Thread(target=histbook.calc.spark.fillspark(x, arrays)) for x in self.itervalues(recursive=True, onlyhist=True)]
            for x in self.itervalues(recursive=True, onlyhist=True):
                x._prefill()
            for x in threads:
                x.start()
            for x in threads:
                x.join()

        elif arrays.__class__.__name__ == "DataFrame" and arrays.__class__.__module__ == "pandas.core.frame":
            # pandas.DataFrame
            if len(more) > 0:
                raise TypeError("if arrays is a Pandas DataFrame, keyword arguments are not allowed")
            self.fill(dict((n, arrays[n].values) for n in arrays.columns))

        else:
            # dict-like of numpy.ndarray (or castable)
            if arrays is None:
                arrays = more
            elif len(more) == 0:
                pass
            else:
                arrays = histbook.util.ChainedDict(arrays, more)

            for x in self.itervalues(recursive=True, onlyhist=True):
                x._prefill()
            length = self._fill(arrays)
            for x in self.itervalues(recursive=True, onlyhist=True):
                x._postfill(arrays, length)

################################################################ statistically relevant books


