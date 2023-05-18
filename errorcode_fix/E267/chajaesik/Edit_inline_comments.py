#고려사항 1번
import time

start = time.time()
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



#고려사항 2,3,4 
def fix_e268(self, result):
    """inline comment are not recommended"""
    line_index = result['line'] - 1
    target = self.source[line_index] 
    offset = result['column'] - 1 
    #code = target[:offset].rstrip(' \t#') 
    # 주석 내용 저장
    comment = target[offset:].lstrip(' \t#')
    while(check_parentheses(target) is False):
        line_index = result['line'] - 1
        target = self.source[line_index] 
        line = result['line'] - 2
        self.source[line_index] = self.source[target] + self.source[line] #해당 줄과 밑의 줄을 합친다
        self.source[line] = ''   #밑줄을 공백으로
    #윗줄에 주석 추가
    line = result['line'] - 2
    self.source['line'] =  comment

# 괄호의 개수로 체크하는 함수
def check_parentheses(expression):
    """Check the number of parentheses """
    count = 0

    for char in expression:
        if char == '(' or char =='[' or char =='{':
            count += 1
        elif char == ')' or char ==']' or char =='}':
            count -= 1

        if count < 0:
            return False
    return count == 0
#괄호 쌍이 일치하지 않는 경우
#여는 괄호와 닫는 괄호의 순서가 잘못된 경우 오류 발생
                    

'''  
고려사항 1
a = 1 + 2 + 3 + 4 + 5  \
    + 5 + 6 + 7 + 8 + 9 \
    + 10 + 11 + 12

    
고려사항 2
if (a and b and
    c.getResult(a, b, c, d
    e, f, g, h)
    ) #이런이런 함수
    
고려사항 3
if (a and b and
    c.getResult(a, b, c, d
                e, f, g, h)) #이런이런 함수
                
고려사항 4
() {} []가 섞여 있을 때
'''