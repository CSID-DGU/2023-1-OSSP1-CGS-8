# __author__ = ('Wonjun Jo <c68254@gmail.com>')
# 작명 컨벤션에 맞게 함수명 변경 시 same_name이 되어서
# 동일 파일 내에 똑같은 이름의 함수가 존재하게 되므로
# 변경해주지 않음

def same_name():
    return None

def SameName():
    return None

def sameName():
    return None

def DiffName():
    return None

# python3 autopep8.py --aggressive --aggressive --aggressive test_same_function_name.py
# python3 autopep8.py -a -a -a test_same_function_name.py