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

import numbers

import histbook.expr
import histbook.instr

import numpy

class Interval(object):
    def __init__(self, low, high, closedlow=True, closedhigh=False):
        self._low = low
        self._high = high
        self._closedlow = closedlow
        self._closedhigh = closedhigh

    def __repr__(self):
        args = [repr(self._low), repr(self._high)]
        if self._closedlow is not True:
            args.append("closedlow={0}".format(self._closedlow))
        if self._closedhigh is not False:
            args.append("closedhigh={0}".format(self._closedhigh))
        return "Interval({0})".format(", ".join(args))

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def closedlow(self):
        return self._closedlow

    @property
    def closedhigh(self):
        return self._closedhigh

    def _num(self, n):
        return "{0:4g}".format(n).strip()

    def __str__(self):
        return "{0}{1}, {2}{3}".format(("[" if self._closedlow else "("), (" " if self._low == float("-inf") else "") + self._num(self._low), self._num(self._high), ("]" if self._closedhigh else ")"))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._low == other._low and self._high == other._high and self._closedlow == other._closedlow and self._closedhigh == other._closedhigh

    def __lt__(self, other):
        if isinstance(other, Interval):
            if isinstance(other, IntervalNaN):
                return True
            else:
                return self._low < other._low
        else:
            return self.__class__ < other.__class__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __gt__(self, other):
        return not self.__lt__(other) and not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __cmp__(self, other):
        if self.__eq__(other):
            return 0
        elif self.__lt__(other):
            return -1
        else:
            return 1

    def __hash__(self):
        return hash((self.__class__, self._low, self._high, self._closedlow, self._closedhigh))

class IntervalNaN(Interval):
    def __init__(self):
        pass

    def __repr__(self):
        return "IntervalNaN()"

    @property
    def low(self):
        return float("nan")

    @property
    def high(self):
        return float("nan")

    @property
    def closedlow(self):
        return True

    @property
    def closedhigh(self):
        return True

    def __str__(self):
        return "{NaN}"

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __lt__(self, other):
        if isinstance(other, Interval):
            return isinstance(other, IntervalNaN)
        else:
            return self.__class__ < other.__class__

    def __hash__(self):
        return hash((self.__class__,))

class IntervalTuple(tuple):
    def __repr__(self):
        return "({0}{1})".format(", ".join(str(x) for x in self), ("," if len(self) == 1 else ""))

class IntervalPair(tuple):
    def __repr__(self):
        return "({0}, {1})".format(str(self[0]), repr(self[1]))

class Axis(object):
    @staticmethod
    def _int(x, n):
        if not isinstance(x, (numbers.Integral, numpy.integer)):
            raise TypeError("{0} must be an integer".format(n))
        else:
            return int(x)

    @staticmethod
    def _nonnegint(x, n):
        if not isinstance(x, (numbers.Integral, numpy.integer)) or x < 0:
            raise TypeError("{0} must be a non-negative integer".format(n))
        else:
            return int(x)

    @staticmethod
    def _real(x, n):
        if not isinstance(x, (numbers.Real, numpy.floating)):
            raise TypeError("{0} must be a real number".format(n))
        else:
            return float(x)

    @staticmethod
    def _bool(x, n):
        if not isinstance(x, (bool, numpy.bool, numpy.bool_)):
            raise TypeError("{0} must be boolean".format(n))
        else:
            return bool(x)

    def __ne__(self, other):
        return not self.__eq__(other)

class GroupAxis(Axis): pass
class FixedAxis(Axis):
    def items(self, content):
        keys = self.keys()
        if len(keys) != len(content):
            raise ValueError("len(keys) is {0} but len(content) is {1}", len(keys), len(content))
        return [IntervalPair(x) for x in zip(keys, content)]

class ProfileAxis(Axis): pass
class RebinFactor(Axis): pass
class RebinSplit(Axis): pass

class groupby(GroupAxis):
    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return "groupby({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

    def relabel(self, label):
        return groupby(label)

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(histbook.expr.Call("histbook.groupby", parsed))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr

    def __hash__(self):
        return hash((self.__class__, self._expr))

    def _select(self, cmp, value, tolerance):
        if cmp == "==":
            return self, lambda x: x == value, None, False
        elif cmp == "!=":
            return self, lambda x: x != value, None, False
        elif cmp == "<":
            return self, lambda x: x < value, None, False
        elif cmp == "<=":
            return self, lambda x: x <= value, None, False
        elif cmp == ">":
            return self, lambda x: x > value, None, False
        elif cmp == ">=":
            return self, lambda x: x >= value, None, False
        elif cmp == "in":
            return self, lambda x: x in value, None, False
        elif cmp == "not in":
            return self, lambda x: x not in value, None, False
        else:
            raise AssertionError(cmp)

    def keys(self, content):
        return [n for n, x in self.items(content)]

    def items(self, content):
        if not isinstance(content, dict):
            raise TypeError("groupby content must be a dict")
        return [IntervalPair((n, content[n])) for n in sorted(content)]

