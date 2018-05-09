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

from histbook.expression import Expr, Const, Name, Call, PlusMinus, TimesDiv, LogicalOr, LogicalAnd, Relation, Predicate

class CallGraphNode(object):
    def __init__(self, goal):
        self.goal = goal
        self.requires = set()
        self.requiredby = set()

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
        print("#{0:<3d} requires {1:<10s} requiredby {2:<10s} for {3}".format(numbers[node], " ".join(repr(numbers[x]) for x in node.requires), " ".join(repr(numbers[x]) for x in node.requiredby), repr(str(node.goal))))

goals = [CallGraphNode(Expr.parse("sqrt(sqrt(x))")), CallGraphNode(Expr.parse("exp(sqrt(x))")), CallGraphNode(Expr.parse("sqrt(x)")), CallGraphNode(Expr.parse("x"))]

table = {}
for x in goals:
    x.grow(table)

show(goals)
