import random
from typing import Tuple
from config.settings import MIN_NUMBER, MAX_NUMBER, OPERATORS


class ExpressionGenerator:    
    @staticmethod
    def generate() -> Tuple[str, int]:
        num1 = random.randint(MIN_NUMBER, MAX_NUMBER)
        num2 = random.randint(MIN_NUMBER, MAX_NUMBER)
        operator = random.choice(OPERATORS)
        
        # Handle division and modulus
        if operator == '/':
            num2 = random.randint(1, 10000) if num2 == 0 else num2
            num1 = num2 * random.randint(MIN_NUMBER // 100, MAX_NUMBER // 100)
        elif operator == '%':
            # Ensure num2 is positive and non-zero for modulus
            num2 = random.randint(1, 10000) if num2 <= 0 else num2
            # Optional: Ensure num1 is positive or reasonable
            num1 = random.randint(0, num2)  # num1 < num2 for meaningful modulus
        
        expr = f"{num1} {operator} {num2}"
        answer = eval(expr)  # Safe in this context as inputs are controlled
        return expr, int(answer)
