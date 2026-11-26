"""Small, budgeted Python expression interpreter for generated pure functions.

This interprets an allowlisted AST; generated code is never passed to exec/eval.
No imports, objects, file/network access, recursion, or input mutation exist here.
"""
import ast
import copy
import json
import math
import operator

class ReturnValue(Exception):
    pass

class PureFunction:

    def __init__(self, source, name):
        if not isinstance(source, str) or not 1 <= len(source) <= 12000:
            raise ValueError('Use 1–12,000 characters of Python')
        tree = ast.parse(source)
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise ValueError('Supply exactly one pure function')
        self.fn = tree.body[0]
        args = self.fn.args
        if self.fn.name != name or self.fn.decorator_list or self.fn.returns or (len(args.args) != 1) or args.posonlyargs or args.kwonlyargs or args.defaults or args.vararg or args.kwarg or args.args[0].annotation:
            raise ValueError('Expected def ' + name + '(data): with one plain argument')
        self.source = source
        allowed = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.Assign, ast.If, ast.For, ast.Expr, ast.Pass, ast.Name, ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.Subscript, ast.Load, ast.Store, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp, ast.Call, ast.Attribute, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn)
        nodes = list(ast.walk(tree))
        if len(nodes) > 600:
            raise ValueError('Function exceeds 600 syntax nodes')
        for node in nodes:
            if not isinstance(node, allowed):
                raise ValueError('Unsupported Python construct: ' + type(node).__name__)
            if isinstance(node, ast.Name) and node.id.startswith('_'):
                raise ValueError('Private names are unavailable')
            if isinstance(node, ast.Attribute) and node.attr != 'get':
                raise ValueError('Only dictionary.get is supported')
            if isinstance(node, ast.Assign) and (len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name)):
                raise ValueError('Assign local variables only; input data is immutable')
            if isinstance(node, ast.For) and (not isinstance(node.target, ast.Name) or node.orelse):
                raise ValueError('Use a simple bounded for loop')
            if isinstance(node, ast.Dict) and any((k is None for k in node.keys)):
                raise ValueError('Dictionary expansion is unavailable')
            if isinstance(node, ast.Constant):
                self.check(node.value)
            if isinstance(node, ast.Call):
                if node.keywords or (isinstance(node.func, ast.Name) and node.func.id not in self.builtins):
                    raise ValueError('Use only the documented pure functions')
                if not isinstance(node.func, (ast.Name, ast.Attribute)):
                    raise ValueError('Indirect calls are unavailable')
    builtins = {'len': len, 'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round, 'int': int, 'float': float, 'bool': bool, 'str': str}
    binary = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
    comparisons = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge, ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}

    @staticmethod
    def check(value):
        if type(value) is int and value.bit_length() > 256:
            raise ValueError('Integer exceeds 256 bits')
        if type(value) is float and (not math.isfinite(value)):
            raise ValueError('Non-finite number')
        if isinstance(value, (str, list, tuple, dict)) and len(value) > 8192:
            raise ValueError('Value exceeds size budget')
        if len(json.dumps(value, allow_nan=False)) > 64000:
            raise ValueError('Value exceeds 64 KB budget')
        return value

    def run(self, data):
        env = {self.fn.args.args[0].arg: copy.deepcopy(self.check(data))}
        budget = [4096]

        def expr(node):
            budget[0] -= 1
            if budget[0] < 0:
                raise ValueError('Function exceeded operation budget')
            if isinstance(node, ast.Constant):
                value = node.value
            elif isinstance(node, ast.Name):
                value = env[node.id]
            elif isinstance(node, (ast.List, ast.Tuple)):
                value = [expr(x) for x in node.elts]
            elif isinstance(node, ast.Dict):
                value = {expr(k): expr(v) for k, v in zip(node.keys, node.values)}
            elif isinstance(node, ast.Subscript):
                value = expr(node.value)[expr(node.slice)]
            elif isinstance(node, ast.IfExp):
                value = expr(node.body if expr(node.test) else node.orelse)
            elif isinstance(node, ast.BoolOp):
                value = expr(node.values[0])
                for item in node.values[1:]:
                    if isinstance(node.op, ast.And) and (not value):
                        break
                    if isinstance(node.op, ast.Or) and value:
                        break
                    value = expr(item)
            elif isinstance(node, ast.UnaryOp):
                value = expr(node.operand)
                value = not value if isinstance(node.op, ast.Not) else -value if isinstance(node.op, ast.USub) else +value
            elif isinstance(node, ast.BinOp):
                left, right = (expr(node.left), expr(node.right))
                if isinstance(node.op, ast.Mult):
                    for sequence, count in ((left, right), (right, left)):
                        if isinstance(sequence, (list, str)) and (type(count) is not int or len(sequence) * max(0, count) > 8192):
                            raise ValueError('Sequence multiplication exceeds budget')
                if isinstance(node.op, ast.Mod) and isinstance(left, str):
                    raise ValueError('String formatting is unavailable')
                value = self.binary[type(node.op)](left, right)
            elif isinstance(node, ast.Compare):
                left = expr(node.left)
                value = True
                for op, other in zip(node.ops, node.comparators):
                    right = expr(other)
                    if not self.comparisons[type(op)](left, right):
                        value = False
                        break
                    left = right
            elif isinstance(node, ast.Call):
                args = [expr(a) for a in node.args]
                if isinstance(node.func, ast.Name):
                    value = self.builtins[node.func.id](*args)
                else:
                    obj = expr(node.func.value)
                    if type(obj) is not dict:
                        raise ValueError('get() requires a dictionary')
                    value = obj.get(*args)
            else:
                raise ValueError('Unsupported expression: ' + type(node).__name__)
            return self.check(value)

        def block(nodes):
            for node in nodes:
                budget[0] -= 1
                if budget[0] < 0:
                    raise ValueError('Function exceeded operation budget')
                if isinstance(node, ast.Return):
                    raise ReturnValue(expr(node.value) if node.value else None)
                if isinstance(node, ast.Assign):
                    env[node.targets[0].id] = expr(node.value)
                elif isinstance(node, ast.If):
                    block(node.body if expr(node.test) else node.orelse)
                elif isinstance(node, ast.For):
                    items = expr(node.iter)
                    if not isinstance(items, (list, dict, str)) or len(items) > 128:
                        raise ValueError('Loop is limited to 128 items')
                    for item in items:
                        env[node.target.id] = item
                        block(node.body)
                elif isinstance(node, ast.Expr):
                    expr(node.value)
                elif isinstance(node, ast.Pass):
                    pass
        try:
            block(self.fn.body)
        except ReturnValue as result:
            return self.check(result.args[0])
        raise ValueError('The function must return a result')
