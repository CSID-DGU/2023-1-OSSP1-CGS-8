# test_overriding_other_file.py
from test_overriding_other_file_super import MyClass

class MySubclass(MyClass):
    def my_method(self):
        print("Hello from MySubclass")
        
obj = MySubclass()
obj.my_method()  # 출력: "Hello from MySubclass"