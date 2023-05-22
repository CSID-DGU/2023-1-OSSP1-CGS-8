
class person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        
    def printInfo(self):
        print("name = {}, age = {}".format(self.name,  self.age) )
        

class computer_engineer(person):
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