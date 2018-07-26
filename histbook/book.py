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
import threading

import numpy

import histbook.calc.spark
import histbook.fill
import histbook.hist
import histbook.util

if sys.version_info[0] <= 2:
    string = basestring
else:
    string = str

################################################################ superclass of all books (glorified dict)

class GenericBook(collections.MutableMapping):
    """
    A generic collection of histograms (:py:class:`Hist <histbook.hist.Hist>`) or other ``Books``.

    This generic superclass can't be filled; for a fillable book, use :py:class:`Book <histbook.book.Book>`.

    Behaves like a dict (item assignment, ``keys``, ``values``).
    """

    def __init__(self, hists1={}, *hists2, **hists3):
        u"""
        Positional arguments may be a dict of str \u2192 :py:class:`Hist <histbook.hist.Hist>` or :py:class:`GenericBook <histbook.book.GenericBook>`.

        Or they may be :py:class:`Hist <histbook.hist.Hist>` or :py:class:`GenericBook <histbook.book.GenericBook>` as unnamed varargs.

        In either case, keyword name \u2192 :py:class:`Hist <histbook.hist.Hist>` or :py:class:`Book <histbook.book.Book>` are also accepted.
        """
        self._content = collections.OrderedDict()
        self._attachment = {}

        if isinstance(hists1, dict):
            for n, x in hists1.items():
                self[n] = x
            if len(hists2) != 0:
                raise TypeError("only one positional argument when the first argument is a dict")

        elif isinstance(hists1, (histbook.hist.Hist, GenericBook)):
            self["0"] = hists1
            for i, x in enumerate(hists2):
                self[str(i + 1)] = x

        else:
            raise TypeError("positional arguments may be a single dict or varargs of unnamed histograms/books")

        for n, x in hists3.items():
            self[n] = x

        self._changed()

    def _changed(self):
        pass

    @classmethod
    def fromdicts(cls, content, attachment):
        """Construct a book from its ``content`` and ``attachment`` dicts."""
        out = cls.__new__(cls)
        out._content = collections.OrderedDict()
        out._attachment = attachment

        for n, x in content.items():
            out[n] = x

        out._changed()
        return out

    def attach(self, key, value):
        """Add an attachment to the book (changing it in-place and returning it)."""
        self._attachment[key] = value
        return self

    def detach(self, key):
        """Remove an attachment from the book (changing it in-place and returning it)."""
        del self._attachment[key]
        return self

    def has(self, key):
        """Returns ``True`` if ``key`` exists in the attachment metadata."""
        return key in self._attachment

    def get(self, key, *default):
        """
        Get an item of attachment metadata.

        If ``key`` isn't found and no ``default`` is specified, raise a ``KeyError``.
        If ``key`` isn't found and a ``default`` is provided, return the ``default`` instead.

        Only one ``default`` is allowed.
        """
        if len(default) == 0:
            return self._attachment[key]
        elif len(default) == 1:
            return self._attachment.get(key, default[0])
        else:
            raise TypeError("get takes 1 or 2 arguments; {0} provided".format(len(default) + 1))

    @property
    def attachment(self):
        """Python dict of attachment metadata (linked, not a copy)."""
        return self._attachment

    def __repr__(self):
        return "<{0} ({1} content{2}{3}) at {4:012x}>".format(self.__class__.__name__, len(self), "" if len(self) == 1 else "s", "" if len(self._attachment) == 0 else " {0} attachment{1}".format(len(self._attachment), "" if len(self._attachment) == 1 else "s"), id(self))

    def __str__(self, indent=",\n      ", first=True):
        return self.__class__.__name__ + "({" + (indent.replace(",", "") if first else "") + indent.join("{0}: {1}".format(repr(n), x.__str__(indent + "      " if isinstance(x, GenericBook) else ", ", True)) for n, x in self.iteritems()) + (indent.replace(",", "") if first else "") + "})"

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._content == other._content and self._attachment == other._attachment

    def __ne__(self, other):
        return not self.__eq__(other)

    def compatible(self, other):
        """Returns True if the books have the same set of histogram names and those histograms with matching names are compatible."""
        return set(self.iterkeys()) == set(other.iterkeys()) and all(self[n].compatible(other[n]) for n in self.iterkeys())

    def assertcompatible(self):
        """Raises ``ValueError`` if not all books have the same set of histogram names and those histograms with matching names are compatible."""
        def recurse(path, one, two):
            if isinstance(one, GenericBook) and one.__class__ is two.__class__:
                if set(one.iterkeys()) != set(two.iterkeys()):
                    raise ValueError("key names at {0} are not compatible (same book types, names, and non-profile axis binning):\n\n    {1}\n\nversus\n\n    {2}\n".format(repr(path), sorted(one.iterkeys()), sorted(two.iterkeys())))
                else:
                    for n in one.iterkeys():
                        recurse(path + "/" + n, one[n], two[n])

            elif isinstance(one, histbook.hist.Hist) and isinstance(two, histbook.hist.Hist):
                if not one.compatible(two):
                    raise ValueError("histograms at {0} are not compatible (same book types, names, and non-profile axis binning):\n\n    {1}\n\nversus\n\n    {2}\n".format(repr(path), repr(one), repr(two)))

            else:
                raise ValueError("histograms at {0} are not compatible (same book types, names, and non-profile axis binning):\n\n    {1}\n\nversus\n\n    {2}\n".format(repr(path), repr(type(one)), repr(type(two))))


        if len(self._content) >= 2:
            items = list(self._content.items())
            for (n1, x1), (n2, x2) in zip(items[:-1], items[1:]):
                recurse("{" + n1 + "," + n2 + "}", x1, x2)

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
            self._changed()
        else:
            attempt = self._content.get(name[:slash], None)
            if attempt is None:
                attempt = self._content[name[:slash]] = Book()
            if isinstance(attempt, GenericBook):
                attempt._set(name[slash + 1:], value, path + "/" + name[:slash])
                self._changed()
            else:
                raise KeyError("value at {0} is a Hist, not a book".format(repr(path)))
            
    def _del(self, name, path):
        if name in self._content:
            del self._content[name]
            self._changed()
        else:
            try:
                slash = name.index("/")
            except ValueError:
                raise KeyError("could not find {0}".format(name if path == "" else path + "/" + name))
            else:
                attempt = self._content.get(name[:slash], None)
                if isinstance(attempt, GenericBook):
                    attempt._del(name[slash + 1:], path + "/" + name[:slash])
                    self._changed()
                else:
                    raise KeyError("could not find {0}".format(name if path == "" else path + "/" + name))

    def __getitem__(self, name):
        if not isinstance(name, string):
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
        if not isinstance(name, string):
            raise TypeError("keys of a {0} must be strings".format(self.__class__.__name__))
        if not isinstance(value, (histbook.hist.Hist, GenericBook)):
            raise TypeError("values of a {0} must be Hists or books".format(self.__class__.__name__))

        self._set(name, value, "")

    def __delitem__(self, name):
        if not isinstance(name, string):
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
        return self.__class__.fromdicts(collections.OrderedDict((n, x.copy()) for n, x in self.items()), dict(self._attachment))

    def copyonfill(self):
        """Return a copy of the book of histograms whose content is copied if filled."""
        return self.__class__.fromdicts(collections.OrderedDict((n, x.copyonfill()) for n, x in self.items()), dict(self._attachment))

    def clear(self):
        """Effectively reset all bins of all histograms to zero."""
        for x in self.itervalues(recursive=True, onlyhist=True):
            x.clear()

    def cleared(self):
        """Return a copy with all bins of all histograms set to zero."""
        return self.__class__.fromdicts(collections.OrderedDict((n, x.cleared()) for n, x in self.items()), dict(self._attachment))

    def __add__(self, other):
        if not isinstance(other, GenericBook):
            raise TypeError("histogram books can only be added to other histogram books")

        content = collections.OrderedDict()
        for n, x in self.iteritems():
            if n in other:
                content[n] = x + other[n]
            else:
                content[n] = x
        for n, x in other.iteritems():
            if n not in self:
                content[n] = x

        attachment = dict(self._attachment)
        attachment.update(other._attachment)
        return self.__class__.fromdicts(content, attachment)

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
        content = collections.OrderedDict()
        for n, x in self.iteritems():
            content[n] = x.__mul__(value)
        return self.__class__.fromdicts(content, dict(self._attachment))

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

        content = collections.OrderedDict()
        for name in functools.reduce(set.union, (set(book.iterkeys()) for book in books.values())):
            nestcls = tuple(set(book[name].__class__ for book in books.values() if name in book))
            if len(nestcls) != 1:
                raise TypeError("books at {0} have different types: {1}".format(repr(name), ", ".join(repr(x) for x in nestcls)))
            content[name] = nestcls[0].group(by=by, **dict((n, book[name]) for n, book in books.items() if name in book))

        attachment = {}
        for book in books.values():
            attachment.update(book._attachment)

        return cls.fromdicts(content, attachment)

