# The ATBL file format

## Introduction

ATBL is an "assembly language for tabular-like data". It is designed to be
easily and unambiguously parsed. It's primary use is as a format-independent
verification suite for parsers for tabular data.

While ATBL is (sort-of) human readable and writable, being written and read by
humans is not its primary purpose.

This README describes the ATBL file format, version 1.0.0. The repo also
provides a reference implmentation of the parser, written in Python.

## Definitions

In the context of ATBL, a *table* is a (possibly nonempty) list of *rows*. A
*row* is a (possibly nonempty) list of *cells*. A *cell*, finally, is simply an
array of bytes. Note, in particular, that an ATBL-table is not necessarily
rectangular. An *ATBL file* is a UTF-8 text file that encodes a table as defined
above.

In the following text, the terms 'table', 'row' and 'cell' will take the meaning
from these definitions.

## Definition

An ATBL-file is constructed as a series of lines (separated by the either `LF`
or `CRLF`). Each line contains a *command* and possibly an argument to the
command. The command itself is made up of three ASCII letters. If a command has
an argument, both are separated by a single space. ATBL supports the following
commands.

- `ver`: This command specifies the major version of ATBL the file uses. It
  takes an argument. At the moment, the only allowed argument is `1`.
- `rem`: Any line starting with this command is ignored by the parser. Use this
  to add comments to the file. It may have an argument but it will be ignored.
- `row`: This command starts constructing a new row in the table. It takes no
  argument.
- `cel`: This command starts construction of a new cell in the row currently
  under construction. It takes no argument.
- `txt`: This command adds content to the cell currently under construction. It
  takes an argument. Its argument can be any UTF-8 text *not* containing line
  feeds or carraige returns. The argument is first converted to bytes before
  being appended to the cell.
- `hex`: This command adds content to the cell currently under construction. It
  takes an argument. Its argument can be any string of hexadecimal digits (0-9,
  a-f, A-F). The argument is first converted to bytes before being appended to
  the cell. If the argument had odd length, an additional zero is put at the
  front to pad it to a multiple of 8 bits.

### Continuation lines

Any line starting with four spaces gets converted to a `txt`-command with an
additional line feed prepended before the actual argument. This makes

```
txt Line 1
hex 10
txt Line 2
```

equivalent to

```
txt Line 1
    Line 2
```

It is syntactic sugar to avoid writing too many `hex`-commands. Cells containing
newlines are a common edge case for testing in tabular formats and this
mechanism of continuation lines allows for more readable test cases.

## A simple Example

*Note*: In the following examples, I will show some tabular data and how it can
be represented in ATBL format. I will often show the tabular data as string
literals. These string literals should be interpreted to mean "The array of
bytes that encode this string literal in UTF-8".

The tabular data

```
[
  ['Hello', 'Everyone'],
  ['Bonjour', 'Tout le monde']
]
```

can be represented by the ATBL-file

```
ver 1
row
cel
txt Hello
cel
txt Everyone
row
cel
txt Bonjour
cel
txt Tout le monde
```


## A more contrived example


This is a valid ATBL-file:

```
ver 1
rem This is a sample table
row
cel
txt Field
hex 10
txt with line break
cel
rem Empty cell
row
```

The first row specifies that this file uses ATBL version 1. The next line is
a comment. Next, a new row is created and a new cell is created in this row.
The cell first gets the bytes of the text "Field 1". Next the byte `0x10`
(a line feed) is added. Finally, the bytes of the text "with line break" are
added. The cell now contains the bytes corresponding to the text

```
Field
with line break
```

On the next line we start a new cell. A comment explains that this cell will be
empty. Indeed, we start a new row on the very next line. This row will also be
empty because we have run through the entire file. This sample file will parse
to the table

```
[
  [ 'Field\nwith line break', ''],
  []
]
```

where we have used escaped strings instead of bytes to represent the cells. This
is not always possible, but in this example it was. We have a table with two
rows.

## Why use yet another format for tabular data?

The ATBL-format is not to be used directly in the sharing of datasets etc. The
end goal of ATBL is to write language-independent test suites for parsers of
tabular data. Someone writing a parser for RFC 4180 compliant CSV-files can
write files `input.csv` and `input.atbl` containing respectively

```
a,b,c
d,e,f
```

and

```
ver 1
row
cell
txt a
cell
txt b
cell
txt c
row
cell
txt d
cell
txt e
cell
txt f
```

Because ATBL is easy to write a correct parser for, the programmer can implment
ATBL and can verify that both files represent the same "list of lists of
bytearrays".

I have taken care to define ATBL such that a lot of edge cases are expressible.
For example, it is possible to define the following *distinct* structures in
ATBL:

- an empty table,
- a table with a single empty row,
- a table with a single, nonempty row containing a single empty field.

ATBL can also represent *every* possible "list of lists of bytearrays". Contrast
this with TSV where some variants do not allow escaping inside fields to
represent tabs and newlines. There are also no delicate escape rules in fields.
The only characters not allowed in `txt`-commands are the carriage return and
the line feed. These can be easily represented with an intermediate `hex`-
command.

## A more detailed look at parsing an ATBL-file

This is more or less the flow the parser follows. I have omitted the handling of
`rem`-commands because these lines are simply ignored. They do not impact the
core logic.

When I describe a command and say that "The only allowed next commands are ...",
I mean that the parser should stop and return an error if any other command
follows the described command.

