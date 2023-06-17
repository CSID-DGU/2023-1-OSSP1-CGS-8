# import ast

# source_code = """
# class ParentClass:
#     def parent_method(self):
#         pass

# class ChildClass(ParentClass):
#     def child_method(self):
#         pass

# def global_function():
#     pass

# global_variable = 42

# def outer_function():
#     def inner_function():
#         child_instance = ChildClass()
#         child_instance.child_method()

#     parent_instance = ParentClass()
#     parent_instance.parent_method()
#     inner_function()
    
# x = 10
# y = 20
# """

# # 소스 코드를 AST로 변환
# ast_tree = ast.parse(source_code)

# # 클래스 이름, 클래스 내부 메소드 이름, 상속 관계에서 자식 클래스의 이름, 변수 이름, 전역 함수 이름,
# # 호출하는 함수 이름, 클래스를 참조해서 호출하는 함수 이름을 저장할 집합(set)
# class_names = set()
# method_names = set()
# child_classes = set()
# variable_names = set()
# global_function_names = set()
# calling_function_names = set()
# referring_class_function_names = set()

# # AST 트리를 순회하며 필요한 정보를 추출
# for node in ast_tree.body:
#     if isinstance(node, ast.ClassDef):
#         class_names.add(node.name)

#         for subnode in node.body:
#             if isinstance(subnode, ast.FunctionDef):
#                 method_names.add(subnode.name)

#             if isinstance(subnode, ast.Assign):
#                 if len(subnode.targets) == 1 and isinstance(subnode.targets[0], ast.Name):
#                     variable_names.add(subnode.targets[0].id)

#     if isinstance(node, ast.FunctionDef):
#         global_function_names.add(node.name)

#         for subnode in ast.walk(node):
#             if isinstance(subnode, ast.Name):
#                 if isinstance(subnode.ctx, ast.Load):
#                     calling_function_names.add(subnode.id)

#     if isinstance(node, ast.ClassDef):
#         if node.bases:
#             for base in node.bases:
#                 if isinstance(base, ast.Name):
#                     child_classes.add((node.name, base.id))

#         for subnode in ast.walk(node):
#             if isinstance(subnode, ast.Attribute):
#                 if isinstance(subnode.value, ast.Name):
#                     if subnode.value.id in class_names:
#                         referring_class_function_names.add(subnode.attr)

# # 결과 출력
# print("Class Names:", class_names)
# print("Method Names:", method_names)
# print("Child Classes:", child_classes)
# print("Variable Names:", variable_names)
# print("Global Function Names:", global_function_names)
# print("Calling Function Names:", calling_function_names)
# print("Referring Class Function Names:", referring_class_function_names)



# # 추가한 부분 - 김위성 - 식별자, 참조되는 식별자를 모두 저장
# # 수정 - 조원준
# def analyze_file(file_path):
#     with open(file_path, 'r') as file:
#         source_code = file.read()
    
#     tree = ast.parse(source_code)
#     identifier = dict()
#     referenced = dict()
#     # identifiers = set()
#     # referenecd = set()

#     for node in ast.walk(tree):
#         if isinstance(node, ast.ClassDef):
#             # 클래스 이름 추출
#             identifier[node.name] = "class"
#             if node.bases:
#                 for base in node.bases:
#                     # 자식 클래스의 이름 추출
#                     if isinstance(base, ast.Name):
#                         identifier[node.name] = "subclass"
#                 for subnode in node.body:
#                     # 내부 메소드 추출
#                     if isinstance():
#                         identifier[] = "method"
#         elif isinstance(node, ast.FunctionDef):
            
        
#     for node in ast.walk(tree):
#         if isinstance(node, ast.ClassDef):
#             # import하는 파일에서 상속하는 클래스
#             for base in node.bases:
#                 if isinstance(base, ast.Name):
#                     referenecd.add(base.id)
#             identifiers.add(node.name)
#         elif isinstance(node, ast.FunctionDef):
#             identifiers.add(node.name)
#         elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
#             identifiers.add(node.id)
#         elif isinstance(node, ast.arg):
#             identifiers.add(node.arg)
#         # import하는 파일에서 호출하는 함수
#         elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
#             referenecd.add(node.func.id)

#     return identifiers, referenecd