################################################################ user-level Book (in the histbook.* namespace)

class Book(GenericBook, histbook.fill.Fillable):
    """
    A collection of histograms (:py:class:`Hist <histbook.hist.Hist>`) or other ``Books`` that can be filled with a single ``fill`` call.

    Behaves like a dict (item assignment, ``keys``, ``values``).
    """

    def __str__(self, indent=",\n      ", first=False):
        return super(Book, self).__str__(indent=indent, first=first)

    def _changed(self):
        self._fields = None

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

################################################################ for constructing fillable views

class ViewableBook(GenericBook):
    def view(self, name):
        if not isinstance(name, string):
            raise TypeError("keys of a {0} must be strings".format(self.__class__.__name__))

        def recurse(node, path):
            if isinstance(node, histbook.hist.Hist):
                if fnmatch.fnmatchcase(path, name):
                    return node
                else:
                    return None

            else:
                content = collections.OrderedDict()
                for n, x in node.iteritems():
                    deep = recurse(x, (n if path is None else path + "/" + n))
                    if deep is not None:
                        content[n] = deep

                if len(content) != 0:
                    return ViewBook.fromdicts(content, node._attachment)
                else:
                    return None

        out = recurse(self, None)
        if out is None:
            raise ValueError("nothing matched path wildcard pattern {0}".format(repr(name)))
        return out

class ViewBook(Book):
    def __str__(self, indent=",\n      ", first=True):
        return super(ViewBook, self).__str__(indent=indent, first=first)

################################################################ statistically relevant books

class ChannelsBook(ViewableBook):
    pass

class SamplesBook(ViewableBook):
    def __init__(self, samples, hists1={}, *hists2, **hists3):
        self._content = collections.OrderedDict()
        self._attachment = {}
        for sample in samples:
            self[sample] = Book(hists1, *hists2, **hists3).copyonfill()
        self._changed()

class SystematicsBook(Book):
    def __str__(self, indent=",\n      ", first=True):
        return super(SystematicsBook, self).__str__(indent=indent, first=first)

    def _changed(self):
        self.assertcompatible()
        if not all(x.has("systematic") for x in self.itervalues(recursive=True, onlyhist=True)):
            raise ValueError("all histograms in a SystematicsBook must have a 'systematic' attachment")
