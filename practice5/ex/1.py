import re

# 1. 
def match_a_followed_by_bs(s):
    pattern = r'^ab*$'
    return bool(re.fullmatch(pattern, s))

# 2.
def match_a_followed_by_two_to_three_bs(s):
    pattern = r'^ab{2,3}$'
    return bool(re.fullmatch(pattern, s))

# 3. 
def find_lowercase_underscore(s):
    pattern = r'\b[a-z]+_[a-z]+\b'
    return re.findall(pattern, s)

# 4. 
def find_upper_followed_by_lower(s):
    pattern = r'\b[A-Z][a-z]+\b'
    return re.findall(pattern, s)

# 5. 
def match_a_anything_b(s):
    pattern = r'^a.*b$'
    return bool(re.fullmatch(pattern, s))

# 6. 
def replace_space_comma_dot(s):
    pattern = r'[ ,.]'
    return re.sub(pattern, ':', s)

# 7. 
def snake_to_camel(s):
    components = s.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

# 8.
def split_at_uppercase(s):
    return re.findall(r'[A-Z][^A-Z]*', s)

# 9. 
def insert_spaces_before_capitals(s):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s)

# 10.
def camel_to_snake(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

if __name__ == "__main__":
    print(match_a_followed_by_bs("abbb"))          
    print(match_a_followed_by_two_to_three_bs("abb"))  
    print(find_lowercase_underscore("hello_world test_text"))  
    print(find_upper_followed_by_lower("Hello World Python"))  
    print(match_a_anything_b("acb"))                
    print(replace_space_comma_dot("Hello, world. How are you?"))  
    print(snake_to_camel("hello_world_example"))    
    print(split_at_uppercase("HelloWorldPython"))   
    print(insert_spaces_before_capitals("HelloWorldPython"))  
    print(camel_to_snake("helloWorldExample"))       