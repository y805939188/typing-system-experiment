import random
import string
from dp.launching.typing import BaseModel, Int, String, Dict
from dp.launching.typing.basic import get_internal_key
from typing import Any, Type
import dict_deep

class Statement:
    ...


class BasicRelationalOperator:
    
    @classmethod
    def __get_operator_name__(cls):
        return cls.__name__


class BasicLogicalOperator:
    ...


class BasicFunction:
    ...

# 变量
# 所有的变量都是一个 BaseModel 的子类

# 流程控制 - 条件运算符


class _Basic_internal_ref_cls:
    @classmethod
    def get_current(cls):
        return cls.current


def getStatement(args: tuple) -> Statement:
    for arg in args:
        if isinstance(arg, type) and issubclass(arg, Statement):
            return arg


def getBasicRelationalOperator(args: tuple) -> BasicRelationalOperator:
    for arg in args:
        if isinstance(arg, type) and issubclass(arg, BasicRelationalOperator):
            return arg


def getBasicLogicalOperator(args: tuple) -> BasicLogicalOperator:
    for arg in args:
        if isinstance(arg, type) and issubclass(arg, BasicLogicalOperator):
            return arg


def is_internal_cls(target: Any) -> bool:
    if not isinstance(target, type):
        return False
    if not issubclass(target, BasicLogicalOperator) and \
            not issubclass(target, BasicRelationalOperator) and \
            not issubclass(target, BasicFunction) and \
            not issubclass(target, Statement) and \
            not issubclass(target, BaseModel):
        return False
    return True


def getOthers(args: tuple) -> tuple:
    res = []
    for arg in args:
        if not is_internal_cls(arg):
            res.append(arg)
    return tuple(res)


def getCurrent(args: tuple) -> BaseModel:
    for arg in args:
        if isinstance(arg, type) and issubclass(arg, _Basic_internal_ref_cls):
            return arg.get_current()


def getRef(args: BaseModel) -> BaseModel:
    for arg in args:
        if isinstance(arg, type) and issubclass(arg, BaseModel):
            return arg


def getRefChain(ref):
    if not ref or not hasattr(ref, "origin_schema"):
        return None
    if not isinstance(ref, type) or not issubclass(ref, _Basic_internal_ref_cls):
        return None
    sch = ref.origin_schema()
    parent = dict_deep.deep_get(
        sch, f'properties.{get_internal_key()}.params')
    return {
        "schema": sch,
        "parent": parent,
    }


class If(Statement):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __call__(self, cls) -> Any:
        args = self.args
        others = getOthers(args)
        operator = getBasicRelationalOperator(args)
        left = getCurrent(args)
        ref = getRef(args)

        internal_key = get_internal_key()

        refChain = getRefChain(ref)

        class _If(Statement):
            @classmethod
            def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
                field_schema.update(
                    scope="internal",
                    statements="control",
                    value="if",
                    params={
                        "ref": refChain,
                        "left": (left or ref).__get_id__(),
                        "operator": operator.__get_operator_name__(),
                        "others": others
                    },
                )

            @classmethod
            def __get_validators__(cls) -> Any:
                yield cls.validate

            @classmethod
            def validate(cls, value: Any) -> "_If":
                return _If("if")

        class _stand(_Basic_internal_ref_cls, cls):
            __annotations__ = {internal_key: _If}
            
            @classmethod
            def get_cls(_):
                return cls

            @classmethod
            def get_cls_name(_):
                return cls.__name__
        
        _stand.__name__ = f'_stand_{cls.__name__}'
        
        _stand.current = cls
        _stand.__get_fields__()
        return _stand

# class Then(Statement): ...
# class Else(Statement): ...
# class Elif(Statement): ...

# 流程控制 - 循环运算符


class For(Statement):
    ...


class While(Statement):
    ...


class Break(Statement):
    ...


class Continue(Statement):
    ...


# 关系运算符
class Equal(BasicRelationalOperator):
    ...


class NotEqual(BasicRelationalOperator):
    ...


class Exists(BasicRelationalOperator):
    ...


class NotExists(BasicRelationalOperator):
    ...


class GreaterThan(BasicRelationalOperator):
    ...


class LessThan(BasicRelationalOperator):
    ...


class GreaterThanOrEqual(BasicRelationalOperator):
    ...


class LessThanOrEqual(BasicRelationalOperator):
    ...

# 逻辑运算符


class And(BasicLogicalOperator):
    ...


class Or(BasicLogicalOperator):
    ...


class Not(BasicLogicalOperator):
    ...

# 函数


class Function(BasicFunction):
    ...
# class Return(Any): ...
