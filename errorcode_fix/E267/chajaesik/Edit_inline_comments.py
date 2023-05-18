#고려사항 1번
import time

def fix_e267(self, result):
    """inline comment are not recommended"""
    start = time.time()
    line_index = result['line'] - 1  #현재 줄 
    target = self.source[line_index]
    offset = result['column'] -1 
    line = result['line'] + 1 #에러가 발생한 라인의 밑줄
    current_line = line_index #다음 줄 
    while current_line >=0:
        current_line -= 1
        if self.source[current_line] == '\\':
            self.source[current_line] = self.source[current_line] + self.source[line] #해당 줄과 밑의 줄을 합친다
            self.source[line] = '' #에러가 발생한 줄의 밑 줄을 빈 문자열로 수정하는 작업
        else:
            continue     
        try:
            compile(line_index, '<string>', 'single')
        except (SyntaxError, TypeError, ValueError):
            break
    end = time.time()
    print(f"{end-start:.5f} sec")





# 고려사항 1,2,3,4 
def fix_e268(self, result):
    """inline comment are not recommended"""
    line_index = result['line'] - 1
    target = self.source[line_index][:] # [:] 복사해서 반환해주는 
    offset = result['column'] - 1 
    # 주석 내용 저장
    comment = target[offset+1:].lstrip()
    count = 0
    #target1에 해당 코드 줄 내용 저장
    target1= self.source[target][:]
    while not check_count_parenthesis(target1, count):
        target1 = self.source[line_index][:] #해당 줄의 내용 저장
        line_index -= 1   #줄의 인덱스를 위로 올리고
        target2 = self.source[line_index][:] #올라간 인덱스의 줄 , 즉 윗줄 내용복사
        target1 = target1 + target2 #오류 발생한 줄과 그 윗줄의 내용을 합친다
    # 들여쓰기 수준 맞추기
    indent = _get_indentation(line_index)
    #윗줄에 주석 추가
    self.source[line_index] =  indent + '# ' + comment


# 괄호의 개수로 체크하는 함수
# 작동 확인
def check_count_parenthesis(expression, count):
    """Check the number of parentheses """
    for char in expression:
        if char == '(' or char =='[' or char =='{':
            count += 1
        elif char == ')' or char ==']' or char =='}':
            count -= 1
    count += expression.count('(') + expression.count('[') + expression.count('{')
    count -= expression.count(")") + expression.count(']') + expression.count('}')
    if count < 0:
        return False
    return True

print(check_count_parenthesis("([a+b+c[abcde]])",0))


'''
고려사항 1
a = 1 + 2 + 3 + 4 + 5  \
    + 5 + 6 + 7 + 8 + 9 \
    + 10 + 11 + 12 #asdfawef
    
#인라인 주석
if (a and b andc.getResult(a, b, c, de, f, g, h))
    
고려사항 3
    # 이런저런 함수
    if (a and b and
        c.getResult(a, b, c, d
                    e, f, g, h)) #이런이런 함수
    
고려사항 4
() {} []가 섞여 있을 때
'''