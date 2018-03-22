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

import ast
import copy
import math
import types

import numpy
import pandas

def _irrbinintervals(edges, closed):
    if len(edges) == 0:
        raise ValueError("at least one bin edge must be provided")
    if closed != "left" and closed != "right":
        raise ValueError("closed must be 'left' for [low, high) or 'right' for (low, high]")
    underflow = pandas.Interval(float("-inf"), edges[0], closed)
    overflow  = pandas.Interval(edges[-1], float("inf"), closed)
    return [underflow] + [pandas.Interval(a, b, closed=closed) for a, b in zip(edges[:-1], edges[1:])] + [overflow]

def _binintervals(numbins, low, high, closed):
    if numbins <= 0:
        raise ValueError("numbins must be at least 1")
    edges = numpy.linspace(low, high, numbins + 1)
    return _irrbinintervals(edges, closed)

def bin(numbins, low, high, expression, closed="left"):
    return _HistogramLayoutBinning([("bin", numbins, low, high, closed, expression)],
                                   [_binintervals(numbins, low, high, closed)],
                                   [expression])

def irrbin(edges, expression, closed="left"):
    return _HistogramLayoutBinning([("irrbin", edges, closed, expression)],
                                   [_irrbinintervals(edges, closed)],
                                   [expression])

def cut(expression):
    return _HistogramLayoutBinning([("cut", expression)],
                                   [["fail", "pass"]],
                                   [expression])

class _HistogramLayout(object):
    def __init__(self, specification, indexes, expressions, columns):
        self._specification = specification
        self._indexes = indexes
        self._expressions = expressions
        self._columns = columns

    def _newcolumn(self, specification, newcolumns):
        columns = list(self._columns)
        for column in newcolumns:
            if column in columns:
                raise ValueError("attempting to attach {0} twice".format(repr(column)))
            if column == "sumw2":
                columns[0] = "sumw"
            columns.append(column)
        return _HistogramLayout(specification, self._indexes, self._expressions, columns)

    def weighted(self):
        return self._newcolumn(self._specification + [("sumw2", "")], ["sumw2"])

    def profile(self, expression):
        return self._newcolumn(self._specification + [("sum", expression), ("sum2", expression)], ["sum({0})".format(expression), "sum2({0})".format(expression)])

    def min(self, expression):
        return self._newcolumn(self._specification + [("min", expression)], ["min({0})".format(expression)])

    def max(self, expression):
        return self._newcolumn(self._specification + [("max", expression)], ["max({0})".format(expression)])

    def minmax(self, expression):
        return self._newcolumn(self._specification + [("min", expression), ("max", expression)], ["min({0})".format(expression), "max({0})".format(expression)])

    def fillable(self, method="python", env={}):
        out = pandas.DataFrame(
            index=pandas.MultiIndex.from_product(self._indexes, names=self._expressions),
            columns=self._columns,
            data=dict((x, float("inf") if x.startswith("min") else float("-inf") if x.startswith("max") else 0.0) for x in self._columns))

        if method == "python":
            fill = _makefill(self._specification, env)
        else:
            raise NotImplementedError("unrecognized fillable method: {0}".format(method))

        out.__dict__["fill"] = types.MethodType(fill, out, out.__class__)
        out.__dict__["fillargs"] = fill.__code__.co_varnames[1:fill.__code__.co_argcount]
        return out

class _HistogramLayoutBinning(_HistogramLayout):
    def __init__(self, specification, indexes, expressions):
        super(_HistogramLayoutBinning, self).__init__(specification, indexes, expressions, ["count"])

    def bin(self, numbins, low, high, expression, closed="left"):
        return _HistogramLayoutBinning(self._specification + [("bin", numbins, low, high, closed, expression)],
                                       self._indexes + [_binintervals(numbins, low, high, closed)],
                                       self._expressions + [expression])

    def irrbin(self, edges, expression, closed="left"):
        return _HistogramLayoutBinning(self._specification + [("irrbin", edges, closed, expression)],
                                       self._indexes + [_irrbinintervals(edges, closed)],
                                       self._expressions + [expression])

    def cut(self, expression):
        return _HistogramLayoutBinning(self._specification + [("cut", expression)],
                                       self._indexes + [["fail", "pass"]],
                                       self._expressions + [expression])

