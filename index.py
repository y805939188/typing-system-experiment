from dp.launching.typing import BaseModel, Int, String
from test import If, Exists, NotExists, Equal

class A(BaseModel):
  a: Int
  
# 如果有 A.a 就有 B  
@If(A, ("a"), Exists)
class B(BaseModel):
  b: Int
  
res = B.schema()
print(111, res)

# 如果有 B 就有 C
@If(B, Exists)
class C(BaseModel):
  c: String

# 如果没有 C 就有 D
@If(C, NotExists)
class D(BaseModel):
  d1: String
  d2: Int

res = D.schema()
print(1111, res)

@If(D, ("d1", "d2"), Equal, ("123", 456))
class E(BaseModel):
  e: String
  
# res2 = E.schema()
# print(2222, res2)

class Model(A, B, C, D, E, BaseModel):
  ...

# class E(If, A, BaseModel):
#   e: String
  
# res = E.schema()
# print(1111, res)
