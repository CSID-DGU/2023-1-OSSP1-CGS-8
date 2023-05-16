def implicit_continuous_line(self, result):
    line_index = result['line'] - 1
    target = self.source[line_index]
    offset = result['column']- 1
    comment = target[offset:].strip()
    target = target[:offset].rstrip()
    
    current_line = line_index
    first_line = self.source[current_line][:]
    while current_line >= 0:
        current_line -= 1
        first_line += self.source[current_line][:-1]
        try:
            compile(first_line, '<string>', 'single')
        except (SyntaxError, TypeError, ValueError):
            break
    
    if current_line < 0: current_line = 0
    else: current_line += 1
    
    indent_word = _get_indentation(self.source[current_line])
    comment = indent_word + comment + '\n'
    self.source[current_line] = comment + self.source[result['line'] - 1]