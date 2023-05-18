# __author__ = ('Wonjun Jo <c68254@gmail.com>')

# 같은 파일 내에서 클래스 상속 후 오버라이딩 메소드 예시
# 문제가 없는 경우
class Person:
    def greeting():
        print('hi.')
        
class Student(Person):
    def greeting():
        print('hi. hello')
        
# W702 에러 -> 포매팅 후 greeting()으로 변경
class A:
    def Greeting():
        print('hi. A')
        
class B(A):
    def Greeting():
        print('hi. B')
        
#W702 에러 -> 포매팅 후 greeting_hi()로 변경
class C:
    def GreetingHi():
        print('hi. C')
        
class D(C):
    def GreetingHi():
        print('hi. D')
        
Person.greeting()
Student.greeting()
A.Greeting()
B.Greeting()
C.GreetingHi()
D.GreetingHi()
