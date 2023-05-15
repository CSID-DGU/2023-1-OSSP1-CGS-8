import string
import re
import keyword

# def snake_to_camel(snake_case):
#         if not is_snake_case(snake_case): return None
#         words = snake_case.split('_')
#         capwords = words[0] + ''.join(word.title() for word in words[1:])
#         return capwords

def is_snake_case(string):
    # 문자열이 비어 있는 경우
    if not string:
        return False

    # 첫 번째 문자가 소문자가 아닌 경우
    if not string[0].islower():
        return False

    # 밑줄 외의 다른 문자가 포함된 경우
    if not all(char.islower() or char == '_' for char in string):
        return False

    # 밑줄이 연속해서 나오는 경우
    if '__' in string:
        return False

    # 함수명이나 예약어인 경우
    if string in keyword.kwlist:
        return False

    return True

def is_camel_case(word):
    # 문자열이 비어 있는 경우
    if not word:
        return False

    # 공백이 포함된 경우
    if ' ' in word:
        return False

    # 밑줄이 포함된 경우
    if '_' in word:
        return False

    # 첫 번째 문자가 대문자인 경우
    if word[0].isupper():
        return False

    # 대문자로 시작하는 단어가 있는 경우
    if any(w[0].isupper() for w in word.split()):
        return False

    return True


# def snake_to_capwords(snake_case):
#     words = snake_case.split('_')
#     cap_words = [word.capitalize() for word in words]
#     cap_words = ''.join(cap_words)
#     return cap_words


def snake_to_capwords(snake_case):
    # if not is_snake_case(snake_case): return snake_case
    capitalized_words = string.capwords(snake_case, sep='_').replace('_', '')
    return capitalized_words


def camel_to_snake(camel_case):
    if not is_camel_case(camel_case): return camel_case.lower()
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
    return snake_case
    
def exam2():
    b = 0
    pass
a = 0
print(a)

# print(snake_to_camel("name_hi"))
print(snake_to_capwords("snake_case"))
print(snake_to_capwords("snakeCase"))
print(camel_to_snake("camelCase"))
print(camel_to_snake("snakeCase"))
print(camel_to_snake("snake_Case"))

# print(is_snake_case("hello_world"))  # True
# print(is_snake_case("Hello_World"))  # False
# print(is_snake_case("helloWorld"))   # False
# print(is_snake_case(""))             # False
# print(is_snake_case("_invalid"))     # False
# print(is_snake_case("__invalid"))    # False
# print(is_snake_case("if"))           # False
# print(is_snake_case("while"))        # False

# print()

# print(is_camel_case("helloWorld"))     # True
# print(is_camel_case("HelloWorld"))     # False
# print(is_camel_case("Hello_World"))    # False
# print(is_camel_case("hello world"))    # False
# print(is_camel_case("camelCaseTest"))  # True
# print(is_camel_case("CamelCaseTest"))  # False
# print(is_camel_case(""))               # False
# print(is_camel_case("singleword"))     # True

def to_capitalized_words_camel_case(word):
    # 카멜 케이스에서 각 단어를 대문자로 시작하도록 변경
    # 알파벳 이외의 문자 또는 대문자와 소문자 사이의 공백 제거하여 형식 조정
    return word[0].upper() + word[1:]#re.sub(r'([a-z])([A-Z])', r'\1\2', word)

def to_capitalized_words_snake_case(word):
    # 스네이크 케이스에서 각 단어를 대문자로 시작하도록 변경
    # 밑줄(_)을 공백으로 대체하여 형식 조정
    return string.capwords(word, sep='_').replace('_', '')
    # return string.replace('_', '')
    
def to_capitalized_words(word):
    if is_snake_case(word): return string.capwords(word, sep='_').replace('_', '') 
    return word[0].upper() + word[1:]

# 카멜 케이스를 CapitalizedWords 형식으로 변경 예시
print(to_capitalized_words("helloWorld"))      # HelloWorld
print(to_capitalized_words("camelCaseTest"))   # CamelCaseTest
print(to_capitalized_words("anotherExample"))  # AnotherExample
print(to_capitalized_words("hello"))

# 스네이크 케이스를 CapitalizedWords 형식으로 변경 예시
print(to_capitalized_words("hello_world"))       # Hello World
print(to_capitalized_words("snake_case_test"))   # Snake Case Test
print(to_capitalized_words("another_example"))  # Another Example

print()
print(is_camel_case("helloWorld"))     # True
print(is_camel_case("HelloWorld"))     # False
print(is_camel_case("Hello_World"))    # False
print(is_camel_case("hello world"))    # False
print(is_camel_case("camelCaseTest"))  # True
print(is_camel_case("CamelCaseTest"))  # False
print(is_camel_case(""))              # False
print(is_camel_case("singleword"))     # True

def CamelCase():    # 카멜 케이스 1
    return 0

def nameConvention():   # 카멜 케이스 2
    return 0

def nouppercase():  # 소문자로만 이루어진 케이스
    return 0

def Mixed_Case():   # 카멜 케이스와 스네이크 케이스가 겹친 경우
    return 0

def mixed_Case(): # 카멜 케이스와 스네이크 케이스가 겹친 경우
    return 0

def mixed_case():   # 스네이크 케이스
    return 0

