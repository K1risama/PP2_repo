class Flyer:
    def fly(self):
        return "I can fly"
    
    def get_info(self):
        return "This is a flying object"

class Swimmer:
    def swim(self):
        return "I can swim"
    
    def get_info(self):
        return "This is a swimming object"

class Duck(Flyer, Swimmer):
    def __init__(self, name):
        self.name = name
    
    def get_info(self):
        return f"Duck named {self.name}"

duck = Duck("Donald")
print(duck.fly())     
print(duck.swim())    
print(duck.get_info())  