class groupbin(GroupAxis, RebinFactor):
    def __init__(self, expr, binwidth, origin=0, nanflow=True, closedlow=True):
        self._expr = expr
        self._binwidth = self._real(binwidth, "binwidth")
        self._origin = self._real(origin, "origin")
        self._nanflow = self._bool(nanflow, "nanflow")
        self._closedlow = self._bool(closedlow, "closedlow")

    def __repr__(self):
        args = [repr(self._expr), repr(self._binwidth)]
        if self._origin != 0:
            args.append("origin={0}".format(repr(self._origin)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "groupbin({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def binwidth(self):
        return self._binwidth

    @property
    def origin(self):
        return self._origin

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

    def relabel(self, label):
        return groupbin(label, self._binwidth, origin=self._origin, nanflow=self._nanflow, closedlow=self._closedlow)

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(histbook.expr.Call("histbook.groupbin{0}{1}".format("N" if self._nanflow else "_", "L" if self._closedlow else "H"), parsed, histbook.expr.Const(self._binwidth), histbook.expr.Const(self._origin)))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr and self._binwidth == other._binwidth and self._origin == other._origin and self._nanflow == other._nanflow and self._closedlow == other._closedlow

    def __hash__(self):
        return hash((self.__class__, self._expr, self._binwidth, self._origin, self._nanflow, self._closedlow))

    def _rebinfactor(self, factor, content, index):
        assert factor > 0

        newaxis = groupbin(self._expr, float(self._binwidth) / float(factor), origin=self._origin, nanflow=self._nanflow, closedlow=self._closedlow)
        if hasattr(self, "_original"):
            newaxis._original = self._original
        if hasattr(self, "_parsed"):
            newaxis._parsed = self._parsed

        def recurse(j, content):
            if j == index:
                out = {}
                for n, x in content.items():
                    if n == "NaN":
                        out[n] = recurse(j + 1, x)

                    else:
                        index = (n - float(self._origin)) / float(self._binwidth)
                        if self._closedlow:
                            index = int(numpy.floor(index))
                        else:
                            index = int(numpy.ceil(index)) - 1

                        index = index // int(factor)

                        n = index * float(newindex._binwidth) + float(newaxis._origin)
                        if n not in out:
                            out[n] = recurse(j + 1, x)
                        else:
                            out[n] += recurse(j + 1, x)

                return out
                        
            elif isinstance(content, dict):
                return dict((n, recurse(j + 1, x)) for n, x in content.items())

            else:
                return content

        if content is None:
            return newaxis, None
        else:
            return newaxis, recurse(0, content)

    def _select(self, cmp, value, tolerance):
        if value == float("-inf") and cmp == ">=":
            return self, lambda x: x != "NaN", None, False

        elif value == float("-inf") and cmp == ">":
            return self, lambda x: x != "NaN", None, False

        elif value == float("-inf") and cmp == "!=":
            return self, lambda x: x != "NaN", None, False

        elif value == float("inf") and cmp == "<=":
            return self, lambda x: x != "NaN", None, False

        elif value == float("inf") and cmp == "<":
            return self, lambda x: x != "NaN", None, False

        elif value == float("inf") and cmp == "!=":
            return self, lambda x: x != "NaN", None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)) and numpy.isnan(value) and cmp == "!=":
            return self, lambda x: x != "NaN", None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)) and numpy.isnan(value) and cmp == "==":
            return self, lambda x: x == "NaN", None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)):
            close = round((value - float(self._origin)) / float(self._binwidth)) * float(self._binwidth) + float(self._origin)
            if abs(value - close) < tolerance:
                if self._closedlow and cmp == "<":
                    return self, lambda x: x < close, close, False
                elif self._closedlow and cmp == ">=":
                    return self, lambda x: x >= close, close, False
                elif not self._closedlow and cmp == ">":
                    return self, lambda x: x >= close, close, False
                elif not self._closedlow and cmp == "<=":
                    return self, lambda x: x < close, close, False
                else:
                    return None, None, close, True
            else:
                return None, None, close, False
        else:
            return None, None, None, False

    def keys(self, content):
        return IntervalTuple(n for n, x in self.items(content))

    def items(self, content):
        if not isinstance(content, dict):
            raise TypeError("groupbin content must be a dict")
        return [IntervalPair((Interval(n, n + float(self._binwidth), closedlow=self._closedlow, closedhigh=(not self._closedlow)), content[n])) for n in sorted(content)]