1. In the beginning, the version line is parsed. If the parser does not support
   the declared version, parsing stops with an error. If the first line is not
   a `ver`-command, parsing stops with an error.
2. With the version line scanned, the parser prepares:
   - an empty table,
   - an uninitialized "row under construction",
   - an uninitialized "cell under construction".
   At this point the only allowed command is `row` to start construction of a
   row.
3. If a `row`-command is given for the first time. The "row under construction"
   is initialized to be an empty row. From now on, the "row under construction"
   can no longer be uninitialized. The only allowed next commands are `row` and
   `cel`.
4. If a `row`-command is given but not for the first time, the parser does some
   checks. Firstly, if the "cell under construction" is initialized, it is added
   to the current "row under construction. The "cell under construction is now
   uninitialized. Next, if the current "row under construction" is initialized,
   it is added to the table. The parser prepares a new empty row which is now
   considered the "row under construction". The only allowed next commands are
   `row` and `cel`.
5. If a `cel`-command is given. The parser checks if the "cell under
   construction" is initialized. If so, it is added to the "row under
   construction" and a new empty cell is created, now considered to be the
   "cell under construction". If not, a new cell is created and considered to be
   the "cell under construction". The allowed next commands are `row`, `cel`,
   `txt` and `hex`.
6. If a `txt`-command is given, its argument is converted from UTF-8 to bytes
   and is appended to the "cell under construction". The allowed next commands
   are `row`, `cel`, `txt` and `hex`.
7. If a `hex`-command is given, the parser checks if its argument is of odd
   length. If so, the argument is padded at the front (left) with a zero.
   After this check, the (maybe padded) argument is converted from a hex string
   to bytes and appended to the "cell under construction". The allowed next
   commands are `row`, `cel`, `txt` and `hex`.
8. At the end of the file, some final checks are made. Firstly, if the "cell
   under construction" is initialized, it is added to the current "row under
   construction. Next, if the current "row under construction" is initialized,
   it is added to the table.
9. If the end of the file is reached and all final checks are made, the full
   table is returned.

## A few edge cases

This is an empty table:

```
ver 1
```

This is a table with a single empty row:

```
ver 1
row
```

This is a table with a single row containing a single empty cell.

```
ver 1	
row
cel
```

## Q&A

**Is there support for header rows, schemas, typing, ...?**

No. The purpose of ATBL is to just describe the *structure* of the data. A
separate description of the data must be provided to correctly *interpret* the
dataset. The only thing ATBL understands is a "list of lists of bytearrays".

**Why only a command for hexadecimal and not also one for base64?**

Functions for dealing with hex-string are more likely to be present in an
arbitrarily chosen programming language. While it is possible to add a command
`b64` to add base64 encoded data to a cell, it doesnt add any functionality
already provided by `hex`. Note again (from the top of the README) that, while
ATBL *can* be read and written by humans, that is not its primary purpose. The
`hex`-command was necessary to add arbitrary binary data (not just UTF-8) to a
cell. Now that we have it, we need no one else to do the same job.

**In SQL there is a difference between a field containing nothing (NULL) and a field containing an empty string. Does ATBL make such a distinction?**

No. While it is possible to extend ATBL with a potential `nul` command that
can allow this distinction, I decided against it. It would complicate the parser
rules. Is a `txt` or `hex` allowed before or after a `nul`? Are multiple `nul`
commands allowed in succession and are they the same as a single `nul`? These
questions need to be answered and their answers need to be implemented in the
parser.

If you need this distinction, one possible way is to encode it in your dataset
before passing it through ATBL. If you have the CSV-file

```
a,b,c
d,NULL,f
g,,i
```

where the `NULL` means an absent value, you can encode the second column as
follows. The inspiration for this encoding came from Option/Maybe/... types in
programming languages that do not contain a literal `null`. Think of the `v` and
`n` as type constructors.

- If the value is an actual string, the encoded value is a literal `v` (for 
  value), followed by a space, followed by the contents of the field.
- If the value is NULL, the encoded value is a literal `n`.

Be sure to mention this in the accompanying description of the dataset, though.
This losslessly encodes the CSV to the following:

```
a,v b,c
d,n,f
g,v ,i
```

(Yes, that is a `v` followed by a *single* space on the last row. The original
field was an empty string after all.)

This might seem to complicate matters, but it has the additional benefit of
making the ATBL-format more robust. It requires you to explicitly declare
which columns are nullable isntead of the format being nullable by default.
It ansures the parser delivers an *actual* "list of lists of bytearrays" and
not a "list of lists of potentially null-valued bytearrays".

**How can you be sure you handled every single edge case?**

You can never be sure. That is why I included the `ver` command from the very
beginning. I do not *intend* it to ever grow beyond one but life does not care
about my version numbers.

The original inspiration for ATBL came from reading
[Falsehoods Programmers Believe About CSVs](https://donatstudios.com/Falsehoods-Programmers-Believe-About-CSVs).
The idea of creating a file format that can handle *all* tables and can be used
as an intermediate format was alluring. The first versions were too meta,
using a tabular-like format to encode the data. In the end I settled for an easy
to parse set of commands for building arbitrary tables.

<!-- TODO Write falsehoods.md and link it here -->
In a separate file I talk about how ATBL takes away many of the problems the
article above (and its comments) talks about.

For all the things it solves, ATBL is unfortunately not readable by Excel (and
unlikely to be readable by Excel in the near future). Let's dream big, though!