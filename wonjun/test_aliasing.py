from test_import_userlib import *

class ex_two:
    def ExFunc(self):
        print('ex2의 함수입니다.')
        
    def aliasing(self):
        print('ex2의 함수입니다.')
        
    def FunctionAliasing(self):
        print('ex2의 함수입니다.')

def ExOne():
    print('ex1입니다.')

def ExFour():
    print('ex1입니다.')

class ExThree:
    def ex_func2(self):
        return None


# python autopep8.py -a -a -a --alias test_aliasing.py


# Aliasing 코드 삽입 결과
"""
class ExTwo:
    def ex_func():
        print('ex2의 함수입니다.')

    ExFunc = ex_func

    def aliasing():
        print('ex2의 함수입니다.')

    def function_aliasing():
        print('ex2의 함수입니다.')

    FunctionAliasing = function_aliasing


ex_two = ExTwo


def ex_one():

    print('ex1입니다.')


ExOne = ex_one


def ex_four():

    print('ex1입니다.')


ExFour = ex_four


class ExThree:
    def ex_func2(self):
        return None
    
ex_two.ExFunc()
ex_two.FunctionAliasing()
ExFour()
ExOne()
"""