class bin(FixedAxis, RebinFactor, RebinSplit):
    def __init__(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._numbins = self._nonnegint(numbins, "numbins")
        self._low = self._real(low, "low")
        self._high = self._real(high, "high")
        if (self._numbins > 0 and self._low >= self._high) or (self._low > self._high):
            raise ValueError("low must not be greater than than high")
        self._underflow = self._bool(underflow, "underflow")
        self._overflow = self._bool(overflow, "overflow")
        self._nanflow = self._bool(nanflow, "nanflow")
        self._closedlow = self._bool(closedlow, "closedlow")
        self._checktot()

    def _checktot(self):
        if self.totbins == 0:
            raise ValueError("at least one bin is required (may be over/under/nanflow)")
        
    def __repr__(self):
        args = [repr(self._expr), repr(self._numbins), repr(self._low), repr(self._high)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "bin({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def numbins(self):
        return self._numbins

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

    def relabel(self, label):
        return bin(label, self._numbins, self._low, self._high, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)

    @property
    def totbins(self):
        return self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + (1 if self._nanflow else 0)

    def split(self):
        splitaxis = split(self._expr, [(float(i) / float(self._numbins)) * (self._high - self._low) + self._low for i in range(self._numbins)] + [self._high], underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)
        if hasattr(self, "_original"):
            splitaxis._original = self._original
        if hasattr(self, "_parsed"):
            splitaxis._parsed = self._parsed
        return splitaxis

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(histbook.expr.Call("histbook.bin{0}{1}{2}{3}".format("U" if self._underflow else "_", "O" if self._overflow else "_", "N" if self._nanflow else "_", "L" if self._closedlow else "H"), parsed, histbook.expr.Const(self._numbins), histbook.expr.Const(self._low), histbook.expr.Const(self._high)))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr and self._numbins == other._numbins and self._low == other._low and self._high == other._high and self._underflow == other._underflow and self._overflow == other._overflow and self._nanflow == other._nanflow and self._closedlow == other._closedlow

    def __hash__(self):
        return hash((self.__class__, self._expr, self._numbins, self._low, self._high, self._underflow, self._overflow, self._nanflow, self._closedlow))

    def _rebinsplit(self, edges, content, index):
        return self.split()._rebinsplit(edges, content, index)

    def _rebinfactor(self, factor, content, index):
        assert factor > 0
        return self._rebinsplit([(float(i) / float(self._numbins)) * (self._high - self._low) + self._low for i in range(0, self._numbins, factor)] + [self._high], content, index)

    def _select(self, cmp, value, tolerance):
        if value == float("-inf") and cmp == ">=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif value == float("inf") and cmp == "<=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)) and numpy.isnan(value) and cmp == "!=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)) and numpy.isnan(value) and cmp == "==":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0), self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + 1), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)):
            scale = float(self._numbins) / float(self._high - self._low)
            edgenum = int(round((value - float(self._low)) * scale))
            close = min(self._numbins, max(0, edgenum)) / scale + float(self._low)

            if abs(value - close) < tolerance:
                out = self.__class__.__new__(self.__class__)
                out.__dict__.update(self.__dict__)

                if self._closedlow and cmp == "<":
                    out._numbins = edgenum
                    out._high = close
                    out._overflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(0, edgenum + (1 if self._underflow else 0)), close, False

                elif self._closedlow and cmp == ">=":
                    out._numbins = self._numbins - edgenum
                    out._low = close
                    out._underflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(edgenum + (1 if self._underflow else 0), self._numbins + (1 if self._underflow else 0) + (1 if out._overflow else 0)), close, False

                elif not self._closedlow and cmp == ">":
                    out._numbins = self._numbins - edgenum
                    out._low = close
                    out._underflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(edgenum + (1 if self._underflow else 0), self._numbins + (1 if self._underflow else 0) + (1 if out._overflow else 0)), close, False

                elif not self._closedlow and cmp == "<=":
                    out._numbins = edgenum
                    out._high = close
                    out._overflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(0, edgenum + (1 if self._underflow else 0)), close, False

                else:
                    return None, None, close, True
            else:
                return None, None, close, False
        else:
            return None, None, None, False

    def keys(self, content=None):
        def i2x(i):
            return (float(i) / float(self._numbins)) * float(self._high - self._low) + float(self._low)
        return IntervalTuple(([Interval(float("-inf"), float(self._low), closedlow=True, closedhigh=(not self._closedlow))] if self.underflow else []) +
                             [Interval(i2x(i), i2x(i + 1), closedlow=self._closedlow, closedhigh=(not self._closedlow)) for i in range(self._numbins)] +
                             ([Interval(float(self._high), float("inf"), closedlow=self._closedlow, closedhigh=True)] if self.overflow else []) +
                             ([IntervalNaN()] if self.nanflow else []))
            
