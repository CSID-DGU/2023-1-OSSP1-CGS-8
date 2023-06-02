import tokenize
import keyword

# def Abcd
# class class_this
def is_capwords(word):

    if not word[0].isupper():
        return False

    return True

def class_name_convention(logical_line, tokens):    
    prev_end = (0, 0)

class calssName:
    def __init__(self):
        self.stats = tokenize.NL

'''
python3 -m tokenize class_in_comment_test.py 결과
NAME으로 def, class_name_convention가 나왔음. (이 뒤엔 꼭 OP (가 나와야 함))
NAME으로 class, className (이 뒤엔 꼭 OP :가 나와야 함.)
'''