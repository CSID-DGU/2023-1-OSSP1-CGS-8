# list

# 작명 컨벤션에 따라 클래스명을 CapWrods(CamelCase) 형식으로 
# 단어의 첫글자를 대문자로 변경하고 단어들을 붙여 변경했을 때
# 1. 함수명과 동일해지는 경우
# 2. 변수명과 동일해지는 경우


# 작명 컨벤션에 따라 함수명을 snake_case 형식으로
# 소문자로 작성하고 단어들을 '_'로 구분하여 변경했을 때
# 1. 클래스명과 동일해지는 경우
# 2. 변수명과 동일해지는 경우

# import 했을 때

# 상속받은 클래스의 메소드에서 오버라이딩

# CASE 클래스의 내부 메소드와 전역 함수의 이름이 같을 때
""" 코드 작성 시 클래스 내부 메소드는 클래스명을 참조헤서 사용하고

전역 함수의 경우 그렇지 않으므로 이름 변경 시 구문 오류 발생하지 않음
"""
# CASE code
class Example:
    def Exam1():
        return None

def Exam1():
    return None

# FORMATTING code
class Example:
    def exam1():
        return None

def exam1():
    return None

# 클래스 상속 여부
# 부모 클래스를 상속하고 있는 자식 클래스일 경우 변경을 해줘야할지 말아야 할지
# 자식 클래스의 이름을 변경할지 말지 

class Person:
    def greeting(self):
        print('안녕하세요.')
 
class Student(Person):
    def greeting(self):
        print('안녕하세요. 저는 파이썬 코딩 도장 학생입니다.')
        
class person:
    def greeting(self):
        print('테스트 케이스 : 상속')
 
class student(person):
    def greeting(self):
        print('테스트케이스 : 상속하고 있을 경우')
        
class parent:
    def d():
        return None
    
class snake_case(parent):
    def a():
        return None

# 카멜 케이스와 스네이크 케이스를 혼용
class user_account:
    def __init__(self, user_name, password_hash):
        self.user_name = user_name
        self.password_hash = password_hash

    def SetUserName(self, user_name):
        self.user_name = user_name

    def get_password_hash(self):
        return self.password_hash

    def validate_password(self, password):
        # 비밀번호 유효성 검사 로직
        pass

    def changePassword(self, new_password):
        # 비밀번호 변경 로직
        pass