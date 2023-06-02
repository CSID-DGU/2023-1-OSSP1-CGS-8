# __author__ = ('Wonjun Jo <c68254@gmail.com>')
# 작명 컨벤션: 클래스 이름 변경
# 클래스 이름은 CapWords 컨벤션을 따른다.

# 변경 X: CapWords 컨벤션 만족
class CapWords:
    def a():
        return None
    
# CamelCase로 변경
class camelCase:    
    def a():
        return None
        
# Noncapwords로 변경
class noncapwords:
    def b():
        return None

# SnakeCase로 변경
class snake_case:
    def c():
        return None

# 변경 X, 약어를 모두 대문자로 사용하는 것이 더 좋다고 PEP8에 명시
class HTTPServerError:
    def d():
        return None

# 변경 X
class A:
    def e():
        return None
    
# MixedCase로 변경
class Mixed_Case:
    def g():
        return None

# # MixedCase2로 변경
# class mixed_Case2:
#     def g2():
#         return None

# 변경 X, Capwords 컨벤션 만족
class AbCd:
    def h():
        return None
    
# python3 autopep8.py --aggressive --aggressive --aggressive test_W701.py