def _symbols(node, inputs, symbols):
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        if node.id not in symbols:
            inputs.append(node.id)
        symbols.add(node.id)
    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        symbols.add(node.id)
    elif isinstance(node, ast.AST):
        for n in node._fields:
            _symbols(getattr(node, n), inputs, symbols)
    elif isinstance(node, dict):
        for x in node.values():
            _symbols(x, inputs, symbols)
    elif isinstance(node, list):
        for x in node:
            _symbols(x, inputs, symbols)

def _newsymbol(symbols):
    trial = None
    while trial is None or trial in symbols:
        trial = "_{0}".format(_newsymbol.n)
        _newsymbol.n += 1
    symbols.add(trial)
    return trial
        
_newsymbol.n = 0

def _wrap(node):
    if isinstance(node, ast.AST):
        if not hasattr(node, "lineno"):
            node.lineno = 1
        if not hasattr(node, "col_offset"):
            node.col_offset = 0
        for n in node._fields:
            _wrap(getattr(node, n))
    elif isinstance(node, dict):
        for x in node.values():
            _wrap(x)
    elif isinstance(node, list):
        for x in node:
            _wrap(x)
    return node
    
def _makefill(specification, env):
    expressions = []
    newspecification = []
    for spec in specification:
        newspecification.append(spec + (ast.parse(spec[-1]).body,))
        expressions.append(newspecification[-1][-1])

    weighted = ("sumw2", "") in specification

    stridemap = {}
    stride = 1
    for i, spec in reversed(list(enumerate(specification))):
        if spec[0] == "bin":
            numbins = int(spec[1])
            stridemap[i] = stride
            stride *= numbins + 2
        elif spec[0] == "irrbin":
            numedges = len(spec[1])
            stridemap[i] = stride
            stride *= numedges + 1
        elif spec[0] == "cut":
            stridemap[i] = stride
            stride *= 2
        elif spec[0] == "sumw2" or spec[0] == "sum" or spec[0] == "sum2" or spec[0] == "min" or spec[0] == "max":
            pass
        else:
            raise AssertionError(spec[0])

    inputs = []
    symbols = set(env)
    _symbols(expressions, inputs, symbols)

    statements = []
    module = ast.parse("def fill(self{0}{1}): REPLACEME".format("".join(", " + x for x in inputs), ", weight=1.0" if weighted else ""))
    module.body[0].body = statements

    floorsym = _newsymbol(symbols)
    ceilsym = _newsymbol(symbols)
    indexsym = _newsymbol(symbols)
    statements.append(_wrap(ast.Assign([ast.Name(indexsym, ast.Store())], ast.Num(0))))

    column = 1
    quantities = {}
    for i, spec in enumerate(newspecification):
        stmts = spec[-1]
        if len(stmts) > 0:
            if not isinstance(stmts[-1], ast.Expr):
                raise SyntaxError("last statement in a quantity must be a pure expression, not {0}".format(repr(spec[-2])))
            if spec[-2] not in quantities:
                quantity = _newsymbol(symbols)
                statements.extend(stmts[:-1])
                statements.append(_wrap(ast.Assign([ast.Name(quantity, ast.Store())], stmts[-1].value)))
                quantities[spec[-2]] = quantity
            else:
                quantity = quantities[spec[-2]]
        else:
            assert spec[0] == "sumw2"

        if spec[0] == "bin":
            numbins = int(spec[1])
            low = float(spec[2])
            high = float(spec[3])
            closed = spec[4]
            statements.extend(ast.parse("""
if {QUANTITY} {GT} {HIGH}:
    {INDEX} += {HIGHSKIP}
elif {QUANTITY} {GT} {LOW}:
    {INDEX} += ({ONE_PLUS}int({FLOOR_OR_CEIL}({FACTOR}*({QUANTITY} - {LOW}))))*{STRIDE}
""".format(QUANTITY=quantity,
           GT=">=" if closed == "left" else ">",
           HIGH=high,
           INDEX=indexsym,
           HIGHSKIP=(numbins + 1)*stridemap[i],
           LOW=low,
           ONE_PLUS="1 + " if closed == "left" else "",
           FLOOR_OR_CEIL=floorsym if closed == "left" else ceilsym,
           FACTOR=numbins/(high - low),
           STRIDE=stridemap[i]
           )).body)

        elif spec[0] == "irrbin":
            edges = map(float, spec[1])
            closed = spec[2]
            chain = []
            for edgei, edge in reversed(list(enumerate(edges))):
                chain.append("""
elif {QUANTITY} {GT} {EDGE}:
    {INDEX} += {SKIP}
""".format(QUANTITY=quantity,
           GT=">=" if closed == "left" else ">",
           EDGE=edge,
           INDEX=indexsym,
           SKIP=(edgei + 1)*stridemap[i]).strip())
            statements.extend(ast.parse("\n".join(chain)[2:]).body)

        elif spec[0] == "cut":
            statements.extend(ast.parse("""
if {QUANTITY}:
    {INDEX} += {SKIP}
""".format(QUANTITY=quantity,
           INDEX=indexsym,
           SKIP=stridemap[i])).body)

        elif spec[0] == "sumw2":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] += weight*weight".format(INDEX=indexsym, COLUMN=column)).body)
            column += 1

        elif spec[0] == "sum":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] += {WEIGHT}{QUANTITY}".format(INDEX=indexsym, COLUMN=column, WEIGHT="weight*" if weighted else "", QUANTITY=quantity)).body)
            column += 1

        elif spec[0] == "sum2":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] += {WEIGHT}{QUANTITY}*{QUANTITY}".format(INDEX=indexsym, COLUMN=column, WEIGHT="weight*" if weighted else "", QUANTITY=quantity)).body)
            column += 1

        elif spec[0] == "min":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] = min(self.values[{INDEX}, {COLUMN}], {QUANTITY})".format(INDEX=indexsym, COLUMN=column, QUANTITY=quantity)).body)
            column += 1

        elif spec[0] == "max":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] = max(self.values[{INDEX}, {COLUMN}], {QUANTITY})".format(INDEX=indexsym, COLUMN=column, QUANTITY=quantity)).body)
            column += 1

        else:
            raise AssertionError(spec[0])

    if weighted:
        statements.extend(ast.parse("self.values[{INDEX}, 0] += weight".format(INDEX=indexsym)).body)
    else:
        statements.extend(ast.parse("self.values[{INDEX}, 0] += 1".format(INDEX=indexsym)).body)

    globs = {floorsym: math.floor, ceilsym: math.ceil}
    globs.update(env)
    exec(compile(module, "<generated by pandhist>", "exec"), globs)
    return globs["fill"]