class intbin(FixedAxis, RebinFactor, RebinSplit):
    def __init__(self, expr, min, max, underflow=True, overflow=True):
        self._expr = expr
        self._min = self._int(min, "min")
        self._max = self._int(max, "max")
        self._underflow = self._bool(underflow, "underflow")
        self._overflow = self._bool(overflow, "overflow")
        self._checktot()

    def _checktot(self):
        if self._min > self._max:
            raise ValueError("min must not be greater than max")

    def __repr__(self):
        args = [repr(self._expr), repr(self._min), repr(self._max)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        return "intbin({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    def relabel(self, label):
        return intbin(label, self._min, self._max, underflow=self._underflow, overflow=self._overflow)

    @property
    def numbins(self):
        return self._max - self._min + 1

    @property
    def totbins(self):
        return self.numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)

    def bin(self):
        binaxis = bin(self._expr, self._max - self._min + 1, self._min - 0.5, self._max + 0.5, underflow=self._underflow, overflow=self._overflow, nanflow=False)
        if hasattr(self, "_original"):
            binaxis._original = self._original
        if hasattr(self, "_parsed"):
            binaxis._parsed = self._parsed
        return binaxis

    def split(self):
        return self.bin().split()

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(histbook.expr.Call("histbook.intbin{0}{1}".format("U" if self._underflow else "_", "O" if self._overflow else "_"), parsed, histbook.expr.Const(self._min), histbook.expr.Const(self._max)))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr and self._min == other._min and self._max == other._max and self._underflow == other._underflow and self._overflow == other._overflow

    def __hash__(self):
        return hash((self.__class__, self._expr, self._min, self._max, self._underflow, self._overflow))

    def _rebinsplit(self, edges, content, index):
        return self.bin()._rebinsplit(edges, content, index)

    def _rebinfactor(self, factor, content, index):
        return self.bin()._rebinfactor(edges, content, index)

    def _select(self, cmp, value, tolerance):
        if value == float("-inf") and cmp == ">=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif value == float("-inf") and cmp == ">":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif value == float("inf") and cmp == "<=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif value == float("inf") and cmp == "<":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)):
            if value + tolerance < self._min:
                return None, None, self._min, False
            if value - tolerance > self._max:
                return None, None, self._max, False

            if abs(value - round(value)) < tolerance:
                out = self.__class__.__new__(self.__class__)
                out.__dict__.update(self.__dict__)

                if cmp == "<":
                    out._max = int(round(value)) - 1
                    out._overflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(None, out._max - self._min + (1 if self._underflow else 0) + 1), round(value), False

                elif cmp == "<=":
                    out._max = int(round(value))
                    out._overflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(None, out._max - self._min + (1 if self._underflow else 0) + 1), round(value), False

                elif cmp == ">":
                    out._min = int(round(value)) + 1
                    out._underflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(out._min - self._min + (1 if self._underflow else 0), None), round(value), False

                elif cmp == ">=":
                    out._min = int(round(value))
                    out._underflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(out._min - self._min + (1 if self._underflow else 0), None), round(value), False

                else:
                    return None, None, round(value), True
            else:
                return None, None, round(value), False
        else:
            return None, None, None, False

    def keys(self, content=None):
        return IntervalTuple(([Interval(float("-inf"), int(self._min), closedlow=True, closedhigh=False)] if self.underflow else []) +
                             [i for i in range(int(self._min), int(self._max) + 1)] +
                             ([Interval(int(self._max), float("inf"), closedlow=False, closedhigh=True)] if self.overflow else []))

