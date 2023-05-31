# 함수에 대한 aliasing 예시
def ex_one():
    print('ex1입니다.')

# ex_one 함수를 ExOne으로 aliasing 코드 추가
ExOne = ex_one

# 별칭된 함수 호출
ExOne()  # 출력: ex1입니다.

# 클래스에 대한 aliasing 예시
class ExTwo:
    def ex2_func(self):
        print('ex2의 함수입니다.')

# ExTwo 클래스를 ex_two로 aliasing 코드 추가
ex_two = ExTwo

# aliasing된 클래스 인스턴스 생성
obj = ex_two()

# aliasing된 클래스의 메서드 호출
obj.ex2_func()  # 출력: ex2의 함수입니다.