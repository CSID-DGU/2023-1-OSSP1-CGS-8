#!/usr/bin/env python

# Copyright (C) 2010-2011 Hideo Hattori
# Copyright (C) 2011-2013 Hideo Hattori, Steven Myint
# Copyright (C) 2013-2016 Hideo Hattori, Steven Myint, Bill Wendling
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Copyright (C) 2006-2009 Johann C. Rocholl <johann@rocholl.net>
# Copyright (C) 2009-2013 Florent Xicluna <florent.xicluna@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Automatically formats Python code to conform to the PEP 8 style guide.

Fixes that only need be done once can be added by adding a function of the form
"fix_<code>(source)" to this module. They should return the fixed source code.
These fixes are picked up by apply_global_fixes().

Fixes that depend on pycodestyle should be added as methods to FixPEP8. See the
class documentation for more information.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import codecs
import collections
import copy
import difflib
import fnmatch
import inspect
import io
import itertools
import keyword
import locale
import os
import re
import signal
import sys
import textwrap
import token
import tokenize
import warnings
import ast
import string
from configparser import ConfigParser as SafeConfigParser, Error

import pycodestyle
from pycodestyle import STARTSWITH_INDENT_STATEMENT_REGEX


__version__ = '2.0.2'


CR = '\r'
LF = '\n'
CRLF = '\r\n'


PYTHON_SHEBANG_REGEX = re.compile(r'^#!.*\bpython[23]?\b\s*$')
LAMBDA_REGEX = re.compile(r'([\w.]+)\s=\slambda\s*([)(=\w,\s.]*):')
COMPARE_NEGATIVE_REGEX = re.compile(r'\b(not)\s+([^][)(}{]+?)\s+(in|is)\s')
COMPARE_NEGATIVE_REGEX_THROUGH = re.compile(r'\b(not\s+in|is\s+not)\s')
BARE_EXCEPT_REGEX = re.compile(r'except\s*:')
STARTSWITH_DEF_REGEX = re.compile(r'^(async\s+def|def)\s.*\):')
DOCSTRING_START_REGEX = re.compile(r'^u?r?(?P<kind>["\']{3})')
ENABLE_REGEX = re.compile(r'# *(fmt|autopep8): *on')
DISABLE_REGEX = re.compile(r'# *(fmt|autopep8): *off')

EXIT_CODE_OK = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_EXISTS_DIFF = 2
EXIT_CODE_ARGPARSE_ERROR = 99

# For generating line shortening candidates.
SHORTEN_OPERATOR_GROUPS = frozenset([
    frozenset([',']),
    frozenset(['%']),
    frozenset([',', '(', '[', '{']),
    frozenset(['%', '(', '[', '{']),
    frozenset([',', '(', '[', '{', '%', '+', '-', '*', '/', '//']),
    frozenset(['%', '+', '-', '*', '/', '//']),
])


DEFAULT_IGNORE = 'E226,E24,W50,W690'    # TODO: use pycodestyle.DEFAULT_IGNORE
DEFAULT_INDENT_SIZE = 4
# these fixes conflict with each other, if the `--ignore` setting causes both
# to be enabled, disable both of them
CONFLICTING_CODES = ('W503', 'W504')

# W602 is handled separately due to the need to avoid "with_traceback".
CODE_TO_2TO3 = {
    'E231': ['ws_comma'],
    'E721': ['idioms'],
    'W690': ['apply',
             'except',
             'exitfunc',
             'numliterals',
             'operator',
             'paren',
             'reduce',
             'renames',
             'standarderror',
             'sys_exc',
             'throw',
             'tuple_params',
             'xreadlines']}


if sys.platform == 'win32':  # pragma: no cover
    DEFAULT_CONFIG = os.path.expanduser(r'~\.pycodestyle')
else:
    DEFAULT_CONFIG = os.path.join(os.getenv('XDG_CONFIG_HOME') or
                                  os.path.expanduser('~/.config'),
                                  'pycodestyle')
# fallback, use .pep8
if not os.path.exists(DEFAULT_CONFIG):  # pragma: no cover
    if sys.platform == 'win32':
        DEFAULT_CONFIG = os.path.expanduser(r'~\.pep8')
    else:
        DEFAULT_CONFIG = os.path.join(os.path.expanduser('~/.config'), 'pep8')
PROJECT_CONFIG = ('setup.cfg', 'tox.ini', '.pep8', '.flake8')


MAX_PYTHON_FILE_DETECTION_BYTES = 1024


def open_with_encoding(filename, mode='r', encoding=None, limit_byte_check=-1):
    """Return opened file with a specific encoding."""
    if not encoding:
        encoding = detect_encoding(filename, limit_byte_check=limit_byte_check)

    return io.open(filename, mode=mode, encoding=encoding,
                   newline='')  # Preserve line endings


def detect_encoding(filename, limit_byte_check=-1):
    """Return file encoding."""
    try:
        with open(filename, 'rb') as input_file:
            from lib2to3.pgen2 import tokenize as lib2to3_tokenize
            encoding = lib2to3_tokenize.detect_encoding(input_file.readline)[0]

        with open_with_encoding(filename, encoding=encoding) as test_file:
            test_file.read(limit_byte_check)

        return encoding
    except (LookupError, SyntaxError, UnicodeDecodeError):
        return 'latin-1'


def readlines_from_file(filename):
    """Return contents of file."""
    with open_with_encoding(filename) as input_file:
        return input_file.readlines()


def extended_blank_lines(logical_line,
                         blank_lines,
                         blank_before,
                         indent_level,
                         previous_logical):
    """Check for missing blank lines after class declaration."""
    if previous_logical.startswith('def '):
        if blank_lines and pycodestyle.DOCSTRING_REGEX.match(logical_line):
            yield (0, 'E303 too many blank lines ({})'.format(blank_lines))
    elif pycodestyle.DOCSTRING_REGEX.match(previous_logical):
        # Missing blank line between class docstring and method declaration.
        if (
            indent_level and
            not blank_lines and
            not blank_before and
            logical_line.startswith(('def ')) and
            '(self' in logical_line
        ):
            yield (0, 'E301 expected 1 blank line, found 0')


pycodestyle.register_check(extended_blank_lines)


def continued_indentation(logical_line, tokens, indent_level, hang_closing,
                          indent_char, noqa):
    """Override pycodestyle's function to provide indentation information."""
    first_row = tokens[0][2][0]
    nrows = 1 + tokens[-1][2][0] - first_row
    if noqa or nrows == 1:
        return

    # indent_next tells us whether the next block is indented. Assuming
    # that it is indented by 4 spaces, then we should not allow 4-space
    # indents on the final continuation line. In turn, some other
    # indents are allowed to have an extra 4 spaces.
    indent_next = logical_line.endswith(':')

    row = depth = 0
    valid_hangs = (
        (DEFAULT_INDENT_SIZE,)
        if indent_char != '\t' else (DEFAULT_INDENT_SIZE,
                                     2 * DEFAULT_INDENT_SIZE)
    )

    # Remember how many brackets were opened on each line.
    parens = [0] * nrows

    # Relative indents of physical lines.
    rel_indent = [0] * nrows

    # For each depth, collect a list of opening rows.
    open_rows = [[0]]
    # For each depth, memorize the hanging indentation.
    hangs = [None]

    # Visual indents.
    indent_chances = {}
    last_indent = tokens[0][2]
    indent = [last_indent[1]]

    last_token_multiline = None
    line = None
    last_line = ''
    last_line_begins_with_multiline = False
    for token_type, text, start, end, line in tokens:

        newline = row < start[0] - first_row
        if newline:
            row = start[0] - first_row
            newline = (not last_token_multiline and
                       token_type not in (tokenize.NL, tokenize.NEWLINE))
            last_line_begins_with_multiline = last_token_multiline

        if newline:
            # This is the beginning of a continuation line.
            last_indent = start

            # Record the initial indent.
            rel_indent[row] = pycodestyle.expand_indent(line) - indent_level

            # Identify closing bracket.
            close_bracket = (token_type == tokenize.OP and text in ']})')

            # Is the indent relative to an opening bracket line?
            for open_row in reversed(open_rows[depth]):
                hang = rel_indent[row] - rel_indent[open_row]
                hanging_indent = hang in valid_hangs
                if hanging_indent:
                    break
            if hangs[depth]:
                hanging_indent = (hang == hangs[depth])

            visual_indent = (not close_bracket and hang > 0 and
                             indent_chances.get(start[1]))

            if close_bracket and indent[depth]:
                # Closing bracket for visual indent.
                if start[1] != indent[depth]:
                    yield (start, 'E124 {}'.format(indent[depth]))
            elif close_bracket and not hang:
                # closing bracket matches indentation of opening bracket's line
                if hang_closing:
                    yield (start, 'E133 {}'.format(indent[depth]))
            elif indent[depth] and start[1] < indent[depth]:
                if visual_indent is not True:
                    # Visual indent is broken.
                    yield (start, 'E128 {}'.format(indent[depth]))
            elif (hanging_indent or
                  (indent_next and
                   rel_indent[row] == 2 * DEFAULT_INDENT_SIZE)):
                # Hanging indent is verified.
                if close_bracket and not hang_closing:
                    yield (start, 'E123 {}'.format(indent_level +
                                                   rel_indent[open_row]))
                hangs[depth] = hang
            elif visual_indent is True:
                # Visual indent is verified.
                indent[depth] = start[1]
            elif visual_indent in (text, str):
                # Ignore token lined up with matching one from a previous line.
                pass
            else:
                one_indented = (indent_level + rel_indent[open_row] +
                                DEFAULT_INDENT_SIZE)
                # Indent is broken.
                if hang <= 0:
                    error = ('E122', one_indented)
                elif indent[depth]:
                    error = ('E127', indent[depth])
                elif not close_bracket and hangs[depth]:
                    error = ('E131', one_indented)
                elif hang > DEFAULT_INDENT_SIZE:
                    error = ('E126', one_indented)
                else:
                    hangs[depth] = hang
                    error = ('E121', one_indented)

                yield (start, '{} {}'.format(*error))

        # Look for visual indenting.
        if (
            parens[row] and
            token_type not in (tokenize.NL, tokenize.COMMENT) and
            not indent[depth]
        ):
            indent[depth] = start[1]
            indent_chances[start[1]] = True
        # Deal with implicit string concatenation.
        elif (token_type in (tokenize.STRING, tokenize.COMMENT) or
              text in ('u', 'ur', 'b', 'br')):
            indent_chances[start[1]] = str
        # Special case for the "if" statement because len("if (") is equal to
        # 4.
        elif not indent_chances and not row and not depth and text == 'if':
            indent_chances[end[1] + 1] = True
        elif text == ':' and line[end[1]:].isspace():
            open_rows[depth].append(row)

        # Keep track of bracket depth.
        if token_type == tokenize.OP:
            if text in '([{':
                depth += 1
                indent.append(0)
                hangs.append(None)
                if len(open_rows) == depth:
                    open_rows.append([])
                open_rows[depth].append(row)
                parens[row] += 1
            elif text in ')]}' and depth > 0:
                # Parent indents should not be more than this one.
                prev_indent = indent.pop() or last_indent[1]
                hangs.pop()
                for d in range(depth):
                    if indent[d] > prev_indent:
                        indent[d] = 0
                for ind in list(indent_chances):
                    if ind >= prev_indent:
                        del indent_chances[ind]
                del open_rows[depth + 1:]
                depth -= 1
                if depth:
                    indent_chances[indent[depth]] = True
                for idx in range(row, -1, -1):
                    if parens[idx]:
                        parens[idx] -= 1
                        break
            assert len(indent) == depth + 1
            if (
                start[1] not in indent_chances and
                # This is for purposes of speeding up E121 (GitHub #90).
                not last_line.rstrip().endswith(',')
            ):
                # Allow to line up tokens.
                indent_chances[start[1]] = text

        last_token_multiline = (start[0] != end[0])
        if last_token_multiline:
            rel_indent[end[0] - first_row] = rel_indent[row]

        last_line = line

    if (
        indent_next and
        not last_line_begins_with_multiline and
        pycodestyle.expand_indent(line) == indent_level + DEFAULT_INDENT_SIZE
    ):
        pos = (start[0], indent[0] + 4)
        desired_indent = indent_level + 2 * DEFAULT_INDENT_SIZE
        if visual_indent:
            yield (pos, 'E129 {}'.format(desired_indent))
        else:
            yield (pos, 'E125 {}'.format(desired_indent))

del pycodestyle._checks['logical_line'][pycodestyle.continued_indentation]
pycodestyle.register_check(continued_indentation)

