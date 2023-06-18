from test_import_userlib import *

class ex_two:
    def ExFunc(self):
        print('ex2의 함수입니다.')
        
    def aliasing(self):
        print('ex2의 함수입니다.')
        
    def FunctionAliasing(self):
        print('ex2의 함수입니다.')
        return None

def ExOne():
    print('ex1입니다.')
    return None

def ExFour():
    for _ in range(10):
        print('ex1입니다.')

class ExThree:
    def ex_func2(self):
        return None


# python autopep8.py -a -a -a --alias test_aliasing.py


# Aliasing 코드 삽입 결과
"""
class ExTwo:
    def ex_func(self):
        print("ex2의 함수입니다.")

    ExFunc = ex_func

    def aliasing(self):
        print("ex2의 함수입니다.")

    def function_aliasing(self):
        print("ex2의 함수입니다.")
        return None

    FunctionAliasing = function_aliasing


ex_two = ExTwo


def ex_one():
    print("ex1입니다.")
    return None


ExOne = ex_one


def ex_four():
    for _ in range(10):
        print("ex1입니다.")


ExFour = ex_four


class ExThree:
    def ex_func2(self):
        return None
"""