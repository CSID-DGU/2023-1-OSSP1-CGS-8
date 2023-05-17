# __author__ = ('Wonjun Jo <c68254@gmail.com>')

# 동일한 클래스명이 주석 안에 있을 경우
# CamelCase -> CamelCase
class CamelCase:
    def a():
        return None
    
# camelCasea -> CamelCasea
class camelCasea:    
    def a():
        return None
    
# camelcaseb -> Camelcaseb
class camelcaseb:
    def b():
        return None

# camel_casec -> CamelCasec
class camel_casec:
    def c():
        return None

# Camelcased -> Camelcased
class Camelcased:
    def d():
        return None
    
# Camel_Casee -> Camel_Casee
class Camel_Casee:
    def e():
        return None

# CAMELcasef -> CAMELcasef
class CAMELcasef:
    def f():
        return None

# CamelCAsEg -> CamelCAsEg
class CamelCAsEg:
    def g():
        return None
    
# ------------------------------------------------------------------------------------------
# 동일한 함수명이 주석안에 있을 경우
# snake_case -> snake_case
def snake_case():
    return None

# SnakeCasea -> snake_casea
def SnakeCasea():
    return None

# snakeCaseb -> snake_caseb
def snakeCaseb():
    return None

# snakecasec -> snakecasec
def snakecasec():
    return None

# Snake_Cased -> snake__cased
def Snake_Cased():
    return None

# snake__casee -> snake__casee
def snake__casee():
    return None

# python3 autopep8.py --aggressive --aggressive --aggressive test_W7_comment.py