"""
Tests for sqllib

.. todo::

  To allow folks to use sqllib regardless of the their underlying
  db backend it may make sense to have libraries translate queries
  paramstyle from one to another at load time.

  sqlite supports at least 3 options for substitutions, namely:
   - select * from greetings where id = ?
   - select * from greetings where id = :1
   - select * from greetings where id = $1

  For example, while sqlite supports the above 3 styles
  MySQLdb supports only %s paramstyle.  The problem I ran
  into was using sqlite to help "unit" test some sql that than ran
  against a mysql database in production.

  To make this work I had a to simply do `query = query.replace("?", "%s")`
  before actually doing `cursor.execute(query, args)`.

  I think having libraries manage that should make this better.

"""

import sqlite3
from twisted.trial import unittest

import sqllib




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
select * from greetings where id = $1

"""
        self.setupDatabase()

    def setupDatabase(self):
        self.connection = sqlite3.Connection(":memory:")
        self.connection.cursor().execute("create table greetings (id int, language int, greeting text)")
        self.connection.cursor().execute("insert into greetings (id, language, greeting) values (1, 1, 'hello world')")
        self.connection.cursor().execute("insert into greetings (id, language, greeting) values (2, 1, 'yo')")

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
                         "select * from greetings where id = $1\n\n")
        lib.connect(self.connection)
        self.assertEqual(lib.onearg(1), [(1, 1, u'hello world')])

    def test_libraryWithArgs2(self):
        lib = self._load_library(self.with_arguments)
        self.assertTrue(hasattr(lib, "onearg"),
                        "lib should have a 'onearg' attribute")
        self.assertEqual(lib.onearg.__name__, "onearg")
        self.assertEqual(lib.onearg.__doc__,
                         "select * from greetings where id = $1\n\n")
        lib.connect(self.connection)
        self.assertEqual(lib.onearg(2), [(2, 1, u'yo')])

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
                         {"onearg":["select * from greetings where id = $1\n", "\n"]})

