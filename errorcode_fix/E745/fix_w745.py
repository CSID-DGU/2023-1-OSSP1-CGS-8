import operator

def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''

def fix_w745(self, result):
        '''e745 docstring'''
        line_index = result['line'] - 1
        target = self.source[line_index]
        result = ''
        count=0
        while count !=2:
            line_index-=1
            target = self.source[line_index]
            if "'''" in target:
                self.source[line_index] = target.replace("'''",'"""')
                count+=1


result = {}
result['line'] = 0
result['column'] = 16
def self(): pass

#test case
self.source =  ["'''해당 줄에서 \
               이 연속으로 3개 \
               나오는 경우를 찾는다'''"]


fix_w745(self, result)
print('\n'.join(self.source))
self.source =  ['"""해당 줄에서 \
               이 연속으로 3개 \
               나오는 경우를 찾는다"""']
fix_w745(self,result)
print('\n'.join(self.source))


