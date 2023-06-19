
class my_class:

    def printHello():
        '''
        print Hello
        '''
        print('Hello')


def addNumbers(a, 
            b,
            c):
    return a +     b + c



obj = my_class  # 객체 생성

result = addNumbers(1, 2, 3)
print(result)

child_obj = my_class.printHello()
obj.printHello
