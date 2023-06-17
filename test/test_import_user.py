from test_import_userlib import *

# 자식 클래스는 이 파일에서만 사용하므로 작명 컨벤션에 맞게 수정
# 부모 클래스는 test_import_userlib에서 import해서 사용하는 파일
# 따라서 부모 클래스는 수정해주지 않음
class my_child_class(my_class):
    # 다른 파일의 함수를 오버라이딩하는 하는 함수이므로 변경하지 않음
    def GreetHi(self):
        print(f"Hi, {self.name}!")

# 할당하는 부분, 수정해주지 않음. import한 사용자 정의 라이브러리에 구현되어 있음
obj = my_class("Alice")
obj.GreetHi()

# 사용자 정의 라이브러리에서 사용중인 함수이므로 변경 X
result = AddNumbers(3, 4)

# 상속 및 오버라이딩, 이 파일에서만 사용하므로 변경해줌
derived_obj = my_child_class("Bob")
# 다른 파일의 함수를 오버라이딩하는 하는 함수 호출이므로 변경하지 않음
derived_obj.GreetHi()

# python3 autopep8.py -a -a -a test_import_user.py