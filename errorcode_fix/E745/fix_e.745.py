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
def double_change_quote(text):
    result=''
    #double_quote인 경우
    for character in text:
        if character == '"':
            result+='\''
        elif character == "'":
            result+='"'
        else:
            result+=character
    return result

def single_change_quote(text):
    result=''
    #single_quote인 경우
    for character in text:
        if character == "'":
            result+="\""
        elif character == '"':
            result+="'"
        else:
            result+=character
    return result

def fix_e744(self,result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    if(target[0] == '"'):
        fix = single_change_quote(target)
    else:
        fix = double_change_quote(target)
    self.source[line_index] = fix
     

result = {}
result['line'] = 0
result['column'] = 16
def self(): pass


#test case
self.source = ["'작은 따옴표 테스트'"]
fix_e744(self, result)
print('\n'.join(self.source))

self.source = ['"큰 따옴표 테스트"']
fix_e744(self, result)
print('\n'.join(self.source))

self.source = ["안뇽하세용'' \
               반갑습니다''"]
fix_e744(self, result)
print('\n'.join(self.source))






