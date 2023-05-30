import pyrestyle
from tabulate import tabulate

file_path = 'test.py'
checker = pyrestyle.Checker(file_path)

# 오류 코드와 발생 횟수 계산
error_counts = {}
for code in [checker.check_all()]:  # 오류 코드와 무시된 오류를 가져옴
    if code in error_counts:
        error_counts[code] += 1
    else:
        error_counts[code] = 1

# 오류 코드와 발생 횟수 데이터 준비
table_data = []
for code, count in error_counts.items():
    table_data.append([code, count])

# 총 오류 코드 수와 발생 횟수 합 계산
num_error_codes = len(error_counts)
total_count = sum(error_counts.values())
table_data.append(['Total', total_count])
table_data.append(['Number of Error Codes', num_error_codes])

# 표 출력
headers = ['Error Code', 'Count']
table = tabulate(table_data, headers=headers)
print(table)