def hadd(*histograms):
    out = None
    for arg in histograms:                      # first level: for varargs
        if isinstance(arg, pandas.DataFrame):
            arg = [arg]
        for histogram in arg:                   # second level: for iterators (so they don't all have to be in memory)
            if out is None:
                out = histogram.copy()
            else:
                if not numpy.array_equal(out.index, histogram.index):
                    raise ValueError("histogram indexes do not match:\n{0}\n{1}".format(out.index, histogram.index))
                if set(out.columns) != set(histogram.columns):
                    raise ValueError("histogram columns do not match:\n{0}\n{1}".format(sorted(out.columns), sorted(histogram.columns)))
                for column in out.columns:
                    if column.startswith("min"):
                        numpy.minimum(out[column].values, histogram[column].values, out[column].values)
                    elif column.startswith("max"):
                        numpy.maximum(out[column].values, histogram[column].values, out[column].values)
                    else:
                        numpy.add(out[column].values, histogram[column].values, out[column].values)
    return out

def concat(*previously_concatted, **new_to_concat):
    histograms = []

    first = None
    for x in previously_concatted:
        if x.index.names is None or len(x.index.names) == 0 or x.index.names[0] != "source":
            raise ValueError("previously concatted histograms would have 'source' as their first multiindex name")
        if first is None and len(x) > 0:
            y = x.index.get_level_values("source")[0]
            first = x.loc[y]
        elif len(x) > 0:
            y = x.index.get_level_values("source")[0]
            if not numpy.array_equal(first.index, x[y].index):
                raise ValueError("histogram indexes do not match:\n{0}\n{1}".format(first.index, x.index))
            if set(first.columns) != set(x.columns):
                raise ValueError("histogram columns do not match:\n{0}\n{1}".format(sorted(first.columns), sorted(x.columns)))
        histograms.append(x)

    if first is not None:
        if not isinstance(first.index, pandas.MultiIndex):
            first.index = pandas.MultiIndex.from_product([first.index], names=[first.index.name])

    for n, x in new_to_concat.items():
        if x.index.names is not None and "source" in x.index.names:
            raise ValueError("histograms that are new to concat would not have 'source' in their multiindex")
        if first is None:
            first = x
        else:
            if not numpy.array_equal(first.index, x.index):
                raise ValueError("histogram indexes do not match:\n{0}\n{1}".format(first.index, x.index))
            if set(first.columns) != set(x.columns):
                raise ValueError("histogram columns do not match:\n{0}\n{1}".format(sorted(first.columns), sorted(x.columns)))
        histograms.append(pandas.concat([x], keys=[n], names=["source"]))

    return pandas.concat(histograms)

