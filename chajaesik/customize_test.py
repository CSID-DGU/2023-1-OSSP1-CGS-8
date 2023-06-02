import operator

def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''

def make_single_quotes(text):
    result=''
    i = 0
    while i < len(text):
        if text[i:i+3] == '"""':
            result += "'''"
            i += 3
        else:
            result += text[i]
            i += 1
    return result


def make_double_quotes(text):
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
    

#quote style을 인수로 받음
def fix_E745(self,result,quote_style):
    line_index = result['line'] - 1
    target = self.source[line_index]
    if quote_style == 0:
        fix = make_double_quotes(target)
    elif quote_style == 1:
        fix = make_single_quotes(target)
    self.source[line_index] = fix



result = {}
result['line'] = 0
result['column'] = 16
def self(): pass


#test case
self.source =  ["'''해당 줄에서 \
               이 연속으로 3개 \
               나오는 경우를 찾는다'''"]


fix_E745(self, result,0)
print('\n'.join(self.source))
self.source =  ['"""해당 줄에서 \
               이 연속으로 3개 \
               나오는 경우를 찾는다"""']
fix_E745(self,result,1)
print('\n'.join(self.source))
