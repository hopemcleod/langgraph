from datetime import datetime, timezone
import functools
import os
import sys
import types
import yaml

def get_current_utc_datetime():
    now_utc = datetime.now(timezone.utc)
    current_time_utc = now_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
    return current_time_utc

# Ignore this - was going to call this in every file and automate adding a decorator to each function
# in that file (module) but it didn't work well. I'm not using it right in the module ...
def apply_decorator_to_all_functions(module, decorator):
    for name in dir(module):
        attr = getattr(module, name, None)
        if isinstance(attr, (types.FunctionType, types.MethodType)):
            setattr(module, name, decorator(attr))

def print_function_name(function_name):
    print(f"\nEntering function: {function_name}\n")

'''
This code defines a decorator function called log_function_call. A decorator is a special kind of function that can modify or 
enhance the behavior of other functions without changing their actual code. The purpose of this decorator is to add logging 
functionality to any function it's applied to.

The log_function_call function takes a single input: the function that it will be decorating (referred to as func in the code).
It doesn't produce any direct output, but it returns a new function (called wrapper) that will replace the original function when
the decorator is used.

Here's how it works: When you use this decorator on a function, it creates a new function (wrapper) that does three things:

It prints a message saying it's entering the original function.
It calls the original function and stores its result.
It prints a message saying it's exiting the original function.
Finally, it returns the result of the original function.
The wrapper function uses *args and **kwargs, which allow it to accept any number and type of arguments. 
This means the decorator can be used on functions with any number of parameters.

The @functools.wraps(func) line is a special decorator that helps preserve the original function's metadata
(like its name and docstring) in the new wrapper function.

When you use this decorator on a function, it will print log messages every time that function is called, showing when 
the function starts and ends its execution. This can be very useful for debugging or understanding the flow of your program,
especially when dealing with complex functions or multiple function calls.
Update: Added ability to print class name too.
'''
def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            print(f"Entering {class_name}.{func.__name__}")
        else:
            print(f"Entering {func.__name__}")
        
        result = func(*args, **kwargs)
        
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            print(f"Exiting {class_name}.{func.__name__}")
        else:
            print(f"Exiting {func.__name__}")
        
        return result
    return wrapper

'''
'''
def load_config(file_path):
    with open(file_path, 'r') as file:
        config =yaml.safe_load(file)

        for key, value in config.items():
            os.environ[key] = value

@log_function_call
def validate_json(data):
    pass