class FixPEP8(object):

    """Fix invalid code.

    Fixer methods are prefixed "fix_". The _fix_source() method looks for these
    automatically.

    The fixer method can take either one or two arguments (in addition to
    self). The first argument is "result", which is the error information from
    pycodestyle. The second argument, "logical", is required only for
    logical-line fixes.

    The fixer method can return the list of modified lines or None. An empty
    list would mean that no changes were made. None would mean that only the
    line reported in the pycodestyle error was modified. Note that the modified
    line numbers that are returned are indexed at 1. This typically would
    correspond with the line number reported in the pycodestyle error
    information.

    [fixed method list]
        - e111,e114,e115,e116
        - e121,e122,e123,e124,e125,e126,e127,e128,e129
        - e201,e202,e203
        - e211
        - e221,e222,e223,e224,e225
        - e231
        - e251,e252
        - e261,e262
        - e271,e272,e273,e274,e275
        - e301,e302,e303,e304,e305,e306
        - e401,e402
        - e502
        - e701,e702,e703,e704
        - e711,e712,e713,e714
        - e722
        - e731
        - w291
        - w503,504
    """

    def __init__(self, filename,
                 options,
                 contents=None,
                 long_line_ignore_cache=None):
        self.filename = filename
        if contents is None:
            self.source = readlines_from_file(filename)
        else:
            sio = io.StringIO(contents)
            self.source = sio.readlines()
        self.options = options
        self.indent_word = _get_indentword(''.join(self.source))

        # collect imports line
        self.imports = {}
        for i, line in enumerate(self.source):
            if (line.find("import ") == 0 or line.find("from ") == 0) and \
                    line not in self.imports:
                # collect only import statements that first appeared
                self.imports[line] = i

        self.long_line_ignore_cache = (
            set() if long_line_ignore_cache is None
            else long_line_ignore_cache)

        # Many fixers are the same even though pycodestyle categorizes them
        # differently.
        self.fix_e115 = self.fix_e112
        self.fix_e121 = self._fix_reindent
        self.fix_e122 = self._fix_reindent
        self.fix_e123 = self._fix_reindent
        self.fix_e124 = self._fix_reindent
        self.fix_e126 = self._fix_reindent
        self.fix_e127 = self._fix_reindent
        self.fix_e128 = self._fix_reindent
        self.fix_e129 = self._fix_reindent
        self.fix_e133 = self.fix_e131
        self.fix_e202 = self.fix_e201
        self.fix_e203 = self.fix_e201
        self.fix_e211 = self.fix_e201
        self.fix_e221 = self.fix_e271
        self.fix_e222 = self.fix_e271
        self.fix_e223 = self.fix_e271
        self.fix_e226 = self.fix_e225
        self.fix_e227 = self.fix_e225
        self.fix_e228 = self.fix_e225
        self.fix_e241 = self.fix_e271
        self.fix_e242 = self.fix_e224
        self.fix_e252 = self.fix_e225
        self.fix_e261 = self.fix_e262
        self.fix_e272 = self.fix_e271
        self.fix_e273 = self.fix_e271
        self.fix_e274 = self.fix_e271
        self.fix_e275 = self.fix_e271
        self.fix_e306 = self.fix_e301
        self.fix_e501 = (
            self.fix_long_line_logically if
            options and (options.aggressive >= 2 or options.experimental) else
            self.fix_long_line_physically)
        self.fix_e703 = self.fix_e702
        self.fix_w292 = self.fix_w291
        self.fix_w293 = self.fix_w291
        
        # 추가한 부분 김위성
        # 작명 컨벤션 aggressive 3레벨 일 경우에만 실행
        if options and (options.aggressive >= 3 or options.experimental):
            self.fix_w701 = self.fix_w705
        
        if options and (options.aggressive >= 3 or options.experimental):
            self.fix_w702 = self.fix_w707

    def _fix_source(self, results):
        try:
            (logical_start, logical_end) = _find_logical(self.source)
            logical_support = True
        except (SyntaxError, tokenize.TokenError):  # pragma: no cover
            logical_support = False

        completed_lines = set()
        for result in sorted(results, key=_priority_key):
            if result['line'] in completed_lines:
                continue

            fixed_methodname = 'fix_' + result['id'].lower()
            if hasattr(self, fixed_methodname):
                fix = getattr(self, fixed_methodname)

                line_index = result['line'] - 1
                original_line = self.source[line_index]

                is_logical_fix = len(_get_parameters(fix)) > 2
                if is_logical_fix:
                    logical = None
                    if logical_support:
                        logical = _get_logical(self.source,
                                               result,
                                               logical_start,
                                               logical_end)
                        if logical and set(range(
                            logical[0][0] + 1,
                            logical[1][0] + 1)).intersection(
                                completed_lines):
                            continue

                    modified_lines = fix(result, logical)
                else:
                    modified_lines = fix(result)

                if modified_lines is None:
                    # Force logical fixes to report what they modified.
                    assert not is_logical_fix

                    if self.source[line_index] == original_line:
                        modified_lines = []

                if modified_lines:
                    completed_lines.update(modified_lines)
                elif modified_lines == []:  # Empty list means no fix
                    if self.options.verbose >= 2:
                        print(
                            '--->  Not fixing {error} on line {line}'.format(
                                error=result['id'], line=result['line']),
                            file=sys.stderr)
                else:  # We assume one-line fix when None.
                    completed_lines.add(result['line'])
            else:
                if self.options.verbose >= 3:
                    print(
                        "--->  '{}' is not defined.".format(fixed_methodname),
                        file=sys.stderr)

                    info = result['info'].strip()
                    print('--->  {}:{}:{}:{}'.format(self.filename,
                                                     result['line'],
                                                     result['column'],
                                                     info),
                          file=sys.stderr)

    def fix(self):
        """Return a version of the source code with PEP 8 violations fixed."""
        pep8_options = {
            'ignore': self.options.ignore,
            'select': self.options.select,
            'max_line_length': self.options.max_line_length,
            'hang_closing': self.options.hang_closing,
        }
        results = _execute_pep8(pep8_options, self.source)

        if self.options.verbose:
            progress = {}
            for r in results:
                if r['id'] not in progress:
                    progress[r['id']] = set()
                progress[r['id']].add(r['line'])
            print('--->  {n} issue(s) to fix {progress}'.format(
                n=len(results), progress=progress), file=sys.stderr)

        if self.options.line_range:
            start, end = self.options.line_range
            results = [r for r in results
                       if start <= r['line'] <= end]

        self._fix_source(filter_results(source=''.join(self.source),
                                        results=results,
                                        aggressive=self.options.aggressive))

        if self.options.line_range:
            # If number of lines has changed then change line_range.
            count = sum(sline.count('\n')
                        for sline in self.source[start - 1:end])
            self.options.line_range[1] = start + count - 1

        return ''.join(self.source)

    def _fix_reindent(self, result):
        """Fix a badly indented line.

        This is done by adding or removing from its initial indent only.

        """
        num_indent_spaces = int(result['info'].split()[1])
        line_index = result['line'] - 1
        target = self.source[line_index]

        self.source[line_index] = ' ' * num_indent_spaces + target.lstrip()

    def fix_e112(self, result):
        """Fix under-indented comments."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        if not target.lstrip().startswith('#'):
            # Don't screw with invalid syntax.
            return []

        self.source[line_index] = self.indent_word + target

    def fix_e113(self, result):
        """Fix unexpected indentation."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        indent = _get_indentation(target)
        stripped = target.lstrip()
        self.source[line_index] = indent[1:] + stripped

    def fix_e116(self, result):
        """Fix over-indented comments."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        indent = _get_indentation(target)
        stripped = target.lstrip()

        if not stripped.startswith('#'):
            # Don't screw with invalid syntax.
            return []

        self.source[line_index] = indent[1:] + stripped

    def fix_e117(self, result):
        """Fix over-indented."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        indent = _get_indentation(target)
        if indent == '\t':
            return []

        stripped = target.lstrip()

        self.source[line_index] = indent[1:] + stripped

    def fix_e125(self, result):
        """Fix indentation undistinguish from the next logical line."""
        num_indent_spaces = int(result['info'].split()[1])
        line_index = result['line'] - 1
        target = self.source[line_index]

        spaces_to_add = num_indent_spaces - len(_get_indentation(target))
        indent = len(_get_indentation(target))
        modified_lines = []

        while len(_get_indentation(self.source[line_index])) >= indent:
            self.source[line_index] = (' ' * spaces_to_add +
                                       self.source[line_index])
            modified_lines.append(1 + line_index)  # Line indexed at 1.
            line_index -= 1

        return modified_lines

    def fix_e131(self, result):
        """Fix indentation undistinguish from the next logical line."""
        num_indent_spaces = int(result['info'].split()[1])
        line_index = result['line'] - 1
        target = self.source[line_index]

        spaces_to_add = num_indent_spaces - len(_get_indentation(target))

        indent_length = len(_get_indentation(target))
        spaces_to_add = num_indent_spaces - indent_length
        if num_indent_spaces == 0 and indent_length == 0:
            spaces_to_add = 4

        if spaces_to_add >= 0:
            self.source[line_index] = (' ' * spaces_to_add +
                                       self.source[line_index])
        else:
            offset = abs(spaces_to_add)
            self.source[line_index] = self.source[line_index][offset:]

    def fix_e201(self, result):
        """Remove extraneous whitespace."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        fixed = fix_whitespace(target,
                               offset=offset,
                               replacement='')

        self.source[line_index] = fixed

    def fix_e224(self, result):
        """Remove extraneous whitespace around operator."""
        target = self.source[result['line'] - 1]
        offset = result['column'] - 1
        fixed = target[:offset] + target[offset:].replace('\t', ' ')
        self.source[result['line'] - 1] = fixed

    def fix_e225(self, result):
        """Fix missing whitespace around operator."""
        target = self.source[result['line'] - 1]
        offset = result['column'] - 1
        fixed = target[:offset] + ' ' + target[offset:]

        # Only proceed if non-whitespace characters match.
        # And make sure we don't break the indentation.
        if (
            fixed.replace(' ', '') == target.replace(' ', '') and
            _get_indentation(fixed) == _get_indentation(target)
        ):
            self.source[result['line'] - 1] = fixed
            error_code = result.get('id', 0)
            try:
                ts = generate_tokens(fixed)
            except (SyntaxError, tokenize.TokenError):
                return
            if not check_syntax(fixed.lstrip()):
                return
            errors = list(
                pycodestyle.missing_whitespace_around_operator(fixed, ts))
            for e in reversed(errors):
                if error_code != e[1].split()[0]:
                    continue
                offset = e[0][1]
                fixed = fixed[:offset] + ' ' + fixed[offset:]
            self.source[result['line'] - 1] = fixed
        else:
            return []

    def fix_e231(self, result):
        """Add missing whitespace."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column']
        fixed = target[:offset].rstrip() + ' ' + target[offset:].lstrip()
        self.source[line_index] = fixed

    def fix_e251(self, result):
        """Remove whitespace around parameter '=' sign."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        # This is necessary since pycodestyle sometimes reports columns that
        # goes past the end of the physical line. This happens in cases like,
        # foo(bar\n=None)
        c = min(result['column'] - 1,
                len(target) - 1)

        if target[c].strip():
            fixed = target
        else:
            fixed = target[:c].rstrip() + target[c:].lstrip()

        # There could be an escaped newline
        #
        #     def foo(a=\
        #             1)
        if fixed.endswith(('=\\\n', '=\\\r\n', '=\\\r')):
            self.source[line_index] = fixed.rstrip('\n\r \t\\')
            self.source[line_index + 1] = self.source[line_index + 1].lstrip()
            return [line_index + 1, line_index + 2]  # Line indexed at 1

        self.source[result['line'] - 1] = fixed

    def fix_e262(self, result):
        """Fix spacing after inline comment hash."""
        target = self.source[result['line'] - 1]
        offset = result['column']

        code = target[:offset].rstrip(' \t#')
        comment = target[offset:].lstrip(' \t#')

        fixed = code + ('  # ' + comment if comment.strip() else '\n')

        self.source[result['line'] - 1] = fixed

    def fix_e265(self, result):
        """Fix spacing after block comment hash."""
        target = self.source[result['line'] - 1]

        indent = _get_indentation(target)
        line = target.lstrip(' \t')
        pos = next((index for index, c in enumerate(line) if c != '#'))
        hashes = line[:pos]
        comment = line[pos:].lstrip(' \t')

        # Ignore special comments, even in the middle of the file.
        if comment.startswith('!'):
            return

        fixed = indent + hashes + (' ' + comment if comment.strip() else '\n')

        self.source[result['line'] - 1] = fixed

    def fix_e266(self, result):
        """Fix too many block comment hashes."""
        target = self.source[result['line'] - 1]

        # Leave stylistic outlined blocks alone.
        if target.strip().endswith('#'):
            return

        indentation = _get_indentation(target)
        fixed = indentation + '# ' + target.lstrip('# \t')

        self.source[result['line'] - 1] = fixed

    def fix_e271(self, result):
        """Fix extraneous whitespace around keywords."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        fixed = fix_whitespace(target,
                               offset=offset,
                               replacement=' ')

        if fixed == target:
            return []
        else:
            self.source[line_index] = fixed

    def fix_e301(self, result):
        """Add missing blank line."""
        cr = '\n'
        self.source[result['line'] - 1] = cr + self.source[result['line'] - 1]

    def fix_e302(self, result):
        """Add missing 2 blank lines."""
        add_linenum = 2 - int(result['info'].split()[-1])
        offset = 1
        if self.source[result['line'] - 2].strip() == "\\":
            offset = 2
        cr = '\n' * add_linenum
        self.source[result['line'] - offset] = (
            cr + self.source[result['line'] - offset]
        )

    def fix_e303(self, result):
        """Remove extra blank lines."""
        delete_linenum = int(result['info'].split('(')[1].split(')')[0]) - 2
        delete_linenum = max(1, delete_linenum)

        # We need to count because pycodestyle reports an offset line number if
        # there are comments.
        cnt = 0
        line = result['line'] - 2
        modified_lines = []
        while cnt < delete_linenum and line >= 0:
            if not self.source[line].strip():
                self.source[line] = ''
                modified_lines.append(1 + line)  # Line indexed at 1
                cnt += 1
            line -= 1

        return modified_lines

    def fix_e304(self, result):
        """Remove blank line following function decorator."""
        line = result['line'] - 2
        if not self.source[line].strip():
            self.source[line] = ''

    def fix_e305(self, result):
        """Add missing 2 blank lines after end of function or class."""
        add_delete_linenum = 2 - int(result['info'].split()[-1])
        cnt = 0
        offset = result['line'] - 2
        modified_lines = []
        if add_delete_linenum < 0:
            # delete cr
            add_delete_linenum = abs(add_delete_linenum)
            while cnt < add_delete_linenum and offset >= 0:
                if not self.source[offset].strip():
                    self.source[offset] = ''
                    modified_lines.append(1 + offset)  # Line indexed at 1
                    cnt += 1
                offset -= 1
        else:
            # add cr
            cr = '\n'
            # check comment line
            while True:
                if offset < 0:
                    break
                line = self.source[offset].lstrip()
                if not line:
                    break
                if line[0] != '#':
                    break
                offset -= 1
            offset += 1
            self.source[offset] = cr + self.source[offset]
            modified_lines.append(1 + offset)   # Line indexed at 1.
        return modified_lines

    def fix_e401(self, result):
        """Put imports on separate lines."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        if not target.lstrip().startswith('import'):
            return []

        indentation = re.split(pattern=r'\bimport\b',
                               string=target, maxsplit=1)[0]
        fixed = (target[:offset].rstrip('\t ,') + '\n' +
                 indentation + 'import ' + target[offset:].lstrip('\t ,'))
        self.source[line_index] = fixed

    def fix_e402(self, result):
        (line_index, offset, target) = get_index_offset_contents(result,
                                                                 self.source)
        for i in range(1, 100):
            line = "".join(self.source[line_index:line_index+i])
            try:
                generate_tokens("".join(line))
            except (SyntaxError, tokenize.TokenError):
                continue
            break
        if not (target in self.imports and self.imports[target] != line_index):
            mod_offset = get_module_imports_on_top_of_file(self.source,
                                                           line_index)
            self.source[mod_offset] = line + self.source[mod_offset]
        for offset in range(i):
            self.source[line_index+offset] = ''

    def fix_long_line_logically(self, result, logical):
        """Try to make lines fit within --max-line-length characters."""
        if (
            not logical or
            len(logical[2]) == 1 or
            self.source[result['line'] - 1].lstrip().startswith('#')
        ):
            return self.fix_long_line_physically(result)

        start_line_index = logical[0][0]
        end_line_index = logical[1][0]
        logical_lines = logical[2]

        previous_line = get_item(self.source, start_line_index - 1, default='')
        next_line = get_item(self.source, end_line_index + 1, default='')

        single_line = join_logical_line(''.join(logical_lines))

        try:
            fixed = self.fix_long_line(
                target=single_line,
                previous_line=previous_line,
                next_line=next_line,
                original=''.join(logical_lines))
        except (SyntaxError, tokenize.TokenError):
            return self.fix_long_line_physically(result)

        if fixed:
            for line_index in range(start_line_index, end_line_index + 1):
                self.source[line_index] = ''
            self.source[start_line_index] = fixed
            return range(start_line_index + 1, end_line_index + 1)

        return []

    def fix_long_line_physically(self, result):
        """Try to make lines fit within --max-line-length characters."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        previous_line = get_item(self.source, line_index - 1, default='')
        next_line = get_item(self.source, line_index + 1, default='')

        try:
            fixed = self.fix_long_line(
                target=target,
                previous_line=previous_line,
                next_line=next_line,
                original=target)
        except (SyntaxError, tokenize.TokenError):
            return []

        if fixed:
            self.source[line_index] = fixed
            return [line_index + 1]

        return []

    def fix_long_line(self, target, previous_line,
                      next_line, original):
        cache_entry = (target, previous_line, next_line)
        if cache_entry in self.long_line_ignore_cache:
            return []

        if target.lstrip().startswith('#'):
            if self.options.aggressive:
                # Wrap commented lines.
                return shorten_comment(
                    line=target,
                    max_line_length=self.options.max_line_length,
                    last_comment=not next_line.lstrip().startswith('#'))
            return []

        fixed = get_fixed_long_line(
            target=target,
            previous_line=previous_line,
            original=original,
            indent_word=self.indent_word,
            max_line_length=self.options.max_line_length,
            aggressive=self.options.aggressive,
            experimental=self.options.experimental,
            verbose=self.options.verbose)

        if fixed and not code_almost_equal(original, fixed):
            return fixed

        self.long_line_ignore_cache.add(cache_entry)
        return None

    def fix_e502(self, result):
        """Remove extraneous escape of newline."""
        (line_index, _, target) = get_index_offset_contents(result,
                                                            self.source)
        self.source[line_index] = target.rstrip('\n\r \t\\') + '\n'

    def fix_e701(self, result):
        """Put colon-separated compound statement on separate lines."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        c = result['column']

        fixed_source = (target[:c] + '\n' +
                        _get_indentation(target) + self.indent_word +
                        target[c:].lstrip('\n\r \t\\'))
        self.source[result['line'] - 1] = fixed_source
        return [result['line'], result['line'] + 1]

    def fix_e702(self, result, logical):
        """Put semicolon-separated compound statement on separate lines."""
        if not logical:
            return []  # pragma: no cover
        logical_lines = logical[2]

        # Avoid applying this when indented.
        # https://docs.python.org/reference/compound_stmts.html
        for line in logical_lines:
            if (result['id'] == 'E702' and ':' in line
                    and STARTSWITH_INDENT_STATEMENT_REGEX.match(line)):
                if self.options.verbose:
                    print(
                        '---> avoid fixing {error} with '
                        'other compound statements'.format(error=result['id']),
                        file=sys.stderr
                    )
                return []

        line_index = result['line'] - 1
        target = self.source[line_index]

        if target.rstrip().endswith('\\'):
            # Normalize '1; \\\n2' into '1; 2'.
            self.source[line_index] = target.rstrip('\n \r\t\\')
            self.source[line_index + 1] = self.source[line_index + 1].lstrip()
            return [line_index + 1, line_index + 2]

        if target.rstrip().endswith(';'):
            self.source[line_index] = target.rstrip('\n \r\t;') + '\n'
            return [line_index + 1]

        offset = result['column'] - 1
        first = target[:offset].rstrip(';').rstrip()
        second = (_get_indentation(logical_lines[0]) +
                  target[offset:].lstrip(';').lstrip())

        # Find inline comment.
        inline_comment = None
        if target[offset:].lstrip(';').lstrip()[:2] == '# ':
            inline_comment = target[offset:].lstrip(';')

        if inline_comment:
            self.source[line_index] = first + inline_comment
        else:
            self.source[line_index] = first + '\n' + second
        return [line_index + 1]

    def fix_e704(self, result):
        """Fix multiple statements on one line def"""
        (line_index, _, target) = get_index_offset_contents(result,
                                                            self.source)
        match = STARTSWITH_DEF_REGEX.match(target)
        if match:
            self.source[line_index] = '{}\n{}{}'.format(
                match.group(0),
                _get_indentation(target) + self.indent_word,
                target[match.end(0):].lstrip())

    def fix_e711(self, result):
        """Fix comparison with None."""
        (line_index, offset, target) = get_index_offset_contents(result,
                                                                 self.source)

        right_offset = offset + 2
        if right_offset >= len(target):
            return []

        left = target[:offset].rstrip()
        center = target[offset:right_offset]
        right = target[right_offset:].lstrip()

        if center.strip() == '==':
            new_center = 'is'
        elif center.strip() == '!=':
            new_center = 'is not'
        else:
            return []

        self.source[line_index] = ' '.join([left, new_center, right])

    def fix_e712(self, result):
        """Fix (trivial case of) comparison with boolean."""
        (line_index, offset, target) = get_index_offset_contents(result,
                                                                 self.source)

        # Handle very easy "not" special cases.
        if re.match(r'^\s*if [\w."\'\[\]]+ == False:$', target):
            self.source[line_index] = re.sub(r'if ([\w."\'\[\]]+) == False:',
                                             r'if not \1:', target, count=1)
        elif re.match(r'^\s*if [\w."\'\[\]]+ != True:$', target):
            self.source[line_index] = re.sub(r'if ([\w."\'\[\]]+) != True:',
                                             r'if not \1:', target, count=1)
        else:
            right_offset = offset + 2
            if right_offset >= len(target):
                return []

            left = target[:offset].rstrip()
            center = target[offset:right_offset]
            right = target[right_offset:].lstrip()

            # Handle simple cases only.
            new_right = None
            if center.strip() == '==':
                if re.match(r'\bTrue\b', right):
                    new_right = re.sub(r'\bTrue\b *', '', right, count=1)
            elif center.strip() == '!=':
                if re.match(r'\bFalse\b', right):
                    new_right = re.sub(r'\bFalse\b *', '', right, count=1)

            if new_right is None:
                return []

            if new_right[0].isalnum():
                new_right = ' ' + new_right

            self.source[line_index] = left + new_right

    def fix_e713(self, result):
        """Fix (trivial case of) non-membership check."""
        (line_index, offset, target) = get_index_offset_contents(result,
                                                                 self.source)

        # to convert once 'not in' -> 'in'
        before_target = target[:offset]
        target = target[offset:]
        match_notin = COMPARE_NEGATIVE_REGEX_THROUGH.search(target)
        notin_pos_start, notin_pos_end = 0, 0
        if match_notin:
            notin_pos_start = match_notin.start(1)
            notin_pos_end = match_notin.end()
            target = '{}{} {}'.format(
                target[:notin_pos_start], 'in', target[notin_pos_end:])

        # fix 'not in'
        match = COMPARE_NEGATIVE_REGEX.search(target)
        if match:
            if match.group(3) == 'in':
                pos_start = match.start(1)
                new_target = '{5}{0}{1} {2} {3} {4}'.format(
                    target[:pos_start], match.group(2), match.group(1),
                    match.group(3), target[match.end():], before_target)
                if match_notin:
                    # revert 'in' -> 'not in'
                    pos_start = notin_pos_start + offset
                    pos_end = notin_pos_end + offset - 4     # len('not ')
                    new_target = '{}{} {}'.format(
                        new_target[:pos_start], 'not in', new_target[pos_end:])
                self.source[line_index] = new_target

    def fix_e714(self, result):
        """Fix object identity should be 'is not' case."""
        (line_index, offset, target) = get_index_offset_contents(result,
                                                                 self.source)

        # to convert once 'is not' -> 'is'
        before_target = target[:offset]
        target = target[offset:]
        match_isnot = COMPARE_NEGATIVE_REGEX_THROUGH.search(target)
        isnot_pos_start, isnot_pos_end = 0, 0
        if match_isnot:
            isnot_pos_start = match_isnot.start(1)
            isnot_pos_end = match_isnot.end()
            target = '{}{} {}'.format(
                target[:isnot_pos_start], 'in', target[isnot_pos_end:])

        match = COMPARE_NEGATIVE_REGEX.search(target)
        if match:
            if match.group(3).startswith('is'):
                pos_start = match.start(1)
                new_target = '{5}{0}{1} {2} {3} {4}'.format(
                    target[:pos_start], match.group(2), match.group(3),
                    match.group(1), target[match.end():], before_target)
                if match_isnot:
                    # revert 'is' -> 'is not'
                    pos_start = isnot_pos_start + offset
                    pos_end = isnot_pos_end + offset - 4     # len('not ')
                    new_target = '{}{} {}'.format(
                        new_target[:pos_start], 'is not', new_target[pos_end:])
                self.source[line_index] = new_target

    def fix_e722(self, result):
        """fix bare except"""
        (line_index, _, target) = get_index_offset_contents(result,
                                                            self.source)
        match = BARE_EXCEPT_REGEX.search(target)
        if match:
            self.source[line_index] = '{}{}{}'.format(
                target[:result['column'] - 1], "except BaseException:",
                target[match.end():])

    def fix_e731(self, result):
        """Fix do not assign a lambda expression check."""
        (line_index, _, target) = get_index_offset_contents(result,
                                                            self.source)
        match = LAMBDA_REGEX.search(target)
        if match:
            end = match.end()
            self.source[line_index] = '{}def {}({}): return {}'.format(
                target[:match.start(0)], match.group(1), match.group(2),
                target[end:].lstrip())

    def fix_w291(self, result):
        """Remove trailing whitespace."""
        fixed_line = self.source[result['line'] - 1].rstrip()
        self.source[result['line'] - 1] = fixed_line + '\n'

    def fix_w391(self, _):
        """Remove trailing blank lines."""
        blank_count = 0
        for line in reversed(self.source):
            line = line.rstrip()
            if line:
                break
            else:
                blank_count += 1

        original_length = len(self.source)
        self.source = self.source[:original_length - blank_count]
        return range(1, 1 + original_length)

    def fix_w503(self, result):
        (line_index, _, target) = get_index_offset_contents(result,
                                                            self.source)
        one_string_token = target.split()[0]
        try:
            ts = generate_tokens(one_string_token)
        except (SyntaxError, tokenize.TokenError):
            return
        if not _is_binary_operator(ts[0][0], one_string_token):
            return
        # find comment
        comment_index = 0
        found_not_comment_only_line = False
        comment_only_linenum = 0
        for i in range(5):
            # NOTE: try to parse code in 5 times
            if (line_index - i) < 0:
                break
            from_index = line_index - i - 1
            if from_index < 0 or len(self.source) <= from_index:
                break
            to_index = line_index + 1
            strip_line = self.source[from_index].lstrip()
            if (
                not found_not_comment_only_line and
                strip_line and strip_line[0] == '#'
            ):
                comment_only_linenum += 1
                continue
            found_not_comment_only_line = True
            try:
                ts = generate_tokens("".join(self.source[from_index:to_index]))
            except (SyntaxError, tokenize.TokenError):
                continue
            newline_count = 0
            newline_index = []
            for index, t in enumerate(ts):
                if t[0] in (tokenize.NEWLINE, tokenize.NL):
                    newline_index.append(index)
                    newline_count += 1
            if newline_count > 2:
                tts = ts[newline_index[-3]:]
            else:
                tts = ts
            old = []
            for t in tts:
                if t[0] in (tokenize.NEWLINE, tokenize.NL):
                    newline_count -= 1
                if newline_count <= 1:
                    break
                if tokenize.COMMENT == t[0] and old and old[0] != tokenize.NL:
                    comment_index = old[3][1]
                    break
                old = t
            break
        i = target.index(one_string_token)
        fix_target_line = line_index - 1 - comment_only_linenum
        self.source[line_index] = '{}{}'.format(
            target[:i], target[i + len(one_string_token):].lstrip())
        nl = find_newline(self.source[fix_target_line:line_index])
        before_line = self.source[fix_target_line]
        bl = before_line.index(nl)
        if comment_index:
            self.source[fix_target_line] = '{} {} {}'.format(
                before_line[:comment_index], one_string_token,
                before_line[comment_index + 1:])
        else:
            if before_line[:bl].endswith("#"):
                # special case
                # see: https://github.com/hhatto/autopep8/issues/503
                self.source[fix_target_line] = '{}{} {}'.format(
                    before_line[:bl-2], one_string_token, before_line[bl-2:])
            else:
                self.source[fix_target_line] = '{} {}{}'.format(
                    before_line[:bl], one_string_token, before_line[bl:])

    def fix_w504(self, result):
        (line_index, _, target) = get_index_offset_contents(result,
                                                            self.source)
        # NOTE: is not collect pointed out in pycodestyle==2.4.0
        comment_index = 0
        operator_position = None    # (start_position, end_position)
        for i in range(1, 6):
            to_index = line_index + i
            try:
                ts = generate_tokens("".join(self.source[line_index:to_index]))
            except (SyntaxError, tokenize.TokenError):
                continue
            newline_count = 0
            newline_index = []
            for index, t in enumerate(ts):
                if _is_binary_operator(t[0], t[1]):
                    if t[2][0] == 1 and t[3][0] == 1:
                        operator_position = (t[2][1], t[3][1])
                elif t[0] == tokenize.NAME and t[1] in ("and", "or"):
                    if t[2][0] == 1 and t[3][0] == 1:
                        operator_position = (t[2][1], t[3][1])
                elif t[0] in (tokenize.NEWLINE, tokenize.NL):
                    newline_index.append(index)
                    newline_count += 1
            if newline_count > 2:
                tts = ts[:newline_index[-3]]
            else:
                tts = ts
            old = []
            for t in tts:
                if tokenize.COMMENT == t[0] and old:
                    comment_row, comment_index = old[3]
                    break
                old = t
            break
        if not operator_position:
            return
        target_operator = target[operator_position[0]:operator_position[1]]

        if comment_index and comment_row == 1:
            self.source[line_index] = '{}{}'.format(
                target[:operator_position[0]].rstrip(),
                target[comment_index:])
        else:
            self.source[line_index] = '{}{}{}'.format(
                target[:operator_position[0]].rstrip(),
                target[operator_position[1]:].lstrip(),
                target[operator_position[1]:])

        next_line = self.source[line_index + 1]
        next_line_indent = 0
        m = re.match(r'\s*', next_line)
        if m:
            next_line_indent = m.span()[1]
        self.source[line_index + 1] = '{}{} {}'.format(
            next_line[:next_line_indent], target_operator,
            next_line[next_line_indent:])

    def fix_w605(self, result):
        (line_index, offset, target) = get_index_offset_contents(result,
                                                                 self.source)
        self.source[line_index] = '{}\\{}'.format(
            target[:offset + 1], target[offset + 1:])
        
    # 추가한 부분 (작명 컨벤션 - 클래스 이름) - 김위성
    def fix_w705(self, result):
        
        """fix class name"""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1
        
        end_index = target.index(":")
        class_name = target[offset:end_index]
        
        # 상속받는 자식 클래스인 경우
        if '(' in class_name:
            class_name = class_name[0 : class_name.index("(")]
            
        class_name = class_name.strip()
        
        fix_class_name = to_capitalized_words(class_name)
        
        # 1. 이중 for문은 아니지만 for문 두 번 돌아야 함 -> 더 효율적인 방법?
        # 2. 단일 파일에서 실행된다고 가정
        if is_vaild_name(fix_class_name, self.source):
            for i, s in enumerate(self.source):
                self.source[i] = s.replace(class_name, fix_class_name)
        
        return None #return 필요 없음, 아래 메소드와 구분 지으려고 잠시 두는 용도

    # 추가한 부분 (작명 컨벤션 - 함수)- 김위성
    def fix_w707(self, result):
        """fix function name"""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1
        
        end_index = target.index("(")
        function_name = target[offset:end_index]
        
        # def Exam1 (): 일 경우.
        # 공백 수정 후 호출되는 것이면 굳이 필요없다.
        # 하지만 customize해서 공백을 제거안했다면 필요하다
        #   -> 이때는 필요한 코드
        function_name = function_name.strip()
        
        fix_function_name = camel_to_snake(function_name)
        
        if is_vaild_name(fix_function_name, self.source):
            for i, s in enumerate(self.source):
                self.source[i] = s.replace(function_name, fix_function_name)
        
        return None #return 필요 없음, 아래 메소드와 구분 지으려고 잠시 두는 용도


# 추가한 부분 - 김위성
# is_vaild_name 메소드를 클래스 내부로 넣을지 말지
def is_vaild_name(name, source):
    if keyword.iskeyword(name): return False
    for s in source:
        if name in s:
            return False
    return True

def is_snake_case(word):
    if not word:
        return False
    if not word[0].islower():
        return False
    if not all(char.islower() or char == '_' for char in word):
        return False
    if '__' in word:
        return False
    if word in keyword.kwlist:
        return False
    
    return True

def is_camel_case(word):
    if not word:
        return False
    if ' ' in word:
        return False
    if '_' in word:
        return False
    if word[0].isupper():
        return False
    if any(w[0].isupper() for w in word.split()):
        return False
    return True

def to_capitalized_words(word):
    """return capitalized words
    
    class naming convention
    """
    if is_snake_case(word): return string.capwords(word, sep='_').replace('_', '') 
    
    return word[0].upper() + word[1:]

def snake_to_capwords(snake_case):
    """return capwords"""
    if is_snake_case(snake_case): return snake_case
    capitalized_words = string.capwords(snake_case, sep='_').replace('_', '')
    return capitalized_words
    
def camel_to_snake(camel_case):
    """return snake case
    
    method naming convention
    """
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
    return snake_case


# 추가한 부분 - 김위성
# 해결해야 할 부분
# - FixPEP8과 상속 문제
# - fix(), _fix_source()
# class NamingConvention:
    
#     def __init__(self, filename,
#                  options,
#                  contents=None,
#                  long_line_ignore_cache=None):
#         self.filename = filename
#         if contents is None:
#             self.source = readlines_from_file(filename)
#         else:
#             sio = io.StringIO(contents)
#             self.source = sio.readlines()
#         self.options = options
#         self.indent_word = _get_indentword(''.join(self.source))
        
#         # collect imports line
#         self.imports = {}
#         for i, line in enumerate(self.source):
#             if (line.find("import ") == 0 or line.find("from ") == 0) and \
#                     line not in self.imports:
#                 # collect only import statements that first appeared
#                 self.imports[line] = i

#         self.long_line_ignore_cache = (
#             set() if long_line_ignore_cache is None
#             else long_line_ignore_cache)
        
#         # option이 aggressive 3레벨 일 경우 또는 experimental에만 실행
#         if options and (options.aggressive >= 3 or options.experimental):
#             self.fix_w701 = self.fix_w705
        
#         if options and (options.aggressive >= 3 or options.experimental):
#             self.fix_w702 = self.fix_w707
        
#         # self.fix_w701 = self.fix_w705 
#         # self.fix_w702 = self.fix_w707

#     def fix_w705(self, result):
#         """fix class name"""
#         line_index = result['line'] - 1
#         target = self.source[line_index]
#         offset = result['column'] - 1
#         end_index = target.index(":")
        
#         class_name = target[offset:end_index]
        
#         # 상속받는 자식 클래스인 경우
#         if '(' in class_name:
#             class_name = class_name[0 : class_name.index("(")]
        
#         class_name = class_name.strip()
        
#         fix_class_name = self.to_capitalized_words(class_name)
        
#         # 1. 이중 for문은 아니지만 for문 두 번 돌아야 함 -> 더 효율적인 방법?
#         # 2. 단일 파일에서 실행된다고 가정
#         if self.is_vaild_name(fix_class_name):
#             for i, s in enumerate(self.source):
#                 self.source[i] = s.replace(class_name, fix_class_name)
        
#         return None #return 필요 없음, 아래 메소드와 구분 지으려고 잠시 두는 용도

#     def fix_w707(self, result):
#         """fix function name"""
#         line_index = result['line'] - 1
#         target = self.source[line_index]
#         offset = result['column'] - 1
        
#         end_index = target.index(":")
#         function_name = target[offset:end_index]
        
#         # def Exam1 (): 일 경우.
#         # 공백 수정 후 호출되는 것이면 굳이 필요없다.
#         # - customize해서 공백을 제거 안했다면 필요한 코드
#         function_name = function_name.strip()
        
#         fix_function_name = self.camel_to_snake(function_name)
        
#         if self.is_vaild_name(fix_function_name):
#             for i, s in enumerate(self.source):
#                 self.source[i] = s.replace(function_name, fix_function_name)
        
#         return None #return 필요 없음, 아래 메소드와 구분 지으려고 잠시 두는 용도
    
#     def is_vaild_name(self, name):
#         """이름 변경 가능 여부 판별"""
        
#         # 변경하려는 이름이 키워드인 경우
#         if keyword.iskeyword(name): return False
#         # 변경하려는 이름이 파일내에 존재
#         for s in self.source:
#             if name in s:
#                 return False
#         return True
    
#     def is_snake_case(word):
#         if not word:
#             return False

#         if not word[0].islower():
#             return False

#         if not all(char.islower() or char == '_' for char in word):
#             return False

#         if '__' in word:
#             return False

#         if word in keyword.kwlist:
#             return False
        
#         return True
    
#     def is_camel_case(word):
#         if not word:
#             return False

#         if ' ' in word:
#             return False

#         if '_' in word:
#             return False

#         if word[0].isupper():
#             return False

#         if any(w[0].isupper() for w in word.split()):
#             return False

#         return True
    
#     def to_capitalized_words(self, word):
#         """return capitalized words
        
