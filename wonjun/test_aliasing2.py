class ex_two:
    def ExFunc(self):
        print('ex2의 함수입니다.')
        
    def aliasing(self):
        print('ex2의 함수입니다.')
        
    def FunctionAliasing(self):
        print('ex2의 함수입니다.')

def ExOne():
    print('ex1입니다.')

def ExFore():
    print('ex1입니다.')

class ExThree:
    def ex_func2(self):
        return None


# python autopep8.py -a -a -a test_aliasing2.py
# python fix_bug.py -a -a -a test_aliasing2.py