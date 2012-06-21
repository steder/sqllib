
import sqlite3
from twisted.trial import unittest

from threadbare.storage import sqllib



class TestLibrary(unittest.TestCase):
    def setUp(self):
        self.simple = """
preface

[sym]
select 1

"""

        self.multiple = """
preface

[sym1]
select 1

[sym2]
select 2

"""

        self.with_arguments = """
preface

[onearg]
select * from test where id = $1

"""
        self.setupDatabase()

    def setupDatabase(self):
        self.connection = sqlite3.Connection(":memory:")
        self.connection.cursor().execute("create table test (id int, n int, description text)")
        self.connection.cursor().execute("insert into test (id, n, description) values (1, 1, 'hello')")
        self.connection.cursor().execute("insert into test (id, n, description) values (2, 1, 'world')")

    def _load_library(self, content):
        lib = sqllib.Library.from_string(content)
        return lib

    def test_libraryDoc(self):
        lib = self._load_library(self.simple)
        self.assertEqual(lib.__doc__,
                         "\n\npreface\n\n\n\n\n\n    ")

    def test_libraryFromLines(self):
        lib = self._load_library(self.simple)
        self.assertTrue(hasattr(lib, "sym"),
                        "lib should have a 'sym' attribute")
        self.assertEqual(lib.sym.__name__, "sym")
        self.assertEqual(lib.sym.__doc__,
                         "select 1\n\n")
        lib.connect(self.connection)
        self.assertEqual(lib.sym(), [(1,)])

    def test_libraryWithArgs(self):
        lib = self._load_library(self.with_arguments)
        self.assertTrue(hasattr(lib, "onearg"),
                        "lib should have a 'onearg' attribute")
        self.assertEqual(lib.onearg.__name__, "onearg")
        self.assertEqual(lib.onearg.__doc__,
                         "select * from test where id = $1\n\n")
        lib.connect(self.connection)
        self.assertEqual(lib.onearg(1), [(1, 1, u'hello')])

    def test_parse_simple(self):
        preface, blocks = sqllib.Library._parse_blocks([s + "\n" for s in self.simple.splitlines()])
        self.assertEqual(preface, "\n\npreface\n\n\n")
        self.assertEqual(blocks, {"sym":["select 1\n", "\n"]})

    def test_parse_multiple(self):
        preface, blocks = sqllib.Library._parse_blocks([s + "\n" for s in self.multiple.splitlines()])
        self.assertEqual(preface, "\n\npreface\n\n\n")
        self.assertEqual(blocks, {"sym1":["select 1\n", "\n"],
                                  "sym2":["select 2\n", "\n"]})

    def test_parse_with_arguments(self):
        preface, blocks = sqllib.Library._parse_blocks(
            [s + "\n" for s in self.with_arguments.splitlines()])
        self.assertEqual(preface, "\n\npreface\n\n\n")
        self.assertEqual(blocks,
                         {"onearg":["select * from test where id = $1\n", "\n"]})

