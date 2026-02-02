import re

def roman_to_int(roman):
    """Converts a Roman numeral string to an integer for sorting."""
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    total = 0
    prev_value = 0
    for char in reversed(roman.upper()):
        curr_value = values.get(char, 0)
        if curr_value >= prev_value:
            total += curr_value
        else:
            total -= curr_value
        prev_value = curr_value
    return total

def canto_sort_key(filename):
    """
    Creates a sorting key by splitting the filename into parts:
    1. Location (Inferno, Purgatorio, Paradiso)
    2. The Roman numeral converted to an integer
    3. The rest of the filename (e.g., speed)
    """
    # Pattern to find the Roman numeral part (e.g., 'XXXIII')
    match = re.search(r'_Canto_([IVXLCDM]+)', filename)
    if match:
        roman_str = match.group(1)
        # Extract the location (the part before the first '_*')
        location = filename.split('_*')[0]
        return (location, roman_to_int(roman_str), filename)
    return (filename,)

# Load your 'cants' file content
with open('cants', 'r') as f:
    filenames = [line.strip() for line in f if line.strip()]

# Sort using the custom key
sorted_cants = sorted(filenames, key=canto_sort_key)

# Display the first few results
for name in sorted_cants:
    print(name)