#         class naming convention
#         """
#         if self.is_snake_case(word): return string.capwords(word, sep='_').replace('_', '') 
#         return word[0].upper() + word[1:]

#     def snake_to_capwords(self, snake_case):
#         """return capwords"""
#         if self.is_snake_case(snake_case): return snake_case
#         capitalized_words = string.capwords(snake_case, sep='_').replace('_', '')
#         return capitalized_words
        
#     def camel_to_snake(self, camel_case):
#         """return snake case
        
#         method naming convention
#         """
#         if not self.is_camel_case(camel_case): return camel_case.lower()
#         snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
#         return snake_case


def get_module_imports_on_top_of_file(source, import_line_index):
    """return import or from keyword position

    example:
      > 0: import sys
        1: import os
        2:
        3: def function():
    """
    def is_string_literal(line):
        if line[0] in 'uUbB':
            line = line[1:]
        if line and line[0] in 'rR':
            line = line[1:]
        return line and (line[0] == '"' or line[0] == "'")

    def is_future_import(line):
        nodes = ast.parse(line)
        for n in nodes.body:
            if isinstance(n, ast.ImportFrom) and n.module == '__future__':
                return True
        return False

    def has_future_import(source):
        offset = 0
        line = ''
        for _, next_line in source:
            for line_part in next_line.strip().splitlines(True):
                line = line + line_part
                try:
                    return is_future_import(line), offset
                except SyntaxError:
                    continue
            offset += 1
        return False, offset

    allowed_try_keywords = ('try', 'except', 'else', 'finally')
    in_docstring = False
    docstring_kind = '"""'
    source_stream = iter(enumerate(source))
    for cnt, line in source_stream:
        if not in_docstring:
            m = DOCSTRING_START_REGEX.match(line.lstrip())
            if m is not None:
                in_docstring = True
                docstring_kind = m.group('kind')
                remain = line[m.end(): m.endpos].rstrip()
                if remain[-3:] == docstring_kind:  # one line doc
                    in_docstring = False
                continue
        if in_docstring:
            if line.rstrip()[-3:] == docstring_kind:
                in_docstring = False
            continue

        if not line.rstrip():
            continue
        elif line.startswith('#'):
            continue

        if line.startswith('import '):
            if cnt == import_line_index:
                continue
            return cnt
        elif line.startswith('from '):
            if cnt == import_line_index:
                continue
            hit, offset = has_future_import(
                itertools.chain([(cnt, line)], source_stream)
            )
            if hit:
                # move to the back
                return cnt + offset + 1
            return cnt
        elif pycodestyle.DUNDER_REGEX.match(line):
            return cnt
        elif any(line.startswith(kw) for kw in allowed_try_keywords):
            continue
        elif is_string_literal(line):
            return cnt
        else:
            return cnt
    return 0


def get_index_offset_contents(result, source):
    """Return (line_index, column_offset, line_contents)."""
    line_index = result['line'] - 1
    return (line_index,
            result['column'] - 1,
            source[line_index])


def get_fixed_long_line(target, previous_line, original,
                        indent_word='    ', max_line_length=79,
                        aggressive=False, experimental=False, verbose=False):
    """Break up long line and return result.

    Do this by generating multiple reformatted candidates and then
    ranking the candidates to heuristically select the best option.

    """
    indent = _get_indentation(target)
    source = target[len(indent):]
    assert source.lstrip() == source
    assert not target.lstrip().startswith('#')

    # Check for partial multiline.
    tokens = list(generate_tokens(source))

    candidates = shorten_line(
        tokens, source, indent,
        indent_word,
        max_line_length,
        aggressive=aggressive,
        experimental=experimental,
        previous_line=previous_line)

    # Also sort alphabetically as a tie breaker (for determinism).
    candidates = sorted(
        sorted(set(candidates).union([target, original])),
        key=lambda x: line_shortening_rank(
            x,
            indent_word,
            max_line_length,
            experimental=experimental))

    if verbose >= 4:
        print(('-' * 79 + '\n').join([''] + candidates + ['']),
              file=wrap_output(sys.stderr, 'utf-8'))

    if candidates:
        best_candidate = candidates[0]

        # Don't allow things to get longer.
        if longest_line_length(best_candidate) > longest_line_length(original):
            return None

        return best_candidate


def longest_line_length(code):
    """Return length of longest line."""
    if len(code) == 0:
        return 0
    return max(len(line) for line in code.splitlines())


def join_logical_line(logical_line):
    """Return single line based on logical line input."""
    indentation = _get_indentation(logical_line)

    return indentation + untokenize_without_newlines(
        generate_tokens(logical_line.lstrip())) + '\n'


def untokenize_without_newlines(tokens):
    """Return source code based on tokens."""
    text = ''
    last_row = 0
    last_column = -1

    for t in tokens:
        token_string = t[1]
        (start_row, start_column) = t[2]
        (end_row, end_column) = t[3]

        if start_row > last_row:
            last_column = 0
        if (
            (start_column > last_column or token_string == '\n') and
            not text.endswith(' ')
        ):
            text += ' '

        if token_string != '\n':
            text += token_string

        last_row = end_row
        last_column = end_column

    return text.rstrip()


def _find_logical(source_lines):
    # Make a variable which is the index of all the starts of lines.
    logical_start = []
    logical_end = []
    last_newline = True
    parens = 0
    for t in generate_tokens(''.join(source_lines)):
        if t[0] in [tokenize.COMMENT, tokenize.DEDENT,
                    tokenize.INDENT, tokenize.NL,
                    tokenize.ENDMARKER]:
            continue
        if not parens and t[0] in [tokenize.NEWLINE, tokenize.SEMI]:
            last_newline = True
            logical_end.append((t[3][0] - 1, t[2][1]))
            continue
        if last_newline and not parens:
            logical_start.append((t[2][0] - 1, t[2][1]))
            last_newline = False
        if t[0] == tokenize.OP:
            if t[1] in '([{':
                parens += 1
            elif t[1] in '}])':
                parens -= 1
    return (logical_start, logical_end)


def _get_logical(source_lines, result, logical_start, logical_end):
    """Return the logical line corresponding to the result.

    Assumes input is already E702-clean.

    """
    row = result['line'] - 1
    col = result['column'] - 1
    ls = None
    le = None
    for i in range(0, len(logical_start), 1):
        assert logical_end
        x = logical_end[i]
        if x[0] > row or (x[0] == row and x[1] > col):
            le = x
            ls = logical_start[i]
            break
    if ls is None:
        return None
    original = source_lines[ls[0]:le[0] + 1]
    return ls, le, original


def get_item(items, index, default=None):
    if 0 <= index < len(items):
        return items[index]

    return default


def reindent(source, indent_size, leave_tabs=False):
    """Reindent all lines."""
    reindenter = Reindenter(source, leave_tabs)
    return reindenter.run(indent_size)


def code_almost_equal(a, b):
    """Return True if code is similar.

    Ignore whitespace when comparing specific line.

    """
    split_a = split_and_strip_non_empty_lines(a)
    split_b = split_and_strip_non_empty_lines(b)

    if len(split_a) != len(split_b):
        return False

    for (index, _) in enumerate(split_a):
        if ''.join(split_a[index].split()) != ''.join(split_b[index].split()):
            return False

    return True


def split_and_strip_non_empty_lines(text):
    """Return lines split by newline.

    Ignore empty lines.

    """
    return [line.strip() for line in text.splitlines() if line.strip()]


def refactor(source, fixer_names, ignore=None, filename=''):
    """Return refactored code using lib2to3.

    Skip if ignore string is produced in the refactored code.

    """
    not_found_end_of_file_newline = source and source.rstrip("\r\n") == source
    if not_found_end_of_file_newline:
        input_source = source + "\n"
    else:
        input_source = source

    from lib2to3 import pgen2
    try:
        new_text = refactor_with_2to3(input_source,
                                      fixer_names=fixer_names,
                                      filename=filename)
    except (pgen2.parse.ParseError,
            SyntaxError,
            UnicodeDecodeError,
            UnicodeEncodeError):
        return source

    if ignore:
        if ignore in new_text and ignore not in source:
            return source

    if not_found_end_of_file_newline:
        return new_text.rstrip("\r\n")

    return new_text


