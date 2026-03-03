import re
# RegEx
txt = "The rain in Spain"
x = re.search("^The.*Spain$", txt)
print(x)
# The findall() Function
import re

txt = "The rain in Spain"
x = re.findall("ai", txt)
print(x)
# The search() Function

x = re.search("\s", txt)

print("The first white-space character is located in position:", x.start())

# The split() Function

txt = "The rain in Spain"
x = re.split("\s", txt)
print(x)

# The sub() Function

x = re.sub("\s", "9", txt)
print(x)

# re.match() 

s = "Hello"

if re.match(r'^[A-Za-z].*\d$', s):
    print("Yes")
else:
    print("No")
    

# Flags
txt = "The rain in Spain"
print(re.findall("spain", txt, re.IGNORECASE))
print(re.findall("spain", txt, re.I))
