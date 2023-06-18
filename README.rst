========
autopyre
========

.. image:: https://img.shields.io/pypi/v/pyrestyle.svg
    :target: https://pypi.org/project/pyrestyle/
    

.. image:: https://img.shields.io/pypi/v/autopyre.svg
    :target: https://pypi.org/project/autopyre/
    

autopep8_ 과 pycodestyle_ 을 개선한 ``Python Code Style Formatter``

* autopyre는 python 코드를 자동으로 PEP8_ 스타일 가이드에 맞게 포매팅하는 도구입니다.
* 파이썬 코드 스타일 가이드 PEP8_ 에 기반한 코드 스타일로 수정해줍니다.
* 사용자가 스타일 설정이 가능하도록 ``커스터마이징`` 기능을 추가해 유연성을 강화했습니다.
* 또한 PEP8에서 언급하는 클래스명, 함수명에 대한 ``작명 컨벤션`` 에 부합하게 구현하였습니다.


.. contents::


Installation
============

.. code-block:: shell

   $ pip install autopyre
   $ pip install --upgrade autopyre


Requirements
============

autopyre requires pyrestyle_

.. code-block:: shell

   $ pip install pyrestyle
   $ pip install --upgrade pyrestyle


Usage
=====

파일 변경 내용을 콘솔로 출력 (default)::

    $ autopyre -a -a -a <filename>

파일 변경 내용을 파일에 덮어쓰기 (aggressive level 3)::

    $ autopyre --in-place -a -a -a <filename>


autopyre 실행 전 코드 (코드의 의미 X, 포매팅에 집중)

.. code-block:: python

    import math, sys;

    def example1():
        ####This is a long comment. This should be wrapped to fit within 72 characters.
        some_tuple=(   1,2, 3,'a'  );
        some_variable={'long':'Long code lines should be wrapped within 79 characters.',
        'other':[math.pi, 100,200,300,9876543210,'This is a long string that goes on'],
        'more':{'inner':'This whole logical line should be wrapped.',some_tuple:[1,
        20,300,40000,5,6000000]}}
        return (some_tuple, some_variable)
    def ExampleTwo(): # inline comment
        return {'has_key() is deprecated':True}.has_key({'f':2}.has_key(''));
    class example_three(   object ):    # inline comment2
        def __init__    ( self, bar ):
            #Comments should have a space after the hash.
            if bar : bar+=1;  bar=bar* bar   ; return bar   # 인라인 주석
            else:
                    some_string = '''
                    여러 줄 문자열 
                    double quote 변환'''
            return (sys.path, some_string)

autopyre 실행 후 코드

.. code-block:: shell

   $ autopyre -a -a -a test_all.py


.. code-block:: python

    import math
    import sys

    def example1():
        # This is a long comment. This should be wrapped to fit within 72
        # characters.
        some_tuple = (1, 2, 3, "a")
        some_variable = {
            "long": "Long code lines should be wrapped within 79 characters.",
            "other": [
                math.pi,
                100,
                200,
                300,
                9876543210,
                "This is a long string that goes on"],
            "more": {
                "inner": "This whole logical line should be wrapped.",
                some_tuple: [
                    1,
                    20,
                    300,
                    40000,
                    5,
                    6000000]}}
        return (some_tuple, some_variable)


    # inline comment
    def example_two():
        return {"has_key() is deprecated": True}.has_key({"f": 2}.has_key(""))


    # inline comment2
    class ExampleThree(object):
        def __init__(self, bar):
            # Comments should have a space after the hash.
            if bar:
                bar += 1
                bar = bar * bar
                # 인라인 주석
                return bar
            else:
                some_string = """
                    여러 줄 문자열
                    double quote 변환"""
            return (sys.path, some_string)


Options::

    usage: autopep8 [-h] [--version] [-v] [-d] [-i] [--global-config filename]
                    [--ignore-local-config] [-r] [-j n] [-p n] [-a]
                    [--experimental] [--exclude globs] [--list-fixes]
                    [--ignore errors] [--select errors] [--max-line-length n]
                    [--line-range line line] [--hang-closing] [--exit-code]
                    [files [files ...]]

            * only autopyre
				    [--customize] [—-alias] [-a -a -a]
                    [--aggressive --aggressive --aggressive]

    Automatically formats Python code to conform to the PEP 8 style guide.

    positional arguments:
      files                 files to format or '-' for standard in

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -v, --verbose         print verbose messages; multiple -v result in more
                            verbose messages
      -d, --diff            print the diff for the fixed source
      -i, --in-place        make changes to files in place
      --global-config filename
                            path to a global pep8 config file; if this file does
                            not exist then this is ignored (default:
                            ~/.config/pep8)
      --ignore-local-config
                            don't look for and apply local config files; if not
                            passed, defaults are updated with any config files in
                            the project's root directory
      -r, --recursive       run recursively over directories; must be used with
                            --in-place or --diff
      -j n, --jobs n        number of parallel jobs; match CPU count if value is
                            less than 1
      -p n, --pep8-passes n
                            maximum number of additional pep8 passes (default:
                            infinite)
      -a, --aggressive      enable non-whitespace changes; multiple -a result in
                            more aggressive changes
      --experimental        enable experimental fixes
      --exclude globs       exclude file/directory names that match these comma-
                            separated globs
      --list-fixes          list codes for fixes; used by --ignore and --select
      --ignore errors       do not fix these errors/warnings (default:
                            E226,E24,W50,W690)
      --select errors       fix only these errors/warnings (e.g. E4,W)
      --max-line-length n   set maximum allowed line length (default: 79)
      --line-range line line, --range line line
                            only fix errors found within this inclusive range of
                            line numbers (e.g. 1 99); line numbers are indexed at
                            1
      --hang-closing        hang-closing option passed to pycodestyle
      --exit-code           change to behavior of exit code. default behavior of
                            return value, 0 is no differences, 1 is error exit.
                            return 2 when add this option. 2 is exists
                            differences.


