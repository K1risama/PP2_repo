import os

os.makedirs("project/data/images", exist_ok=True)

for item in os.listdir("."):
    if os.path.isfile(item):
        print("File:", item)
    else:
        print("Folder:", item)