def code_to_2to3(select, ignore, where='', verbose=False):
    fixes = set()
    for code, fix in CODE_TO_2TO3.items():
        if code_match(code, select=select, ignore=ignore):
            if verbose:
                print('--->  Applying {} fix for {}'.format(where,
                                                            code.upper()),
                      file=sys.stderr)
            fixes |= set(fix)
    return fixes


def fix_2to3(source,
             aggressive=True, select=None, ignore=None, filename='',
             where='global', verbose=False):
    """Fix various deprecated code (via lib2to3)."""
    if not aggressive:
        return source

    select = select or []
    ignore = ignore or []

    return refactor(source,
                    code_to_2to3(select=select,
                                 ignore=ignore,
                                 where=where,
                                 verbose=verbose),
                    filename=filename)


def find_newline(source):
    """Return type of newline used in source.

    Input is a list of lines.

    """
    assert not isinstance(source, str)

    counter = collections.defaultdict(int)
    for line in source:
        if line.endswith(CRLF):
            counter[CRLF] += 1
        elif line.endswith(CR):
            counter[CR] += 1
        elif line.endswith(LF):
            counter[LF] += 1

    return (sorted(counter, key=counter.get, reverse=True) or [LF])[0]


def _get_indentword(source):
    """Return indentation type."""
    indent_word = '    '  # Default in case source has no indentation
    try:
        for t in generate_tokens(source):
            if t[0] == token.INDENT:
                indent_word = t[1]
                break
    except (SyntaxError, tokenize.TokenError):
        pass
    return indent_word


def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''


def get_diff_text(old, new, filename):
    """Return text of unified diff between old and new."""
    newline = '\n'
    diff = difflib.unified_diff(
        old, new,
        'original/' + filename,
        'fixed/' + filename,
        lineterm=newline)

    text = ''
    for line in diff:
        text += line

        # Work around missing newline (http://bugs.python.org/issue2142).
        if text and not line.endswith(newline):
            text += newline + r'\ No newline at end of file' + newline

    return text


def _priority_key(pep8_result):
    """Key for sorting PEP8 results.

    Global fixes should be done first. This is important for things like
    indentation.

    """
    priority = [
        # Fix multiline colon-based before semicolon based.
        'e701',
        # Break multiline statements early.
        'e702',
        # Things that make lines longer.
        'e225', 'e231',
        # Remove extraneous whitespace before breaking lines.
        'e201',
        # Shorten whitespace in comment before resorting to wrapping.
        'e262'
    ]
    middle_index = 10000
    lowest_priority = [
        # We need to shorten lines last since the logical fixer can get in a
        # loop, which causes us to exit early.
        'e501',
    ]
    key = pep8_result['id'].lower()
    try:
        return priority.index(key)
    except ValueError:
        try:
            return middle_index + lowest_priority.index(key) + 1
        except ValueError:
            return middle_index


def shorten_line(tokens, source, indentation, indent_word, max_line_length,
                 aggressive=False, experimental=False, previous_line=''):
    """Separate line at OPERATOR.

    Multiple candidates will be yielded.

    """
    for candidate in _shorten_line(tokens=tokens,
                                   source=source,
                                   indentation=indentation,
                                   indent_word=indent_word,
                                   aggressive=aggressive,
                                   previous_line=previous_line):
        yield candidate

    if aggressive:
        for key_token_strings in SHORTEN_OPERATOR_GROUPS:
            shortened = _shorten_line_at_tokens(
                tokens=tokens,
                source=source,
                indentation=indentation,
                indent_word=indent_word,
                key_token_strings=key_token_strings,
                aggressive=aggressive)

            if shortened is not None and shortened != source:
                yield shortened

    if experimental:
        for shortened in _shorten_line_at_tokens_new(
                tokens=tokens,
                source=source,
                indentation=indentation,
                max_line_length=max_line_length):

            yield shortened


def _shorten_line(tokens, source, indentation, indent_word,
                  aggressive=False, previous_line=''):
    """Separate line at OPERATOR.

    The input is expected to be free of newlines except for inside multiline
    strings and at the end.

    Multiple candidates will be yielded.

    """
    for (token_type,
         token_string,
         start_offset,
         end_offset) in token_offsets(tokens):

        if (
            token_type == tokenize.COMMENT and
            not is_probably_part_of_multiline(previous_line) and
            not is_probably_part_of_multiline(source) and
            not source[start_offset + 1:].strip().lower().startswith(
                ('noqa', 'pragma:', 'pylint:'))
        ):
            # Move inline comments to previous line.
            first = source[:start_offset]
            second = source[start_offset:]
            yield (indentation + second.strip() + '\n' +
                   indentation + first.strip() + '\n')
        elif token_type == token.OP and token_string != '=':
            # Don't break on '=' after keyword as this violates PEP 8.

            assert token_type != token.INDENT

            first = source[:end_offset]

            second_indent = indentation
            if (first.rstrip().endswith('(') and
                    source[end_offset:].lstrip().startswith(')')):
                pass
            elif first.rstrip().endswith('('):
                second_indent += indent_word
            elif '(' in first:
                second_indent += ' ' * (1 + first.find('('))
            else:
                second_indent += indent_word

            second = (second_indent + source[end_offset:].lstrip())
            if (
                not second.strip() or
                second.lstrip().startswith('#')
            ):
                continue

            # Do not begin a line with a comma
            if second.lstrip().startswith(','):
                continue
            # Do end a line with a dot
            if first.rstrip().endswith('.'):
                continue
            if token_string in '+-*/':
                fixed = first + ' \\' + '\n' + second
            else:
                fixed = first + '\n' + second

            # Only fix if syntax is okay.
            if check_syntax(normalize_multiline(fixed)
                            if aggressive else fixed):
                yield indentation + fixed


def _is_binary_operator(token_type, text):
    return ((token_type == tokenize.OP or text in ['and', 'or']) and
            text not in '()[]{},:.;@=%~')


# A convenient way to handle tokens.
Token = collections.namedtuple('Token', ['token_type', 'token_string',
                                         'spos', 'epos', 'line'])


class ReformattedLines(object):

    """The reflowed lines of atoms.

    Each part of the line is represented as an "atom." They can be moved
    around when need be to get the optimal formatting.

    """

    ###########################################################################
    # Private Classes

    class _Indent(object):

        """Represent an indentation in the atom stream."""

        def __init__(self, indent_amt):
            self._indent_amt = indent_amt

        def emit(self):
            return ' ' * self._indent_amt

        @property
        def size(self):
            return self._indent_amt

    class _Space(object):

        """Represent a space in the atom stream."""

        def emit(self):
            return ' '

        @property
        def size(self):
            return 1

    class _LineBreak(object):

        """Represent a line break in the atom stream."""

        def emit(self):
            return '\n'

        @property
        def size(self):
            return 0

    def __init__(self, max_line_length):
        self._max_line_length = max_line_length
        self._lines = []
        self._bracket_depth = 0
        self._prev_item = None
        self._prev_prev_item = None

    def __repr__(self):
        return self.emit()

    ###########################################################################
    # Public Methods

    def add(self, obj, indent_amt, break_after_open_bracket):
        if isinstance(obj, Atom):
            self._add_item(obj, indent_amt)
            return

        self._add_container(obj, indent_amt, break_after_open_bracket)

    def add_comment(self, item):
        num_spaces = 2
        if len(self._lines) > 1:
            if isinstance(self._lines[-1], self._Space):
                num_spaces -= 1
            if len(self._lines) > 2:
                if isinstance(self._lines[-2], self._Space):
                    num_spaces -= 1

        while num_spaces > 0:
            self._lines.append(self._Space())
            num_spaces -= 1
        self._lines.append(item)

    def add_indent(self, indent_amt):
        self._lines.append(self._Indent(indent_amt))

    def add_line_break(self, indent):
        self._lines.append(self._LineBreak())
        self.add_indent(len(indent))

    def add_line_break_at(self, index, indent_amt):
        self._lines.insert(index, self._LineBreak())
        self._lines.insert(index + 1, self._Indent(indent_amt))

    def add_space_if_needed(self, curr_text, equal=False):
        if (
            not self._lines or isinstance(
                self._lines[-1], (self._LineBreak, self._Indent, self._Space))
        ):
            return

        prev_text = str(self._prev_item)
        prev_prev_text = (
            str(self._prev_prev_item) if self._prev_prev_item else '')

        if (
            # The previous item was a keyword or identifier and the current
            # item isn't an operator that doesn't require a space.
            ((self._prev_item.is_keyword or self._prev_item.is_string or
              self._prev_item.is_name or self._prev_item.is_number) and
             (curr_text[0] not in '([{.,:}])' or
              (curr_text[0] == '=' and equal))) or

            # Don't place spaces around a '.', unless it's in an 'import'
            # statement.
            ((prev_prev_text != 'from' and prev_text[-1] != '.' and
              curr_text != 'import') and

             # Don't place a space before a colon.
             curr_text[0] != ':' and

             # Don't split up ending brackets by spaces.
             ((prev_text[-1] in '}])' and curr_text[0] not in '.,}])') or

              # Put a space after a colon or comma.
              prev_text[-1] in ':,' or

              # Put space around '=' if asked to.
              (equal and prev_text == '=') or

              # Put spaces around non-unary arithmetic operators.
              ((self._prev_prev_item and
                (prev_text not in '+-' and
                 (self._prev_prev_item.is_name or
                  self._prev_prev_item.is_number or
                  self._prev_prev_item.is_string)) and
                prev_text in ('+', '-', '%', '*', '/', '//', '**', 'in')))))
        ):
            self._lines.append(self._Space())

    def previous_item(self):
        """Return the previous non-whitespace item."""
        return self._prev_item

    def fits_on_current_line(self, item_extent):
        return self.current_size() + item_extent <= self._max_line_length

    def current_size(self):
        """The size of the current line minus the indentation."""
        size = 0
        for item in reversed(self._lines):
            size += item.size
            if isinstance(item, self._LineBreak):
                break

        return size

    def line_empty(self):
        return (self._lines and
                isinstance(self._lines[-1],
                           (self._LineBreak, self._Indent)))

    def emit(self):
        string = ''
        for item in self._lines:
            if isinstance(item, self._LineBreak):
                string = string.rstrip()
            string += item.emit()

        return string.rstrip() + '\n'

    ###########################################################################
    # Private Methods

    def _add_item(self, item, indent_amt):
        """Add an item to the line.

        Reflow the line to get the best formatting after the item is
        inserted. The bracket depth indicates if the item is being
        inserted inside of a container or not.

        """
        if self._prev_item and self._prev_item.is_string and item.is_string:
            # Place consecutive string literals on separate lines.
            self._lines.append(self._LineBreak())
            self._lines.append(self._Indent(indent_amt))

        item_text = str(item)
        if self._lines and self._bracket_depth:
            # Adding the item into a container.
            self._prevent_default_initializer_splitting(item, indent_amt)

            if item_text in '.,)]}':
                self._split_after_delimiter(item, indent_amt)

        elif self._lines and not self.line_empty():
            # Adding the item outside of a container.
            if self.fits_on_current_line(len(item_text)):
                self._enforce_space(item)

            else:
                # Line break for the new item.
                self._lines.append(self._LineBreak())
                self._lines.append(self._Indent(indent_amt))

        self._lines.append(item)
        self._prev_item, self._prev_prev_item = item, self._prev_item

        if item_text in '([{':
            self._bracket_depth += 1

        elif item_text in '}])':
            self._bracket_depth -= 1
            assert self._bracket_depth >= 0

    def _add_container(self, container, indent_amt, break_after_open_bracket):
        actual_indent = indent_amt + 1

        if (
            str(self._prev_item) != '=' and
            not self.line_empty() and
            not self.fits_on_current_line(
                container.size + self._bracket_depth + 2)
        ):

            if str(container)[0] == '(' and self._prev_item.is_name:
                # Don't split before the opening bracket of a call.
                break_after_open_bracket = True
                actual_indent = indent_amt + 4
            elif (
                break_after_open_bracket or
                str(self._prev_item) not in '([{'
            ):
                # If the container doesn't fit on the current line and the
                # current line isn't empty, place the container on the next
                # line.
                self._lines.append(self._LineBreak())
                self._lines.append(self._Indent(indent_amt))
                break_after_open_bracket = False
        else:
            actual_indent = self.current_size() + 1
            break_after_open_bracket = False

        if isinstance(container, (ListComprehension, IfExpression)):
            actual_indent = indent_amt

        # Increase the continued indentation only if recursing on a
        # container.
        container.reflow(self, ' ' * actual_indent,
                         break_after_open_bracket=break_after_open_bracket)

    def _prevent_default_initializer_splitting(self, item, indent_amt):
        """Prevent splitting between a default initializer.

        When there is a default initializer, it's best to keep it all on
        the same line. It's nicer and more readable, even if it goes
        over the maximum allowable line length. This goes back along the
        current line to determine if we have a default initializer, and,
        if so, to remove extraneous whitespaces and add a line
        break/indent before it if needed.

        """
        if str(item) == '=':
            # This is the assignment in the initializer. Just remove spaces for
            # now.
            self._delete_whitespace()
            return

        if (not self._prev_item or not self._prev_prev_item or
                str(self._prev_item) != '='):
            return

        self._delete_whitespace()
        prev_prev_index = self._lines.index(self._prev_prev_item)

        if (
            isinstance(self._lines[prev_prev_index - 1], self._Indent) or
            self.fits_on_current_line(item.size + 1)
        ):
            # The default initializer is already the only item on this line.
            # Don't insert a newline here.
            return

        # Replace the space with a newline/indent combo.
        if isinstance(self._lines[prev_prev_index - 1], self._Space):
            del self._lines[prev_prev_index - 1]

        self.add_line_break_at(self._lines.index(self._prev_prev_item),
                               indent_amt)

    def _split_after_delimiter(self, item, indent_amt):
        """Split the line only after a delimiter."""
        self._delete_whitespace()

        if self.fits_on_current_line(item.size):
            return

        last_space = None
        for current_item in reversed(self._lines):
            if (
                last_space and
                (not isinstance(current_item, Atom) or
                 not current_item.is_colon)
            ):
                break
            else:
                last_space = None
            if isinstance(current_item, self._Space):
                last_space = current_item
            if isinstance(current_item, (self._LineBreak, self._Indent)):
                return

        if not last_space:
            return

        self.add_line_break_at(self._lines.index(last_space), indent_amt)

    def _enforce_space(self, item):
        """Enforce a space in certain situations.

        There are cases where we will want a space where normally we
        wouldn't put one. This just enforces the addition of a space.

        """
        if isinstance(self._lines[-1],
                      (self._Space, self._LineBreak, self._Indent)):
            return

        if not self._prev_item:
            return

        item_text = str(item)
        prev_text = str(self._prev_item)

        # Prefer a space around a '.' in an import statement, and between the
        # 'import' and '('.
        if (
            (item_text == '.' and prev_text == 'from') or
            (item_text == 'import' and prev_text == '.') or
            (item_text == '(' and prev_text == 'import')
        ):
            self._lines.append(self._Space())

    def _delete_whitespace(self):
        """Delete all whitespace from the end of the line."""
        while isinstance(self._lines[-1], (self._Space, self._LineBreak,
                                           self._Indent)):
            del self._lines[-1]


class Atom(object):

    """The smallest unbreakable unit that can be reflowed."""

    def __init__(self, atom):
        self._atom = atom

    def __repr__(self):
        return self._atom.token_string

    def __len__(self):
        return self.size

    def reflow(
        self, reflowed_lines, continued_indent, extent,
        break_after_open_bracket=False,
        is_list_comp_or_if_expr=False,
        next_is_dot=False
    ):
        if self._atom.token_type == tokenize.COMMENT:
            reflowed_lines.add_comment(self)
            return

        total_size = extent if extent else self.size

        if self._atom.token_string not in ',:([{}])':
            # Some atoms will need an extra 1-sized space token after them.
            total_size += 1

        prev_item = reflowed_lines.previous_item()
        if (
            not is_list_comp_or_if_expr and
            not reflowed_lines.fits_on_current_line(total_size) and
            not (next_is_dot and
                 reflowed_lines.fits_on_current_line(self.size + 1)) and
            not reflowed_lines.line_empty() and
            not self.is_colon and
            not (prev_item and prev_item.is_name and
                 str(self) == '(')
        ):
            # Start a new line if there is already something on the line and
            # adding this atom would make it go over the max line length.
            reflowed_lines.add_line_break(continued_indent)
        else:
            reflowed_lines.add_space_if_needed(str(self))

        reflowed_lines.add(self, len(continued_indent),
                           break_after_open_bracket)

    def emit(self):
        return self.__repr__()

    @property
    def is_keyword(self):
        return keyword.iskeyword(self._atom.token_string)

    @property
    def is_string(self):
        return self._atom.token_type == tokenize.STRING

    @property
    def is_name(self):
        return self._atom.token_type == tokenize.NAME

    @property
    def is_number(self):
        return self._atom.token_type == tokenize.NUMBER

    @property
    def is_comma(self):
        return self._atom.token_string == ','

    @property
    def is_colon(self):
        return self._atom.token_string == ':'

    @property
    def size(self):
        return len(self._atom.token_string)


class Container(object):

    """Base class for all container types."""

    def __init__(self, items):
        self._items = items

    def __repr__(self):
        string = ''
        last_was_keyword = False

        for item in self._items:
            if item.is_comma:
                string += ', '
            elif item.is_colon:
                string += ': '
            else:
                item_string = str(item)
                if (
                    string and
                    (last_was_keyword or
                     (not string.endswith(tuple('([{,.:}]) ')) and
                      not item_string.startswith(tuple('([{,.:}])'))))
                ):
                    string += ' '
                string += item_string

            last_was_keyword = item.is_keyword
        return string

    def __iter__(self):
        for element in self._items:
            yield element

    def __getitem__(self, idx):
        return self._items[idx]

    def reflow(self, reflowed_lines, continued_indent,
               break_after_open_bracket=False):
        last_was_container = False
        for (index, item) in enumerate(self._items):
            next_item = get_item(self._items, index + 1)

            if isinstance(item, Atom):
                is_list_comp_or_if_expr = (
                    isinstance(self, (ListComprehension, IfExpression)))
                item.reflow(reflowed_lines, continued_indent,
                            self._get_extent(index),
                            is_list_comp_or_if_expr=is_list_comp_or_if_expr,
                            next_is_dot=(next_item and
                                         str(next_item) == '.'))
                if last_was_container and item.is_comma:
                    reflowed_lines.add_line_break(continued_indent)
                last_was_container = False
            else:  # isinstance(item, Container)
                reflowed_lines.add(item, len(continued_indent),
                                   break_after_open_bracket)
                last_was_container = not isinstance(item, (ListComprehension,
                                                           IfExpression))

            if (
                break_after_open_bracket and index == 0 and
                # Prefer to keep empty containers together instead of
                # separating them.
                str(item) == self.open_bracket and
                (not next_item or str(next_item) != self.close_bracket) and
                (len(self._items) != 3 or not isinstance(next_item, Atom))
            ):
                reflowed_lines.add_line_break(continued_indent)
                break_after_open_bracket = False
            else:
                next_next_item = get_item(self._items, index + 2)
                if (
                    str(item) not in ['.', '%', 'in'] and
                    next_item and not isinstance(next_item, Container) and
                    str(next_item) != ':' and
                    next_next_item and (not isinstance(next_next_item, Atom) or
                                        str(next_item) == 'not') and
                    not reflowed_lines.line_empty() and
                    not reflowed_lines.fits_on_current_line(
                        self._get_extent(index + 1) + 2)
                ):
                    reflowed_lines.add_line_break(continued_indent)

    def _get_extent(self, index):
        """The extent of the full element.

        E.g., the length of a function call or keyword.

        """
        extent = 0
        prev_item = get_item(self._items, index - 1)
        seen_dot = prev_item and str(prev_item) == '.'
        while index < len(self._items):
            item = get_item(self._items, index)
            index += 1

            if isinstance(item, (ListComprehension, IfExpression)):
                break

            if isinstance(item, Container):
                if prev_item and prev_item.is_name:
                    if seen_dot:
                        extent += 1
                    else:
                        extent += item.size

                    prev_item = item
                    continue
            elif (str(item) not in ['.', '=', ':', 'not'] and
                  not item.is_name and not item.is_string):
                break

            if str(item) == '.':
                seen_dot = True

            extent += item.size
            prev_item = item

        return extent

    @property
    def is_string(self):
        return False

    @property
    def size(self):
        return len(self.__repr__())

    @property
    def is_keyword(self):
        return False

    @property
    def is_name(self):
        return False

    @property
    def is_comma(self):
        return False

    @property
    def is_colon(self):
        return False

    @property
    def open_bracket(self):
        return None

    @property
    def close_bracket(self):
        return None