def steps(independent, dependent=None):
    return _PlotLayout("steps", False, independent, dependent, [])

def area(independent, dependent=None):
    return _PlotLayout("area", False, independent, dependent, [])

def lines(independent, dependent=None):
    return _PlotLayout("lines", False, independent, dependent, [])

def points(independent, dependent=None):
    return _PlotLayout("points", False, independent, dependent, [])

class _PlotLayoutErrors(object):
    def errors(self):
        return _PlotLayout(self._rendering, True, self._ind, self._dep, self._splits)

class _PlotLayoutOverlay(object):
    def overlay(self, quantity):
        return _PlotLayout(self._rendering, self._errors, self._ind, self._dep, self._splits + [("overlay", quantity)])

class _PlotLayoutStack(object):
    def stack(self, quantity):
        return _PlotLayout(self._rendering, self._errors, self._ind, self._dep, self._splits + [("stack", quantity)])

class _PlotLayoutRow(object):
    def row(self, quantity):
        return _PlotLayout(self._rendering, self._errors, self._ind, self._dep, self._splits + [("row", quantity)])

class _PlotLayoutColumn(object):
    def column(self, quantity):
        return _PlotLayout(self._rendering, self._errors, self._ind, self._dep, self._splits + [("column", quantity)])

class _PlotLayout(object):
    def __init__(self, rendering, errors, independent, dependent, splits):
        self._rendering = rendering
        self._errors = errors
        self._ind = independent
        self._dep = dependent
        self._splits = splits

        renderings = [r for r, q in splits]
        bases = [_PlotLayout]
        if (rendering == "lines" or rendering == "points") and not errors and not "row" in renderings and not "column" in renderings:
            bases.append(_PlotLayoutErrors)
        if "overlay" not in renderings:
            bases.append(_PlotLayoutOverlay)
        if (rendering == "area" and "stack") not in renderings:
            bases.append(_PlotLayoutStack)
        if "row" not in renderings and not errors:
            bases.append(_PlotLayoutRow)
        if "column" not in renderings and not errors:
            bases.append(_PlotLayoutColumn)
        self.__class__ = type(([self._rendering] + renderings)[-1], tuple(bases), {})

    def data(self, df):
        indnames = [self._ind] + [q for r, q in self._splits]

        if self._dep is None:
            dep = "count"
            if "sumw" in df.columns and "sumw2" in df.columns:
                depnames = ["sumw", "sumw2"]
            else:
                depnames = ["count"]
        else:
            dep = self._dep
            depnames = ["sum({0})".format(dep), "sum2({0})".format(dep)]
            if "sumw" in df.columns and "sumw2" in df.columns:
                depnames.append("sumw")
            else:
                depnames.append("count")
            if depnames[0] not in df.columns or depnames[1] not in df.columns:
                if (dep.startswith("max(") and dep.endswith(")") and dep in df.columns) or (dep.startswith("min(") and dep.endswith(")") and dep in df.columns):
                    if self._errors:
                        raise ValueError("{0} has no error".format(dep))
                    depnames = [dep]
                elif dep.startswith("minmax(") and dep.endswith(")"):
                    depnames = ["min({0})".format(dep[7:-1]), "max({0})".format(dep[7:-1])]
                else:
                    raise ValueError("missing columns named {0}, {1}".format(*depnames))

        summable = df[[n for n in depnames if not n.startswith("min") and not n.startswith("max")]]
        minable = df[[n for n in depnames if n.startswith("min")]]
        maxable = df[[n for n in depnames if n.startswith("max")]]
        summable = summable.sum(level=indnames)
        minable = minable.min(level=indnames)
        maxable = maxable.max(level=indnames)

        plottable = pandas.concat([summable, minable, maxable], 1)

        if self._dep is None:
            if self._errors:
                if "sumw2" in plottable.columns:
                    plottable["error"] = numpy.sqrt(plottable["sumw2"])
                else:
                    plottable["error"] = numpy.sqrt(numpy.absolute(plottable["count"]))
                plottable.replace({"error": {float("nan"): 0.0}}, inplace=True)
        elif depnames[0].startswith("sum("):
            if "sumw" in plottable.columns:
                sumw = plottable["sumw"]
            else:
                sumw = plottable["count"]
            plottable[dep] = plottable[depnames[0]] / sumw
            if self._errors:
                plottable["error"] = numpy.sqrt((plottable[depnames[1]] / sumw) - (numpy.square(plottable[depnames[0]] / sumw)))
        elif depnames[0].startswith("minmax("):
            raise NotImplementedError

        if "sumw" in plottable.columns:
            plottable.rename(columns={"sumw": "count"}, inplace=True)

        plottable.replace([float("-inf"), float("inf")], float("nan"), inplace=True)
        plottable.dropna(inplace=True)

        if self._errors:
            depnames = [dep, "error"]
        else:
            depnames = [dep]

        plottable = pandas.DataFrame(index=plottable.index, columns=depnames, data=plottable)
        colnames = indnames + depnames

        if self._rendering == "steps" or self._rendering == "area":
            noindex = plottable.reset_index(level=indnames)
            noindex[self._ind] = noindex[self._ind].apply(lambda x: x.left)
            noindex.replace({self._ind: {float("-inf"): float("nan")}}, inplace=True)
            noindex.dropna([noindex.columns.tolist().index(self._ind)], inplace=True)
            array = noindex[colnames].values.tolist()

            if self._rendering == "steps":
                mark = {"type": "line", "interpolate": "step-before"}
            else:
                mark = {"type": "area", "interpolate": "step-before"}
                
            encoding = {"x": {"field": self._ind, "type": "quantitative", "scale": {"zero": False}},
                        "y": {"field": colnames[colnames.index(dep)], "type": "quantitative", "axis": {"title": dep}}}
            for r, q in self._splits:
                if r == "overlay":
                    encoding["color"] = {"field": q, "type": "nominal"}
                elif r == "stack":
                    encoding["color"] = {"field": q, "type": "nominal"}
                    encoding["y"]["aggregate"] = "sum"
                    encoding["y"]["axis"]["title"] = "stacked {0}".format(encoding["y"]["axis"]["title"])
                elif r == "row":
                    encoding["row"] = {"field": q, "type": "nominal"}
                elif r == "column":
                    encoding["column"] = {"field": q, "type": "nominal"}

        elif self._rendering == "lines" or self._rendering == "points":
            noindex = plottable.reset_index(level=indnames)
            noindex[self._ind] = noindex[self._ind].apply(lambda x: x.mid)
            noindex.replace({self._ind: {float("-inf"): float("nan"), float("inf"): float("nan")}}, inplace=True)
            noindex.dropna([noindex.columns.tolist().index(self._ind)], inplace=True)

            array = noindex[colnames].values.tolist()

            if self._rendering == "lines":
                mark = {"type": "line", "interpolate": "linear"}
            else:
                mark = {"type": "point", "filled": "true"}
                
            encoding = {"x": {"field": self._ind, "type": "quantitative", "scale": {"zero": False}},
                        "y": {"field": colnames[colnames.index(dep)], "type": "quantitative", "axis": {"title": dep}}}
            for r, q in self._splits:
                if r == "overlay":
                    encoding["color"] = {"field": q, "type": "nominal"}
                elif r == "row":
                    encoding["row"] = {"field": q, "type": "nominal"}
                elif r == "column":
                    encoding["column"] = {"field": q, "type": "nominal"}

        else:
            raise AssertionError(self._rendering)

        data = {"values": [dict(zip(colnames, row)) for row in array]}
        for x in data["values"]:
            x["id"] = 0

        if self._errors:
            errencoding = encoding.copy()
            errencoding["y"] = {"field": "error-down", "type": "quantitative"}
            errencoding["y2"] = {"field": "error-up", "type": "quantitative"}

            return {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
                    "data": data,
                    "layer": [
                        {"mark": mark, "encoding": encoding, "transform": [{"filter": {"field": "id", "equal": 0}}]},
                        {"mark": "rule", "encoding": errencoding, "transform": [
                            {"filter": {"field": "id", "equal": 0}},
                            {"calculate": "datum." + colnames[colnames.index(dep)] + " - datum.error", "as": "error-down"},
                            {"calculate": "datum." + colnames[colnames.index(dep)] + " + datum.error", "as": "error-up"}]}
                    ]}
        else:
            return {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
                    "data": data,
                    "layer": [{
                        "mark": mark,
                        "encoding": encoding,
                        "transform": [{"filter": {"field": "id", "equal": 0}}]}
                    ]}

