--
-- greetings.sql
--

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
