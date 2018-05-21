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
COUNTTYPE = numpy.float64

import histbook.axis
import histbook.calc
import histbook.export
import histbook.expr
import histbook.proj
import histbook.instr
import histbook.vega

class _ChainedDict(object):
    def __init__(self, one, two):
        self._one = one
        self._two = two

    def __getitem__(self, n):
        if n in self._two:         # self._two is a real dict
            return self._two[n]    # and it has precedence
        else:
            return self._one[n]    # self._one might only have __getitem__
        
class Fillable(object):
    @property
    def fields(self):
        if self._fields is None:
            table = {}
            goals = set(self._goals)

            for x in goals:
                x.clear()
            for x in goals:
                x.grow(table)
            
            fields = histbook.instr.sources(goals, table)

            self._instructions = self._streamline(0, list(histbook.instr.instructions(fields, goals)))
            self._fields = sorted(x.goal.value for x in fields)

        return self._fields

    def _fill(self, arrays):
        self.fields  # for the side-effect of creating self._instructions

        length = None
        symbols = {}
        for instruction in self._instructions:
            if isinstance(instruction, histbook.instr.Param):
                try:
                    array = arrays[instruction.extern]
                except KeyError:
                    raise ValueError("required field {0} not found in fill arguments".format(repr(instruction.extern)))

                if not isinstance(array, numpy.ndarray):
                    array = numpy.array(array)

                if length is None:
                    length = len(array)
                elif length != len(array):
                    raise ValueError("array {0} has len {1} but other arrays have len {2}".format(repr(instruction.extern), len(array), length))

                symbols[instruction.name] = array

            elif isinstance(instruction, histbook.instr.Assign):
                symbols[instruction.name] = histbook.calc.calculate(instruction.expr, symbols)

            elif isinstance(instruction, histbook.instr.Export):
                data = symbols[instruction.name]
                for i, j in instruction.destination:
                    self._destination[i][j] = data

            elif isinstance(instruction, histbook.instr.Delete):
                del symbols[instruction.name]

            else:
                raise AssertionError(instruction)

        return length

class Book(collections.MutableMapping, Fillable):
    def __init__(self, hists={}, **keywords):
        self._fields = None
        self._hists = collections.OrderedDict()
        for n, x in hists.items():
            self._hists[n] = x
        for n, x in keywords.items():
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
                self._hists[name + "/" + n] = x.copy()
                self._fields = None
        elif isinstance(value, Hist):
            self._hists[name] = value.copy()
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
        if arrays is None:
            arrays = more
        elif len(more) == 0:
            pass
        else:
            arrays = _ChainedDict(arrays, more)

        for x in self._hists.values():
            x._prefill()
        length = self._fill(arrays)
        for x in self._hists.values():
            x._postfill(arrays, length)

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

    @staticmethod
    def group(by="source", **books):
        if any(not isinstance(x, Book) for x in books.values()):
            raise TypeError("only histogram Books can be grouped")
        out = Book()
        for n in functools.reduce(set.union, (set(x.keys()) for x in books.values())):
            out._hists[n] = Hist.group(by=by, **dict((name, book[n]) for name, book in books.items() if n in book.keys()))
        return out

