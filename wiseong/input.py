# from import_input import *
import import_input

class computer_engineer(import_input.person): #computer_engineer
    def __init__(self, name, age, job):
        self.job = job
        super().__init__(name, age)  
        
    def printInfo(self):  
        print("name = {}, age = {}, job = {}".format(self.name, self.age, self.job))        

def addNumber(x, y):
    return x + y

def subNumber(x, y):
    return x - y

engineer = computer_engineer("jaesik", 24, "computer engineer")
engineer.printInfo()
addNumber(1 + 10)