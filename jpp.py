import re
import os
import math
import random
import ast
from sys import argv

class JPPInterpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.math_ops = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '%': lambda x, y: x % y,
            '^': lambda x, y: x ** y,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'ceil': math.ceil,
            'floor': math.floor,
            'randint': random.randint,
            'random': random.random,
            'choice': lambda x: random.choice(x) if x else None,
            'input': lambda prompt=None: input(prompt)  # <-- تمت الإضافة هنا
        }
    
    def run(self, code):
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            self.execute(line)
    
    def execute(self, line):
        # Handle variable assignment
        match = re.match(r'var (\w+) = (.+)', line)
        if match:
            var_name, value = match.groups()
            self.variables[var_name] = self.evaluate(value)
            return
        
        # Handle print statements
        match = re.match(r'print (.+)', line)
        if match:
            value = match.group(1)
            result = self.evaluate(value)
            if result is not None:
                print(result)
            return
        
        # Handle if conditions
        match = re.match(r'if (.+) then (.+)', line)
        if match:
            condition, action = match.groups()
            cond_result = self.evaluate_condition(condition)
            if cond_result is not None and cond_result:
                self.execute(action)
            return
        
        # Handle direct calculations
        match = re.match(r'calc (.+)', line)
        if match:
            expression = match.group(1)
            result = self.evaluate(expression)
            if result is not None:
                print(result)
            return
        
        # Unknown command
        print(f"Error: Unknown command - '{line}'")
    
    def evaluate(self, expr):
        try:
            expr = expr.strip()
            
            # Handle input function
            if expr.startswith('input(') and expr.endswith(')'):
                prompt = expr[6:-1].strip()
                if prompt and (prompt[0] == prompt[-1] and prompt[0] in ['"', "'"]):
                    prompt = prompt[1:-1]
                elif prompt in self.variables:
                    prompt = str(self.variables[prompt])
                else:
                    prompt = None
                return input(prompt)
            
            # If it's a list (e.g., ["red", "green", "blue"])
            if expr.startswith('[') and expr.endswith(']'):
                try:
                    return ast.literal_eval(expr)
                except:
                    print(f"Error: Invalid list expression '{expr}'")
                    return None
            
            # Replace ^ with ** for exponentiation
            expr = expr.replace('^', '**')
            
            # If simple arithmetic expression
            if re.match(r'^[\d+\-*/().% ]+$', expr):
                return eval(expr, {'math': math, **self.variables})
            
            # If contains math functions
            if any(op in expr for op in self.math_ops):
                return self.evaluate_math_expression(expr)
            
            # If variable
            if expr in self.variables:
                return self.variables[expr]
            
            # If string
            if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                return expr[1:-1]
            
            # Unknown expression
            print(f"Error: Unknown expression '{expr}'")
            return None
            
        except Exception as e:
            print(f"Evaluation error: {e}")
            return None
    
    def evaluate_math_expression(self, expr):
        try:
            # Replace ^ with ** for exponentiation
            expr = expr.replace('^', '**')
            
            # Replace function names with proper calls
            for op, func in self.math_ops.items():
                if op in ['+', '-', '*', '/', '%']:
                    continue
                expr = expr.replace(f"{op}(", f"math.{op}(" if op in dir(math) else f"self.math_ops['{op}'](")
            
            # Evaluate the expression with access to variables and functions
            return eval(expr, {'math': math, 'self': self, 'random': random, **self.variables})
        except Exception as e:
            print(f"Math evaluation error: {e}")
            return None
    
    def evaluate_condition(self, cond):
        try:
            # Check mathematical conditions
            ops = {
                '==': lambda x, y: x == y,
                '!=': lambda x, y: x != y,
                '>': lambda x, y: x > y,
                '<': lambda x, y: x < y,
                '>=': lambda x, y: x >= y,
                '<=': lambda x, y: x <= y,
            }
            
            for op, func in ops.items():
                if op in cond:
                    left, right = cond.split(op)
                    left_val = self.evaluate(left.strip())
                    right_val = self.evaluate(right.strip())
                    
                    if left_val is None or right_val is None:
                        print("Error: Invalid operands in condition")
                        return None
                        
                    return func(left_val, right_val)
            
            result = self.evaluate(cond)
            return bool(result) if result is not None else None
        except Exception as e:
            print(f"Condition evaluation error: {e}")
            return None

def is_jpp_file(filename):
    """Check if file has .jpp extension"""
    return os.path.splitext(filename)[1].lower() == '.jpp'

if __name__ == '__main__':
    interpreter = JPPInterpreter()
    
    if len(argv) > 1:
        # Check file extension
        if not is_jpp_file(argv[1]):
            print("Error: Only .jpp files are supported!")
            print("Please provide a file with .jpp extension")
            exit(1)
            
        # Run from file
        try:
            with open(argv[1], 'r', encoding='utf-8') as f:
                code = f.read()
            interpreter.run(code)
        except FileNotFoundError:
            print(f"Error: File '{argv[1]}' not found!")
        except Exception as e:
            print(f"Runtime error: {e}")
    else:
        # Interactive mode
        print("JPP Language Interpreter - Type 'exit' to quit")
        print("Supported functions:", ', '.join(interpreter.math_ops.keys()))
        print("Example with input: var name = input(\"Enter your name: \"); print \"Hello, \" + name")
        while True:
            try:
                line = input("JPP> ")
                if line.strip() == 'exit':
                    break
                interpreter.execute(line)
            except Exception as e:
                print(f"Error: {e}")
