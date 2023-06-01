a = 'This is "string"'
b = 'This is \'string\''
# c = "This is "string""
d = "Thid is \"string\""
e = "This is 'string'"
f = 'this'
'this " abc" '
"this 'abc' " 

print(a)
print(b)
print(d)
print(e)

'''
W744는 string이 single quote로 둘러싸인 경우 오류를 출력함.
ex. 'This is my "apple" and...' -> "This is my "apple" and..."
해당 string token 내부에 위처럼 "~"이 존재하는 경우 오류 발생 so, \"로 수정
만약 'This is my \'apple\' and...'인 경우 "This is my \"apple\" and..."로 수정(내부는 변화 X)
'''