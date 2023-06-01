import tokenize
import keyword

# def Abcd
# class class_this
def is_capwords(word):
    
    # 밑줄이 포함된 경우
    if '_' in word:
        return False
    
    # 첫 번째 문자가 대문자가 아닌 경우
    if not word[0].isupper():
        return False

    return True

def class_name_convention(logical_line, tokens):    
    prev_end = (0, 0)
    for token_type, text, start, end, line in tokens:
        if token_type == tokenize.NAME and text not in keyword.kwlist and not is_capwords(text) and "class" in line:
            not_recommend_class_name = line[:start[1]].strip()
            if not_recommend_class_name:
                yield (start, "W701 class name is recommended CapitalizedWords")
        elif token_type != tokenize.NL:
            prev_end = end

class className:
    def __init__(self):
        self.stats = tokenize.NL

'''
python3 -m tokenize class_in_comment_test.py 결과
NAME으로 def, class_name_convention가 나왔음. (이 뒤엔 꼭 OP (가 나와야 함))
NAME으로 class, className (이 뒤엔 꼭 OP :가 나와야 함.)
'''