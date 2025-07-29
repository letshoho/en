import re
import os
import math
import random
import ast
import threading
from sys import argv
from datetime import datetime
import telebot
from telebot import types

class JPPInterpreter:
    def __init__(self):
        self.variables = {
            'bot_token': None,
            'chat_id': None,
            'bot_active': False
        }
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
            'now': lambda: str(datetime.now()),
            'input': self.input_wrapper
        }
        self.bot = None
        self.bot_thread = None
        self.message_handlers = {}
        self.command_handlers = {}
        self.callback_handlers = {}
        self.input_prompt = None

    def input_wrapper(self, prompt=""):
        """Wrapper function to handle input with optional prompt"""
        self.input_prompt = prompt
        return input(prompt if prompt else "")

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
        
        # Handle input statements
        match = re.match(r'input (\w+)(?:\s*,\s*(.+))?', line)
        if match:
            var_name, prompt = match.groups()
            prompt = self.evaluate(prompt) if prompt else ""
            self.variables[var_name] = input(prompt)
            return
        
        # Handle if conditions
        match = re.match(r'if (.+) then (.+)', line)
        if match:
            condition, action = match.groups()
            cond_result = self.evaluate_condition(condition)
            if cond_result is not None and cond_result:
                self.execute(action)
            return
        
        # Handle bot commands
        match = re.match(r'bot set token (.+)', line)
        if match:
            token = match.group(1).strip('"\'')
            self.variables['bot_token'] = token
            print("Bot token set")
            return
        
        match = re.match(r'bot start', line)
        if match:
            self.start_bot()
            return
        
        match = re.match(r'bot stop', line)
        if match:
            self.stop_bot()
            return
        
        match = re.match(r'bot send (.+) to (.+)', line)
        if match:
            message, recipient = match.groups()
            self.send_message(recipient, message)
            return
        
        match = re.match(r'bot on message (.+) do (.+)', line)
        if match:
            pattern, action = match.groups()
            self.add_message_handler(pattern, action)
            return
        
        match = re.match(r'bot on command (.+) do (.+)', line)
        if match:
            command, action = match.groups()
            self.add_command_handler(command, action)
            return
        
        match = re.match(r'bot on callback (.+) do (.+)', line)
        if match:
            callback_data, action = match.groups()
            self.add_callback_handler(callback_data, action)
            return
        
        match = re.match(r'bot reply keyboard (.+)', line)
        if match:
            buttons = self.evaluate(match.group(1))
            if isinstance(buttons, list):
                self.create_reply_keyboard(buttons)
            return
        
        match = re.match(r'bot inline keyboard (.+)', line)
        if match:
            buttons = self.evaluate(match.group(1))
            if isinstance(buttons, list):
                self.create_inline_keyboard(buttons)
            return
        
        # Handle direct calculations
        match = re.match(r'calc (.+)', line)
        if match:
            expression = match.group(1)
            result = self.evaluate(expression)
            if result is not None:
                print(result)
            return
        
        # Handle function definition
        match = re.match(r'function (\w+)\(([^)]*)\) = (.+)', line)
        if match:
            func_name, params, body = match.groups()
            self.functions[func_name] = (params.split(','), body)
            return
        
        # Unknown command
        print(f"Error: Unknown command - '{line}'")
    
    def evaluate(self, expr):
        try:
            expr = expr.strip()
            
            # If it's a list
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
            
            return eval(expr, {'math': math, 'self': self, 'random': random, **self.variables})
        except Exception as e:
            print(f"Math evaluation error: {e}")
            return None
    
    def evaluate_condition(self, cond):
        try:
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
    
    def start_bot(self):
        if self.variables['bot_token'] is None:
            print("Error: Bot token not set. Use 'bot set token YOUR_TOKEN'")
            return
        
        if self.bot is not None:
            print("Bot is already running")
            return
        
        self.bot = telebot.TeleBot(self.variables['bot_token'])
        self.variables['bot_active'] = True
        
        # Register handlers
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            self.variables['chat_id'] = message.chat.id
            for pattern, action in self.message_handlers.items():
                if re.search(pattern, message.text):
                    self.execute(action.replace('{message}', message.text))
                    break
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            for pattern, action in self.callback_handlers.items():
                if re.search(pattern, call.data):
                    self.execute(action.replace('{callback_data}', call.data))
                    break
        
        self.bot_thread = threading.Thread(target=self.bot.polling)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        print("Bot started successfully")
    
    def stop_bot(self):
        if self.bot is None:
            print("Bot is not running")
            return
        
        self.bot.stop_polling()
        self.bot = None
        self.bot_thread = None
        self.variables['bot_active'] = False
        print("Bot stopped")
    
    def send_message(self, recipient, message):
        if self.bot is None:
            print("Error: Bot is not running")
            return
        
        chat_id = self.evaluate(recipient)
        if chat_id is None:
            print("Error: Invalid chat ID")
            return
        
        message_text = str(self.evaluate(message))
        try:
            self.bot.send_message(chat_id, message_text)
            print(f"Message sent to {chat_id}")
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def add_message_handler(self, pattern, action):
        self.message_handlers[pattern] = action
        print(f"Added message handler for pattern: {pattern}")
    
    def add_command_handler(self, command, action):
        self.command_handlers[command] = action
        print(f"Added command handler for: /{command}")
        
        if self.bot is not None:
            @self.bot.message_handler(commands=[command])
            def handle_command(message):
                self.execute(action.replace('{message}', message.text))
    
    def add_callback_handler(self, callback_data, action):
        self.callback_handlers[callback_data] = action
        print(f"Added callback handler for: {callback_data}")
    
    def create_reply_keyboard(self, buttons):
        if self.bot is None:
            print("Error: Bot is not running")
            return
        
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        for button_row in buttons:
            if isinstance(button_row, list):
                row_buttons = [types.KeyboardButton(str(btn)) for btn in button_row]
                markup.add(*row_buttons)
            else:
                markup.add(types.KeyboardButton(str(button_row)))
        
        self.variables['last_keyboard'] = markup
        print("Reply keyboard created")
    
    def create_inline_keyboard(self, buttons):
        if self.bot is None:
            print("Error: Bot is not running")
            return
        
        markup = types.InlineKeyboardMarkup()
        for button_row in buttons:
            if isinstance(button_row, list):
                row_buttons = []
                for btn in button_row:
                    if isinstance(btn, dict) and 'text' in btn and 'data' in btn:
                        row_buttons.append(types.InlineKeyboardButton(
                            text=str(btn['text']),
                            callback_data=str(btn['data'])))
                    else:
                        row_buttons.append(types.InlineKeyboardButton(
                            text=str(btn),
                            callback_data=str(btn)))
                markup.add(*row_buttons)
            else:
                if isinstance(buttons, dict) and 'text' in buttons and 'data' in buttons:
                    markup.add(types.InlineKeyboardButton(
                        text=str(buttons['text']),
                        callback_data=str(buttons['data'])))
                else:
                    markup.add(types.InlineKeyboardButton(
                        text=str(buttons),
                        callback_data=str(buttons)))
        
        self.variables['last_inline_keyboard'] = markup
        print("Inline keyboard created")

