# Ported engine definitions. Original launchers and UI entry points are excluded.
from typing import List

class BalancedTernaryProcessor:
    """
    Executes core matrix math using Base-3 Balanced logic parameters (-1, 0, 1).
    Maps high-level moral alignment definitions onto operational calculations.
    """

    def __init__(self):
        self.states = {-1: 'Disvirtue/Friction', 0: 'Zero-Point Potential', 1: 'Virtue/Alignment'}

    @staticmethod
    def encode_integer_balanced(value: int) -> str:
        """Encode an integer in balanced ternary using '-', '0', and '+'."""
        if not isinstance(value, int):
            raise TypeError('Balanced ternary input must be an integer.')
        if value == 0:
            return '0'
        digits = []
        while value:
            value, remainder = divmod(value, 3)
            if remainder == 2:
                digits.append('-')
                value += 1
            else:
                digits.append('+' if remainder == 1 else '0')
        return ''.join(reversed(digits))

    @classmethod
    def encode_bytes_balanced(cls, data: bytes) -> List[str]:
        """Encode each byte as a separate balanced-ternary integer."""
        return [cls.encode_integer_balanced(byte) for byte in data]

    def ternary_dot_product(self, vector_a: List[int], vector_b: List[int]) -> int:
        """
        Calculates a dot product constrained directly to balanced ternary limits.
        """
        if len(vector_a) != len(vector_b):
            raise ValueError('Vector dimensions must match exactly.')
        raw_sum = 0
        for val_a, val_b in zip(vector_a, vector_b):
            if val_a not in self.states or val_b not in self.states:
                raise ValueError('Encountered an invalid state value outside ternary bounds (-1, 0, 1).')
            raw_sum += val_a * val_b
        if raw_sum > 0:
            return 1
        elif raw_sum < 0:
            return -1
        return 0

    def compute_optimization_grid(self, grid: List[List[int]]) -> List[int]:
        """
        Collapses a multi-dimensional array down into a linear execution vector.
        """
        output_vector = []
        for row in grid:
            running_val = 1
            for element in row:
                running_val *= element
            if running_val > 0:
                output_vector.append(1)
            elif running_val < 0:
                output_vector.append(-1)
            else:
                output_vector.append(0)
        return output_vector
