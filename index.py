from dp.launching.typing import BaseModel, Int, String, Field
from test import If, Exists, NotExists, Equal
# from dp.launching.service.ui.streamlit_ui import 
from streamlit_pydantic import pydantic_form
# stand
class A(BaseModel):
  a: Int
# A.schema
# 如果有 A.a 就有 B  
@If(A, ("a"), Exists)
class B(BaseModel):
  b: Int
  
# res = B.schema()
# print(111, res)

# 如果有 B 就有 C
@If(B, Exists)
class C(BaseModel):
  c: String

# 如果没有 C 就有 D
@If(C, NotExists)
class D(BaseModel):
  d1: String
  d2: Int

# res = D.schema()
# print(1111, res)

@If(D, ("d1", "d2"), Equal, ("123", 456))
class E(BaseModel):
  e: String
  eee: Int = Field(ding_test=89898989)
  
# res2 = E.schema()
# print(2222, res2)

class Model(A, B, C, D, E, BaseModel):
  ...
  
  
# alternate
  
res = Model.schema()
# print(12134, res)

import json
with open("./ding-test.json", "w") as f:
  json.dump(res, f, indent=2, ensure_ascii=False)
  # res = json.dumps(res)
  # print(res)
  # f.write(json.dumps(json.loads(res), indent=4, ensure_ascii=False))
  
# res5 = E.schema()
# print(788878, res5)

# res6 = E.__get_fields__()
# print(123123123, res6)

# res7 = E.schema()
# print(67890, res7)

# if __name__ == "__main__":
#   form = pydantic_form("test", Model)
#   print(1111, form)

# class E(If, A, BaseModel):
#   e: String
  
# res = E.schema()
# print(1111, res)
