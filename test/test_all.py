import math, sys;

def example1():
    ####This is a long comment. This should be wrapped to fit within 72 characters.
    some_tuple=(   1,2, 3,'a'  );
    some_variable={'long':'Long code lines should be wrapped within 79 characters.',
    'other':[math.pi, 100,200,300,9876543210,'This is a long string that goes on'],
    'more':{'inner':'This whole logical line should be wrapped.',some_tuple:[1,
    20,300,40000,5,6000000]}}
    return (some_tuple, some_variable)
def ExampleTwo(): # inline comment
    return {'has_key() is deprecated':True}.has_key({'f':2}.has_key(''));
class example_three(   object ):    # inline comment2
    def __init__    ( self, bar ):
        #Comments should have a space after the hash.
        if bar : bar+=1;  bar=bar* bar   ; return bar   # 인라인 주석
        else:
                some_string = '''
                여러 줄 문자열 
                double quote 변환'''
        return (sys.path, some_string)