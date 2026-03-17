with open("file.txt", "a") as f:
  f.write("Now the file has more content!")
  
with open("file.txt") as f:
  print(f.read())