def is_jpp_file(filename):
    return os.path.splitext(filename)[1].lower() == '.jpp'

if __name__ == '__main__':
    interpreter = JPPInterpreter()
    
    if len(argv) > 1:
        if not is_jpp_file(argv[1]):
            print("Error: Only .jpp files are supported!")
            print("Please provide a file with .jpp extension")
            exit(1)
            
        try:
            with open(argv[1], 'r', encoding='utf-8') as f:
                code = f.read()
            interpreter.run(code)
        except FileNotFoundError:
            print(f"Error: File '{argv[1]}' not found!")
        except Exception as e:
            print(f"Runtime error: {e}")
    else:
        print("JPP Language Interpreter with Input - Type 'exit' to quit")
        print("Supported commands:")
        print("  - var x = value")
        print("  - print expression")
        print("  - input variable_name, prompt_message")
        print("  - if condition then action")
        print("  - calc expression")
        print("  - function name(params) = body")
        print("Bot commands:")
        print("  - bot set token YOUR_TOKEN")
        print("  - bot start/stop")
        print("  - bot send message to chat_id")
        print("  - bot on message pattern do action")
        print("  - bot on command cmd do action")
        print("  - bot on callback data do action")
        print("  - bot reply keyboard [[btn1, btn2], [btn3]]")
        print("  - bot inline keyboard [[{text: 'Btn', data: 'data'}]]")
        
        while True:
            try:
                if interpreter.input_prompt:
                    line = input(interpreter.input_prompt)
                    interpreter.input_prompt = None
                else:
                    line = input("JPP> ")
                
                if line.strip() == 'exit':
                    if interpreter.variables['bot_active']:
                        interpreter.stop_bot()
                    break
                interpreter.execute(line)
            except KeyboardInterrupt:
                if interpreter.variables['bot_active']:
                    interpreter.stop_bot()
                break
            except Exception as e:
                print(f"Error: {e}")