class Tuple(Container):

    """A high-level representation of a tuple."""

    @property
    def open_bracket(self):
        return '('

    @property
    def close_bracket(self):
        return ')'


class List(Container):

    """A high-level representation of a list."""

    @property
    def open_bracket(self):
        return '['

    @property
    def close_bracket(self):
        return ']'


class DictOrSet(Container):

    """A high-level representation of a dictionary or set."""

    @property
    def open_bracket(self):
        return '{'

    @property
    def close_bracket(self):
        return '}'


class ListComprehension(Container):

    """A high-level representation of a list comprehension."""

    @property
    def size(self):
        length = 0
        for item in self._items:
            if isinstance(item, IfExpression):
                break
            length += item.size
        return length


class IfExpression(Container):

    """A high-level representation of an if-expression."""


def _parse_container(tokens, index, for_or_if=None):
    """Parse a high-level container, such as a list, tuple, etc."""

    # Store the opening bracket.
    items = [Atom(Token(*tokens[index]))]
    index += 1

    num_tokens = len(tokens)
    while index < num_tokens:
        tok = Token(*tokens[index])

        if tok.token_string in ',)]}':
            # First check if we're at the end of a list comprehension or
            # if-expression. Don't add the ending token as part of the list
            # comprehension or if-expression, because they aren't part of those
            # constructs.
            if for_or_if == 'for':
                return (ListComprehension(items), index - 1)

            elif for_or_if == 'if':
                return (IfExpression(items), index - 1)

            # We've reached the end of a container.
            items.append(Atom(tok))

            # If not, then we are at the end of a container.
            if tok.token_string == ')':
                # The end of a tuple.
                return (Tuple(items), index)

            elif tok.token_string == ']':
                # The end of a list.
                return (List(items), index)

            elif tok.token_string == '}':
                # The end of a dictionary or set.
                return (DictOrSet(items), index)

        elif tok.token_string in '([{':
            # A sub-container is being defined.
            (container, index) = _parse_container(tokens, index)
            items.append(container)

        elif tok.token_string == 'for':
            (container, index) = _parse_container(tokens, index, 'for')
            items.append(container)

        elif tok.token_string == 'if':
            (container, index) = _parse_container(tokens, index, 'if')
            items.append(container)

        else:
            items.append(Atom(tok))

        index += 1

    return (None, None)


def _parse_tokens(tokens):
    """Parse the tokens.

    This converts the tokens into a form where we can manipulate them
    more easily.

    """

    index = 0
    parsed_tokens = []

    num_tokens = len(tokens)
    while index < num_tokens:
        tok = Token(*tokens[index])

        assert tok.token_type != token.INDENT
        if tok.token_type == tokenize.NEWLINE:
            # There's only one newline and it's at the end.
            break

        if tok.token_string in '([{':
            (container, index) = _parse_container(tokens, index)
            if not container:
                return None
            parsed_tokens.append(container)
        else:
            parsed_tokens.append(Atom(tok))

        index += 1
    print(parsed_tokens)
    return parsed_tokens


def _reflow_lines(parsed_tokens, indentation, max_line_length,
                  start_on_prefix_line):
    """Reflow the lines so that it looks nice."""

    if str(parsed_tokens[0]) == 'def':
        # A function definition gets indented a bit more.
        continued_indent = indentation + ' ' * 2 * DEFAULT_INDENT_SIZE
    else:
        continued_indent = indentation + ' ' * DEFAULT_INDENT_SIZE

    break_after_open_bracket = not start_on_prefix_line

    lines = ReformattedLines(max_line_length)
    lines.add_indent(len(indentation.lstrip('\r\n')))

    if not start_on_prefix_line:
        # If splitting after the opening bracket will cause the first element
        # to be aligned weirdly, don't try it.
        first_token = get_item(parsed_tokens, 0)
        second_token = get_item(parsed_tokens, 1)

        if (
            first_token and second_token and
            str(second_token)[0] == '(' and
            len(indentation) + len(first_token) + 1 == len(continued_indent)
        ):
            return None

    for item in parsed_tokens:
        lines.add_space_if_needed(str(item), equal=True)

        save_continued_indent = continued_indent
        if start_on_prefix_line and isinstance(item, Container):
            start_on_prefix_line = False
            continued_indent = ' ' * (lines.current_size() + 1)

        item.reflow(lines, continued_indent, break_after_open_bracket)
        continued_indent = save_continued_indent

    return lines.emit()


def _shorten_line_at_tokens_new(tokens, source, indentation,
                                max_line_length):
    """Shorten the line taking its length into account.

    The input is expected to be free of newlines except for inside
    multiline strings and at the end.

    """
    # Yield the original source so to see if it's a better choice than the
    # shortened candidate lines we generate here.
    yield indentation + source

    parsed_tokens = _parse_tokens(tokens)

    if parsed_tokens:
        # Perform two reflows. The first one starts on the same line as the
        # prefix. The second starts on the line after the prefix.
        fixed = _reflow_lines(parsed_tokens, indentation, max_line_length,
                              start_on_prefix_line=True)
        if fixed and check_syntax(normalize_multiline(fixed.lstrip())):
            yield fixed

        fixed = _reflow_lines(parsed_tokens, indentation, max_line_length,
                              start_on_prefix_line=False)
        if fixed and check_syntax(normalize_multiline(fixed.lstrip())):
            yield fixed


def _shorten_line_at_tokens(tokens, source, indentation, indent_word,
                            key_token_strings, aggressive):
    """Separate line by breaking at tokens in key_token_strings.

    The input is expected to be free of newlines except for inside
    multiline strings and at the end.
    """
    offsets = []
    for (index, _t) in enumerate(token_offsets(tokens)):
        (token_type,
         token_string,
         start_offset,
         end_offset) = _t

        assert token_type != token.INDENT

        if token_string in key_token_strings:
            # Do not break in containers with zero or one items.
            unwanted_next_token = {
                '(': ')',
                '[': ']',
                '{': '}'}.get(token_string)
            if unwanted_next_token:
                if (
                    get_item(tokens,
                             index + 1,
                             default=[None, None])[1] == unwanted_next_token or
                    get_item(tokens,
                             index + 2,
                             default=[None, None])[1] == unwanted_next_token
                ):
                    continue

            if (
                index > 2 and token_string == '(' and
                tokens[index - 1][1] in ',(%['
            ):
                # Don't split after a tuple start, or before a tuple start if
                # the tuple is in a list.
                continue

            if end_offset < len(source) - 1:
                # Don't split right before newline.
                offsets.append(end_offset)
        else:
            # Break at adjacent strings. These were probably meant to be on
            # separate lines in the first place.
            previous_token = get_item(tokens, index - 1)
            if (
                token_type == tokenize.STRING and
                previous_token and previous_token[0] == tokenize.STRING
            ):
                offsets.append(start_offset)

    current_indent = None
    fixed = None
    for line in split_at_offsets(source, offsets):
        if fixed:
            fixed += '\n' + current_indent + line

            for symbol in '([{':
                if line.endswith(symbol):
                    current_indent += indent_word
        else:
            # First line.
            fixed = line
            assert not current_indent
            current_indent = indent_word

    assert fixed is not None

    if check_syntax(normalize_multiline(fixed)
                    if aggressive > 1 else fixed):
        return indentation + fixed

    return None


def token_offsets(tokens):
    """Yield tokens and offsets."""
    end_offset = 0
    previous_end_row = 0
    previous_end_column = 0
    for t in tokens:
        token_type = t[0]
        token_string = t[1]
        (start_row, start_column) = t[2]
        (end_row, end_column) = t[3]

        # Account for the whitespace between tokens.
        end_offset += start_column
        if previous_end_row == start_row:
            end_offset -= previous_end_column

        # Record the start offset of the token.
        start_offset = end_offset

        # Account for the length of the token itself.
        end_offset += len(token_string)

        yield (token_type,
               token_string,
               start_offset,
               end_offset)

        previous_end_row = end_row
        previous_end_column = end_column


def normalize_multiline(line):
    """Normalize multiline-related code that will cause syntax error.

    This is for purposes of checking syntax.

    """
    if line.startswith('def ') and line.rstrip().endswith(':'):
        return line + ' pass'
    elif line.startswith('return '):
        return 'def _(): ' + line
    elif line.startswith('@'):
        return line + 'def _(): pass'
    elif line.startswith('class '):
        return line + ' pass'
    elif line.startswith(('if ', 'elif ', 'for ', 'while ')):
        return line + ' pass'

    return line


def fix_whitespace(line, offset, replacement):
    """Replace whitespace at offset and return fixed line."""
    # Replace escaped newlines too
    left = line[:offset].rstrip('\n\r \t\\')
    right = line[offset:].lstrip('\n\r \t\\')
    if right.startswith('#'):
        return line

    return left + replacement + right


def _execute_pep8(pep8_options, source):
    """Execute pycodestyle via python method calls."""
    class QuietReport(pycodestyle.BaseReport):

        """Version of checker that does not print."""

        def __init__(self, options):
            super(QuietReport, self).__init__(options)
            self.__full_error_results = []

        def error(self, line_number, offset, text, check):
            """Collect errors."""
            code = super(QuietReport, self).error(line_number,
                                                  offset,
                                                  text,
                                                  check)
            if code:
                self.__full_error_results.append(
                    {'id': code,
                     'line': line_number,
                     'column': offset + 1,
                     'info': text})

        def full_error_results(self):
            """Return error results in detail.

            Results are in the form of a list of dictionaries. Each
            dictionary contains 'id', 'line', 'column', and 'info'.

            """
            return self.__full_error_results

    checker = pycodestyle.Checker('', lines=source, reporter=QuietReport,
                                  **pep8_options)
    checker.check_all()
    return checker.report.full_error_results()

def _remove_leading_and_normalize(line, with_rstrip=True):
    # ignore FF in first lstrip()
    if with_rstrip:
        return line.lstrip(' \t\v').rstrip(CR + LF) + '\n'
    return line.lstrip(' \t\v')

