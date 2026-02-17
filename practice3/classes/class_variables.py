class Student:
    school = "Python University"
    student_count = 0  
    def __init__(self, name, age):
        self.name = name
        self.age = age
        Student.student_count += 1

student1 = Student("Alice", 20)
student2 = Student("Bob", 22)

print(student1.school)        
print(student2.school)        
print(Student.school)        
print(Student.student_count)  

Student.school = "New Python University"
print(student1.school)  
print(student2.school)  