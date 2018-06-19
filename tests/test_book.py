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

import unittest

import numpy

from histbook.axis import *
from histbook.hist import *
from histbook.book import *

class TestBook(unittest.TestCase):
    def runTest(self):
        pass

    def test_fill(self):
        b = Book()
        b["one"] = Hist(bin("x", 2, 0, 3, underflow=False, overflow=False, nanflow=False))
        b["two"] = Hist(split("x", 1.5, nanflow=False))
        b.fill(x=[1, 1, 1, 2, 2])
        self.assertEqual(b["one"]._content.tolist(), [[3], [2]])
        self.assertEqual(b["two"]._content.tolist(), [[3], [2]])

        b = Book()
        b["one"] = Hist(bin("x", 2, 0, 3, underflow=False, overflow=False, nanflow=False))
        b["two"] = Hist(split("y", 1.5, nanflow=False))
        b.fill(x=[1, 1, 1, 2, 2], y=[1, 1, 1, 2, 2])
        self.assertEqual(b["one"]._content.tolist(), [[3], [2]])
        self.assertEqual(b["two"]._content.tolist(), [[3], [2]])

    def test_hierarchy(self):
        h = Hist(bin("x", 100, -5, 5))
        outer = Book()
        outer["one"] = h
        outer["two/three"] = h
        self.assertEqual(outer["one"], h)
        self.assertEqual(outer["two/three"], h)
        self.assertEqual(outer["two"]["three"], h)
        self.assertEqual(len(outer["two"]), 1)
        del outer["two/three"]
        self.assertEqual(len(outer["two"]), 0)

    def test_match(self):
        h = Hist(bin("x", 100, -5, 5))
        outer = Book()
        outer["one-a"] = h
        outer["one-b"] = h
        outer["one-c"] = h
        outer["two/three-a"] = h
        outer["two/three-b"] = h
        self.assertEqual(len(outer["one*"]), 3)
        self.assertEqual(len(outer["tw*/*"]), 2)

    def test_add(self):
        book1, book2 = Book(), Book()
        book1["a"] = Hist(bin("x", 4, 0, 4), fill=[0, 0, 0])
        book1["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 1])
        book1["d"] = Hist(bin("x", 4, 0, 4), fill=[])
        book2["a"] = Hist(bin("x", 4, 0, 4), fill=[2, 2])
        book2["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 3, 3, 3, 3])
        book2["c"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 2, 3])

        book = book1 + book2
        self.assertEqual(book["a"][:].tolist(), [[0], [3], [0], [2], [0], [0], [0]])
        self.assertEqual(book["b"][:].tolist(), [[0], [2], [2], [0], [4], [0], [0]])
        self.assertEqual(book["d"][:].tolist(), [[0], [0], [0], [0], [0], [0], [0]])
        self.assertEqual(book["c"][:].tolist(), [[0], [1], [1], [1], [1], [0], [0]])

    def test_iadd(self):
        book1, book2 = Book(), Book()
        book1["a"] = Hist(bin("x", 4, 0, 4), fill=[0, 0, 0])
        book1["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 1])
        book1["d"] = Hist(bin("x", 4, 0, 4), fill=[])
        book2["a"] = Hist(bin("x", 4, 0, 4), fill=[2, 2])
        book2["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 3, 3, 3, 3])
        book2["c"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 2, 3])

        book1 += book2
        self.assertEqual(book1["a"][:].tolist(), [[0], [3], [0], [2], [0], [0], [0]])
        self.assertEqual(book1["b"][:].tolist(), [[0], [2], [2], [0], [4], [0], [0]])
        self.assertEqual(book1["d"][:].tolist(), [[0], [0], [0], [0], [0], [0], [0]])
        self.assertEqual(book1["c"][:].tolist(), [[0], [1], [1], [1], [1], [0], [0]])

    def test_mul(self):
        book1 = Book()
        book1["a"] = Hist(bin("x", 4, 0, 4), fill=[0, 0, 0])
        book1["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 1])
        book1["d"] = Hist(bin("x", 4, 0, 4), fill=[])

        book = book1 * 1.5
        self.assertEqual(book["a"][:].tolist(), [[0], [4.5], [0], [0], [0], [0], [0]])
        self.assertEqual(book["b"][:].tolist(), [[0], [1.5], [3], [0], [0], [0], [0]])
        self.assertEqual(book["d"][:].tolist(), [[0], [0], [0], [0], [0], [0], [0]])

    def test_rmul(self):
        book1 = Book()
        book1["a"] = Hist(bin("x", 4, 0, 4), fill=[0, 0, 0])
        book1["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 1])
        book1["d"] = Hist(bin("x", 4, 0, 4), fill=[])

        book = 1.5 * book1
        self.assertEqual(book["a"][:].tolist(), [[0], [4.5], [0], [0], [0], [0], [0]])
        self.assertEqual(book["b"][:].tolist(), [[0], [1.5], [3], [0], [0], [0], [0]])
        self.assertEqual(book["d"][:].tolist(), [[0], [0], [0], [0], [0], [0], [0]])

    def test_imul(self):
        book1 = Book()
        book1["a"] = Hist(bin("x", 4, 0, 4), fill=[0, 0, 0])
        book1["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 1])
        book1["d"] = Hist(bin("x", 4, 0, 4), fill=[])

        book1 *= 1.5
        self.assertEqual(book1["a"][:].tolist(), [[0], [4.5], [0], [0], [0], [0], [0]])
        self.assertEqual(book1["b"][:].tolist(), [[0], [1.5], [3], [0], [0], [0], [0]])
        self.assertEqual(book1["d"][:].tolist(), [[0], [0], [0], [0], [0], [0], [0]])

    def test_group(self):
        book1, book2 = Book(), Book()
        book1["a"] = Hist(bin("x", 4, 0, 4), fill=[0, 0, 0])
        book1["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 1])
        book1["d"] = Hist(bin("x", 4, 0, 4), fill=[])
        book2["a"] = Hist(bin("x", 4, 0, 4), fill=[2, 2])
        book2["b"] = Hist(bin("x", 4, 0, 4), fill=[0, 3, 3, 3, 3])
        book2["c"] = Hist(bin("x", 4, 0, 4), fill=[0, 1, 2, 3])

        book = Book.group(x=book1, y=book2)

        self.assertEqual(book["a"].groupkeys("source"), set(["x", "y"]))
        self.assertEqual(book["b"].groupkeys("source"), set(["x", "y"]))
        self.assertEqual(book["c"].groupkeys("source"), set(["y"]))
        self.assertEqual(book["d"].groupkeys("source"), set(["x"]))

    def test_views(self):
        everything = ChannelsBook(
            mass = SamplesBook(["data", "signal", "background"],
                               SystematicsBook(Hist(bin("x", 5, 0, 5), systematic=[0]),
                                               Hist(bin("x + epsilon", 5, 0, 5), systematic=[1]),
                                               Hist(bin("x - epsilon", 5, 0, 5), systematic=[-1]))),
            truth = SamplesBook(["signal", "background"],
                                Book(par1=Hist(bin("par1", 5, 0, 5)),
                                     par2=Hist(bin("par2", 5, 0, 5)))))

        everything.view("*/data/*").fill(x=numpy.random.uniform(0, 5, 100000), epsilon=numpy.random.normal(0, 0.01, 100000))

        self.assertNotEqual(everything["mass/data/0/0"].table(recarray=False).sum(), 0)
        self.assertEqual(everything["mass/signal/0/0"].table(recarray=False).sum(), 0)
