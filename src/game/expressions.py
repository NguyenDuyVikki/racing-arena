import random
from typing import Tuple
from config.settings import MIN_NUMBER, MAX_NUMBER, OPERATORS


class ExpressionGenerator:    
    @staticmethod
    def generate() -> Tuple[str, int]:
        """Generate a random math expression and its answer"""
        num1 = random.randint(MIN_NUMBER, MAX_NUMBER)
        num2 = random.randint(MIN_NUMBER, MAX_NUMBER)
        operator = random.choice(OPERATORS)
        
        # Handle division to ensure integer result
        if operator == '/':
            num2 = random.randint(1, 10000) if num2 == 0 else num2
            num1 = num2 * random.randint(MIN_NUMBER // 100, MAX_NUMBER // 100)
        
        expr = f"{num1} {operator} {num2}"
        answer = eval(expr)  # Safe in this context as inputs are controlled
        return expr, int(answer)
