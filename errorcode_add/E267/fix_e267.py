def fix_e267(self, result):
    """inline comment are not recommended"""
    #e401
    line_index = result['line'] - 1
    target = self.source[line_index]
    offset = result['column']- 1
    comment = target[offset:]
    target = target[:offset].rstrip()

'''  
고려사항 1
a = 1 + 2 + 3 + 4 + 5 \
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