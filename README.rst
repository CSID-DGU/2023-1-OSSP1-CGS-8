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

.. image:: https://github.com/CSID-DGU/2023-1-OSSP1-CGS-8/assets/75564221/57d971f8-5e06-43b8-898b-a0c14762efe1.gif
   :alt: autopyre 사용법

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

    usage: autopyre [--customize] [-a -a -a] [—-alias]
                    [--aggressive --aggressive --aggressive]
                    [-a -a -a --in-place]
                    [-a -a -a --alias --in-place]
                    [-d] [--diff] [-i] [--in-place]
				    

    Automatically formats Python code to conform to the PEP 8 style guide.

    positional arguments:
      files                 files to format or '-' for standard in

    optional arguments:
      -i, --in-place        make changes to files in place
      -a, --aggressive      enable non-whitespace changes; multiple -a result in
                            more aggressive changes
      -d, --diff            show difference before formatting and after formatting
      --experimental        enable experimental fixes
      --customize           customzie formatting style with modifying custom.txt file



Features
========

autopyre fixes the following issues_ reported by pyrestyle_::

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
    
    * [-a -a -a]
    PEP8 스타일 가이드에서 권장하는 클래스와 함수의 작명 규칙을 
    따르지 않을 경우 권장하는 스타일에 맞게 수정합니다.

    예시
    $ autopyre -a -a -a input.py


    * [--alias]
    Aliasing 코드 삽입

    예시
    $ autopyre -a -a -a --alias input.py

Customize
=========

Description::

    * [--customize]
    custom.txt 파일을 수정해서 적용할 수 있습니다.

    예시
    autopyre --customize input.py


+------------+------------+-----------+
| 커스터마이징 가능 항목 | 필요 조건 |
+============+============+===========+
| 공백 문자 기준 들여쓰기 수준 설정 | 0보다 큰 양수 |
+------------+------------+-----------+
| 닫힌 괄호 위치 스타일 설정 | 0, 1로 스타일 선택 |
+------------+------------+-----------+
| 이항 연산자 줄바꿈 스타일 설정 | 0, 1로 스타일 선택 |
+------------+------------+-----------+
| 한 줄의 최대 길이 설정 | 0보다 큰 양수 |
+------------+------------+-----------+
| 문자열 쿼트 스타일 설정 | 0, 1로 스타일 선택 |
+------------+------------+-----------+
| select argument 설정 | ,를 기준으로 에러 코드 나열 |
+------------+------------+-----------+
| ignore argument 설정 | ,를 기준으로 에러 코드 나열 |
+------------+------------+-----------+
| 각 항목에 대한 무시 여부 설정 | True 시 각 항목 무시 가능 |
+------------+------------+-----------+


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
* pyrestyle_
* pycodestyle_

.. _PyPI: https://pypi.org/project/autopep8/
.. _autopep8: https://github.com/hhatto/autopep8
.. _autopyre: https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08
.. _pycodestyle: https://github.com/PyCQA/pycodestyle
.. _pyrestyle: https://github.com/CSID-DGU/2023-1-OSSP1-CGS-8/blob/main/pyrestyle.py
.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _LICENSE: https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08/blob/main/LICENSE
.. _issues: https://pycodestyle.readthedocs.org/en/latest/intro.html#error-codes
