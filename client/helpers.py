def check_empty_lines(file_path: str):
    """
    Checks for empty lines in the given text file.
    Prints the line numbers of empty lines and raises an error if any are found.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    empty_line_numbers = [i + 1 for i, line in enumerate(lines) if line.strip() == '']

    if empty_line_numbers:
        print(f"Empty lines found in {file_path} at line(s):")
        for line_num in empty_line_numbers:
            print(f"Line {line_num}")
        return True
    else:
        #print(f"Hurray!, {file_path} has no empty lines.")
        return False
    
def extract_values(metric_dicts):
    values = []
    for metric_dict in metric_dicts:
        values.append([
            float(metric_dict.score),
            float(metric_dict.mean),
            float(metric_dict.ci),
            float(metric_dict.p_value) if metric_dict.p_value is not None else metric_dict.p_value
        ])
    return values

# Function to format values
def format_score(score, mean, ci, p_value):
    formatted = f"{score:.1f} ({mean:.1f} ± {ci:.1f})"
    if p_value is not None:
        formatted += f" (p = {p_value:.4f})"
        if p_value < 0.05:
            formatted += "*"
    return formatted

# Function to highlight the maximum in a column
def highlight_max(s):
    is_max = s == s.max()
    return ['font-weight: bold' if v else '' for v in is_max]

# Function to highlight the minimum in the TER column
def highlight_min(s):
    is_min = s == s.min()
    return ['font-weight: bold' if v else '' for v in is_min]
