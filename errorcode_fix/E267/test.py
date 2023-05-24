import operator

def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''

# 추가한 부분 - 이선호
# 이항 연산자인지 확인
def is_binary_operator(char):
    binary_operators = [
        "+", "-", "*", "/", "%", "**", "//", "==", "!=", ">", "<", ">=", "<=",
        "and", "or", "in", "not in", "is", "is not"
    ]
    
    return char in binary_operators or getattr(operator, char, None) is not None

# 추가한 부분 - 이선호
# 단항 연산자인지 확인
def is_unary_operator(char):
    unary_operators = [
        "+", "-", "~", "not"
    ]
    
    return char in unary_operators or getattr(operator, char + " ", None) is not None

# 추가한 부분 - 이선호
# 현재 줄에 열린 괄호 개수 반환
def count_open_bracket(line):
    open_bracket = line.count('(')\
        + line.count('{')\
        + line.count('[')
    return open_bracket

# 추가한 부분 - 이선호
# 현재 줄에 닫힌 괄호 개수 반환
def count_close_bracket(line):
    close_bracket = line.count(')')\
        + line.count('}')\
        + line.count(']')
    return close_bracket
    
def fix_test1(self, result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    offset = result['column']- 1
    comment = target[offset:].strip()
    self.source[line_index] = target[:offset].rstrip()
    
    open_bracket, close_bracket = 0, 0
    while line_index >= 0:
        current_line = self.source[line_index]
        open_bracket += count_open_bracket(current_line)
        close_bracket += count_close_bracket(current_line)
        
        if (line_index-1 >= 0 and
                self.source[line_index-1][-1] == chr(92)):
            line_index -= 1
            continue
        
        if (open_bracket == close_bracket):
            break
        line_index -= 1
        
    # 암시적 줄 잇기가 시작되는 줄의 들여쓰기와 인라인 주석의
    # 들여쓰기 수준 맞추기
    indent_word = _get_indentation(self.source[line_index])
    comment = indent_word + comment + '\n'
    self.source[line_index] = comment + self.source[line_index]
    
def fix_test2(self, result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    offset = result['column']- 1
    comment = target[offset:].strip()
    self.source[line_index] = target[:offset].rstrip()
        
    # 암시적 줄 잇기가 시작되는 줄의 들여쓰기와 인라인 주석의
    # 들여쓰기 수준 맞추기
    indent_word = _get_indentation(self.source[line_index])
    comment = indent_word + comment + '\n'
    self.source[line_index] = comment + self.source[line_index]


result = {}
result['line'] = 4
result['column'] = 29
def self(): pass
self.source = ['    if (a and b and', '        c.getResult(1 + 2 + 3\\',
               '            + 4 + 5 + 6\\', '                + 7) == 10): #이런이런 함수']

fix_test2(self, result)
print('\n'.join(self.source))

'''
a = [1,2,3, # 1
     4,5,6, # 2
     7,8,9, # 3
     10,11,12 # 4
     13,14,15] # 5
if (a and b and # 6
    c.getResult(1 + 2 + 3\ # 7
        + 4 + 5 + 6\ # 8
            + 7) == 10) # 9
b = 1,2,3, # 10
c = 1,2,3, # 11
d = 1,2,3, # 12
1,2,3 # 13

a = [1,2,3, # 1
     4,5,6, # 2
     7,8,9, # 3
     10,11,12 # 4
     13,14,15] # 5
c = 1,2,3, # 11
d = 1,2,3, # 12

# 1
# 2
# 3
# 4
#5
a = [1,2,3,
     4,5,6,
     7,8,9,
     10,11,12
     13,14,15]
# 11
c = 1,2,3,
# 12
d = 1,2,3,


,가 단순히 이항 연산자라고 생각해서 위쪽 라인으로 올리면 안됨
아래와 같은 반례가 존재

a = 4,5,6, # ,로 끝나는 경우 튜플로 처리
b = 5,6,7, # 주석2

'''