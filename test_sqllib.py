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

import os
import sqlite3
import unittest

import sqllib



class TestConverting(unittest.TestCase):
    """
    Basically if we're given sql that uses
    different param styles than what is supported
    for a dbapi driver we want to convert that sql
    to the current drivers paramstyle.

    """


class TestDetectingParamstyle(unittest.TestCase):
    qmark = "select * from table where id = ?"
    qmark_false_positive = "select * from table where name like '?'"
    numeric = "select * from table where id = :1"
    numeric_false_positive = "select * from table where name like ':1'"
    # numeric2 not in pep-249, is it just a sqlite thing?
    numeric2 = "select * from table where id = $1"
    numeric2_false_positive = "select * from table where name like '$1'"
    named = "select * from table where id = :name"
    named_false_positive = "select * from table where name like ':name'"
    format = "select * from table where id = %s"
    format_false_positive = "select * from table where name like '%s'"
    pyformat = "select * from table where id = %(name)s"
    pyformat_false_positive = "select * from table where name like '%(name)s'"

    # this is just one of many possible combinations
    # that needs to raise some kind of invalid sql exception
    conflicting = "select * from table where name = ? and value = %s"

    def test_qmark(self):
        style = sqllib.detect_paramstyle(self.qmark)
        self.assertEqual(style, "qmark")

    def test_qmark_false_positive(self):
        style = sqllib.detect_paramstyle(self.qmark_false_positive)
        self.assertEqual(style, None)

    def test_numeric(self):
        style = sqllib.detect_paramstyle(self.numeric)
        self.assertEqual(style, "numeric")

    def test_numeric_false(self):
        style = sqllib.detect_paramstyle(self.numeric_false_positive)
        self.assertEqual(style, None)

    def test_numeric2(self):
        style = sqllib.detect_paramstyle(self.numeric2)
        self.assertEqual(style, "numeric")

    def test_numeric2_false(self):
        style = sqllib.detect_paramstyle(self.numeric2_false_positive)
        self.assertEqual(style, None)

    def test_named(self):
        style = sqllib.detect_paramstyle(self.named)
        self.assertEqual(style, "named")

    def test_named_false(self):
        style = sqllib.detect_paramstyle(self.named_false_positive)
        self.assertEqual(style, None)

    def test_format(self):
        style = sqllib.detect_paramstyle(self.format)
        self.assertEqual(style, "format")

    def test_format_false(self):
        style = sqllib.detect_paramstyle(self.format_false_positive)
        self.assertEqual(style, None)

    def test_pyformat(self):
        style = sqllib.detect_paramstyle(self.pyformat)
        self.assertEqual(style, "pyformat")

    def test_pyformat_false(self):
        style = sqllib.detect_paramstyle(self.pyformat_false_positive)
        self.assertEqual(style, None)



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

[onearg:id]
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

    def test_libraryFromLinesRaw(self):
        """To get the raw SQL query it's just

        lib.<query name>.raw

        """
        lib = self._load_library(self.simple)
        self.assertEqual(lib.sym.raw, "select 1")

    def test_libraryWithArgs(self):
        lib = self._load_library(self.with_arguments)
        self.assertTrue(hasattr(lib, "onearg"),
                        "lib should have a 'onearg:id' attribute")
        self.assertEqual(lib.onearg.__name__, "onearg")
        self.assertEqual(lib.onearg.__doc__,
                         "select * from greetings where id = $1\n\n")
        lib.connect(self.connection)
        self.assertEqual(lib.onearg(1), [(1, 1, u'hello world')])

    def test_libraryWithArgs2(self):
        lib = self._load_library(self.with_arguments)
        self.assertTrue(hasattr(lib, "onearg"),
                        "lib should have a 'onearg:id' attribute")
        self.assertEqual(lib.onearg.__name__, "onearg")
        self.assertEqual(lib.onearg.__doc__,
                         "select * from greetings where id = $1\n\n")
        lib.connect(self.connection)
        self.assertEqual(lib.onearg(2), [(2, 1, u'yo')])

    def test_parse_simple(self):
        preface, blocks = sqllib.Library._parse_blocks([s + "\n" for s in self.simple.splitlines()])
        self.assertEqual(preface, "\n\npreface\n\n\n")
        self.assertEqual(dict((b.name, b.statements) for b in blocks.values()),
                         {"sym":["select 1\n", "\n"]})

    def test_parse_multiple(self):
        preface, blocks = sqllib.Library._parse_blocks([s + "\n" for s in self.multiple.splitlines()])
        self.assertEqual(preface, "\n\npreface\n\n\n")
        self.assertEqual(dict((b.name, b.statements) for b in blocks.values()),
                         {"sym1":["select 1\n", "\n"],
                          "sym2":["select 2\n", "\n"]})

    def test_parse_with_arguments(self):
        preface, blocks = sqllib.Library._parse_blocks(
            [s + "\n" for s in self.with_arguments.splitlines()])
        self.assertEqual(preface, "\n\npreface\n\n\n")
        self.assertEqual(dict((b.name, b.statements) for b in blocks.values()),
                         {"onearg":["select * from greetings where id = $1\n", "\n"]})


class TestLibraryFromFile(unittest.TestCase):
    def setUp(self):
        self.root = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(self.root, "greetings.sql")
        self.connection = sqlite3.Connection(":memory:")

    def test_load_file(self):
        lib = sqllib.Library.from_path(self.filepath)
        lib.connect(self.connection)
        #self.assertEqual(lib.create_greetings.__doc__, "")
        print lib.create_greetings
        lib.create_greetings()
        lib.create_languages()
        lib.add_language(1, "en")
        lib.add_greeting(1, 1, "hello world")
        results = lib.get_greeting(1)
        self.assertEqual(results, [(1, 1, u'hello world')])


class TestLibraryReloadsOnFileChange(unittest.TestCase):
    def setUp(self):
        self.root = os.path.dirname(os.path.abspath(__file__))
        self.dir = "/tmp/test"
        self.filepath = os.path.join(self.dir, "test.sql")
        try:
            os.mkdir("/tmp/test")
        except OSError:
            pass
        with open(self.filepath, "w") as f:
            f.write("this is a test file\n\n")
        self.connection = sqlite3.Connection(":memory:")

    def test_file_reloads(self):
        lib = sqllib.Library.from_path(self.filepath)
        self.assertTrue('sym1' not in dir(lib))
        self.assertTrue('sym2' not in dir(lib))
        with open(self.filepath, "w") as f:
            f.write("""
[sym1]
select 1

[sym2]
select 2
"""
                    )
        lib.reload()
        self.assertTrue('sym1' in dir(lib))
        self.assertTrue('sym2' in dir(lib))
