import operator

def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''

# 1) '를 "로,

a = 'This is "string"'
a = "This is \'string\'"
# 2) "를 '로,
a = "This is 'string'"
a = 'This is \"string\"'

def fix_w744(self,result):
        line_index = result['line'] - 1
        target = self.source[line_index]
        i =0 
        check = False
        # 해당 라인을 읽어와 ' 또는 " 로 시작하는지 확인
        while i <len(target):
            if target[i] == '"':
                check = False
                break
            elif target[i] == "'":
                check  = True
                break
            else:
                i+=1
        # 변환 해주는 작업
        double_quote = {
            ord('"') : "'",
            ord("'") : '\"'
        }
        single_quote = {
            ord("'") : '"',
            ord('"') : "\'"
        }
        # 라인 업데이트
        if check == False:
            self.source[line_index] = target.translate(double_quote)
        
        else:
            self.source[line_index] = target.translate(single_quote)
     

result = {}
result['line'] = 0
result['column'] = 16
def self(): pass


#test case
self.source = ["'작은 따옴표 테스트'"]
fix_w744(self, result)
print('\n'.join(self.source))

self.source = ['"큰 따옴표 테스트"']
fix_w744(self, result)
print('\n'.join(self.source))

self.source = ["안뇽하세용'' \
               반갑습니다''"]
fix_w744(self, result)
print('\n'.join(self.source))


self.source = ["'''안뇽하세용'\n",
               '반갑습니다""\n',
               '""하이용"']
fix_w744(self, result)
print('\n'.join(self.source))




