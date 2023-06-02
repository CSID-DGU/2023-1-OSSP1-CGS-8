# __author__ = ('Wonjun Jo <c68254@gmail.com>')
# 동일한 함수, 클래스명이 주석 안에 있을 경우 -> 컨벤션에 맞게 변경
# 주석 안의 함수명이나 클래스명은 변경하지 않아야 함

# 변경해야 할 클래스 이름과 함수 이름이 주석 안에 있는 경우
# 클래스명과 함수명이 바뀌지 않음
# class snake_case:
#     def SnakeCase():
#         return None

# 바꿨을 때 동일한 클래스명과 동일한 함수명이 주석 안에 있는 경우
# 클래스명과 함수명은 컨벤션이 맞게 변경되어야 함
class capWords:    # class CapWords:
    def SnakeCase():    # def snake_case():
        return None
    
# mixed word의 경우
class Mixed_Word_Case_C: # class MixedWordCaseC:
    def Mixed_Word_Case_S():    # def mixed_word_case_S():
        return None
    
# 바꿨을 때 클래스 이름과 클래스 내부의 메소드의 이름이 동일할 경우
# 클래스명과 함수명은 바뀌지 않음
class camel_case:    # class camel_case:
    def CamelCase():    # def CamelCase():
        return None
    
# mixed word의 경우
class CapWordCase:    # class CapWordCase: {CapWordCase: "class"}
    def CapWordCase():    # def cap_word_case():
        return None

# python3 autopep8.py --aggressive --aggressive --aggressive test_W7_comment.py
# python3 autopep8.py -a -a -a test_W7_comment.py