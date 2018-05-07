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

import unittest

from histbook.expression import *

class TestExpression(unittest.TestCase):
    def runTest(self):
        pass

    def test_const(self):
        self.assertEqual(Expr.parse("None").expr, Const(None))
        self.assertEqual(Expr.parse("True").expr, Const(True))
        self.assertEqual(Expr.parse("False").expr, Const(False))
        self.assertEqual(Expr.parse("1").expr, Const(1))
        self.assertEqual(Expr.parse("'hello'").expr, Const('hello'))
        self.assertEqual(Expr.parse("{}").expr, Const(set()))
        self.assertEqual(Expr.parse("{1, 2, 3}").expr, Const({1, 2, 3}))

    def test_name(self):
        self.assertEqual(Expr.parse("hello").names, ["hello"])
        self.assertEqual(Expr.parse("hello").expr, Name("hello"))

    def test_relation(self):
        self.assertEqual(Expr.parse("0 == x").expr, Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x == 0").expr, Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 != x").expr, Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x != 0").expr, Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 < x").expr, Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x < 0").expr, Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("0 <= x").expr, Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x <= 0").expr, Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("0 > x").expr, Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("x > 0").expr, Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 >= x").expr, Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("x >= 0").expr, Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x in {}").expr, Relation("in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("x in {1, 2, 3}").expr, Relation("in", Name("x"), Const({1, 2, 3})))
        self.assertEqual(Expr.parse("x not in {}").expr, Relation("not in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("x not in {1, 2, 3}").expr, Relation("not in", Name("x"), Const({1, 2, 3})))

    def test_interval(self):
        self.assertEqual(Expr.parse("0 <= x < 3").expr, Interval(Const(0), Const(3), Name("x"), lowclosed=True))
        self.assertEqual(Expr.parse("0 < x <= 3").expr, Interval(Const(0), Const(3), Name("x"), lowclosed=False))
        self.assertEqual(Expr.parse("3 > x >= 0").expr, Interval(Const(0), Const(3), Name("x"), lowclosed=True))
        self.assertEqual(Expr.parse("3 >= x > 0").expr, Interval(Const(0), Const(3), Name("x"), lowclosed=False))

