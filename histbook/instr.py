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

import functools

import histbook.expr

class CallGraphNode(object):
    def __init__(self, goal):
        self.goal = goal
        self.clear()

    def clear(self):
        self.requires = set()
        self.requiredby = set()
        self.numrequiredby = 0
        
    def __repr__(self):
        return "<CallGraphNode for {0}>".format(repr(str(self.goal)))

    def __hash__(self):
        return hash((CallGraphNode, self.goal))

    def __eq__(self, other):
        return isinstance(other, CallGraphNode) and self.goal == other.goal

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return self.goal < other.goal
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def grow(self, table):
        if self not in table:
            table[self] = self

        if isinstance(self.goal, (histbook.expr.Const, histbook.expr.Name, histbook.expr.Predicate)):
            pass

        elif isinstance(self.goal, histbook.expr.Call):
            for arg in self.goal.args:
                if not isinstance(arg, histbook.expr.Const):
                    node = CallGraphNode(arg)
                    if node not in table:
                        table[node] = node
                    else:
                        node = table[node]
                    self.requires.add(node)
                    node.requiredby.add(self)
                    node.grow(table)

        else:
            raise AssertionError(repr(self.goal))

        self.numrequiredby += 1

    def sources(self, table):
        if isinstance(self.goal, histbook.expr.Const):
            return set()

        elif isinstance(self.goal, (histbook.expr.Name, histbook.expr.Predicate)):
            return set([self])

        elif isinstance(self.goal, histbook.expr.Call):
            out = set()
            for arg in self.goal.args:
                if not isinstance(arg, histbook.expr.Const):
                    node = table[CallGraphNode(arg)]
                    out.update(node.sources(table))
            return out

        else:
            raise NotImplementedError

    def rename(self, names):
        return self.goal.rename(names)