#김위성##############################################################################################################################
"""
잘못 들여쓰기된 코드 4개의 공백 들여쓰기로 다시 들여씀
object - 소스(source), 남은 탭(leave_tab)
"""
class Reindenter(object):
    """Reindents badly-indented code to uniformly use four-space indentation.

    Released to the public domain, by Tim Peters, 03 October 2000.
    """
    
    
    """
    input_text : 분석할 source code를 문자열로 입력받음
    leave_tabs : True면 들여쓰기에 사용되는 탭 문자를 삭제하지 않고 그대로 둡니다.
                False면 탭 문자를 공백으로 바꿈 -> PEP-8에서 탭 대신 공백 4칸 권장.
    """
    def __init__(self, input_text, leave_tabs=False):
        
        # io.StringIO()를 사용하면 input_text를 읽기 전용으로 처리할 수 있다.
        sio = io.StringIO(input_text)  
        
        #sio.readlines() 모든 줄을 읽음
        source_lines = sio.readlines()  

        """ 
        multiline_string_lines 함수를 사용하여 
        input_text에서 멀티라인 문자열의 첫 줄 번호 목록을 
        가져와 string_content_line_numbers 변수에 저장합니다.
        
        multiline_string_lines(input_text)는 아래와 같은 코드에서 1을 반환
        line_number
        1 if a > b 
        2     and b < c
        3     and c < d: print("hello")
        """
        self.string_content_line_numbers = multiline_string_lines(input_text)

        # File lines, rstripped & tab-expanded. Dummy at start is so
        # that we can use tokenize's 1-based line numbering easily.
        # Note that a line is all-blank iff it is a newline.
        # 파일 라인이 줄 바뀜하고 탭을 확장시킨다. 
        # 각 줄의 번호와 해당 줄 내용(소스 코드)를 튜플로 저장시켜준다.! -> 
        # init 이기 때문에 일단 소스 분석하고 저장만 함.
        # 때문에 start=1로 설정, 새 줄(new line)이면 해당 라인의 소스코드가 없겠지
        self.lines = []
        for line_number, line in enumerate(source_lines, start=1):
            # Do not modify if inside a multiline string.
            
            # 라인이 멀티라인이면
            if line_number in self.string_content_line_numbers:
                self.lines.append(line)
            else: # 라인이 멀티라인이 아니면 
                # Only expand leading tabs.
                with_rstrip = line_number != len(source_lines)
                if leave_tabs: # leave_tabs가 True면 tab을 공백 4칸으로 안 바꾸고 들여쓰기로 사용
                    
                    # _remove_leading_and_normalize 함수를 사용하여 
                    # 해당 줄의 앞쪽 공백 문자를 삭제하고
                    self.lines.append(
                        _get_indentation(line) +
                        _remove_leading_and_normalize(line, with_rstrip)
                    )
                else: #  False이면 탭 문자를 공백으로 바꿈
                    #  _remove_leading_and_normalize 함수를 사용하여 
                    # 해당 줄의 앞쪽 공백 문자를 삭제합니다. 이렇게 처리된 줄은 lines 리스트에 추가됩니다.
                    self.lines.append(
                        _get_indentation(line).expandtabs() +
                        _remove_leading_and_normalize(line, with_rstrip)
                    )

        # 마지막으로, None 값을 lines 리스트의 첫 번째 요소로 추가하고, 
        # index 변수를 1로 초기화합니다. index 변수는 소스 코드에서 다음으로 처리할 줄의 인덱스를 나타냄
        # input_text 변수는 생성자가 호출될 때 받은 input_text 매개변수의 값을 그대로 저장합니다.
        self.lines.insert(0, None)
        self.index = 1  # index into self.lines of next line
        self.input_text = input_text

    """
    들여쓰기를 수정하고, 라인 번호를 수정함.
    line number는 1부터 인덱스 되어있다.
    indent_size=DEFAULT_INDENT_SIZE인데 
    DEFAULT_INDENT_SIZE = 4, 공백 4칸을 디폴트로 들여쓰기 하겠다는 뜻
    """
    def run(self, indent_size=DEFAULT_INDENT_SIZE):
        """Fix indentation and return modified line numbers.

        Line numbers are indexed at 1.
        
        """
        if indent_size < 1:
            return self.input_text

        # _reindent_stats 함수는 tokenize.generate_tokens 함수를 사용하여 코드를 분석하고, 
        # 코드의 각 줄에 대한 들여쓰기 상태를 반환
        # tokenize.generate_tokens(self.getline)을 활용하여 
        # 라인의 문자열 상태 반환받음 (라인 번호와 들여쓰기 레벨)
        try:
            stats = _reindent_stats(tokenize.generate_tokens(self.getline))
        except (SyntaxError, tokenize.TokenError):  # 라인에 구문 에러나 토큰 에러 있을 경우 
            return self.input_text
        
        # Remove trailing empty lines. - 뒤의 빈 라인 지우려고 line변수 사용
        lines = self.lines
        
        # Sentinel.  - 작업하는 라인의 길이
        stats.append((len(lines), 0))
        
        # Map count of leading spaces to # we want. - 각 줄의 들여쓰기가 어떻게 바뀔지를 나타내는 딕셔너리 have2want
        have2want = {}
        # Program after transformation.
        # after는 들여쓰기가 변환된 코드 저장
        after = []
        # Copy over initial empty lines -- there's nothing to do until
        # we see a line with *something* on it.
        i = stats[0][0]
        after.extend(lines[1:i])
        
        """
        1. 들여쓰기를 조정할 라인을 선택합니다.
        2. 해당 라인의 현재 들여쓰기 수(have)와 원하는 들여쓰기 수(want)를 계산합니다.
        3. have 값과 want 값을 기억해 두는데, have 값이 같으면 want 값도 같도록 매핑(mapping)합니다.
        4. 현재 라인의 들여쓰기 수(have)와 원하는 들여쓰기 수(want)의 차이(diff)를 계산합니다.
        5. diff 값에 따라 들여쓰기를 적절히 조정합니다.
            diff 값이 0이면 들여쓰기를 조정하지 않습니다.
            diff 값이 양수이면 들여쓰기 수를 늘립니다.
            diff 값이 음수이면 들여쓰기 수를 줄입니다.
        6. 적절한 들여쓰기가 적용된 라인을 after 리스트에 추가합니다.
        """
        for i in range(len(stats) - 1):
            thisstmt, thislevel = stats[i]
            nextstmt = stats[i + 1][0]
            have = _leading_space_count(lines[thisstmt])
            want = thislevel * indent_size
            if want < 0:
                # A comment line.
                if have:
                    # An indented comment line. If we saw the same
                    # indentation before, reuse what it most recently
                    # mapped to.
                    want = have2want.get(have, -1)
                    if want < 0:
                        # Then it probably belongs to the next real stmt.
                        for j in range(i + 1, len(stats) - 1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                if have == _leading_space_count(lines[jline]):
                                    want = jlevel * indent_size
                                break
                    # Maybe it's a hanging comment like this one,
                    if want < 0:
                        # in which case we should shift it like its base
                        # line got shifted.
                        for j in range(i - 1, -1, -1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                want = (have + _leading_space_count(
                                        after[jline - 1]) -
                                        _leading_space_count(lines[jline]))
                                break
                    if want < 0:
                        # Still no luck -- leave it alone.
                        want = have
                else:
                    want = 0
            assert want >= 0
            have2want[have] = want
            diff = want - have
            if diff == 0 or have == 0:
                after.extend(lines[thisstmt:nextstmt])
            else:
                for line_number, line in enumerate(lines[thisstmt:nextstmt],
                                                    start=thisstmt):
                    if line_number in self.string_content_line_numbers:
                        after.append(line)
                    elif diff > 0:
                        if line == '\n':
                            after.append(line)
                        else:
                            after.append(' ' * diff + line)
                    else:
                        remove = min(_leading_space_count(line), -diff)
                        after.append(line[remove:])

        return ''.join(after)

    # 토크나이징을 위한 라인 반환
    def getline(self):
        """Line-getter for tokenize."""
        if self.index >= len(self.lines):
            line = ''
        else:
            line = self.lines[self.index]
            self.index += 1
        return line

"""
line number와 indent level을 결정하여 반환해준다.
각 라인의 statement와 주석 라인을 처리
주석 라인은 indent level이 -1로 처리했는데,
    토큰화하는 signal이 주석에 대해 뭘 처리해줘야 될지 모르기 때문이다. 이건 autopep8 측도 해결 안된듯.
    
tokens 매개변수는 tokenize.generate_tokens()에 의해 토크나이징된 (문자열)이터레이터
"""
def _reindent_stats(tokens):
    """Return list of (lineno, indentlevel) pairs.

    One for each stmt and comment line. indentlevel is -1 for comment
    lines, as a signal that tokenize doesn't know what to do about them;
    indeed, they're our headache!

    """
    find_stmt = 1  # Next token begins a fresh stmt? - 다음 토큰이 새로운 statement를 시작하는 놈인지
    level = 0  # Current indent level. - 현재 들여쓰기 레벨 저장하는 level 변수
    stats = []

    for t in tokens:
        token_type = t[0]
        sline = t[2][0]
        line = t[4]

        # tokenize.NEWLINE 토큰이 나오면, 
        # 새로운 문장이 시작될 것이기 때문에. find_stmt를 1로 설정해줌
        if token_type == tokenize.NEWLINE: 
            # A program statement, or ENDMARKER, will eventually follow,
            # after some (possibly empty) run of tokens of the form
            #     (NL | COMMENT)* (INDENT | DEDENT+)?
            find_stmt = 1

        # tokenize.INDENT 토큰이 나오면, 새로운 문장이 시작하기 때문에  
        # find_stmt를 1로 설정하고, level을 1 증가시킴
        elif token_type == tokenize.INDENT:
            find_stmt = 1
            level += 1

        # tokenize.DEDENT 토큰이 나오면, 새로운 문장이 시작될 것입니다. 
        #   -> DEDENT는 INDENT라인이 끝나고 나오는 라인
        #   elif token_type == tokenize.DEDENT:
        #       find_stmt = 1
        #       level -= 1
        #   #### 위 코드를 예시로 따지면 이 라인에 해당됨 ####
        # find_stmt를 1로 설정하고, level을 1 감소시킨다.
        elif token_type == tokenize.DEDENT:
            find_stmt = 1
            level -= 1

        # tokenize.COMMENT 토큰이 나오면, 이전 문장에 대한 주석이 있습니다. 
        # find_stmt가 1이면, 이전 문장은 주석입니다. 
        # stats 리스트에 주석에 대한 (행 번호, 들여쓰기 레벨) 튜플을 추가합니다. 
        # find_stmt는 유지됩니다. - 새로운 statement를 찾아야하므로 그대로 유지
        elif token_type == tokenize.COMMENT:
            if find_stmt:
                stats.append((sline, -1)) # 주석이므로 -1
                # But we're still looking for a new stmt, so leave
                # find_stmt alone.
        
        # tokenize.NL (New Line) 토큰은 무시합니다.
        elif token_type == tokenize.NL:
            pass
        
        # find_stmt가 1이면, 이제부터 다음 문장을 찾고 있습니다. 
        # 이제 line이 비어 있지 않으면, 이것은 새로운 문장입니다. 
        # stats 리스트에 (행 번호, 들여쓰기 레벨) 튜플을 추가하고 find_stmt를 0으로 설정합니다.
        elif find_stmt:
            # 이것은 NEWLINE 다음에 오는 첫 번째 "실제 토큰"이므로 다음 프로그램 문의 첫 번째 토큰 또는 ENDMARKER여야 합니다.
            # This is the first "real token" following a NEWLINE, so it
            # must be the first token of the next program statement, or an
            # ENDMARKER.
            find_stmt = 0
            if line:   # Not endmarker.
                stats.append((sline, level))

    return stats

# 이 함수는 주어진 문자열에서 앞부분에 몇 개의 공백 문자가 있는지 세는 기능을 합니다.
# line = '    i = 0' 이 경우 4를 반환
def _leading_space_count(line):
    """라인에 리딩 공백의 수를 반환"""
    """Return number of leading spaces in line."""
    i = 0
    while i < len(line) and line[i] == ' ':
        i += 1
    return i


"""
1. lib2to3 모듈을 파이썬 2 코드를 파이썬 3코드로 자동변환
2. 즉, 파이썬 2 코드인 source_text를 파이썬 3코드로 변환하고, 변환된 코드를 문자열로 반환
"""
def refactor_with_2to3(source_text, fixer_names, filename=''):
    """Use lib2to3 to refactor the source.

    Return the refactored source code.

    """
    from lib2to3.refactor import RefactoringTool
    fixers = ['lib2to3.fixes.fix_' + name for name in fixer_names]
    
    # refactor_with_2to3 함수 내부에서는 lib2to3 모듈의 RefactoringTool 클래스를 사용하여 파이썬 2 코드를 파이썬 3 코드로 변환합니다.
    tool = RefactoringTool(fixer_names=fixers, explicit=fixers)

    from lib2to3.pgen2 import tokenize as lib2to3_tokenize
    try:
        # The name parameter is necessary particularly for the "import" fixer.
        return str(tool.refactor_string(source_text, name=filename))
    except lib2to3_tokenize.TokenError:
        return source_text


"""
Syntax 에러 있는지 체크함
SyntaxError, TypeError, ValueError가 나면 False
아니면 True - syntax is okay
"""
def check_syntax(code):
    """Return True if syntax is okay."""
    try:
        return compile(code, '<string>', 'exec', dont_inherit=True)
    except (SyntaxError, TypeError, ValueError):
        return False

"""
정규 표현식 re의
re.finditer()를 사용하여 패턴이 발견된 문자열을 찾은 후, 
contents 문자열에서 문자열이 위치한 라인 번호를 찾음

contents에서 pattern이 발견된 line number를 리스트로 반환
"""
def find_with_line_numbers(pattern, contents):
    """A wrapper around 're.finditer' to find line numbers.

    Returns a list of line numbers where pattern was found in contents.
    """
    matches = list(re.finditer(pattern, contents))
    if not matches:
        return []

    end = matches[-1].start()

    # -1 so a failed `rfind` maps to the first line.
    # 각 라인에서의 매칭되는 시작 위치와 해당하는 라인 번호 저장  
    newline_offsets = {
        -1: 0
    }
    for line_num, m in enumerate(re.finditer(r'\n', contents), 1):
        offset = m.start()
        if offset > end:
            break
        newline_offsets[offset] = line_num

    """
    파일 내용에서 문자열의 매치되는 line number 반환
    newline을 찾는데 실패해도 괜찮음, -1, 0 매핑하면 돼
    """
    def get_line_num(match, contents):
        """Get the line number of string in a files contents.

        Failing to find the newline is OK, -1 maps to 0

        """
        newline_offset = contents.rfind('\n', 0, match.start())
        return newline_offsets[newline_offset]

    return [get_line_num(match, contents) + 1 for match in matches]

""" 
비활성화된 범위를 나타내는 튜플 리스트을 반환한다.
비활성화되어 있고 다시 활성화되지 않으면 나머지 파일에 대해 비활성화됨
"""
def get_disabled_ranges(source):
    """Returns a list of tuples representing the disabled ranges.

    If disabled and no re-enable will disable for rest of file.

    """
    # 활성화된 line number 리스트
    enable_line_nums = find_with_line_numbers(ENABLE_REGEX, source)
    # 비활성화된 line number 리스트
    disable_line_nums = find_with_line_numbers(DISABLE_REGEX, source)
    # 총 line 길이
    total_lines = len(re.findall("\n", source)) + 1

    # 딕셔너리 enable_commands는 key : line number, value : 활성화 여부
    enable_commands = {}
    for num in enable_line_nums:
        enable_commands[num] = True
    for num in disable_line_nums:
        enable_commands[num] = False

    # 다음 3개의 리스트와 변수들은 비활성화된 범위를 찾으려고 쓰임
    disabled_ranges = [] # 비활성화 범위 저장
    currently_enabled = True 
    disabled_start = None

    # 라인 순서대로 활성화인지 비활성화인지 탐색
    for line, commanded_enabled in sorted(enable_commands.items()):
        if commanded_enabled is False and currently_enabled is True:
            disabled_start = line
            currently_enabled = False
        elif commanded_enabled is True and currently_enabled is False:
            disabled_ranges.append((disabled_start, line))
            currently_enabled = True

    if currently_enabled is False:
        disabled_ranges.append((disabled_start, total_lines))

    return disabled_ranges

""" 
행(line)이 비활성화된 범위 내에 속한다면, 함수는 False를 반환하여 해당 결과물이 필터링되도록 합니다. 
반면, 비활성화된 범위 내에 속하지 않는다면 True를 반환하여 해당 결과물이 유지되도록 합니다
- 비활성화 범위를 필터링하기 위함.
"""

def filter_disabled_results(result, disabled_ranges):
    """Filter out reports based on tuple of disabled ranges.

    """
    line = result['line']
    for disabled_range in disabled_ranges:
        if disabled_range[0] <= line <= disabled_range[1]:
            return False
    return True

""" 
pycodestyle로 부터 보고되는 문제를 검사하고 결과를 필터링한다.
source : 검사 대상 소스 코드
result : pycodestyle에서 보고된 결과
aggressive : 허용도 옵션 - True일 경우에는 위험한(fixes) 수정도 허용하는 옵션

필터링된 결과를 반환한다.
"""
def filter_results(source, results, aggressive):
    """Filter out spurious reports from pycodestyle.

    If aggressive is True, we allow possibly unsafe fixes (E711, E712).

    """
    # 소스코드에서 독스트링을 제외한 line number들을 가져온다.
    non_docstring_string_line_numbers = multiline_string_lines(
        source, include_docstrings=False)
    # 소스코드에서 독스트링을 포함함 line number들을 가져온다.
    all_string_line_numbers = multiline_string_lines(
        source, include_docstrings=True)
    
    # 소스코드 내에서 주석처리된 코드 line number들을 가져옴
    # comment out code란 설명하기 위한 주석이 아닌 
    # 코드를 동작 안시키려고 작성한 주석 "# x += 1"
    commented_out_code_line_numbers = commented_out_code_lines(source)

    # Filter out the disabled ranges
    # 소스 코드 내 비활성화(disabled)된 부분을 가져와 해당 부분에 대한 보고를 필터링함
    disabled_ranges = get_disabled_ranges(source)
    if disabled_ranges:
        results = [
            result for result in results if filter_disabled_results(
                result,
                disabled_ranges,
            )
        ]

    # pycodestyle의 보고된 결과중 E901이 있는지 any()함수를 통해 has_e901에 True/ False 할당
    has_e901 = any(result['id'].lower() == 'e901' for result in results)

    # pycodestyle의 보고된 결과를 모두 분석함
    for r in results:
        issue_id = r['id'].lower()
        
        # 보고된 라인의 에러가 독스트링을 제외한 라인인 경우, 
        # E1xxx, E501, W191 관련 보고는 필터링합니다.
        if r['line'] in non_docstring_string_line_numbers:
            if issue_id.startswith(('e1', 'e501', 'w191')):
                continue
            
        # e501 - line too long error 
        # all_string_line_numbers인 경우 필터링
        if r['line'] in all_string_line_numbers:
            if issue_id in ['e501']:
                continue

        # We must offset by 1 for lines that contain the trailing contents of
        # multiline strings.
        # 여러 줄 문자열의 후행 내용을 포함하는 줄의 경우 1로 오프셋해야 함
        if not aggressive and (r['line'] + 1) in all_string_line_numbers:
            # Do not modify multiline strings in non-aggressive mode. Remove
            # trailing whitespace could break doctests.
            
            # non-aggressive mode에서는 여러 줄 문자열을 수정하면 안됨
            # 후행 공백을 제거하면 doctest가 중단될 수 있습니다.
            if issue_id.startswith(('w29', 'w39')):
                continue
        
        # aggressive <= 0이면 E711, E72x, W6x 관련 보고는 필터링합니다.
        if aggressive <= 0:
            if issue_id.startswith(('e711', 'e72', 'w6')):
                continue
        
        # aggressive <= 1이고 E712, E713, E714 관련 보고는 필터링합니다.
        if aggressive <= 1:
            if issue_id.startswith(('e712', 'e713', 'e714')):
                continue
        
        # aggressive <= 2이고 E704 관련 보고는 필터링합니다.
        if aggressive <= 2:
            if issue_id.startswith(('e704')):
                continue
        
        # 보고된 라인 번호가 주석 처리된 코드에 있는 경우, E261, E262, E501 관련 보고는 필터링합니다.
        if r['line'] in commented_out_code_line_numbers:
            if issue_id.startswith(('e261', 'e262', 'e501')):
                continue

        # Do not touch indentation if there is a token error caused by
        # incomplete multi-line statement. Otherwise, we risk screwing up the
        # indentation.
        # 불완전한 다중 줄 문으로 인해 토큰 오류가 발생한 경우 들여쓰기를 누르지 마십시오. 그렇지 않으면 들여쓰기를 망칠 위험이 있습니다.
        # 에러 코드 E901이 존재하고, 보고된 라인이 해당 코드와 관련된 경우, E1xxx, E7xxx 관련 보고는 필터링합니다.
        if has_e901:
            if issue_id.startswith(('e1', 'e7')):
                continue
        
        # 위의 조건을 만족하지 않는 보고만 남겨두고 필터링한 결과를 반환합니다.
        # 위의 보고들은 포매팅되지 않는 부분인듯 하다.
        
        # yield - 반환하는 녀석인데
        # return과 다르게 하나씩 반환해줄 수 있음
        # 값이 아닌 제너레이터를 반환한다는 점도 있음
        yield r

"""
소스코드에서 line numbers(set 자료구조)를 반환한다.
include_docstrings를 True | False로 docstring 
라인 번호을 포함할지 안할지 결정
"""
def multiline_string_lines(source, include_docstrings=False):
    """Return line numbers that are within multiline strings.

    The line numbers are indexed at 1.

    Docstrings are ignored.

    """
    line_numbers = set()
    previous_token_type = ''
    try:
        for t in generate_tokens(source): # 소스코드 토크나이징
            token_type = t[0]
            start_row = t[2][0]
            end_row = t[3][0]

            # token_type이 문자열이고, 시작, 끝 행이 같지 않을 때
            if token_type == tokenize.STRING and start_row != end_row:
                # 독스트링을 포함하고, 이전 token_type이 INDENT가 아닐 때
                if (
                    include_docstrings or
                    previous_token_type != tokenize.INDENT
                ):
                    # We increment by one since we want the contents of the
                    # string.
                    # 문자열의 contents을 원하기 때문에 하나씩 증가합니다. 
                    #   -> 여기서 알 수 있는 점, 문자열의 contents를 고려하려고 하는 듯하다.
                    line_numbers |= set(range(1 + start_row, 1 + end_row))

            previous_token_type = token_type
    except (SyntaxError, tokenize.TokenError):
        pass

    return line_numbers


"""
코드일 가능성이 있는 주석의 행 번호를 반환한다. 
코멘트 아웃 코드는 나쁜 관행이지만, 그것을 수정하는 것은 훨씬 더 혼란스럽게 할 뿐이다.
그러므로 주석 처리된 코드를 수정하면 코드만 더 복잡해지므로 수정하지 않고 남겨두는 것이 좋다.
따라서 코드 라인에 주석이 포함되어 있는지 확인하고, 주석의 내용이 Python 구문에 맞는지 검사해준다.
"""
def commented_out_code_lines(source):
    """Return line numbers of comments that are likely code.

    Commented-out code is bad practice, but modifying it just adds even
    more clutter.

    """
    line_numbers = []
    try:
        for t in generate_tokens(source):
            token_type = t[0]
            token_string = t[1]
            start_row = t[2][0]
            line = t[4]

            # Ignore inline comments.
            # inline comments 무시함
            if not line.lstrip().startswith('#'):
                continue
            
            # token_type이 COMMENT면
            # '#'을 제거한 후 내용이 Python 구문에 맞는지 검사해준다.
            if token_type == tokenize.COMMENT:
                # '#'을 제거(좌우 공백도 제거)하여 stripped_line에 할당해줌
                stripped_line = token_string.lstrip('#').strip()
                
                # warnings.catch_warnings()을 활용해 SyntaxWarning 에러 무시하도록 설정
                with warnings.catch_warnings():
                    # ignore SyntaxWarning in Python3.8+
                    # refs:
                    #   https://bugs.python.org/issue15248
                    #   https://docs.python.org/3.8/whatsnew/3.8.html#other-language-changes
                    warnings.filterwarnings("ignore", category=SyntaxWarning)
                    if (
                        ' ' in stripped_line and
                        '#' not in stripped_line and
                        check_syntax(stripped_line)
                    ): # 주석을 지운 코드 - stripped_line이 파이썬 코드인 겨우 line_numbers에 추가해준다.
                        line_numbers.append(start_row)
    except (SyntaxError, tokenize.TokenError):
        pass

    return line_numbers

""" 
긴 주석 라인을 자르거나 또는 분할하여 반환합니다.

바로 뒤에 주석이 없으면 텍스트를 감싼다.
일반적으로 모든 주석에 이 래핑을 수행하면 주석 텍스트가 들쭉날쭉해질 수 있습니다.

max_line_length - 한 줄에 올 수 있는 문자열 최대길이 인데
이거보다 크면 분할해줌.

line: 분할 또는 자를 문자열
max_line_length: 문자열의 최대 길이
last_comment: 마지막 주석인지 여부
"""
def shorten_comment(line, max_line_length, last_comment=False):
    """Return trimmed or split long comment line.

    If there are no comments immediately following it, do a text wrap.
    Doing this wrapping on all comments in general would lead to jagged
    comment text.

    """
    # len(line)이 max_line_length보다 크다고 가정하고 코드 진행
    assert len(line) > max_line_length
    # 1. line의 오른쪽 공백을 제거합니다.
    line = line.rstrip()

    # PEP 8 recommends 72 characters for comment text.
    # PEP 8에서 권장하는 주석 텍스트 최대 길이 : 72자. line의 들여쓰기를 포함한 최대 길이를 계산합니다.
    indentation = _get_indentation(line) + '# '
    max_line_length = min(max_line_length,
                          len(indentation) + 72)

    # line이 MIN_CHARACTER_REPEAT개 이상의 같은 문자를 반복하며 끝나고, 마지막 문자가 알파벳이나 숫자가 아닌 경우, 문자열을 자릅니다.
    MIN_CHARACTER_REPEAT = 5
    if (
        len(line) - len(line.rstrip(line[-1])) >= MIN_CHARACTER_REPEAT and
        not line[-1].isalnum()
    ):
        # Trim comments that end with things like ---------
        # -----------와 같은 것으로 끝나는 주석 잘라내기
        return line[:max_line_length] + '\n'
    
    # last_comment가 True이고, line이 #로 시작하고 단어가 바로 뒤에 나오는 경우, 문자열을 text wrap 합니다.
    elif last_comment and re.match(r'\s*#+\s*\w+', line):
        split_lines = textwrap.wrap(line.lstrip(' \t#'),
                                    initial_indent=indentation,
                                    subsequent_indent=indentation,
                                    width=max_line_length,
                                    break_long_words=False,
                                    break_on_hyphens=False)
        return '\n'.join(split_lines) + '\n'
    
    # 변경된 문자열을 반환
    return line + '\n'

""" 
주어진 문자열 목록에서 모든 줄 끝을 주어진 새 줄 종결자(newline)로 통일하는 함수
각 줄의 줄 끝에 있는 '\n' 또는 '\r\n' 등의 다양한 줄 종결자를 제거한 후 
새 줄 종결자(newline)를 각 줄 끝에 추가하여 모든 줄 끝을 통일합니다.
"""
def normalize_line_endings(lines, newline):
    """Return fixed line endings.

    All lines will be modified to use the most common line ending.
    """
    line = [line.rstrip('\n\r') + newline for line in lines]
    if line and lines[-1] == lines[-1].rstrip('\n\r'):
        line[-1] = line[-1].rstrip('\n\r')
    return line


"""
b문자열이 a로 시작하는지 또는 a문자열이 b로 시작하는지 여부를 반환
True | False
"""
def mutual_startswith(a, b):
    return b.startswith(a) or a.startswith(b)


""" 
code가 ignore인지 select인지 판단

code: 코드 문자열
select: 선택할 코드 문자열 리스트
ignore: 무시할 코드 문자열 리스트
"""
def code_match(code, select, ignore):
    
    # ignore 리스트에 있는 문자열 중 하나가 code 문자열의 부분 문자열이라면 False를 반환하고, 
    if ignore:
        assert not isinstance(ignore, str)
        for ignored_code in [c.strip() for c in ignore]:
            if mutual_startswith(code.lower(), ignored_code.lower()):
                return False

    # code 문자열 중 하나가 select 리스트의 부분 문자열이면 True를 반환
    if select:
        assert not isinstance(select, str)
        for selected_code in [c.strip() for c in select]:
            if mutual_startswith(code.lower(), selected_code.lower()):
                return True
        return False

    return True


"""
fix_code 함수는 주어진 source 코드를 PEP8 스타일에 맞게 수정하고 그 결과를 반환하는 함수
source : 소스 코드 - str 형식이거나 encoding을 지정하여 byte string으로 지정할 수 있습니다.
apply_config 매개변수가 True로 지정된 경우, pyproject.toml 파일에서 설정된 옵션을 사용하여 수정을 진행합니다.
"""
def fix_code(source, options=None, encoding=None, apply_config=False):
    """Return fixed source code.

    "encoding" will be used to decode "source" if it is a byte string.

    """
    # get_options 함수를 사용하여 options 매개변수를 분석
    options = _get_options(options, apply_config)
    
    # normalize
    # options.ignore와 options.select에서 (에러코드나 경고 메세지 같은 것들)대소문자를 구분하지 않도록 정규화합니다.
    options.ignore = [opt.upper() for opt in options.ignore]
    options.select = [opt.upper() for opt in options.select]

    # check ignore args
    # NOTE: If W50x is not included, add W50x because the code
    #       correction result is indefinite.
    
    # options.ignore 매개변수는 코드에서 무시해야 하는 오류나 경고 메시지를 지정할 수 있습니다. 
    # ignore 매개변수로 지정한 문자열과 일치하거나, 
    # ignore 매개변수의 각 항목과 공통된 prefix를 가지는 경우, 해당 코드는 수정하지 않습니다
    ignore_opt = options.ignore
    if not {"W50", "W503", "W504"} & set(ignore_opt):
        options.ignore.append("W50")

    # options.select 매개변수는 수정 대상 코드를 선택합니다. 
    # select 매개변수에 지정한 문자열과 일치하는 코드만 수정됩니다.
    if not isinstance(source, str):
        source = source.decode(encoding or get_encoding())

    sio = io.StringIO(source)
    
    # fix_lines 함수를 사용하여 라인마다 코드 수정을 진행하고, 
    # 수정된 코드를 반환합니다.
    return fix_lines(sio.readlines(), options=options)


"""
파싱되는 옵션을 반환한다.
autopep8 -i filename.py 일 때
-i 반환 
"""
def _get_options(raw_options, apply_config):
    """Return parsed options."""
    
    if not raw_options: # 기본 옵션이면 반환
        return parse_args([''], apply_config=apply_config)

    if isinstance(raw_options, dict):
        options = parse_args([''], apply_config=apply_config)
        for name, value in raw_options.items():
            if not hasattr(options, name): # 입력한 옵션이 없으면
                raise ValueError("No such option '{}'".format(name))

            # Check for very basic type errors.
            # 매우 기본적인 타입의 에러를 검사
            expected_type = type(getattr(options, name))
            if not isinstance(expected_type, (str, )):
                if isinstance(value, (str, )):
                    raise ValueError( #옵션이 string이 아닐 경우
                        "Option '{}' should not be a string".format(name))
            setattr(options, name, value)
    else:
        options = raw_options

    return options

"""
수정된 소스 라인 반환
source_lines : 소스 코드를 줄 단위로 나눈 리스트 
options : 수정 옵션을 담은 객체
filename : 수정 대상 파일의 이름
"""
def fix_lines(source_lines, options, filename=''):
    """Return fixed source code."""
    # Transform everything to line feed. Then change them back to original
    # before returning fixed source code.
    
    original_newline = find_newline(source_lines)
    # 소스 코드의 줄 바꿈 문자를 통일
    tmp_source = ''.join(normalize_line_endings(source_lines, '\n'))

    # Keep a history to break out of cycles.
    # 소스 코드가 cycle에 빠지지 않도록
    previous_hashes = set()

    if options.line_range:
        # Disable "apply_local_fixes()" for now due to issue #175.
        fixed_source = tmp_source
    else:
        # Apply global fixes only once (for efficiency).
        # apply_global_fixes() 함수를 통해 전역적인 수정을 적용(효율을 위해)
        fixed_source = apply_global_fixes(tmp_source,
                                          options,
                                          filename=filename)

    passes = 0
    long_line_ignore_cache = set()
    
    # previous_hashes 집합을 이용하여 소스 코드가 변하지 않을 때까지 린트 작업을 반복
    while hash(fixed_source) not in previous_hashes:
        if options.pep8_passes >= 0 and passes > options.pep8_passes:
            break
        passes += 1

        previous_hashes.add(hash(fixed_source))

        tmp_source = copy.copy(fixed_source)

        # FixPEP8 클래스의 fix() 메서드를 이용하여 소스 코드의 린트 작업을 수행
        fix = FixPEP8(
            filename,
            options,
            contents=tmp_source,
            long_line_ignore_cache=long_line_ignore_cache)

        # 수정된 소스 저장
        fixed_source = fix.fix()

    sio = io.StringIO(fixed_source)
    return ''.join(normalize_line_endings(sio.readlines(), original_newline))


""" 
주어진 파일을 고쳐서 반환하거나 출력한다. 함수는 파일 이름, 옵션 및 출력을 입력 받는다.
filename : 수정할 파일 이름
options : 수정할 옵션
output : 옵션이 있는 경우 수정된 소스 코드를 출력. 수정 사항이 없으면 아무것도 반환하지 않는다.

"""
def fix_file(filename, options=None, output=None, apply_config=False):
    if not options: # 수정 옵션이 없으면 parse_args를 이용해 command line을 파싱해옴
        options = parse_args([filename], apply_config=apply_config)

    # original_source를 이용해 수정 파일의 코드를 한 줄씩 읽어옴
    original_source = readlines_from_file(filename)

    fixed_source = original_source

    # in_place 또는 diff 또는 output 옵션이 있는 경우, 파일의 인코딩을 방식을 지정해준다.
    # -d, --diff : print the diff for the fixed source
    # -i, --in-place : make changes to files in place
    if options.in_place or options.diff or output:
        encoding = detect_encoding(filename)

    # if output 매개변수를 전달한 경우,
    # output에 파일을 인코딩하여 저장
    if output:
        output = LineEndingWrapper(wrap_output(output, encoding=encoding))

    #fix_lines 함수로 파일의 라인 단위로 수정
    fixed_source = fix_lines(fixed_source, options, filename=filename)

    # -d, --diff 옵션인 경우
    # origin code 부분과 fixed code 부분의 차이 출력
    if options.diff: 
        new = io.StringIO(fixed_source)
        new = new.readlines()
        diff = get_diff_text(original_source, new, filename)
        if output:
            output.write(diff)
            output.flush()
        elif options.jobs > 1:
            diff = diff.encode(encoding)
        return diff
    
    # -i, --in_place 옵션
    # 변경된 소스를 반환
    elif options.in_place:
        original = "".join(original_source).splitlines()
        fixed = fixed_source.splitlines()
        original_source_last_line = (
            original_source[-1].split("\n")[-1] if original_source else ""
        )
        fixed_source_last_line = fixed_source.split("\n")[-1]
        if original != fixed or (
            original_source_last_line != fixed_source_last_line
        ):
            with open_with_encoding(filename, 'w', encoding=encoding) as fp:
                fp.write(fixed_source)
            return fixed_source
        return None
    else:
        if output:
            output.write(fixed_source)
            output.flush()
    return fixed_source

""" 
전역함수을 검사함 여러 개의 (코드, 함수) 튜플을 yield 해줌
"""
def global_fixes():
    """Yield multiple (code, function) tuples."""
    
    for function in list(globals().values()):
        if inspect.isfunction(function): #함수가 맞는지 검사
            arguments = _get_parameters(function) # _get_parameters를 사용해 인자 가져옴
            if arguments[:1] != ['source']:
                continue

            code = extract_code_from_function(function) # 함수에서 코드 추출 - 함수 정의 부분을 제외한 코드 부분
            if code:
                yield (code, function)


# 함수의 인자 반환
def _get_parameters(function):
    # pylint: disable=deprecated-method
    if sys.version_info.major >= 3:
        # We need to match "getargspec()", which includes "self" as the first
        # value for methods.
        # https://bugs.python.org/issue17481#msg209469
        if inspect.ismethod(function): # 메소드인지 검사
            function = function.__func__
            
        # 반환된 inspect.Parameter 객체를 이용하여 매개변수의 이름, 기본값 등의 정보를 얻을 수 있습니다.
        return list(inspect.signature(function).parameters) # getargspec(function)을 활용해 파라미터 반환
    else:
        # inspect.getargspec() 함수는 함수의 매개변수 목록, 기본값, 가변 인자, 키워드 인자 등의 정보를 담은 튜플을 반환합니다.
        return inspect.getargspec(function)[0] # getargspec를 활용해 함수의 인자 반환


""" 
소스 코드에 대한 글로벌 수정을 실행합니다. 
이러한 수정 사항은 한 번만 수행하면 됩니다(pycodestyle에 의존하는 FixPEP8과는 다름)

source: 교정 대상 소스 코드 문자열입니다.
options: 명령줄 옵션과 구성 파일에서 파싱된 옵션 객체입니다.
where: 어디서(global/local) 교정이 적용되는지를 지정하는 문자열입니다. 기본값은 'global'입니다.
filename: 현재 처리중인 파일의 이름입니다.
codes: 교정을 적용할 코드에 대한 목록입니다.
"""
def apply_global_fixes(source, options, where='global', filename='',
                       codes=None):
    """Run global fixes on source code.

    These are fixes that only need be done once (unlike those in
    FixPEP8, which are dependent on pycodestyle).

    """
    if codes is None:
        codes = []
    
    # E101 (indentation contains mixed spaces and tabs - 스페이스와 탭을 혼합해서 파일한 경우) 또는 
    # E111 (indentation is not a multiple of four - 들여쓰기가 4의 배수가 아닌 경우) 코드가 옵션에 지정되어 있는 경우, 
    # reindent() 함수를 사용하여 들여쓰기를 조정합니다.
    if any(code_match(code, select=options.select, ignore=options.ignore)
           for code in ['E101', 'E111']):
        source = reindent(
            source,
            indent_size=options.indent_size,
            
            # W191(indentation contains tabs - 탭으로 들여쓰기)
            leave_tabs=not (
                code_match( 
                    'W191', 
                    select=options.select,
                    ignore=options.ignore
                )
            )
        )

    
    # global_fixes() 함수를 사용하여 전역 교정을 적용합니다.
    for (code, function) in global_fixes():
        if code_match(code, select=options.select, ignore=options.ignore):
            if options.verbose:
                print('--->  Applying {} fix for {}'.format(where,
                                                            code.upper()),
                      file=sys.stderr)
            source = function(source,
                              aggressive=options.aggressive)

    # fix_2to3() 함수를 사용하여 Python 2에서 작성된 코드를 
    # Python 3에서 실행할 수 있는 코드로 변환합니다.
    source = fix_2to3(source,
                      aggressive=options.aggressive,
                      select=options.select,
                      ignore=options.ignore,
                      filename=filename,
                      where=where,
                      verbose=options.verbose)

    return source


# 함수에서 코드 추출
def extract_code_from_function(function):
    """Return code handled by function."""
    
    # fix_"로 시작하지 않는 경우 None을 반환
    if not function.__name__.startswith('fix_'):
        return None

    # fix_"로 시작하지만 뒤에 숫자가 없거나 숫자 이외의 문자가 따라오는 경우에도 None을 반환합니다.
    code = re.sub('^fix_', '', function.__name__)
    if not code:
        return None

    # 그 외의 경우에는 함수 이름에서 "fix_"를 제거하고 반환
    try:
        int(code[1:])
    except ValueError:
        return None

    return code

# pycodestyle의 버전을 문자열로 봔환
def _get_package_version():
    packages = ["pycodestyle: {}".format(pycodestyle.__version__)]
    return ", ".join(packages)

""" 
argparse 모듈을 사용하여 커맨드 라인 인자 파싱을 위한 파서를 생성합니다. 
argparse 모듈을 사용하면 명령행 인자를 파싱하고 해당 인자를 사용하여 
프로그램을 실행할 수 있습니다.

command-line을 파싱하여 반환
autopep8 <option>
autopep8 <option> filename
"""

def create_parser():
    """Return command-line parser."""
    parser = argparse.ArgumentParser(description=docstring_summary(__doc__),
                                     prog='autopep8')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {} ({})'.format(
                            __version__, _get_package_version()))
    parser.add_argument('-v', '--verbose', action='count',
                        default=0,
                        help='print verbose messages; '
                             'multiple -v result in more verbose messages')
    parser.add_argument('-d', '--diff', action='store_true',
                        help='print the diff for the fixed source')
    parser.add_argument('-i', '--in-place', action='store_true',
                        help='make changes to files in place')
    parser.add_argument('--global-config', metavar='filename',
                        default=DEFAULT_CONFIG,
                        help='path to a global pep8 config file; if this file '
                             'does not exist then this is ignored '
                             '(default: {})'.format(DEFAULT_CONFIG))
    parser.add_argument('--ignore-local-config', action='store_true',
                        help="don't look for and apply local config files; "
                             'if not passed, defaults are updated with any '
                             "config files in the project's root directory")
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='run recursively over directories; '
                             'must be used with --in-place or --diff')
    parser.add_argument('-j', '--jobs', type=int, metavar='n', default=1,
                        help='number of parallel jobs; '
                             'match CPU count if value is less than 1')
    parser.add_argument('-p', '--pep8-passes', metavar='n',
                        default=-1, type=int,
                        help='maximum number of additional pep8 passes '
                             '(default: infinite)')
    parser.add_argument('-a', '--aggressive', action='count', default=0,
                        help='enable non-whitespace changes; '
                             'multiple -a result in more aggressive changes')
    parser.add_argument('--experimental', action='store_true',
                        help='enable experimental fixes')
    parser.add_argument('--exclude', metavar='globs',
                        help='exclude file/directory names that match these '
                             'comma-separated globs')
    parser.add_argument('--list-fixes', action='store_true',
                        help='list codes for fixes; '
                        'used by --ignore and --select')
    parser.add_argument('--ignore', metavar='errors', default='',
                        help='do not fix these errors/warnings '
                             '(default: {})'.format(DEFAULT_IGNORE))
    parser.add_argument('--select', metavar='errors', default='',
                        help='fix only these errors/warnings (e.g. E4,W)')
    parser.add_argument('--max-line-length', metavar='n', default=79, type=int,
                        help='set maximum allowed line length '
                             '(default: %(default)s)')
    parser.add_argument('--line-range', '--range', metavar='line',
                        default=None, type=int, nargs=2,
                        help='only fix errors found within this inclusive '
                             'range of line numbers (e.g. 1 99); '
                             'line numbers are indexed at 1')
    parser.add_argument('--indent-size', default=DEFAULT_INDENT_SIZE,
                        type=int, help=argparse.SUPPRESS)
    parser.add_argument('--hang-closing', action='store_true',
                        help='hang-closing option passed to pycodestyle')
    parser.add_argument('--exit-code', action='store_true',
                        help='change to behavior of exit code.'
                             ' default behavior of return value, 0 is no '
                             'differences, 1 is error exit. return 2 when'
                             ' add this option. 2 is exists differences.')
    parser.add_argument('files', nargs='*',
                        help="files to format or '-' for standard in")

    return parser