class Hist(Fillable, histbook.proj.Projectable, histbook.export.Exportable, histbook.vega.PlottingChain):
    @property
    def _source(self):
        return self

    @property
    def _chain(self):
        return ()

    def weight(self, expr):
        return Hist(*[x.relabel(x._original) for x in self._group + self._fixed + self._profile], weight=expr, defs=self._defs)

    @staticmethod
    def _copycontent(content):
        if content is None:
            return None
        elif isinstance(content, numpy.ndarray):
            return content.copy()
        else:
            return dict((n, Hist._copycontent(x)) for n, x in content.items())

    def copy(self):
        out = self.__class__.__new__(self.__class__)
        out.__dict__.update(self.__dict__)
        out._content = Hist._copycontent(self._content)
        return out

    def __init__(self, *axis, **opts):
        weight = opts.pop("weight", None)
        defs = opts.pop("defs", {})
        if len(opts) > 0:
            raise TypeError("unrecognized options for Hist: {0}".format(" ".join(opts)))

        self._defs = defs
        self._group = []
        self._fixed = []
        self._profile = []

        newaxis = []
        for old in axis:
            if isinstance(old, histbook.axis._nullaxis):
                newaxis.append(old)
            else:
                expr, label = histbook.expr.Expr.parse(old._expr, defs=defs, returnlabel=True)
                new = old.relabel(label)
                new._original = old._expr
                new._parsed = expr
                newaxis.append(new)

        self._goals = set()
        self._destination = [[]]
        self._lookup = {}
        def dest(goals):
            self._goals.update(set(goals))
            for goal in goals:
                if goal.goal not in self._lookup:
                    self._lookup[goal.goal] = []
                self._lookup[goal.goal].append(len(self._destination[0]))
                self._destination[0].append(None)

        dictindex = 0
        for new in newaxis:
            if isinstance(new, histbook.axis.GroupAxis):
                self._group.append(new)
                new._dictindex = dictindex
                dictindex += 1
                dest(new._goals(new._parsed))

        self._shape = []
        for new in newaxis:
            if isinstance(new, histbook.axis.FixedAxis):
                self._fixed.append(new)
                new._shapeindex = len(self._shape)
                self._shape.append(new.totbins)
                if not isinstance(new, histbook.axis._nullaxis):
                    dest(new._goals(new._parsed))

        self._shape.append(0)
        for new in newaxis:
            if isinstance(new, histbook.axis.ProfileAxis):
                self._profile.append(new)
                new._sumwxindex = self._shape[-1]
                new._sumwx2index = self._shape[-1] + 1
                self._shape[-1] += 2
                dest(new._goals(new._parsed))

        if weight is None:
            self._weightoriginal, self._weightparsed, self._weightlabel = None, None, None
            self._sumwindex = self._shape[-1]
            self._shape[-1] += 1

        else:
            self._weightoriginal = weight
            self._weightparsed, self._weightlabel = histbook.expr.Expr.parse(weight, defs=self._defs, returnlabel=True)
            self._sumwindex = self._shape[-1]
            self._sumw2index = self._shape[-1] + 1
            self._shape[-1] += 2
            dest([histbook.instr.CallGraphGoal(self._weightparsed),
                  histbook.instr.CallGraphGoal(histbook.expr.Call("numpy.multiply", self._weightparsed, self._weightparsed))])

        self._group = tuple(self._group)
        self._fixed = tuple(self._fixed)
        self._profile = tuple(self._profile)

        self._weight = weight
        self._shape = tuple(self._shape)
        self._content = None
        self._fields = None
        
    def __repr__(self, indent=", "):
        out = [repr(x) for x in self._group + self._fixed + self._profile]
        if self._weightlabel is not None:
            out.append("weight={0}".format(repr(self._weightlabel)))
        if len(self._defs) > 0:
            out.append("defs={" + ", ".join("{0}: {1}".format(repr(n), repr(str(x)) if isinstance(x, histbook.expr.Expr) else repr(x)) for n, x in self._defs.items()) + "}")
        return "Hist(" + indent.join(out) + ")"

    def __str__(self):
        return self.__repr__(",\n     ")

    @property
    def shape(self):
        return self._shape

    def _streamline(self, i, instructions):
        for instruction in instructions:
            if isinstance(instruction, histbook.instr.Export):
                if not hasattr(instruction, "destination"):
                    instruction.destination = []
                if instruction.goal in self._lookup:
                    for j in self._lookup[instruction.goal]:
                        instruction.destination.append((i, j))

        return instructions

    def fill(self, arrays=None, **more):
        if arrays is None:
            arrays = more
        elif len(more) == 0:
            pass
        else:
            arrays = _ChainedDict(arrays, more)

        self._prefill()
        length = self._fill(arrays)
        self._postfill(arrays, length)

    def _prefill(self):
        if self._content is None:
            if len(self._group) == 0:
                self._content = numpy.zeros(self._shape, dtype=COUNTTYPE)
            else:
                self._content = {}

    def _postfill(self, arrays, length):
        j = len(self._group)
        step = 0
        indexes = None
        for axis in self._fixed:
            if step == 0:
                indexes = self._destination[0][j]
            elif step == 1:
                indexes = indexes.copy()
            if step > 0:
                numpy.multiply(indexes, self._shape[axis._shapeindex], indexes)
                numpy.add(indexes, self._destination[0][j], indexes)
            j += 1
            step += 1

        axissumx, axissumx2 = [], []
        for axis in self._profile:
            axissumx.append(self._destination[0][j])
            axissumx2.append(self._destination[0][j + 1])
            j += 2

        if self._weightparsed is None:
            weight = 1
            weight2 = None
        else:
            weight = self._destination[0][j]
            weight2 = self._destination[0][j + 1]
            selection = numpy.isnan(weight)
            if selection.any():
                weight = weight.copy()
                weight2 = weight2.copy()
                weight[selection] = 0.0
                weight2[selection] = 0.0

        def fillblock(content, indexes, axissumx, axissumx2, weight, weight2):
            for sumx, sumx2, axis in zip(axissumx, axissumx2, self._profile):
                if indexes is None:
                    indexes = numpy.ma.zeros(len(sumx), dtype=histbook.calc.INDEXTYPE)
                if weight2 is not None:
                    selection = numpy.ma.getmask(indexes)
                    if selection is not numpy.ma.nomask:
                        selection = numpy.bitwise_not(selection)
                        weight = weight[selection]
                        weight2 = weight2[selection]
                numpy.add.at(content.reshape((-1, self._shape[-1]))[:, axis._sumwxindex], indexes.compressed(), sumx * weight)
                numpy.add.at(content.reshape((-1, self._shape[-1]))[:, axis._sumwx2index], indexes.compressed(), sumx2 * weight)

            if weight2 is None:
                if indexes is None:
                    content.reshape((-1, self._shape[-1]))[:, self._sumwindex] += (1 if length is None else length) * weight
                else:
                    numpy.add.at(content.reshape((-1, self._shape[-1]))[:, self._sumwindex], indexes.compressed(), weight)
            else:
                if indexes is None:
                    indexes = numpy.ma.zeros(len(weight), dtype=histbook.calc.INDEXTYPE)
                selection = numpy.ma.getmask(indexes)
                if selection is not numpy.ma.nomask:
                    selection = numpy.bitwise_not(selection)
                    weight = weight[selection]
                    weight2 = weight2[selection]
                numpy.add.at(content.reshape((-1, self._shape[-1]))[:, self._sumwindex], indexes.compressed(), weight)
                numpy.add.at(content.reshape((-1, self._shape[-1]))[:, self._sumw2index], indexes.compressed(), weight2)

        def filldict(j, content, indexes, axissumx, axissumx2, weight, weight2, allselection):
            if j == len(self._group):
                fillblock(content, indexes, axissumx, axissumx2, weight, weight2)

            else:
                uniques, inverse = self._destination[0][j]
                for idx, unique in enumerate(uniques):
                    if allselection is None:
                        selection = (inverse == idx)
                    else:
                        selection = (inverse[allselection] == idx)
                    
                    if unique not in content:
                        if j + 1 == len(self._group):
                            content[unique] = numpy.zeros(self._shape, dtype=COUNTTYPE)
                        else:
                            content[unique] = {}

                    subcontent = content[unique]
                    if indexes is None:
                        subindexes = numpy.ma.zeros(numpy.count_nonzero(selection), dtype=histbook.calc.INDEXTYPE)
                    else:
                        subindexes = indexes[selection]
                    subaxissumx = [x[selection] for x in axissumx]
                    subaxissumx2 = [x[selection] for x in axissumx2]
                    if weight2 is None:
                        subweight, subweight2 = weight, weight2
                    else:
                        subweight = weight[selection]
                        subweight2 = weight2[selection]

                    if allselection is None:
                        suballselection = selection
                    else:
                        suballselection = allselection.copy()
                        suballselection[inverse != idx] = False

                    filldict(j + 1, subcontent, subindexes, subaxissumx, subaxissumx2, subweight, subweight2, suballselection)

        filldict(0, self._content, indexes, axissumx, axissumx2, weight, weight2, None)
            
        for j in range(len(self._destination[0])):
            self._destination[0][j] = None

    def __add__(self, other):
        if not isinstance(other, Hist):
            raise TypeError("histograms can only be added to other histograms")

        if self._group + self._fixed + self._profile != other._group + other._fixed + other._profile:
            raise TypeError("histograms can only be added to other histograms with the same axis specifications")

        def add(selfcontent, othercontent):
            if selfcontent is None and othercontent is None:
                return None

            elif selfcontent is None:
                return Hist._copycontent(othercontent)

            elif othercontent is None:
                return Hist._copycontent(selfcontent)

            elif isinstance(selfcontent, numpy.ndarray) and isinstance(othercontent, numpy.ndarray):
                return selfcontent + othercontent

            else:
                assert isinstance(selfcontent, dict) and isinstance(othercontent, dict)
                out = {}
                for n in selfcontent:
                    if n in othercontent:
                        out[n] = add(selfcontent[n], othercontent[n])
                    else:
                        out[n] = selfcontent[n]
                for n in othercontent:
                    if n not in selfcontent:
                        out[n] = othercontent[n]
                return out

        out = self.__class__.__new__(self.__class__)
        out.__dict__.update(self.__dict__)
        out._content = add(self._content, other._content)
        return out

    def __iadd__(self, other):
        if not isinstance(other, Hist):
            raise TypeError("histograms can only be added to other histograms")

        if self._group + self._fixed + self._profile != other._group + other._fixed + other._profile:
            raise TypeError("histograms can only be added to other histograms with the same axis specifications")

        def add(selfcontent, othercontent):
            assert isinstance(selfcontent, dict) and isinstance(othercontent, dict)
            for n in selfcontent:
                if n in othercontent:
                    if isinstance(selfcontent[n], numpy.ndarray):
                        selfcontent[n] += othercontent[n]
                    else:
                        add(selfcontent[n], othercontent[n])
            for n in othercontent:
                if n not in selfcontent:
                    selfcontent[n] = Hist._copycontent(othercontent[n])

        if other._content is None:
            pass

        elif self._content is None:
            self._content = Hist._copycontent(other._content)

        elif isinstance(self._content, numpy.ndarray):
            self._content += other._content

        else:
            add(self._content, other._content)

    @staticmethod
    def group(by="source", **hists):
        if any(not isinstance(x, Hist) for x in hists.values()):
            raise TypeError("only histograms can be grouped")

        axis = None
        for x in hists.values():
            if axis is None:
                axis = x._group + x._fixed + x._profile
            elif axis != x._group + x._fixed + x._profile:
                raise TypeError("histograms can only be grouped with the same axis specifications")

        if axis is None:
            raise ValueError("at least one histogram must be provided")

        if histbook.axis.groupby(by) in axis:
            raise ValueError("groupby({0}) already exists in these histograms; use hist.togroup(other) to add to a group".format(repr(by)))

        weight = None
        for x in hists.values():
            if weight is None:
                weight = x._weight
            elif weight != x._weight:
                weight = None
                break

        defs = {}
        for x in hists.values():
            defs.update(x._defs)

        out = Hist(*([histbook.axis.groupby(by)] + [x.relabel(x._original) for x in self._group + self._fixed + self._profile]), weight=weight, defs=defs)
        for n, x in hists.items():
            out._content[n] = Hist._copycontent(x._content)
        return out

    def togroup(**hists):
        if len(self._group) == 0 or not isinstance(self._group[0], histbook.axis.groupby):
            raise ValueError("togroup can only be used on histograms whose first axis is a groupby")

        if any(not isinstance(x, Hist) for x in hists.values()):
            raise TypeError("only histograms can be grouped")

        for x in hists.values():
            if self._group[1:] + self._fixed + self._profile != x._group + x._fixed + x._profile:
                raise TypeError("histograms can only be grouped with the same axis specifications")

        def add(selfcontent, othercontent):
            assert isinstance(selfcontent, dict) and isinstance(othercontent, dict)
            for n in selfcontent:
                if n in othercontent:
                    if isinstance(selfcontent[n], numpy.ndarray):
                        selfcontent[n] += othercontent[n]
                    else:
                        add(selfcontent[n], othercontent[n])
            for n in othercontent:
                if n not in selfcontent:
                    selfcontent[n] = Hist._copycontent(othercontent[n])

        for n, x in hists.items():
            if n in self._content:
                add(self._content[n], other._content)
            else:
                self._content[n] = Hist._copycontent(other._content)
