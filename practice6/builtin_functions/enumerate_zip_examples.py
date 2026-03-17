names = ["Alice", "Bob", "Charlie"]

for i, name in enumerate(names):
    print(i, name)
    
names = ["Alice", "Bob"]
scores = [90, 85]

for name, score in zip(names, scores):
    print(name, score)