""" 
각각의 에러 코드(E/W codes)를 풀어서 개별적인 코드로 확장한 후

"""
def _expand_codes(codes, ignore_codes):
    """expand to individual E/W codes"""
    ret = set()

    # codes 리스트에 있는 코드 중에서 충돌이 일어날 수 있는 코드가 모두 있는지를 확인
    is_conflict = False
    if all(
            any(
                conflicting_code.startswith(code)
                for code in codes
            )
            for conflicting_code in CONFLICTING_CODES
    ):
        is_conflict = True

    # ignore_codes 리스트에 
    # W503 ( line break before binary operator )이 있으면 is_ignore_w503를 True로,
    # W504 ( line break after binary operator ) 가 있으면 is_ignore_w504를 True로
    is_ignore_w503 = "W503" in ignore_codes
    is_ignore_w504 = "W504" in ignore_codes

    # W와 관련된 에러는 
    # indentation, white space, blank, line break, deprecation 등..
    # W503, W504가 무시되는지 에 따라 처리할 W 관련 에러 업데이트해주고 반환
    for code in codes:
        if code == "W":
            if is_ignore_w503 and is_ignore_w504:
                ret.update({"W1", "W2", "W3", "W505", "W6"})
            elif is_ignore_w503:
                ret.update({"W1", "W2", "W3", "W504", "W505", "W6"})
            else:
                ret.update({"W1", "W2", "W3", "W503", "W505", "W6"})
        elif code in ("W5", "W50"):
            if is_ignore_w503 and is_ignore_w504:
                ret.update({"W505"})
            elif is_ignore_w503:
                ret.update({"W504", "W505"})
            else:
                ret.update({"W503", "W505"})
        elif not (code in ("W503", "W504") and is_conflict):
            ret.add(code)

    return ret

