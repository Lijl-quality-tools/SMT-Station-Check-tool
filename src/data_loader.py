import pandas as pd
import xlwings as xw
import os
import tempfile
import threading
import streamlit as st
import logging
from config.settings import CACHE_TTL
from src.utils import deduplicate_headers

EXCEL_LOCK = threading.Lock()

HEADER_CANDIDATES = [
    {"安装号码", "元件名", "备注", "图样名", "总数"},
    {"编号", "物料描述", "位置号", "位置号1", "位置号2"},
    {"BOM料号", "BOM位号", "BOM描述"},
]


def _clean_cell(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text in ("nan", "None", "<NA>"):
        return ""
    return text


def _detect_header_row(df: pd.DataFrame):
    """返回首个可能的表头行索引，若未命中则返回 0。"""
    for idx in range(len(df)):
        row_vals = [_clean_cell(v) for v in df.iloc[idx].tolist()]
        if not any(row_vals):
            continue
        row_set = set(row_vals)
        for candidate in HEADER_CANDIDATES:
            overlap = row_set & candidate
            # 命中 3 项以上即可认为是表头
            if len(overlap) >= min(3, len(candidate)):
                return idx
        # 若此行包含典型关键词，也认为是表头
        if any(key in row_set for key in ("安装号码", "元件名", "图样名", "编号", "位置号1")):
            return idx
    return 0


def _materialize_dataframe(df: pd.DataFrame):
    """将任意无表头 DataFrame 规范化 -> 以检测到的 header 行作为列名。"""
    if df is None or df.empty:
        return df
    df = df.fillna("")

    # 1) 先去掉全空白列，避免出现 Col_x 这种无意义列
    non_empty_cols = []
    for col in df.columns:
        col_values = [_clean_cell(v) for v in df[col]]
        if any(col_values):
            non_empty_cols.append(col)
    if non_empty_cols:
        df = df[non_empty_cols]

    # 2) 同样可去掉全空白行，减少噪音
    df = df.loc[~df.apply(lambda row: all(_clean_cell(v) == "" for v in row), axis=1)]
    df = df.reset_index(drop=True)

    header_idx = _detect_header_row(df)
    header_row = df.iloc[header_idx].tolist()
    columns = []
    for i, val in enumerate(header_row):
        cleaned = _clean_cell(val)
        columns.append(cleaned if cleaned else f"Col_{i}")

    # 应用去重逻辑：处理重复列名
    columns = deduplicate_headers(columns)

    data = df.iloc[header_idx + 1 :].copy()

    # 对齐列名数量与实际列数，避免 Length mismatch
    col_count = data.shape[1]
    if len(columns) > col_count:
        columns = columns[:col_count]
    elif len(columns) < col_count:
        # 理论上不会出现；防御性补齐
        for i in range(len(columns), col_count):
            columns.append(f"Col_{i}")

    data.columns = columns
    data = data.replace(["None", "nan", "<NA>"], "")
    data = data.dropna(how="all").reset_index(drop=True)
    return data

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_excel_secure(file) -> pd.DataFrame:
    if file is None: return None
    filename = file.name
    file_ext = os.path.splitext(filename)[1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(file.getvalue())
        tmp_path = tmp.name
    abs_path = os.path.abspath(tmp_path)
    df = None
    pandas_error = None

    try:
        if file_ext == '.csv':
            df = pd.read_csv(abs_path, dtype=str, header=None, encoding='utf-8', engine='python')
        elif file_ext == '.xlsx':
            df = pd.read_excel(abs_path, dtype=str, engine='openpyxl', header=None)
        elif file_ext == '.xls':
            df = pd.read_excel(abs_path, dtype=str, engine='xlrd', header=None)
        else:
            df = pd.read_excel(abs_path, dtype=str, header=None)
        try: os.remove(abs_path)
        except: pass
        if df is not None:
            return _materialize_dataframe(df)
    except Exception as e:
        pandas_error = e
        logging.warning(f"Pandas 读取失败: {e}")

    app = None
    with EXCEL_LOCK:
        try:
            app = xw.App(visible=False, add_book=False)
            app.display_alerts = False; app.screen_updating = False
            book = app.books.open(abs_path)
            sheet = book.sheets[0]
            raw_data = sheet.used_range.options(numbers=str).value
            book.close()
            if raw_data and len(raw_data) > 0:
                df = pd.DataFrame(raw_data)
                df = _materialize_dataframe(df)
        except Exception as e_xw:
            error_msg_xw = str(e_xw)
            if "Microsoft Excel" in error_msg_xw or "not found" in error_msg_xw:
                if pandas_error and "No module named" in str(pandas_error):
                    st.error("❌ 环境缺失依赖库"); st.info("请在终端运行: `pip install openpyxl xlrd`")
                else:
                    st.error("❌ 文件解析失败")
            else:
                st.error("❌ 文件读取失败"); st.warning(f"详情: {e_xw}")
            return None
        finally:
            if app: 
                try: app.quit()
                except: pass
            try: os.remove(abs_path)
            except: pass
    return df