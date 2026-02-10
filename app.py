# app.py
import streamlit as st
import logging
from config.settings import PAGE_CONFIG
from config.styles import CUSTOM_CSS
from ui.sidebar import render_sidebar
from ui.main_content import render_main_area

# 1. 初始化
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# 2. 主程序
def main():
    # 获取全局布局容器
    c_left, c_right = st.columns([2.5, 7.5], gap="medium")

    # 渲染左侧栏 (传入容器 c_left)
    with c_left:
        bom_file, station_file, ignore_nc = render_sidebar()

    # 渲染右侧主工作区 (传入容器 c_right)
    with c_right:
        render_main_area(bom_file, station_file, ignore_nc)

if __name__ == "__main__":
    main()