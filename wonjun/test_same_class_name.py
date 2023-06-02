# __author__ = ('Wonjun Jo <c68254@gmail.com>')
# 작명 컨벤션에 맞게 함수명 변경 시 SameClass가 되어서
# 동일 파일 내에 똑같은 이름의 클래스가 존재하게 되므로
# 변경해주지 않음

class SameClass:
    def a():
        return None
    
class same_class:
    def b():
        return None
    
class sameClass:
    def c():
        return None
    
class diff_class:
    def d():
        return None


# python3 autopep8.py --aggressive --aggressive --aggressive test_same_class_name.py
# python3 autopep8.py -a -a -a test_same_class_name.py