import os
if os.path.exists("file.txt"):
  os.remove("file.txt")
else:
  print("The file does not exist")