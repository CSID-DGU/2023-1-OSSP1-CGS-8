# 클래스 이름 변경 예시 - import하여 상속하는 경우

from import_test8 import *


class child(parent):
    def b():
        print("hello")
        pass


p = parent
child.b()
