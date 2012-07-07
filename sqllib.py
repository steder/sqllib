#-*- test-case-name: threadbare.tests.test_sqllib
"""
Libraries are intended to allow the programmer to isolate and manage SQL outside
of a system's code-flow. It provides a means to construct the basic Python
interfaces to a sql based application.

"""
import functools



class LibraryDisconnected(Exception):
    """
    Raised whenever we try to run sql without first connecting
    the library to the database.
    """



class Library(object):
    """
    """
    def __init__(self, preface, blocks):
        self.connection = None
        self.__doc__ = "%s\n\n%s"%(preface, self.__doc__)
        #self._blocks = blocks
        for blockName, lines in blocks.iteritems():
            body = "".join(lines)
            if "$1" in body or "?" in body or ":1" in body:
                def sql(body, *args):
                    print "running:", body, args
                    # TODO: the function signature should be enforced
                    if not self.connection:
                        raise LibraryDisconnected()
                    return self.connection.cursor().execute(body, args).fetchall()
            else:
                def sql(body):
                    print "running:", body
                    if not self.connection:
                        raise LibraryDisconnected()
                    return self.connection.cursor().execute(body).fetchall()
            sql.__name__ = blockName
            sql.__doc__ = """%s"""%(body)
            wrapped = functools.update_wrapper(functools.partial(sql, body), sql)

            setattr(self, blockName, wrapped)

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
                currentBlockId = line.strip().strip("[]")
                if currentBlockId not in blocks:
                    blocks[currentBlockId] = []
            elif currentBlockId is None:
                prefaceLines.append(line)
            else:
                #print "Adding to block:", line
                blocks[currentBlockId].append(line)

        return "\n".join(prefaceLines), blocks

    @classmethod
    def from_lines(cls, lines):
        preface, blocks = cls._parse_blocks(lines)
        return cls(preface, blocks)

    @classmethod
    def from_string(cls, string):
        lines = [s + "\n" for s in string.splitlines()]
        return cls.from_lines(lines)

    @classmethod
    def from_path(cls, path):
        with open(path, "r") as libfile:
            lines = libfile.readlines()
        return cls.from_lines(lines)

