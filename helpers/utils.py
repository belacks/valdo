
import re

def increment_string(s: str, steps: int = 1) -> str:
    """
    Increments the last numeric sequence in a string by 'steps'.
    Preserves zero padding.
    
    Example:
    'BTPNINFJKT/0124/4.0055 NB' + 1 -> 'BTPNINFJKT/0124/4.0056 NB'
    'SN-100' + 2 -> 'SN-102'
    'NoNumber' -> 'NoNumber'
    """
    if not s:
        return s
        
    # Find all numeric sequences
    matches = list(re.finditer(r'\d+', s))
    if not matches:
        return s
        
    # Get the last match (smartest guess for ID increment)
    last_match = matches[-1]
    start, end = last_match.span()
    
    prefix = s[:start]
    number_str = s[start:end]
    suffix = s[end:]
    
    # Calculate new number with preserved padding
    try:
        current_val = int(number_str)
        new_val = current_val + steps
        # Keep same length padding if original had it (e.g. 05 -> 06, not 6)
        new_number_str = str(new_val).zfill(len(number_str))
        
        return f"{prefix}{new_number_str}{suffix}"
    except ValueError:
        return s
