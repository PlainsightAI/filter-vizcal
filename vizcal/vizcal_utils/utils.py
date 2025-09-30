import numpy as np

# Helper function to convert non-serializable types
def convert_dict_to_serializable(d):
    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively handle nested dictionaries
            d[key] = convert_dict_to_serializable(value)
        elif isinstance(value, np.uint8):
            # Convert uint8 to int
            d[key] = int(value)
        elif isinstance(value, np.generic):
            # Convert other numpy types (e.g., int32, float64) to native Python types
            d[key] = value.item()
    return d
