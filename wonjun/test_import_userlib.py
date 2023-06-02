# test_import_user.py에서 참조 및 상속되고 있는 클래스이므로 변경 X
class my_class:
    def __init__(self, name):
        self.name = name

    # test_import_user.py에서 오버라이딩 하고있는 함수이므로 변경 X
    def GreetHi(self):
        print(f"Hello, {self.name}!")

# test_import_user.py에서 참조 및 호출하고 있는 함수이므로 변경 X
def AddNumbers(a, b):
    return a + b

# test_import_user.py에서 사용되고 있지 않는 함수이므로 변경함
def DiffNumbers(a, b):
    return a - b

# test_import_user.py에서 사용되고 있지 않는 클래스이므로 변경함
class no_use_class:
    def NoUseFunction():
        return None
    
# python3 autopep8.py -a -a -a test_import_userlib.py