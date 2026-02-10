# src/utils.py
import pandas as pd
import re
import socket
import hashlib
from config.settings import SPLIT_PATTERN, SPEC_PATTERNS

# --- 基础清洗 ---
def clean_text(text):
    """基础文本清洗：去空、转大写、去隐形字符"""
    if pd.isna(text): return ""
    text_str = str(text).strip().upper()
    return text_str.replace('\t', '').replace('\u200b', '')

def normalize_pn_value(value):
    """[核心] 修复科学计数法 (3.00E+13 -> 3008...)"""
    if pd.isna(value): return ""
    text = clean_text(value)
    try:
        f_val = float(text)
        # 如果包含 E 或 . 且转数字成功，则认为是科学计数法
        if 'E' in text or '.' in text:
            return str(int(f_val))
    except ValueError:
        pass
    return text

def normalize_ref_designator(ref):
    """[核心] 位号归一化 (LED-1 -> LED1)"""
    if not ref: return ""
    return re.sub(r'[^A-Z0-9]', '', ref)

def parse_refs(ref_str, pattern):
    """解析位号字符串 -> Set"""
    text = clean_text(ref_str)
    if not text: return set()
    return set(r.strip() for r in re.split(pattern, text) if r.strip())

def parse_subs(sub_str, pattern):
    """解析替代料"""
    text = clean_text(sub_str)
    if not text: return []
    raw_subs = [r.strip() for r in re.split(pattern, text) if r.strip()]
    return [normalize_pn_value(s) for s in raw_subs]

def guess_column_index(cols, keys):
    """智能猜测列名"""
    for k in keys:
        for c in cols:
            if k.upper() in c.upper(): return cols.index(c)
    return 0

def guess_column_names(cols, keys, exclude_keys=None):
    """
    智能猜测多个匹配列名，支持排除关键词过滤
    
    Args:
        cols: 所有列名列表
        keys: 要匹配的关键词列表
        exclude_keys: 排除关键词列表（如包含这些词则剔除该列）
    
    Returns:
        List[str]: 匹配到的列名列表
    """
    matched_cols = []
    
    for col in cols:
        col_upper = col.upper()
        
        # 检查是否包含排除关键词
        if exclude_keys:
            excluded = False
            for exclude_key in exclude_keys:
                if exclude_key.upper() in col_upper:
                    excluded = True
                    break
            if excluded:
                continue
        
        # 检查是否包含任意匹配关键词
        for key in keys:
            if key.upper() in col_upper:
                matched_cols.append(col)
                break
    
    return matched_cols

# --- [v5.0] 规格提取逻辑 ---
def extract_specs(text):
    """提取封装、耐压等参数"""
    specs = {}
    text = clean_text(text)
    for key, pattern in SPEC_PATTERNS.items():
        match = re.search(pattern, text)
        if match: specs[key] = match.group(1)
    return specs

def check_spec_conflict(bom_desc, st_desc):
    """检查规格是否冲突"""
    bom_specs = extract_specs(bom_desc)
    st_specs = extract_specs(st_desc)
    conflicts = []
    
    for key, bom_val in bom_specs.items():
        # 如果站位表也有这个参数，且不相等，则报错
        if key in st_specs and st_specs[key] != bom_val:
            conflicts.append(f"{key}: BOM({bom_val})≠Station({st_specs[key]})")
            
    if conflicts: return True, " | ".join(conflicts)
    return False, ""

# --- [v5.1] 追溯与安全 ---
def get_machine_info():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return f"{hostname} ({ip})"
    except: return "Unknown Device"

def generate_signature(data_str):
    """生成防篡改 MD5 指纹"""
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:16].upper()

# --- [核心修复] 补全缺失的函数 ---
def extract_file_id(filename):
    """
    从文件名提取开头编号
    例如: "12345_BOM.xlsx" -> "12345"
    """
    if not filename: return None
    # 匹配开头的连续字母或数字
    match = re.match(r'^([a-zA-Z0-9]+)', filename)
    if match:
        return match.group(1)
    return None

def deduplicate_headers(headers):
    """
    处理列表中的重复字符串，为重复项添加序号后缀
    
    Args:
        headers: 字符串列表（如表头）
    
    Returns:
        List[str]: 处理后的新列表，重复项被添加 .1, .2 等后缀
    
    Example:
        ['A', 'B', 'A', 'C'] -> ['A', 'B', 'A.1', 'C']
    """
    seen = {}
    result = []
    
    for header in headers:
        if header not in seen:
            seen[header] = 0
            result.append(header)
        else:
            seen[header] += 1
            result.append(f"{header}.{seen[header]}")
    
    return result