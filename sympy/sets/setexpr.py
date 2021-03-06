from sympy.core import Basic, Expr, Function, Add, Mul, Pow, Dummy, Integer
from sympy import latex, Min, Max, Set, sympify, Lambda, symbols
from sympy.sets import (imageset, Interval, FiniteSet, Union, ImageSet,
        ProductSet)
from sympy.core.decorators import call_highest_priority, _sympifyit
from sympy.utilities.iterables import sift
from sympy.multipledispatch import dispatch, Dispatcher


d = Dummy('d')


class SetExpr(Expr):
    """An expression that can take on values of a set

    >>> from sympy import Interval, FiniteSet
    >>> from sympy.sets.setexpr import SetExpr

    >>> a = SetExpr(Interval(0, 5))
    >>> b = SetExpr(FiniteSet(1, 10))
    >>> (a + b).set
    Union(Interval(1, 6), Interval(10, 15))
    >>> (2*a + b).set
    Interval(1, 20)
    """
    _op_priority = 11.0

    def __new__(cls, setarg):
        return Expr.__new__(cls, setarg)

    set = property(lambda self: self.args[0])

    def _latex(self, printer):
        return r"SetExpr\left({0}\right)".format(printer._print(self.set))

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__radd__')
    def __add__(self, other):
        return _setexpr_apply_operation(set_add, self, other)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__add__')
    def __radd__(self, other):
        return _setexpr_apply_operation(set_add, other, self)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__rmul__')
    def __mul__(self, other):
        return _setexpr_apply_operation(set_mul, self, other)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__mul__')
    def __rmul__(self, other):
        return _setexpr_apply_operation(set_mul, other, self)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__rsub__')
    def __sub__(self, other):
        return _setexpr_apply_operation(set_sub, self, other)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__sub__')
    def __rsub__(self, other):
        return _setexpr_apply_operation(set_sub, other, self)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__rpow__')
    def __pow__(self, other):
        return _setexpr_apply_operation(set_pow, self, other)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__pow__')
    def __rpow__(self, other):
        return _setexpr_apply_operation(set_pow, other, self)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__rdiv__')
    def __div__(self, other):
        return _setexpr_apply_operation(set_div, self, other)

    @_sympifyit('other', NotImplemented)
    @call_highest_priority('__div__')
    def __rdiv__(self, other):
        return _setexpr_apply_operation(set_div, other, self)

    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    def _eval_func(self, func):
        # TODO: this could be implemented straight into `imageset`:
        res = set_function(func, self.set)
        if res is None:
            return SetExpr(ImageSet(func, self.set))
        return SetExpr(res)


def _setexpr_apply_operation(op, x, y):
    if isinstance(x, SetExpr):
        x = x.set
    if isinstance(y, SetExpr):
        y = y.set
    out = op(x, y)
    return SetExpr(out)


def _handle_finite_sets(op, x, y, commutative):
    # Handle finite sets:
    fs_args, other = sift([x, y], lambda x: isinstance(x, FiniteSet), binary=True)
    if len(fs_args) == 2:
        return FiniteSet(*[op(i, j) for i in fs_args[0] for j in fs_args[1]])
    elif len(fs_args) == 1:
        sets = [_apply_operation(op, other[0], i, commutative) for i in fs_args[0]]
        return Union(*sets)
    else:
        return None

def _apply_operation(op, x, y, commutative):
    out = _handle_finite_sets(op, x, y, commutative)
    if out is None:
        out = op(x, y)

    if out is None and commutative:
        out = op(y, x)
    if out is None:
        _x, _y = symbols("x y")
        if isinstance(x, Set) and not isinstance(y, Set):
            out = ImageSet(Lambda(d, op(d, y)), x).doit()
        elif not isinstance(x, Set) and isinstance(y, Set):
            out = ImageSet(Lambda(d, op(x, d)), y).doit()
        else:
            out = ImageSet(Lambda((_x, _y), op(_x, _y)), x, y)
    return out

def set_add(x, y):
    from sympy.sets.handlers.add import _set_add
    return _apply_operation(_set_add, x, y, commutative=True)

def set_sub(x, y):
    from sympy.sets.handlers.add import _set_sub
    return _apply_operation(_set_sub, x, y, commutative=False)

def set_mul(x, y):
    from sympy.sets.handlers.mul import _set_mul
    return _apply_operation(_set_mul, x, y, commutative=True)

def set_div(x, y):
    from sympy.sets.handlers.mul import _set_div
    return _apply_operation(_set_div, x, y, commutative=False)

def set_pow(x, y):
    from sympy.sets.handlers.power import _set_pow
    return _apply_operation(_set_pow, x, y, commutative=False)

def set_function(f, x):
    from sympy.sets.handlers.functions import _set_function
    return _set_function(f, x)
