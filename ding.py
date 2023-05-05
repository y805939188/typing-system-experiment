class A:
  __id = None
  @classmethod
  def __create_id__(self):
    self.__id = id(self)
    return self.__id
  
  @classmethod
  def __get_id__(self):
    if self.__id is None:
      return self.__create_id__()
    return self.__id
  
print(11111, A.__get_id__())
print(22222, A.__get_id__())
print(33333, A.__get_id__())
print(44444, A.__get_id__())