Features
========

autopyre fixes the following issues_ reported by pyrestyle_::

    E101 - Reindent all lines.
    E11  - Fix indentation.
    E121 - Fix indentation to be a multiple of four.
    E122 - Add absent indentation for hanging indentation.
    E123 - Align closing bracket to match opening bracket.
    E124 - Align closing bracket to match visual indentation.
    E125 - Indent to distinguish line from next logical line.
    E126 - Fix over-indented hanging indentation.
    E127 - Fix visual indentation.
    E128 - Fix visual indentation.
    E129 - Fix visual indentation.
    E131 - Fix hanging indent for unaligned continuation line.
    E133 - Fix missing indentation for closing bracket.
    E20  - Remove extraneous whitespace.
    E211 - Remove extraneous whitespace.
    E22  - Fix extraneous whitespace around keywords.
    E224 - Remove extraneous whitespace around operator.
    E225 - Fix missing whitespace around operator.
    E226 - Fix missing whitespace around arithmetic operator.
    E227 - Fix missing whitespace around bitwise/shift operator.
    E228 - Fix missing whitespace around modulo operator.
    E231 - Add missing whitespace.
    E241 - Fix extraneous whitespace around keywords.
    E242 - Remove extraneous whitespace around operator.
    E251 - Remove whitespace around parameter '=' sign.
    E252 - Missing whitespace around parameter equals.
    E26  - Fix spacing after comment hash for inline comments.
    E265 - Fix spacing after comment hash for block comments.
    E266 - Fix too many leading '#' for block comments.
    E27  - Fix extraneous whitespace around keywords.
    E301 - Add missing blank line.
    E302 - Add missing 2 blank lines.
    E303 - Remove extra blank lines.
    E304 - Remove blank line following function decorator.
    E305 - Expected 2 blank lines after end of function or class.
    E306 - Expected 1 blank line before a nested definition.
    E401 - Put imports on separate lines.
    E402 - Fix module level import not at top of file
    E501 - Try to make lines fit within --max-line-length characters.
    E502 - Remove extraneous escape of newline.
    E701 - Put colon-separated compound statement on separate lines.
    E70  - Put semicolon-separated compound statement on separate lines.
    E711 - Fix comparison with None.
    E712 - Fix comparison with boolean.
    E713 - Use 'not in' for test for membership.
    E714 - Use 'is not' test for object identity.
    E721 - Use "isinstance()" instead of comparing types directly.
    E722 - Fix bare except.
    E731 - Use a def when use do not assign a lambda expression.
    W291 - Remove trailing whitespace.
    W292 - Add a single newline at the end of the file.
    W293 - Remove trailing whitespace on blank line.
    W391 - Remove trailing blank lines.
    W503 - Fix line break before binary operator.
    W504 - Fix line break after binary operator.
    W605 - Fix invalid escape sequence 'x'.
    W690 - Fix various deprecated code (via lib2to3).

    * only autopyre

    E267 - Remove inline comment and add block comment
    W705 - Modify class name to capwords case
    W706 - Modify class name to capwords case and add aliasing code
    W707 - Modify function name to snake case
    W708 - Modify function name to snake case and add aliasing code
    w744 - Modify single quote to double quote
    w745 - Modify triple single quote to triple double quote


Naming Convention
=================

Description::
    
    - [-a -a -a]
    PEP8 스타일 가이드에서 권장하는 클래스와 함수의 작명 규칙을 
    따르지 않을 경우 권장하는 스타일에 맞게 수정합니다.

    예시
    $ autopyre -a -a -a input.py


    - [--alias]
    Aliasing 코드 삽입

    예시
    $ autopyre -a -a -a --alias input.py

Customize
=========

Description::

    - [--customize]
    custom.txt 파일을 수정해서 적용할 수 있습니다.

    예시
    autopyre --customize input.py


License
=======

MIT 라이선스를 준수하며 LICENSE_ 에서 자세한 정보를 확인할 수 있습니다. 


Contacts
========

- 김위성 `github <https://github.com/kimwiseong>`_ – 2019112083@dgu.ac.kr
- 김태욱 `github <https://github.com/Taew00k>`_ – davis0625@dgu.ac.kr
- 이선호 `github <https://github.com/prefer52>`_ – 2019111998@dgu.ac.kr
- 조원준 `github <https://github.com/jun6292>`_ – c68254@dgu.ac.kr
- 차재식 `github <https://github.com/Chajaesik01>`_ – 2019112003@dgu.ac.kr
- 하지은 `github <https://github.com/HAJIEUN02>`_ – 2021111937@dgu.ac.kr


Links
=====

* PyPI_
* PEP8_
* autopep8_
* autopyre_
* pyrestlye_
* pycodestyle_

.. _PyPI: https://pypi.org/project/autopep8/
.. _autopep8: https://github.com/hhatto/autopep8
.. _autopyre: https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08
.. _pycodestyle: https://github.com/PyCQA/pycodestyle
.. _pyrestyle: https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08/blob/main/pyrestyle.py
.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _LICENSE: https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08/blob/main/LICENSE
.. _issues: https://pycodestyle.readthedocs.org/en/latest/intro.html#error-codes