def totree(expr):
    def linear(fcn, args):
        if len(args) == 1:
            return args[0]
        return histbook.expr.Call(fcn, args[0], linear(fcn, args[1:]))

    def duplicates(fcn, args):
        if len(args) == 1:
            return args[0]

        uniques = set(args)
        if len(uniques) == len(args):
            return reduce(fcn, args)
        else:
            newargs = []
            for x in sorted(uniques):
                newargs.append(linear(fcn, (x,) * args.count(x)))
            return reduce(fcn, tuple(newargs))

    def reduce(fcn, args):
        if len(args) == 1:
            return args[0]

        left = args[:len(args) // 2]
        right = args[len(args) // 2:]

        if len(left) == 0:
            return reduce(fcn, right)
        if len(right) == 0:
            return reduce(fcn, left)

        if len(left) == 1:
            left, = left
        else:
            left = reduce(fcn, left)

        if len(right) == 1:
            right, = right
        else:
            right = reduce(fcn, right)

        return histbook.expr.Call(fcn, left, right)

    if isinstance(expr, (histbook.expr.Const, histbook.expr.Name, histbook.expr.Predicate)):
        return expr

    elif isinstance(expr, histbook.expr.Call):
        return histbook.expr.Call(expr.fcn, *(totree(x) for x in expr.args))

    elif isinstance(expr, histbook.expr.Relation):
        if expr.cmp == "==":
            return histbook.expr.Call("numpy.equal", totree(expr.left), totree(expr.right))

        elif expr.cmp == "!=":
            return histbook.expr.Call("numpy.not_equal", totree(expr.left), totree(expr.right))

        elif expr.cmp == "<":
            return histbook.expr.Call("numpy.less", totree(expr.left), totree(expr.right))

        elif expr.cmp == "<=":
            return histbook.expr.Call("numpy.less_equal", totree(expr.left), totree(expr.right))

        elif expr.cmp == "in":
            return histbook.expr.Call("numpy.isin", totree(expr.left), totree(expr.right))

        elif expr.cmp == "not in":
            return histbook.expr.Call("numpy.logical_not", histbook.expr.Call("numpy.isin", totree(expr.left), totree(expr.right)))

        else:
            raise AssertionError(repr(expr.cmp))

    elif isinstance(expr, histbook.expr.PlusMinus):
        out = None
        if len(expr.pos) > 0:
            out = reduce("numpy.add", tuple(totree(x) for x in expr.pos))

        if expr.const != expr.identity or out is None:
            if out is None:
                out = histbook.expr.Const(expr.const)
            else:
                out = histbook.expr.Call("numpy.add", out, histbook.expr.Const(expr.const))

        if len(expr.neg) > 0:
            out = histbook.expr.Call("numpy.subtract", out, reduce("numpy.add", tuple(totree(x) for x in expr.neg)))

        return out

    elif isinstance(expr, histbook.expr.TimesDiv):
        out = None
        if len(expr.pos) > 0:
            out = duplicates("numpy.multiply", tuple(totree(x) for x in expr.pos))

        if expr.const != expr.identity or out is None:
            if out is None:
                out = histbook.expr.Const(expr.const)
            else:
                out = histbook.expr.Call("numpy.multiply", out, histbook.expr.Const(expr.const))

        if len(expr.neg) > 0:
            out = histbook.expr.Call("numpy.true_divide", out, duplicates("numpy.multiply", tuple(totree(x) for x in expr.neg)))

        return out

    elif isinstance(expr, histbook.expr.LogicalOr):
        return reduce("numpy.logical_or", tuple(totree(x) for x in expr.args))

    elif isinstance(expr, histbook.expr.LogicalAnd):
        return reduce("numpy.logical_and", tuple(totree(x) for x in expr.args))

    else:
        raise AssertionError(expr)

class CallGraphGoal(CallGraphNode):
    def __init__(self, goal):
        super(CallGraphGoal, self).__init__(totree(goal))
        self.original = goal

def sources(goals, table):
    return functools.reduce(set.union, (x.sources(table) for x in goals), set())

def walkdown(sources):
    seen = set()
    def recurse(node):
        if node not in seen:
            seen.add(node)
            yield node

            pairs = [(x.numrequiredby, x) for x in node.requiredby]
            pairs.sort(reverse=True)
            for num, x in pairs:
                if all(y in seen for y in x.requires):
                    for y in recurse(x):
                        yield y

    for source in sources:
        for x in recurse(source):
            yield x

# def walkdown(sources):
#     seen = set()
#     whenready = []
#     def recurse(node):
#         if node not in seen:
#             seen.add(node)
#             whenready.append(node)

#         notready = []
#         for trial in whenready:
#             if all(x in seen for x in trial.requires):
#                 yield trial
#             else:
#                 notready.append(trial)
#         del whenready[:]
#         whenready.extend(notready)

#         pairs = [(x.numrequiredby, x) for x in node.requiredby]
#         pairs.sort(reverse=True)
#         for num, x in pairs:
#             for y in recurse(x):
#                 yield y

#     for source in sources:
#         for x in recurse(source):
#             yield x

class Instruction(object): pass

class Param(Instruction):
    def __init__(self, name, extern):
        self.name = name
        self.extern = extern

    def __repr__(self):
        return "Param({0}, {1})".format(repr(self.name), repr(self.extern))

class Assign(Instruction):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __repr__(self):
        return "Assign({0}, {1})".format(repr(self.name), repr(str(self.expr)))

class Export(Instruction):
    def __init__(self, name, goal):
        self.name = name
        self.goal = goal

    def __repr__(self):
        return "Export({0}, {1})".format(repr(self.name), repr(str(self.goal)))

class Delete(Instruction):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Delete({0})".format(repr(self.name))

def instructions(sources, goals):
    live = {}
    names = {}
    namenum = [0]
    def newname(node):
        name = "x{0}".format(namenum[0])
        namenum[0] += 1
        live[name] = node
        return name

    nodes = list(walkdown(sources))
    for i, node in enumerate(nodes):
        if isinstance(node.goal, histbook.expr.Const):
            pass

        elif isinstance(node.goal, (histbook.expr.Name, histbook.expr.Predicate)):
            name = newname(node)
            yield Param(name, node.goal.value)
            names[node.goal] = name

        elif isinstance(node.goal, histbook.expr.Call):
            name = newname(node)
            yield Assign(name, node.goal.rename(names))
            names[node.goal] = name

        else:
            raise NotImplementedError

        if node in goals:
            yield Export(name, node.goal)

        dead = []
        for n, x in live.items():
            if not any(x in nodes[j].requires for j in range(i + 1, len(nodes))):
                dead.append(n)
        for n in dead:
            del live[n]
            yield Delete(n)

# def show(goals):
#     numbers = {}
#     order = []
#     def recurse(node):
#         for x in node.requires:
#             recurse(x)
#         if node not in numbers:
#             number = numbers[node] = len(numbers)
#             order.append(node)
#     for goal in goals:
#         recurse(goal)
#     for node in order:
#         print("#{0:<3d} requires {1:<10s} requiredby {2:<10s} ({3} total) for {4}".format(numbers[node], " ".join(map(repr, sorted(numbers[x] for x in node.requires))), " ".join(map(repr, sorted(numbers[x] for x in node.requiredby))), node.numrequiredby, repr(str(node.goal))))