class split(FixedAxis, RebinFactor, RebinSplit):
    def __init__(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        if isinstance(edges, (numbers.Real, numpy.floating)):
            self._edges = (float(edges),)
        else:
            if len(edges) < 1 or not all(isinstance(x, (numbers.Real, numpy.floating)) for x in edges):
                raise TypeError("edges must be a non-empty list of real numbers")
            self._edges = tuple(sorted(float(x) for x in edges),)
        if len(self._edges) != len(set(self._edges)):
            raise ValueError("edges must all be distinct")
        self._underflow = self._bool(underflow, "underflow")
        self._overflow = self._bool(overflow, "overflow")
        self._nanflow = self._bool(nanflow, "nanflow")
        self._closedlow = self._bool(closedlow, "closedlow")
        self._checktot()

    def _checktot(self):
        if self.totbins == 0:
            raise ValueError("at least one bin is required (may be over/under/nanflow)")

    def __repr__(self):
        args = [repr(self._expr), repr(self._edges)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "split({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def edges(self):
        return self._edges

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

    @property
    def low(self):
        return self._edges[0]

    @property
    def high(self):
        return self._edges[-1]

    def relabel(self, label):
        return split(label, self._edges, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)

    @property
    def numbins(self):
        return len(self._edges) - 1

    @property
    def totbins(self):
        return self.numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + (1 if self._nanflow else 0)

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(histbook.expr.Call("histbook.split{0}{1}{2}{3}".format("U" if self._underflow else "_", "O" if self._overflow else "_", "N" if self._nanflow else "_", "L" if self._closedlow else "H"), parsed, histbook.expr.Const(self._edges)))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr and self._edges == other._edges and self._underflow == other._underflow and self._overflow == other._overflow and self._nanflow == other._nanflow and self._closedlow == other._closedlow

    def __hash__(self):
        return hash((self.__class__, self._expr, self._edges, self._underflow, self._overflow, self._nanflow, self._closedlow))

    def _rebinsplit(self, edges, content, index):
        for x in edges:
            if not x in self._edges:
                raise ValueError("cannot rebin: edge {0} is not in the original edges {1}".format(x, self._edges))

        newaxis = split(self._expr, edges, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)
        if hasattr(self, "_original"):
            newaxis._original = self._original
        if hasattr(self, "_parsed"):
            newaxis._parsed = self._parsed
        
        numbins = len(newaxis._edges) - 1 + (1 if newaxis._underflow else 0) + (1 if newaxis._overflow else 0) + (1 if newaxis._nanflow else 0)

        def recurse(content):
            if isinstance(content, dict):
                return dict((n, recurse(x)) for n, x in content.items())
            else:
                newshape = tuple(numbins if i == index else x for i, x in enumerate(content.shape))
                newcontent = numpy.empty(newshape, dtype=content.dtype)

                oldi, oldi2, newi = 0, 0, 0
                while self._edges[oldi2] < newaxis._edges[0]:
                    oldi2 += 1

                if newaxis._underflow:
                    oldi2 += 1
                    newcontent[[newi if i == index else slice(None) for i, x in enumerate(content.shape)]] = numpy.sum(content[[slice(oldi, oldi2) if i == index else slice(None) for i, x in enumerate(content.shape)]], axis=index)
                    newi += 1

                oldi = oldi2
                if not newaxis._underflow:
                    oldi2 += 1

                for edge in newaxis._edges[1:]:
                    while self._edges[oldi2] < edge:
                        oldi2 += 1
                    if newaxis._underflow:
                        oldi2 += 1

                    newcontent[[newi if i == index else slice(None) for i, x in enumerate(content.shape)]] = numpy.sum(content[[slice(oldi, oldi2) if i == index else slice(None) for i, x in enumerate(content.shape)]], axis=index)
                    newi += 1
                    oldi = oldi2
                    if not newaxis._underflow:
                        oldi2 += 1

                if newaxis._overflow:
                    oldi2 = len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0)
                    newcontent[[newi if i == index else slice(None) for i, x in enumerate(content.shape)]] = numpy.sum(content[[slice(oldi, oldi2) if i == index else slice(None) for i, x in enumerate(content.shape)]], axis=index)
                    newi += 1
                    oldi = oldi2

                if newaxis._nanflow:
                    oldi = len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0)
                    oldi2 = oldi + 1
                    newcontent[[newi if i == index else slice(None) for i, x in enumerate(content.shape)]] = numpy.sum(content[[slice(oldi, oldi2) if i == index else slice(None) for i, x in enumerate(content.shape)]], axis=index)

                return newcontent

        if content is None:
            return newaxis, None
        else:
            return newaxis, recurse(content)

    def _rebinfactor(self, factor, content, index):
        assert factor > 0
        return self._rebinsplit(self.edges[0:-1:factor] + self.edges[-1], content, index)

    def _select(self, cmp, value, tolerance):
        if value == float("-inf") and cmp == ">=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif value == float("inf") and cmp == "<=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)) and numpy.isnan(value) and cmp == "!=":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(0, len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0)), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)) and numpy.isnan(value) and cmp == "==":
            out = self.__class__.__new__(self.__class__)
            out.__dict__.update(self.__dict__)
            out._nanflow = False
            out._checktot()
            return out, slice(len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0), len(self._edges) - 1 + (1 if self._underflow else 0) + (1 if self._overflow else 0) + 1), None, False

        elif isinstance(value, (numbers.Real, numpy.floating, numpy.integer)):
            dist, edgex, edgei = sorted((abs(value - x), x, i) for i, x in enumerate(self._edges))[0]

            if dist < tolerance:
                out = self.__class__.__new__(self.__class__)
                out.__dict__.update(self.__dict__)

                cuti = edgei + (1 if self._underflow else 0)

                if self._closedlow and cmp == "<":
                    out._edges = self._edges[:edgei + 1]
                    out._overflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(0, cuti), edgex, False

                elif self._closedlow and cmp == ">=":
                    out._edges = self._edges[edgei:]
                    out._underflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(cuti, cuti + len(out._edges) + (1 if out._overflow else 0) - 1), edgex, False

                elif not self._closedlow and cmp == ">":
                    out._edges = self._edges[edgei:]
                    out._underflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(cuti, cuti + len(out._edges) + (1 if out._overflow else 0) - 1), edgex, False

                elif not self._closedlow and cmp == "<=":
                    out._edges = self._edges[:edgei + 1]
                    out._overflow = False
                    out._nanflow = False
                    out._checktot()
                    return out, slice(0, cuti), edgex, False

                else:
                    return None, None, edgex, True
            else:
                return None, None, edgex, False
        else:
            return None, None, None, False

    def keys(self, content=None):
        return IntervalTuple(([Interval(float("-inf"), float(self._edges[0]), closedlow=True, closedhigh=(not self._closedlow))] if self.underflow else []) +
                             [Interval(float(low), float(high), closedlow=self._closedlow, closedhigh=(not self._closedlow)) for low, high in zip(self._edges[:-1], self._edges[1:])] +
                             ([Interval(float(self._edges[-1]), float("inf"), closedlow=self._closedlow, closedhigh=True)] if self.overflow else []) +
                             ([IntervalNaN()] if self.nanflow else []))

