sqllib
===============

Sometimes you want to try to separate SQL from Python code but you're not interested
in using a real ORM.

Basically you'd just like to better organize and delineate your SQL and Python.

`sqllib` is a simple python library that attempts to do that by allowing you to
load up `*.sql` files from within your Python code.  It depends on some special markers in the sql files to give each query a name addressable from Python.

sqllib "hello world" example
=================================

Imagine you have a couple simple tables (for convenience I'm assuming SQLite but `sqllib`
should work with any Python DBAPI-compatible database.  Anyway, let's say you have tables
like this:

```
# example database schema:
create table greetings (id int, language int, greeting text);
create table languages (id int, name text);
```

Now you might have a very simple script to query those tables with Python and SQL combined that looks like this:

```
# hello.py
import sqllite3

get_all_greetings = """select * from greetings"""

connection = sqlite3.connect("mydb")
cursor = connection.cursor()
cursor.execute(get_all_greetings)
for row in cursor.fetchall():
    print row
```

At this point we're obviously not very complicated as we have no parameters for the SQL queries
and we're really only talking about a single trivial select statement as well, but as queries get larger and more more complicated you end up with potentially a lot of SQL along side your python code and intertwined with it.

Some folks find this really messy and want to be able to extract this SQL into its own place.

So `sqllib` would let you do the following:

First, you might want to create a directory structure for all your SQL files:

```
mkdir sql
touch greetings.sql
```

Next, actually create one or more SQL files and put stuff in 'em:

```
-- greetings.sql

[create_greetings]
create table greetings (id int, language int, greeting text)

[add_greeting:id,language,greeting]
insert into greetings (id, language, greeting) values (?, ?, ?)

[get_greeting:id]
select * from greetings where id = ?

[create_languages]
create table languages (id int, name text)

[add_language:id,name]
insert into languages (id, name) values (?, ?)

[get_all_greetings]
select * from greetings

```

Now we can update our python script with `sqllib`:

```
# hello_sqllib.py
import sqllite3
import sqllib

sql = sqllib.Library.from_path("sql/greetings.sql")

connection = sqlite3.connect("mydb")
cursor = connection.cursor()
cursor.execute(sql.get_all_greetings.raw)
for row in cursor.fetchall():
    print row
```

Of course, if your needs are pretty simple you can also connect the library to your database
and actually "call" your SQL functions.

```
# hello_sqllib_connect.py
import sqllite3
import sqllib

sql = sqllib.Library.from_path("sql/greetings.sql")
sql.connect(sqlite3.connect("mydb"))
for row in sql.get_all_greetings()
    print row
```

This'll also work for SQL queries with parameters (the `?`, `%s`, or `:1` markers), for example,
after connecting as above one could do:

```
sql.add_language(1, "esperanto")
sql.add_language(2, "english")
sql.create_greeting(1, 2, "Hello World!")
sql.get_greeting(1)[2] == "Hello World!"
```
