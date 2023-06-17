# __author__ = ('Wonjun Jo <c68254@gmail.com>')

# 같은 파일 내에서 클래스 상속 후 오버라이딩 메소드 예시
# 올바른 작명 컨벤션
class Person:
    def greeting():
        print('hi.')
        
class Student(Person):
    def greeting():
        print('hi. hello')

# W701 애러 -> 포매팅 후 SuperClass: 로 변경
# W702 에러 -> 포매팅 후 greeting_hello()으로 변경
class super_class:
    def GreetingHello():
        print('hi. A')

# W701 애러 -> 포매팅 후 SubClass(SuperClass): 로 변경
# W702 에러 -> 포매팅 후 greeting_hello()으로 변경
class sub_class(super_class):
    def GreetingHello():
        print('hi. B')
        
#W702 에러 -> 포매팅 후 greeting_hi()로 변경
class C:
    def greetingHi():
        print('hi. C')
        
class D(C):
    def greetingHi():
        print('hi. D')
        
# 변경 X
Person.greeting()
Student.greeting()

# 포매팅 후 SuperClass.greeting_hello()로 변경
super_class.GreetingHello()

# 포매팅 후 SubClass.greeting_hello()로 변경
sub_class.GreetingHello()

# 포매팅 후 C.greeting_hi()로 변경
C.greetingHi()

# 포매팅 후 D.greeting_hi()로 변경
D.greetingHi()

# python3 autopep8.py --aggressive --aggressive --aggressive test_overriding_same_file.py