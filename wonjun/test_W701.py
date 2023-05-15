import string
import re
import keyword

def is_snake_case(word):
    if not word:
        return False
    
    if not word[0].islower():
        return False
    
    if not all(char.islower() or char == '_' for char in word):
        return False
    
    if '__' in word:
        return False
    
    if word in keyword.kwlist:
        return False
    
    return True
    
def is_camel_case(word):
    if not word:
        return False
    if ' ' in word:
        return False
    if '_' in word:
        return False
    if word[0].isupper():
        return False
    if any(w[0].isupper() for w in word.split()):
        return False
    return True

def to_capitalized_words(word):
    """return capitalized words
    
    class naming convention
    """
    if is_snake_case(word): return string.capwords(word, sep='_').replace('_', '') 
    return word[0].upper() + word[1:]

def snake_to_capwords(snake_case):
    """return capwords"""
    if is_snake_case(snake_case): return snake_case
    capitalized_words = string.capwords(snake_case, sep='_').replace('_', '')
    return capitalized_words
    
def camel_to_snake(camel_case):
    """return snake case
    
    method naming convention
    """
    if not is_camel_case(camel_case): return camel_case.lower()
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
    return snake_case

# CamelCase
# Camel case
# Camel_Case
# Camel_case
# camelCase
# camel_case
# camelcase
# 