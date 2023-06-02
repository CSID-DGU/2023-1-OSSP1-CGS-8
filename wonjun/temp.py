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
    
# class Cap_Word_Case2: 
#     def Cap_Word_Case2(): 
#         print("hello")
#         return None
    
# print(Cap_Word_Case2.Cap_Word_Case2())

# x = 10
# y = 20
# """

# # 소스 코드를 AST로 변환
# ast_tree = ast.parse(source_code)

# # 식별자와 프로퍼티 정보를 저장할 딕셔너리
# identifiers = {}

# # AST 트리를 순회하며 식별자와 프로퍼티 정보를 추출
# for node in ast.walk(ast_tree):
#     if isinstance(node, ast.Name):
#         identifier = node.id
#         if identifier not in identifiers:
#             properties = {
#                 'class': isinstance(node.ctx, ast.Load),
#                 'function': isinstance(node.ctx, ast.Load),
#                 'variable': isinstance(node.ctx, ast.Load)
#             }
#             identifiers[identifier] = properties

# # 결과 출력
# print("Identifiers with Properties:")
# for identifier, properties in identifiers.items():
#     print(f"Identifier: {identifier}")
#     print("Properties:")
#     print(f"\tClass: {properties['class']}")
#     print(f"\tFunction: {properties['function']}")
#     print(f"\tVariable: {properties['variable']}")
#     print()
    
# # Identifiers with Properties:
# # Identifier: ParentClass
# # Properties:
# #     Class: True
# #     Function: False
# #     Variable: False

# # Identifier: parent_method
# # Properties:
# #     Class: False
# #     Function: True
# #     Variable: False

# # Identifier: ChildClass
# # Properties:
# #     Class: True
# #     Function: False
# #     Variable: False

# # Identifier: child_method
# # Properties:
# #     Class: False
# #     Function: True
# #     Variable: False

# # Identifier: global_function
# # Properties:
# #     Class: False
# #     Function: True
# #     Variable: False

# # Identifier: global_variable
# # Properties:
# #     Class: False
# #     Function: False
# #     Variable: True

# # Identifier: outer_function
# # Properties:
# #     Class: False
# #     Function: True
# #     Variable: False

# # Identifier: inner_function
# # Properties:
# #     Class: False
# #     Function: True
# #     Variable: False

# # Identifier: child_instance
# # Properties:
# #     Class: False