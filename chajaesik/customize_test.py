import operator

def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''

def replace_quotes(text):
    result = ''
    i = 0
    while i < len(text):
        if text[i:i+3] == "'''":
            result += '"""'
            i += 3
        else:
            result += text[i]
            i += 1
    return result
    
    
def fix_test(self, result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    fix = replace_quotes(target)
    self.source[line_index] = fix



''' 암시적 줄 읽기의 공백을 삭제해야 한다면 .. 
target = replace_quotes(self.source[line_index])
    offset = result['column']-1
    comment = target[offset:].strip()
    self.source[line_index] = target[:offset].rstrip()
    #print(self.source[line_index]+comment)
    self.source[line_index] = self.source[line_index]+comment '''

result = {}
result['line'] = 0
result['column'] = 16
def self(): pass



self.source =  ["'''해당 줄에서 \
               이 연속으로 3개 \
               나오는 경우를 찾는다'''"]



fix_test(self, result)
print('\n'.join(self.source))