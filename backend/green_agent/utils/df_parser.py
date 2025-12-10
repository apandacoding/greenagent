"""Utility to parse DataFrame operations from Python code."""
import re
from typing import List, Dict, Any, Optional


def extract_df_operations(code: str) -> List[Dict[str, Any]]:
    """
    Extract DataFrame operations from Python code.
    
    Args:
        code: Python code string (typically from python_repl_ast tool input)
        
    Returns:
        List of dictionaries containing operation details
    """
    operations = []
    
    if not code or not isinstance(code, str):
        return operations
    
    # Common DataFrame operation patterns
    patterns = {
        'shape': r'\.shape\b',
        'columns': r'\.columns(?:\.tolist\(\))?',
        'info': r'\.info\(\)',
        'describe': r'\.describe\(\)',
        'head': r'\.head\([^)]*\)',
        'tail': r'\.tail\([^)]*\)',
        'copy': r'\.copy\([^)]*\)',
        'sort_values': r'\.sort_values\([^)]+\)',
        'sort_index': r'\.sort_index\([^)]*\)',
        'filter': r'\.filter\([^)]+\)',
        'loc': r'\.loc\[[^\]]+\]',
        'iloc': r'\.iloc\[[^\]]+\]',
        'query': r'\.query\([^)]+\)',
        'groupby': r'\.groupby\([^)]+\)',
        'agg': r'\.agg\([^)]+\)',
        'aggregate': r'\.aggregate\([^)]+\)',
        'sum': r'\.sum\([^)]*\)',
        'mean': r'\.mean\([^)]*\)',
        'max': r'\.max\([^)]*\)',
        'min': r'\.min\([^)]*\)',
        'count': r'\.count\([^)]*\)',
        'nunique': r'\.nunique\([^)]*\)',
        'unique': r'\.unique\([^)]*\)',
        'drop': r'\.drop\([^)]+\)',
        'dropna': r'\.dropna\([^)]*\)',
        'fillna': r'\.fillna\([^)]+\)',
        'rename': r'\.rename\([^)]+\)',
        'merge': r'\.merge\([^)]+\)',
        'join': r'\.join\([^)]+\)',
        'concat': r'(?:pd\.|pandas\.)?concat\([^)]+\)',
        'iterrows': r'\.iterrows\(\)',
        'itertuples': r'\.itertuples\([^)]*\)',
        'to_string': r'\.to_string\([^)]*\)',
        'to_dict': r'\.to_dict\([^)]*\)',
        'to_json': r'\.to_json\([^)]*\)',
        'isna': r'\.isna\(\)',
        'isnull': r'\.isnull\(\)',
        'notna': r'\.notna\(\)',
        'notnull': r'\.notnull\(\)',
        'astype': r'\.astype\([^)]+\)',
        'select_dtypes': r'\.select_dtypes\([^)]+\)',
        'str.contains': r'\.str\.contains\([^)]+\)',
    }
    
    # Boolean operations
    boolean_patterns = [
        r'\[[^\]]*==[^\]]*\]',  # Boolean indexing with ==
        r'\[[^\]]*!=[^\]]*\]',  # Boolean indexing with !=
        r'\[[^\]]*>[^\]]*\]',   # Boolean indexing with >
        r'\[[^\]]*<[^\]]*\]',   # Boolean indexing with <
        r'\[[^\]]*>=[^\]]*\]',  # Boolean indexing with >=
        r'\[[^\]]*<=[^\]]*\]',  # Boolean indexing with <=
        r'\[[^\]]*&[^\]]*\]',   # Boolean indexing with &
        r'\[[^\]]*\|[^\]]*\]',  # Boolean indexing with |
    ]
    
    # Find DataFrame variable names (common patterns: df, df_, df_name, etc.)
    df_var_pattern = r'\b(df(?:_\w+)?|\w*df\w*)\b'
    df_vars = set(re.findall(df_var_pattern, code, re.IGNORECASE))
    
    # Remove common false positives
    df_vars.discard('describe')
    df_vars.discard('filter')
    
    # Track operations per DataFrame variable
    for df_var in df_vars:
        if len(df_var) < 2:  # Skip single character matches
            continue
            
        # Check for each operation pattern
        for op_name, pattern in patterns.items():
            # Look for patterns like df.operation or df_name.operation
            full_pattern = rf'\b{re.escape(df_var)}\.{pattern}'
            matches = re.finditer(full_pattern, code, re.MULTILINE)
            
            for match in matches:
                # Extract the full operation line
                line_start = code.rfind('\n', 0, match.start()) + 1
                line_end = code.find('\n', match.end())
                if line_end == -1:
                    line_end = len(code)
                
                operation_line = code[line_start:line_end].strip()
                
                operations.append({
                    'dataframe': df_var,
                    'operation': op_name,
                    'full_expression': operation_line,
                    'position': match.start()
                })
        
        # Check for boolean indexing
        for bool_pattern in boolean_patterns:
            full_pattern = rf'\b{re.escape(df_var)}{bool_pattern}'
            matches = re.finditer(full_pattern, code, re.MULTILINE)
            
            for match in matches:
                line_start = code.rfind('\n', 0, match.start()) + 1
                line_end = code.find('\n', match.end())
                if line_end == -1:
                    line_end = len(code)
                
                operation_line = code[line_start:line_end].strip()
                
                operations.append({
                    'dataframe': df_var,
                    'operation': 'boolean_indexing',
                    'full_expression': operation_line,
                    'position': match.start()
                })
    
    # Also check for assignments (e.g., df_analysis = df.copy())
    assignment_pattern = r'(\w+)\s*=\s*(?:df(?:_\w+)?|\w*df\w*)\.(\w+)\('
    assignments = re.finditer(assignment_pattern, code, re.IGNORECASE)
    
    for match in assignments:
        new_var = match.group(1)
        op_name = match.group(2)
        
        line_start = code.rfind('\n', 0, match.start()) + 1
        line_end = code.find('\n', match.end())
        if line_end == -1:
            line_end = len(code)
        
        operation_line = code[line_start:line_end].strip()
        
        operations.append({
            'dataframe': 'assignment',
            'operation': f'{new_var} = ...{op_name}()',
            'full_expression': operation_line,
            'position': match.start()
        })
    
    # Sort by position in code
    operations.sort(key=lambda x: x['position'])
    
    # Remove duplicates (same operation at same position)
    seen = set()
    unique_ops = []
    for op in operations:
        key = (op['position'], op['operation'])
        if key not in seen:
            seen.add(key)
            unique_ops.append(op)
    
    return unique_ops