""" 
command-line의 옵션들을 파싱한다.
EXIT_CODE_ARGPARSE_ERROR가 발생하면 그에 매핑되는 에러코드 출력

arguments를 파싱하여 파싱한 결과를 리턴함
apply_config가 True로 설정되면, args에 저장된 값을 
기준으로 설정 파일을 읽어들여 추가적인 설정을 적용하게 됩니다.

rgs.select는 적용할 코드 스타일을 선택할 수 있게 해주고, 
args.ignore는 무시할 코드 스타일을 선택
"""
def parse_args(arguments, apply_config=False):
    """Parse command-line options."""
    parser = create_parser()
    
    # args.files 파일의 경로 저장
    args = parser.parse_args(arguments)

    # 파일에 대한 유효성 검사
    if not args.files and not args.list_fixes:
        parser.exit(EXIT_CODE_ARGPARSE_ERROR, 'incorrect number of arguments')

    
    
    args.files = [decode_filename(name) for name in args.files]

    if apply_config:
        parser = read_config(args, parser)
        # prioritize settings when exist pyproject.toml's tool.autopep8 section
        try:
            parser_with_pyproject_toml = read_pyproject_toml(args, parser)
        except Exception:
            parser_with_pyproject_toml = None
        if parser_with_pyproject_toml:
            parser = parser_with_pyproject_toml
        args = parser.parse_args(arguments)
        args.files = [decode_filename(name) for name in args.files]

    if '-' in args.files:
        if len(args.files) > 1:
            parser.exit(
                EXIT_CODE_ARGPARSE_ERROR,
                'cannot mix stdin and regular files',
            )

        if args.diff:
            parser.exit(
                EXIT_CODE_ARGPARSE_ERROR,
                '--diff cannot be used with standard input',
            )

        if args.in_place:
            parser.exit(
                EXIT_CODE_ARGPARSE_ERROR,
                '--in-place cannot be used with standard input',
            )

        if args.recursive:
            parser.exit(
                EXIT_CODE_ARGPARSE_ERROR,
                '--recursive cannot be used with standard input',
            )

    if len(args.files) > 1 and not (args.in_place or args.diff):
        parser.exit(
            EXIT_CODE_ARGPARSE_ERROR,
            'autopep8 only takes one filename as argument '
            'unless the "--in-place" or "--diff" args are used',
        )

    if args.recursive and not (args.in_place or args.diff):
        parser.exit(
            EXIT_CODE_ARGPARSE_ERROR,
            '--recursive must be used with --in-place or --diff',
        )

    if args.in_place and args.diff:
        parser.exit(
            EXIT_CODE_ARGPARSE_ERROR,
            '--in-place and --diff are mutually exclusive',
        )

    if args.max_line_length <= 0:
        parser.exit(
            EXIT_CODE_ARGPARSE_ERROR,
            '--max-line-length must be greater than 0',
        )

    if args.indent_size <= 0:
        parser.exit(
            EXIT_CODE_ARGPARSE_ERROR,
            '--indent-size must be greater than 0',
        )

    # 인자의 select와 ignore 구분
    if args.select:
        args.select = _expand_codes(
            _split_comma_separated(args.select),
            (_split_comma_separated(args.ignore) if args.ignore else [])
        )

    if args.ignore:
        args.ignore = _split_comma_separated(args.ignore)
        if all(
                not any(
                    conflicting_code.startswith(ignore_code)
                    for ignore_code in args.ignore
                )
                for conflicting_code in CONFLICTING_CODES
        ):
            args.ignore.update(CONFLICTING_CODES)
    elif not args.select:
        if args.aggressive:
            # Enable everything by default if aggressive.
            # aggressive인 경우 아래의 친구들도 select해줌
            # 추가한 부분 - 김위성
            args.select = {'E', 'W1', 'W2', 'W3', 'W6', 'W7'}
        else:
            args.ignore = _split_comma_separated(DEFAULT_IGNORE)

    if args.exclude:
        args.exclude = _split_comma_separated(args.exclude)
    else:
        args.exclude = {}

    if args.jobs < 1:
        # Do not import multiprocessing globally in case it is not supported
        # on the platform.
        import multiprocessing
        args.jobs = multiprocessing.cpu_count()

    if args.jobs > 1 and not (args.in_place or args.diff):
        parser.exit(
            EXIT_CODE_ARGPARSE_ERROR,
            'parallel jobs requires --in-place',
        )

    if args.line_range:
        if args.line_range[0] <= 0:
            parser.exit(
                EXIT_CODE_ARGPARSE_ERROR,
                '--range must be positive numbers',
            )
        if args.line_range[0] > args.line_range[1]:
            parser.exit(
                EXIT_CODE_ARGPARSE_ERROR,
                'First value of --range should be less than or equal '
                'to the second',
            )

    return args

""" 
Python 프로그램에서 커맨드 라인 옵션과 구성 파일에 대한 입력을 사용하여 일반적으로 설정 파일로부터 가져오는 설정 값을 정규화
args : argparse 모듈로부터 생성된 argument 객체입니다. 파싱된 command-line 인자 값이 들어있는 객체입니다.
config : configparser 모듈로부터 생성된 config 객체입니다. ini 파일 형식의 설정 파일을 파싱하여 생성한 객체입니다.
section : 파싱하려는 설정 파일의 섹션 이름입니다.
option_list : 파싱하려는 옵션 목록입니다.

설정 파일의 [tool.autopep8] 
섹션에 --max-line-length=79 옵션이 있고, option_list에 해당 옵션이 존재하면, 
이 함수는 튜플 ('max_line_length', '--max-line-length', 79)를 반환
"""
def _get_normalize_options(args, config, section, option_list):
    # 첫 번째 요소는 옵션의 정규화된 이름, 
    # 두 번째 요소는 옵션 이름, 
    # 세 번째 요소는 정규화된 값
    
    for (k, v) in config.items(section):
        # --max-line-length -> max_line_length
        norm_opt = k.lstrip('-').replace('-', '_') 
        if not option_list.get(norm_opt):
            continue
        
        
        opt_type = option_list[norm_opt]
        # 옵션의 타입 검사
        if opt_type is int:
            if v.strip() == "auto":
                # skip to special case
                # 특별한 auto인경우
                if args.verbose:
                    print(f"ignore config: {k}={v}")
                continue
            value = config.getint(section, k)
        elif opt_type is bool:
            value = config.getboolean(section, k)
        else:
            value = config.get(section, k)
        yield norm_opt, k, value


#1000라인 끝##############################################################################################################


def read_config(args, parser):
    """Read both user configuration and local configuration."""
    config = SafeConfigParser()

    try:
        if args.verbose and os.path.exists(args.global_config):
            print("read config path: {}".format(args.global_config))
        config.read(args.global_config)

        if not args.ignore_local_config:
            parent = tail = args.files and os.path.abspath(
                os.path.commonprefix(args.files))
            while tail:
                if config.read([os.path.join(parent, fn)
                                for fn in PROJECT_CONFIG]):
                    if args.verbose:
                        for fn in PROJECT_CONFIG:
                            config_file = os.path.join(parent, fn)
                            if not os.path.exists(config_file):
                                continue
                            print(
                                "read config path: {}".format(
                                    os.path.join(parent, fn)
                                )
                            )
                    break
                (parent, tail) = os.path.split(parent)

        defaults = {}
        option_list = {o.dest: o.type or type(o.default)
                       for o in parser._actions}

        for section in ['pep8', 'pycodestyle', 'flake8']:
            if not config.has_section(section):
                continue
            for norm_opt, k, value in _get_normalize_options(
                args, config, section, option_list
            ):
                if args.verbose:
                    print("enable config: section={}, key={}, value={}".format(
                        section, k, value))
                defaults[norm_opt] = value

        parser.set_defaults(**defaults)
    except Error:
        # Ignore for now.
        pass

    return parser


def read_pyproject_toml(args, parser):
    """Read pyproject.toml and load configuration."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    config = None

    if os.path.exists(args.global_config):
        with open(args.global_config, "rb") as fp:
            config = tomllib.load(fp)

    if not args.ignore_local_config:
        parent = tail = args.files and os.path.abspath(
            os.path.commonprefix(args.files))
        while tail:
            pyproject_toml = os.path.join(parent, "pyproject.toml")
            if os.path.exists(pyproject_toml):
                with open(pyproject_toml, "rb") as fp:
                    config = tomllib.load(fp)
                    break
            (parent, tail) = os.path.split(parent)

    if not config:
        return None

    if config.get("tool", {}).get("autopep8") is None:
        return None

    config = config.get("tool").get("autopep8")

    defaults = {}
    option_list = {o.dest: o.type or type(o.default)
                   for o in parser._actions}

    TUPLED_OPTIONS = ("ignore", "select")
    for (k, v) in config.items():
        norm_opt = k.lstrip('-').replace('-', '_')
        if not option_list.get(norm_opt):
            continue
        if type(v) in (list, tuple) and norm_opt in TUPLED_OPTIONS:
            value = ",".join(v)
        else:
            value = v
        if args.verbose:
            print("enable pyproject.toml config: "
                  "key={}, value={}".format(k, value))
        defaults[norm_opt] = value

    if defaults:
        # set value when exists key-value in defaults dict
        parser.set_defaults(**defaults)

    return parser


def _split_comma_separated(string):
    """Return a set of strings."""
    return {text.strip() for text in string.split(',') if text.strip()}


def decode_filename(filename):
    """Return Unicode filename."""
    if isinstance(filename, str):
        return filename

    return filename.decode(sys.getfilesystemencoding())


def supported_fixes():
    """Yield pep8 error codes that autopep8 fixes.

    Each item we yield is a tuple of the code followed by its
    description.

    """
    yield ('E101', docstring_summary(reindent.__doc__))

    instance = FixPEP8(filename=None, options=None, contents='')
    for attribute in dir(instance):
        code = re.match('fix_([ew][0-9][0-9][0-9])', attribute)
        if code:
            yield (
                code.group(1).upper(),
                re.sub(r'\s+', ' ',
                       docstring_summary(getattr(instance, attribute).__doc__))
            )

    for (code, function) in sorted(global_fixes()):
        yield (code.upper() + (4 - len(code)) * ' ',
               re.sub(r'\s+', ' ', docstring_summary(function.__doc__)))

    for code in sorted(CODE_TO_2TO3):
        yield (code.upper() + (4 - len(code)) * ' ',
               re.sub(r'\s+', ' ', docstring_summary(fix_2to3.__doc__)))


def docstring_summary(docstring):
    """Return summary of docstring."""
    return docstring.split('\n')[0] if docstring else ''


def line_shortening_rank(candidate, indent_word, max_line_length,
                         experimental=False):
    """Return rank of candidate.

    This is for sorting candidates.

    """
    if not candidate.strip():
        return 0

    rank = 0
    lines = candidate.rstrip().split('\n')

    offset = 0
    if (
        not lines[0].lstrip().startswith('#') and
        lines[0].rstrip()[-1] not in '([{'
    ):
        for (opening, closing) in ('()', '[]', '{}'):
            # Don't penalize empty containers that aren't split up. Things like
            # this "foo(\n    )" aren't particularly good.
            opening_loc = lines[0].find(opening)
            closing_loc = lines[0].find(closing)
            if opening_loc >= 0:
                if closing_loc < 0 or closing_loc != opening_loc + 1:
                    offset = max(offset, 1 + opening_loc)

    current_longest = max(offset + len(x.strip()) for x in lines)

    rank += 4 * max(0, current_longest - max_line_length)

    rank += len(lines)

    # Too much variation in line length is ugly.
    rank += 2 * standard_deviation(len(line) for line in lines)

    bad_staring_symbol = {
        '(': ')',
        '[': ']',
        '{': '}'}.get(lines[0][-1])

    if len(lines) > 1:
        if (
            bad_staring_symbol and
            lines[1].lstrip().startswith(bad_staring_symbol)
        ):
            rank += 20

    for lineno, current_line in enumerate(lines):
        current_line = current_line.strip()

        if current_line.startswith('#'):
            continue

        for bad_start in ['.', '%', '+', '-', '/']:
            if current_line.startswith(bad_start):
                rank += 100

            # Do not tolerate operators on their own line.
            if current_line == bad_start:
                rank += 1000

        if (
            current_line.endswith(('.', '%', '+', '-', '/')) and
            "': " in current_line
        ):
            rank += 1000

        if current_line.endswith(('(', '[', '{', '.')):
            # Avoid lonely opening. They result in longer lines.
            if len(current_line) <= len(indent_word):
                rank += 100

            # Avoid the ugliness of ", (\n".
            if (
                current_line.endswith('(') and
                current_line[:-1].rstrip().endswith(',')
            ):
                rank += 100

            # Avoid the ugliness of "something[\n" and something[index][\n.
            if (
                current_line.endswith('[') and
                len(current_line) > 1 and
                (current_line[-2].isalnum() or current_line[-2] in ']')
            ):
                rank += 300

            # Also avoid the ugliness of "foo.\nbar"
            if current_line.endswith('.'):
                rank += 100

            if has_arithmetic_operator(current_line):
                rank += 100

        # Avoid breaking at unary operators.
        if re.match(r'.*[(\[{]\s*[\-\+~]$', current_line.rstrip('\\ ')):
            rank += 1000

        if re.match(r'.*lambda\s*\*$', current_line.rstrip('\\ ')):
            rank += 1000

        if current_line.endswith(('%', '(', '[', '{')):
            rank -= 20

        # Try to break list comprehensions at the "for".
        if current_line.startswith('for '):
            rank -= 50

        if current_line.endswith('\\'):
            # If a line ends in \-newline, it may be part of a
            # multiline string. In that case, we would like to know
            # how long that line is without the \-newline. If it's
            # longer than the maximum, or has comments, then we assume
            # that the \-newline is an okay candidate and only
            # penalize it a bit.
            total_len = len(current_line)
            lineno += 1
            while lineno < len(lines):
                total_len += len(lines[lineno])

                if lines[lineno].lstrip().startswith('#'):
                    total_len = max_line_length
                    break

                if not lines[lineno].endswith('\\'):
                    break

                lineno += 1

            if total_len < max_line_length:
                rank += 10
            else:
                rank += 100 if experimental else 1

        # Prefer breaking at commas rather than colon.
        if ',' in current_line and current_line.endswith(':'):
            rank += 10

        # Avoid splitting dictionaries between key and value.
        if current_line.endswith(':'):
            rank += 100

        rank += 10 * count_unbalanced_brackets(current_line)

    return max(0, rank)


def standard_deviation(numbers):
    """Return standard deviation."""
    numbers = list(numbers)
    if not numbers:
        return 0
    mean = sum(numbers) / len(numbers)
    return (sum((n - mean) ** 2 for n in numbers) /
            len(numbers)) ** .5


def has_arithmetic_operator(line):
    """Return True if line contains any arithmetic operators."""
    for operator in pycodestyle.ARITHMETIC_OP:
        if operator in line:
            return True

    return False


def count_unbalanced_brackets(line):
    """Return number of unmatched open/close brackets."""
    count = 0
    for opening, closing in ['()', '[]', '{}']:
        count += abs(line.count(opening) - line.count(closing))

    return count


def split_at_offsets(line, offsets):
    """Split line at offsets.

    Return list of strings.

    """
    result = []

    previous_offset = 0
    current_offset = 0
    for current_offset in sorted(offsets):
        if current_offset < len(line) and previous_offset != current_offset:
            result.append(line[previous_offset:current_offset].strip())
        previous_offset = current_offset

    result.append(line[current_offset:])

    return result


class LineEndingWrapper(object):

    r"""Replace line endings to work with sys.stdout.

    It seems that sys.stdout expects only '\n' as the line ending, no matter
    the platform. Otherwise, we get repeated line endings.

    """

    def __init__(self, output):
        self.__output = output

    def write(self, s):
        self.__output.write(s.replace('\r\n', '\n').replace('\r', '\n'))

    def flush(self):
        self.__output.flush()


def match_file(filename, exclude):
    """Return True if file is okay for modifying/recursing."""
    base_name = os.path.basename(filename)

    if base_name.startswith('.'):
        return False

    for pattern in exclude:
        if fnmatch.fnmatch(base_name, pattern):
            return False
        if fnmatch.fnmatch(filename, pattern):
            return False

    if not os.path.isdir(filename) and not is_python_file(filename):
        return False

    return True


def find_files(filenames, recursive, exclude):
    """Yield filenames."""
    while filenames:
        name = filenames.pop(0)
        if recursive and os.path.isdir(name):
            for root, directories, children in os.walk(name):
                filenames += [os.path.join(root, f) for f in children
                              if match_file(os.path.join(root, f),
                                            exclude)]
                directories[:] = [d for d in directories
                                  if match_file(os.path.join(root, d),
                                                exclude)]
        else:
            is_exclude_match = False
            for pattern in exclude:
                if fnmatch.fnmatch(name, pattern):
                    is_exclude_match = True
                    break
            if not is_exclude_match:
                yield name


def _fix_file(parameters):
    """Helper function for optionally running fix_file() in parallel."""
    if parameters[1].verbose:
        print('[file:{}]'.format(parameters[0]), file=sys.stderr)
    try:
        return fix_file(*parameters)
    except IOError as error:
        print(str(error), file=sys.stderr)
        raise error


def fix_multiple_files(filenames, options, output=None):
    """Fix list of files.

    Optionally fix files recursively.

    """
    results = []
    filenames = find_files(filenames, options.recursive, options.exclude)
    if options.jobs > 1:
        import multiprocessing
        pool = multiprocessing.Pool(options.jobs)
        rets = []
        for name in filenames:
            ret = pool.apply_async(_fix_file, ((name, options),))
            rets.append(ret)
        pool.close()
        pool.join()
        if options.diff:
            for r in rets:
                sys.stdout.write(r.get().decode())
                sys.stdout.flush()
        results.extend([x.get() for x in rets if x is not None])
    else:
        for name in filenames:
            ret = _fix_file((name, options, output))
            if ret is None:
                continue
            if options.diff:
                if ret != '':
                    results.append(ret)
            elif options.in_place:
                results.append(ret)
            else:
                original_source = readlines_from_file(name)
                if "".join(original_source).splitlines() != ret.splitlines():
                    results.append(ret)
    return results


def is_python_file(filename):
    """Return True if filename is Python file."""
    if filename.endswith('.py'):
        return True

    try:
        with open_with_encoding(
                filename,
                limit_byte_check=MAX_PYTHON_FILE_DETECTION_BYTES) as f:
            text = f.read(MAX_PYTHON_FILE_DETECTION_BYTES)
            if not text:
                return False
            first_line = text.splitlines()[0]
    except (IOError, IndexError):
        return False

    if not PYTHON_SHEBANG_REGEX.match(first_line):
        return False

    return True


def is_probably_part_of_multiline(line):
    """Return True if line is likely part of a multiline string.

    When multiline strings are involved, pep8 reports the error as being
    at the start of the multiline string, which doesn't work for us.

    """
    return (
        '"""' in line or
        "'''" in line or
        line.rstrip().endswith('\\')
    )


def wrap_output(output, encoding):
    """Return output with specified encoding."""
    return codecs.getwriter(encoding)(output.buffer
                                      if hasattr(output, 'buffer')
                                      else output)


def get_encoding():
    """Return preferred encoding."""
    return locale.getpreferredencoding() or sys.getdefaultencoding()


def main(argv=None, apply_config=True):
    """Command-line entry."""
    # symtable
    if argv is None:
        argv = sys.argv

    try:
        # Exit on broken pipe.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:  # pragma: no cover
        # SIGPIPE is not available on Windows.
        pass

    try:
        args = parse_args(argv[1:], apply_config=apply_config)

        if args.list_fixes:
            for code, description in sorted(supported_fixes()):
                print('{code} - {description}'.format(
                    code=code, description=description))
            return EXIT_CODE_OK

        if args.files == ['-']:
            assert not args.in_place

            encoding = sys.stdin.encoding or get_encoding()
            read_stdin = sys.stdin.read()
            fixed_stdin = fix_code(read_stdin, args, encoding=encoding)

            # LineEndingWrapper is unnecessary here due to the symmetry between
            # standard in and standard out.
            wrap_output(sys.stdout, encoding=encoding).write(fixed_stdin)

            if hash(read_stdin) != hash(fixed_stdin):
                if args.exit_code:
                    return EXIT_CODE_EXISTS_DIFF
        else:
            if args.in_place or args.diff:
                args.files = list(set(args.files))
            else:
                assert len(args.files) == 1
                assert not args.recursive

            results = fix_multiple_files(args.files, args, sys.stdout)
            if args.diff:
                ret = any([len(ret) != 0 for ret in results])
            else:
                # with in-place option
                ret = any([ret is not None for ret in results])
            if args.exit_code and ret:
                return EXIT_CODE_EXISTS_DIFF
    except IOError:
        return EXIT_CODE_ERROR
    except KeyboardInterrupt:
        return EXIT_CODE_ERROR  # pragma: no cover

class CachedTokenizer(object):

    """A one-element cache around tokenize.generate_tokens().

    Original code written by Ned Batchelder, in coverage.py.

    """

    def __init__(self):
        self.last_text = None
        self.last_tokens = None

    def generate_tokens(self, text):
        """A stand-in for tokenize.generate_tokens()."""
        if text != self.last_text:
            string_io = io.StringIO(text)
            self.last_tokens = list(
                tokenize.generate_tokens(string_io.readline)
            )
            self.last_text = text
        return self.last_tokens


_cached_tokenizer = CachedTokenizer()
generate_tokens = _cached_tokenizer.generate_tokens


if __name__ == '__main__':
    sys.exit(main())