def overlay(*graphics):
    out = {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
           "data": {"values": []},
           "layer": []}
    usedids = set()
    lastid = 0

    for arg in graphics:                        # first level: for varargs
        if isinstance(arg, dict):
            arg = [arg]
        for graphic in arg:                     # second level: for iterators
            if "hconcat" in graphic or "vconcat" in graphic:
                raise ValueError("cannot overlay concated graphics")

            translate = {}
            observed = set()
            for datum in graphic["data"]["values"]:
                if datum["id"] in usedids:
                    while lastid in usedids:
                        lastid += 1
                    translate[datum["id"]] = lastid
                observed.add(datum["id"])

            def dataid(x):
                return translate.get(x, x)
            
            def transformid(transform):
                transform = copy.deepcopy(transform)
                transform[0]["filter"]["equal"] = translate.get(transform[0]["filter"]["equal"], transform[0]["filter"]["equal"])
                return transform

            # FIXME: this is hyper-specialized to the graphics produced by _PlotLayout
            out["data"]["values"].extend([dict((n, dataid(x) if n == "id" else x) for n, x in datum.items()) for datum in graphic["data"]["values"]])
            out["layer"].extend([{"mark": layer["mark"], "encoding": layer["encoding"], "transform": transformid(layer["transform"])} for layer in graphic["layer"]])

            usedids.update(observed)

    return out

def hconcat(*graphics):
    raise NotImplementedError

def vconcat(*graphics):
    raise NotImplementedError

import vegascope
c = vegascope.LocalCanvas()

h1 = bin(5, 0, 5, "x").fillable()
h1.fill(1)
h1.fill(2)
h1.fill(3)
h1.fill(1)
h1.fill(2)
h1.fill(3)
h1.fill(1)
h1.fill(2)
h1.fill(3)
h1.fill(1)
h1.fill(2)
h1.fill(3)

h2 = bin(5, 0, 5, "x").fillable()
h2.fill(0)
h2.fill(0)
h2.fill(0)
h2.fill(0)
h2.fill(1)
h2.fill(2)
h2.fill(3)
h2.fill(4)
h2.fill(4)
h2.fill(4)
h2.fill(4)

c(overlay(steps("x").data(h1), points("x").errors().data(h2)))