class cut(FixedAxis):
    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return "cut({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

    def relabel(self, label):
        return cut(label)

    @property
    def numbins(self):
        return 2

    @property
    def totbins(self):
        return self.numbins

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(histbook.expr.Call("histbook.cut", parsed))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr

    def __hash__(self):
        return hash((self.__class__, self._expr))

    def _select(self, cmp, value, tolerance):
        if isinstance(value, (bool, numpy.bool, numpy.bool_)):
            if (cmp == "==" and value == True) or (cmp == "!=" and value == False):
                return _nullaxis(), slice(1, 2), None, False

            elif (cmp == "==" and value == False) or (cmp == "!=" and value == True):
                return _nullaxis(), slice(0, 1), None, False

            else:
                return None, None, None, True
        else:
            return None, None, None, False

    def keys(self, content=None):
        return [False, True]

class _nullaxis(FixedAxis):
    def __repr__(self):
        return "_nullaxis()"

    @property
    def expr(self):
        return histbook.expr.Name("???")

    def relabel(self, label):
        return self

    @property
    def numbins(self):
        return 1

    @property
    def totbins(self):
        return self.numbins

    def _goals(self, parsed=None):
        return []

    def __eq__(self, other):
        return self.__class__ is other.__class__

    def __hash__(self):
        return hash((self.__class__,))

    def _select(self, cmp, value, tolerance):
        return None, None, None, False

    def keys(self):
        return []

class profile(ProfileAxis):
    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return "profile({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

    def relabel(self, label):
        return profile(label)

    def _goals(self, parsed=None):
        if parsed is None:
            parsed = histbook.expr.Expr.parse(self._expr)
        return [histbook.instr.CallGraphGoal(parsed),
                histbook.instr.CallGraphGoal(histbook.expr.Call("numpy.multiply", parsed, parsed))]

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._expr == other._expr

    def __hash__(self):
        return hash((self.__class__, self._expr))
