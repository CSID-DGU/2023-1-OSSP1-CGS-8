def implicit_continuous_line(self, result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    offset = result['column']- 1
    comment = target[offset:].strip()
    target = target[:offset].rstrip()
    
    # 현재 읽고 있는 라인의 번호를 저장
    current_line = line_index
    first_line = self.source[current_line][:]
    # 암시적으로 이어지는 줄을 하나의 줄로 합쳐서 컴파일
    while current_line >= 0:
        current_line -= 1
        # 만약 '\'가 포함되어있다면 '\' 제거 후 줄 합치기
        if self.source[current_line][-1] == chr(92):
            first_line += self.source[current_line][:-1]
        else:
            first_line += self.source[current_line][:]
        try:
            compile(first_line, '<string>', 'single')
            # 암시적 줄 잇기가 시작되는 줄을 만나면
            # 정상적으로 컴파일되므로 루프 탈출
            break
        except (SyntaxError, TypeError, ValueError):
            continue
    
    # 암시적 줄 잇기가 시작되는 줄의 들여쓰기와 인라인 주석의
    # 들여쓰기 수준 맞추기
    indent_word = _get_indentation(self.source[current_line])
    comment = indent_word + comment + '\n'
    self.source[current_line] = comment + self.source[result['line'] - 1]
    
def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]

    return ''
    
def fix_test(self, result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    offset = result['column']- 1
    comment = target[offset:].strip()
    self.source[line_index] = target[:offset].rstrip()
    
    open_bracket, close_bracket = 0, 0
    while line_index >= 0:
        current_line = self.source[line_index]
        
        open_bracket += current_line.count('(')\
            + current_line.count('{')\
            + current_line.count('[')
        close_bracket += current_line.count(')')\
            + current_line.count('}')\
            + current_line.count(']')
        
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