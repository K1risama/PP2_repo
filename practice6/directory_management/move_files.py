import shutil
import os

os.makedirs(r"C:\Users\arkor\Documents\PP2_repo\practice6\directory_management\backup", exist_ok=True)
os.makedirs(r"C:\Users\arkor\Documents\PP2_repo\practice6\directory_management\archhive", exist_ok=True)

shutil.copy(r"C:\Users\arkor\Documents\PP2_repo\practice6\directory_management\file.txt", r"C:\Users\arkor\Documents\PP2_repo\practice6\directory_management\backup\file.txt")
shutil.move(r"C:\Users\arkor\Documents\PP2_repo\practice6\directory_management\file.txt", r"C:\Users\arkor\Documents\PP2_repo\practice6\directory_management\archhive\file.txt")