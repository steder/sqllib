#-*- test-case-name: threadbare.tests.test_sqllib
"""
Libraries are intended to allow the programmer to isolate and manage SQL outside
of a system's code-flow. It provides a means to construct the basic Python
interfaces to a sql based application.

"""
import collections
import functools
import os
import re


def detect_paramstyle(sql):
    string_literals = re.compile(r"'.*?'")
    named = re.compile(r".*:[a-zA-Z]+.*")
    pyformat = re.compile(r".*%(.*?)s.*")
    sql = string_literals.sub("", sql)
    if "?" in sql:
        return "qmark"
    elif "$1" in sql or ":1" in sql:
        return "numeric"
    elif named.match(sql):
        return "named"
    elif "%s" in sql:
        return "format"
    elif pyformat.match(sql):
        return "pyformat"


class SqlBlock(object):
    """
    Simple wrapper around a block of SQL
    """
    def __init__(self, name, args=None, kwargs=None):
        self.statements = []
        self.name = name
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else {}


class LibraryDisconnected(Exception):
    """
    Raised whenever we try to run sql without first connecting
    the library to the database.
    """


class Library(object):
    """
    """
    def __init__(self, preface, blocks, path=None):
        self.path = path
        if self.path:
            self.modified = os.stat(path).st_mtime
        self.connection = None
        self._load_library(preface, blocks)

    def _load_library(self, preface, blocks):
        self.__doc__ = "%s\n\n%s"%(preface, self.__doc__)
        for blockName, block in blocks.items():
            body = "".join(block.statements)
            #if "$1" in body or "?" in body or ":1" in body:
            if block.args and block.kwargs:
                print 'defining args,kwargs'
                def sql(body, *args, **kwargs):
                    print "running:", body, args, kwargs
                    # TODO: the function signature should be enforced
                    if not self.connection:
                        raise LibraryDisconnected()
                    return self.connection.cursor().execute(body, args, kwargs).fetchall()
            elif not block.args and block.kwargs:
                print 'defining just kwargs'
                def sql(body, **kwargs):
                    print "running:", body, kwargs
                    # TODO: the function signature should be enforced
                    if not self.connection:
                        raise LibraryDisconnected()
                    return self.connection.cursor().execute(body, kwargs).fetchall()
            elif block.args and not block.kwargs:
                print 'defining just args'
                def sql(body, *args):
                    print "running:", body, args
                    # TODO: the function signature should be enforced
                    if not self.connection:
                        raise LibraryDisconnected()
                    return self.connection.cursor().execute(body, args).fetchall()
            else:
                print 'defining no args'
                def sql(body):
                    print "running:", body
                    if not self.connection:
                        raise LibraryDisconnected()
                    return self.connection.cursor().execute(body).fetchall()

            sql.__name__ = blockName
            sql.__doc__ = """%s"""%(body)
            wrapped = functools.update_wrapper(functools.partial(sql, body), sql)

            setattr(self, blockName, wrapped)

    def reload(self):
        """
        Only applies if this has `path` associated with it
        """
        if self.path:
            with open(self.path, "r") as libfile:
                lines = libfile.readlines()
            self._load_library(*self._parse_blocks(lines))

    def connect(self, connection):
        self.connection = connection

    @classmethod
    def _parse_blocks(cls, lines):
        blocks = {}

        prefaceLines = []
        currentBlockId = None

        for line in lines:
            #print "line:", line
            l = line.strip()
            if l.startswith("[") and l.endswith("]"):
                #print "new block:", line
                # new block:
                blockHeader = line.strip().strip("[]")
                parts = blockHeader.split(":")
                currentBlockId = parts[0]
                if len(parts) > 1:
                    args = parts[1:]
                else:
                    args = []
                if currentBlockId not in blocks:
                    blocks[currentBlockId] = SqlBlock(currentBlockId, args=args)
            elif currentBlockId is None:
                prefaceLines.append(line)
            else:
                #print "Adding to block:", line
                blocks[currentBlockId].statements.append(line)

        return "\n".join(prefaceLines), blocks

    @classmethod
    def from_lines(cls, lines, **kwargs):
        preface, blocks = cls._parse_blocks(lines)
        return cls(preface, blocks, **kwargs)

    @classmethod
    def from_string(cls, string, **kwargs):
        lines = [s + "\n" for s in string.splitlines()]
        return cls.from_lines(lines, **kwargs)

    @classmethod
    def from_path(cls, path):
        with open(path, "r") as libfile:
            lines = libfile.readlines()
        return cls.from_lines(lines, path=path)
