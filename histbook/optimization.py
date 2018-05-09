#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
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

# from histbook.expression import Expr, Const, Name, Call, PlusMinus, TimesDiv, LogicalOr, LogicalAnd, Relation, Predicate

class CallGraphNode(object):
    def __init__(self, goal):
        self.goal = goal
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

    def grow(self, table):
        if self not in table:
            table[self] = self

        if isinstance(self.goal, (Const, Name, Predicate)):
            pass

        elif isinstance(self.goal, Call):
            for arg in self.goal.args:
                node = CallGraphNode(arg)
                if node not in table:
                    table[node] = node
                else:
                    node = table[node]
                self.requires.add(node)
                node.requiredby.add(self)
                node.grow(table)

        else:
            raise NotImplementedError

        self.numrequiredby += 1

    def sources(self, table):
        if isinstance(self.goal, Const):
            return set()

        elif isinstance(self.goal, (Name, Predicate)):
            return set([self])

        elif isinstance(self.goal, Call):
            out = set()
            for arg in self.goal.args:
                node = table[CallGraphNode(arg)]
                out.update(node.sources(table))
            return out

        else:
            raise NotImplementedError

    @staticmethod
    def allsources(goals, table):
        return functools.reduce(set.union, (x.sources(table) for x in goals))

    def rename(self, names):
        return self.goal.rename(names)

def walkdown(sources):
    seen = set()
    def recurse(node):
        if node not in seen:
            seen.add(node)
            yield node
            for num, x in sorted((x.numrequiredby, x) for x in node.requiredby):
                if all(y in seen for y in x.requires):
                    for y in recurse(x):
                        yield y
    for source in sources:
        for x in recurse(source):
            yield x

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
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __repr__(self):
        return "Export({0}, {1})".format(repr(self.name), repr(str(self.expr)))

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
        if isinstance(node.goal, Const):
            pass

        elif isinstance(node.goal, (Name, Predicate)):
            name = newname(node)
            yield Param(name, node.goal.value)
            names[node.goal] = name

        elif isinstance(node.goal, Call):
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

def show(goals):
    numbers = {}
    order = []
    def recurse(node):
        for x in node.requires:
            recurse(x)
        if node not in numbers:
            number = numbers[node] = len(numbers)
            order.append(node)
    for goal in goals:
        recurse(goal)

    for node in order:
        print("#{0:<3d} requires {1:<10s} requiredby {2:<10s} ({3} total) for {4}".format(numbers[node], " ".join(map(repr, sorted(numbers[x] for x in node.requires))), " ".join(map(repr, sorted(numbers[x] for x in node.requiredby))), node.numrequiredby, repr(str(node.goal))))

goals = [CallGraphNode(Expr.parse("sqrt(sqrt(x))")),
         CallGraphNode(Expr.parse("sqrt(sqrt(y))")),
         CallGraphNode(Expr.parse("exp(sqrt(y))")),
         CallGraphNode(Expr.parse("x")),
         CallGraphNode(Expr.parse("y")),
         CallGraphNode(Expr.parse("atan2(sqrt(x), sqrt(y))"))]

table = {}
for x in goals:
    x.grow(table)

show(goals)
