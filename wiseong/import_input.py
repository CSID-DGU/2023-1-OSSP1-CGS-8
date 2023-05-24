from input import * 

class person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        
    def printInfo(self):
        print("name = {}, age = {}".format(self.name,  self.age) )
        
addNumber(1 + 10)