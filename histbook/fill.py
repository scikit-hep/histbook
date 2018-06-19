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

import numpy

import histbook.calc
import histbook.expr
import histbook.instr

class Fillable(object):
    """Mix-in for objects with a ``fill`` method, like `Hist <histbook.hist.Hist>` and `Book <histbook.hist.Book>`."""

    @property
    def fields(self):
        """Names of fields that must be provided in the ``fill`` method."""

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

    def _showgoals(self):
        self.fields  # for the side-effect of creating self._instructions

        numbers = {}
        order = []
        def recurse(node):
            for x in node.requires:
                recurse(x)
            if node not in numbers:
                number = numbers[node] = len(numbers)
                order.append(node)
        for goal in sorted(self._goals):
            recurse(goal)
        print("goals:")
        print("------")
        for node in order:
            print("#{0:<3d} requires {1:<10s} requiredby {2:<10s} ({3} total) for {4}".format(numbers[node], " ".join(map(repr, sorted(numbers[x] for x in node.requires))), " ".join(map(repr, sorted(numbers[x] for x in node.requiredby))), node.numrequiredby, repr(str(node.goal))))
        print("")
        print("instructions:")
        print("-------------")
        for instruction in self._instructions:
            print(instruction)
        print("")
        
    def _fill(self, arrays):
        self.fields  # for the side-effect of creating self._instructions
        
        length = None
        firstinstruction = None
        firstarray = None
        for instruction in self._instructions:
            if isinstance(instruction, histbook.instr.Param) and not isinstance(instruction.extern, histbook.expr.BroadcastConst):
                try:
                    array = arrays[instruction.extern.value]
                except KeyError:
                    if instruction.extern.value in histbook.expr.Expr.maybeconstants:
                        continue
                    else:
                        raise ValueError("required field {0} not found in fill arguments".format(repr(str(instruction.extern))))

                if not isinstance(array, numpy.ndarray):
                    array = numpy.array(array)
                if array.shape != ():
                    length = array.shape[0]
                    firstinstruction = instruction.name
                    firstarray = array
                    break

        if length is None:
            length = 1

        symbols = {}
        for instruction in self._instructions:
            if isinstance(instruction, histbook.instr.Param):
                if isinstance(instruction.extern, histbook.expr.BroadcastConst):
                    array = numpy.full(length, instruction.extern.value)
                elif instruction.name == firstinstruction:
                    array = firstarray
                else:
                    try:
                        array = arrays[instruction.extern.value]
                    except KeyError:
                        if instruction.extern.value in histbook.expr.Expr.maybeconstants:
                            array = numpy.full(length, histbook.expr.Expr.maybeconstants[instruction.extern.value])
                        else:
                            raise ValueError("required field {0} not found in fill arguments".format(repr(str(instruction.extern))))

                if not isinstance(array, numpy.ndarray):
                    array = numpy.array(array)
                if array.shape == ():
                    array = numpy.full(length, array)

                if length != array.shape[0]:
                    raise ValueError("array {0} has len {1} but other arrays have len {2}".format(repr(str(instruction.extern)), len(array), length))

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
