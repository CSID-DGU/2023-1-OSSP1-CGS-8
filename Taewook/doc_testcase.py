# case 1 space 0
'''안녕하세요'''


# case 2 tab
    '''안녕하세요
    '''

# case 3 whitespace
'''안녕하세요''' 

# case 4 첫번쨰 '''에 문자열에 이어서, 
'''single quote를 사용한 docstring documented comment
Hi
''' 

# case 3 첫번째 ''' 줄다음 문자열
    '''    
    주석 앞에 공백이 있는 docstring

   
    abcd
    '''  
 #case 4 두번째 문자열 이후 '''
    '''


    bc'''  
# case 5 두번쨰 마지막에 ''' 
'''
a
sdf
'''