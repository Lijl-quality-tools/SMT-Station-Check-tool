# ui/main_content.py
import streamlit as st
import pandas as pd
import io
import re
import gc
from datetime import datetime
from config.styles import BANNER_HTML
from config.mappings import EXCLUDE_QTY_KEYWORDS
from src.user_manager import get_inspector_list, get_mappings

# --- [核心修复] 修正引用路径，与实际文件名保持一致 ---
from src.utils import guess_column_index, guess_column_names, get_machine_info, generate_signature
from src.data_loader import load_excel_secure   # 修正: io_engine -> data_loader
from src.logic import run_smt_comparison        # 修正: core_logic -> logic

def extract_file_id(filename):
    match = re.match(r'^([a-zA-Z0-9]+)', filename)
    if match: return match.group(1)
    return None

def render_main_area(bom_file, station_file, ignore_nc):
    st.markdown(BANNER_HTML, unsafe_allow_html=True)
    
    # 从数据库获取最新的映射配置
    current_aliases = get_mappings()

    # 场景 A: 未上传文件
    if not (bom_file and station_file):
        st.info(f"👋 欢迎使用 SMT 智能防错系统。请在左侧上传文件。")
        
        with st.container(border=True):
            st.markdown("### 📖 SMT 核对作业指导书 (SOP)")
            t1, t2, t3 = st.tabs(["1️⃣ 准备工作", "2️⃣ 核心逻辑", "3️⃣ 结果判定"])
            with t1:
                st.markdown("#### 📂 文件准备规范")
                st.warning("**文件名强制要求**：必须以 `机种编号` 开头。")
                c1, c2 = st.columns(2)
                with c1: st.success("✅ **正确**: `8088_BOM.xlsx`")
                with c2: st.error("❌ **错误**: `BOM.xlsx`")
            with t2:
                st.markdown("#### 🧠 系统自动处理")
                st.markdown("- 清洗科学计数法\n- 合并一料多站\n- 识别替代料")
            with t3:
                st.markdown("#### 🚦 结果状态")
                c1, c2, c3, c4 = st.columns(4)
                c1.error("🔴 缺料/错料"); c2.warning("🟠 位号不符")
                c3.warning("🟠 规格预警"); c4.success("🟢 通过")
        return

    # 场景 B: 业务处理
    bom_id = extract_file_id(bom_file.name)
    st_id = extract_file_id(station_file.name)
    if not bom_id or not st_id:
        st.error("❌ 文件名不规范"); return
    if bom_id != st_id:
        st.error(f"🛑 编号不匹配: {bom_id} vs {st_id}"); return

    with st.spinner("⏳ 解析中..."):
        df_bom = load_excel_secure(bom_file)
        df_station = load_excel_secure(station_file)

    if df_bom is not None and df_station is not None:
        # 有比对结果时，默认将映射配置折叠，避免占用空间
        show_mapping_expanded = 'comparison_results' not in st.session_state
        with st.expander("🧩 映射配置（如需调整，请展开）", expanded=show_mapping_expanded):
            with st.container(border=True):
                # 字段映射区
                c1, c2 = st.columns(2, gap="large")
                b_cols = df_bom.columns.tolist()
                s_cols = df_station.columns.tolist()

                with c1:
                    st.markdown('<div class="bom-header">📋 BOM 表配置</div>', unsafe_allow_html=True)
                    with st.container(border=True):
                        b1, b2 = st.columns(2)
                        with b1:
                            idx_b_pn = guess_column_index(b_cols, current_aliases['BOM_PN'])
                            sel_b_pn = st.selectbox("料号列", b_cols, index=min(idx_b_pn, len(b_cols)-1), label_visibility="collapsed")
                            st.caption("BOM料号")
                        with b2:
                            # BOM 位号列 - 使用多选支持 T/B 面分列
                            default_b_ref = guess_column_names(b_cols, current_aliases['BOM_REF'], exclude_keys=EXCLUDE_QTY_KEYWORDS)
                            sel_b_ref = st.multiselect("位号列", b_cols, default=default_b_ref, label_visibility="collapsed")
                            st.caption("BOM位号（支持多列）")
                        
                        b3, b4 = st.columns(2)
                        with b3:
                            idx_b_desc = guess_column_index(b_cols, current_aliases['BOM_DESC'])
                            sel_b_desc = st.selectbox("描述列", ["(不显示)"]+b_cols, index=min(idx_b_desc+1, len(b_cols)) if idx_b_desc < len(b_cols) else 0, label_visibility="collapsed")
                            if sel_b_desc == "(不显示)": sel_b_desc = None
                            st.caption("规格描述")
                        with b4:
                            idx_sub = guess_column_index(b_cols, current_aliases['BOM_SUB'])
                            d_idx = idx_sub if idx_sub < len(b_cols) and any(k in b_cols[idx_sub] for k in ["替代", "Sub"]) else 0
                            sel_b_sub = st.selectbox("替代列", ["(无)"]+b_cols, index=min(d_idx+1, len(b_cols)) if d_idx else 0, label_visibility="collapsed")
                            if sel_b_sub == "(无)": sel_b_sub = None
                            st.caption("替代料")

                with c2:
                    st.markdown('<div class="station-header">🏗️ 站位表配置</div>', unsafe_allow_html=True)
                    with st.container(border=True):
                        s1, s2 = st.columns(2)
                        with s1:
                            idx_s_pn = guess_column_index(s_cols, current_aliases['ST_PN'])
                            sel_s_pn = st.selectbox("物料列", s_cols, index=min(idx_s_pn, len(s_cols)-1), label_visibility="collapsed")
                            st.caption("物料编号")
                        with s2:
                            # 站位表 位号列 - 使用多选支持 T/B 面分列
                            default_s_ref = guess_column_names(s_cols, current_aliases['ST_REF'], exclude_keys=EXCLUDE_QTY_KEYWORDS)
                            sel_s_ref = st.multiselect("位号列", s_cols, default=default_s_ref, label_visibility="collapsed")
                            st.caption("位号（支持多列）")
                        
                        s3, s4 = st.columns(2)
                        with s3:
                            idx_s_desc = guess_column_index(s_cols, current_aliases['ST_DESC'])
                            sel_s_desc = st.selectbox("备注列", ["(无)"]+s_cols, index=min(idx_s_desc+1, len(s_cols)) if idx_s_desc < len(s_cols) else 0, label_visibility="collapsed")
                            if sel_s_desc == "(无)": sel_s_desc = None
                            st.caption("物料规格")
                        with s4:
                            idx_s_slot = guess_column_index(s_cols, current_aliases['ST_SLOT'])
                            sel_s_slot = st.selectbox("安装号", ["(无)"]+s_cols, index=min(idx_s_slot+1, len(s_cols)) if idx_s_slot < len(s_cols) else 0, label_visibility="collapsed")
                            if sel_s_slot == "(无)": sel_s_slot = None
                            st.caption("安装号码")

        st.write("")
        if st.button("🚀 执行自动化比对"):
            config_map = {
                'bom_pn': sel_b_pn, 'bom_ref': sel_b_ref, 'bom_sub': sel_b_sub, 'bom_desc': sel_b_desc,
                'st_pn': sel_s_pn, 'st_ref': sel_s_ref, 'st_slot': sel_s_slot,
                'st_desc': sel_s_desc
            }

            with st.status("🔍 运算中...", expanded=True) as status:
                st.write("🔄 清洗数据...")
                results, err_cnt, total = run_smt_comparison(df_bom, df_station, config_map, ignore_nc)
                status.update(label="✅ 完成", state="complete", expanded=False)

            # 缓存比对结果到 session_state，避免后续输入时丢失
            st.session_state.comparison_results = results
            st.session_state.comparison_err_cnt = err_cnt
            st.session_state.comparison_total = total
            st.session_state.comparison_config = config_map

        # 工单信息输入区（如果已有缓存结果，则进入导出信息填写与统计展示）
        if 'comparison_results' in st.session_state:
            results = st.session_state.comparison_results
            err_cnt = st.session_state.comparison_err_cnt
            total = st.session_state.comparison_total
            config_map = st.session_state.comparison_config

            st.write("")
            st.write("")
            st.markdown("---")
            st.markdown("### 📦 工单信息 - 导出前确认")
            
            with st.container(border=True):
                col_ins, col_wo, col_qty = st.columns([2, 2, 2])
                
                # 检验员选择
                with col_ins:
                    inspectors = get_inspector_list()
                    inspector_options = ["请选择..."] + inspectors
                    selected_inspector = st.selectbox(
                        "检验人 👩🏻‍🚒",
                        inspector_options,
                        index=0,
                        label_visibility="visible"
                    )
                    inspector = selected_inspector if selected_inspector != "请选择..." else None
                    if inspector is None:
                        st.caption("🔴 *必填项*")
                
                # 订单号输入
                with col_wo:
                    wo_number = st.text_input(
                        "订单号 #️⃣",
                        placeholder="PO20250101",
                        label_visibility="visible"
                    )
                    if not wo_number.strip():
                        st.caption("🔴 *必填项*")
                
                # 订单数量输入
                with col_qty:
                    wo_qty = st.number_input(
                        "订单数量 📊",
                        value=0,
                        min_value=0,
                        step=1,
                        label_visibility="visible"
                    )
                    if wo_qty <= 0:
                        st.caption("🔴 *必填项*")
                
                # 校验逻辑并显示下载按钮
                is_valid = inspector is not None and wo_number.strip() and wo_qty > 0
                
                if is_valid:
                    # 工单信息完整，生成导出按钮
                    now = datetime.now()
                    date_str = now.strftime("%y%m%d")
                    report_name = f"{bom_id}_{inspector}_{date_str}核对报告.xlsx"
                    
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                        df_res = pd.DataFrame(results)
                        df_res.to_excel(writer, index=False, sheet_name='核对结果', startrow=3)
                        
                        df_bom.to_excel(writer, index=False, sheet_name='原BOM表')
                        df_station.to_excel(writer, index=False, sheet_name='原站位表')

                        wb = writer.book
                        text_fmt = wb.add_format({'align': 'left', 'valign': 'vcenter'})
                        
                        protect_opts = {
                            'select_locked_cells': True, 'select_unlocked_cells': True,
                            'format_cells': True, 'format_columns': True, 'format_rows': True,
                            'autofilter': True, 'sort': True
                        }

                        # Sheet 1 - 核对结果
                        ws = writer.sheets['核对结果']
                        ws.protect('admin', protect_opts)
                        
                        # 添加工单信息到顶栏
                        header_fmt = wb.add_format({
                            'bold': True, 'align': 'left', 'valign': 'vcenter',
                            'bg_color': '#D9E8F5', 'border': 1, 'font_size': 10
                        })
                        info_fmt = wb.add_format({
                            'align': 'left', 'valign': 'vcenter',
                            'bg_color': '#E7F0F7', 'border': 1, 'font_size': 10
                        })
                        
                        ws.set_row(0, 18)
                        ws.set_row(1, 18)
                        ws.write('A1', '订单号:', header_fmt)
                        ws.write('B1', wo_number, info_fmt)
                        ws.write('C1', '订单数量:', header_fmt)
                        ws.write('D1', wo_qty, info_fmt)
                        ws.write('A2', '核对时间:', header_fmt)
                        ws.write('B2', now.strftime('%Y-%m-%d %H:%M:%S'), info_fmt)
                        ws.write('C2', '检验人:', header_fmt)
                        ws.write('D2', inspector, info_fmt)
                        
                        # 添加数据开始行的格式
                        fmt_red = wb.add_format({'font_color':'#D00000', 'bold':True})
                        fmt_org = wb.add_format({'font_color':'#FF8800', 'bold':True})
                        fmt_grn = wb.add_format({'font_color':'#008000'})
                        ws.conditional_format('A5:A9999', {'type':'text', 'criteria':'containing', 'value':'严重', 'format':fmt_red})
                        ws.conditional_format('A5:A9999', {'type':'text', 'criteria':'containing', 'value':'警告', 'format':fmt_org})
                        ws.conditional_format('A5:A9999', {'type':'text', 'criteria':'containing', 'value':'正常', 'format':fmt_grn})
                        ws.set_column('E:E', 25); ws.set_column('F:F', 25); ws.set_column('G:G', 40)

                        # Sheet 2/3 - 原始表格
                        for sheet_name in ['原BOM表', '原站位表']:
                            ws_raw = writer.sheets[sheet_name]
                            ws_raw.protect('admin', protect_opts)
                            ws_raw.set_column('A:Z', 15, text_fmt)

                    st.download_button(
                        label="📥 导出报告",
                        data=out.getvalue(),
                        file_name=report_name,
                        mime="application/vnd.ms-excel",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.info("⏳ 请完整填写上述信息后，下载按钮将自动显示")


        # 显示对比结果（如果有缓存）
        if 'comparison_results' in st.session_state:
            results = st.session_state.comparison_results
            err_cnt = st.session_state.comparison_err_cnt
            total = st.session_state.comparison_total
            config_map = st.session_state.comparison_config
            
            # 显示统计指标
            st.markdown("---")
            st.markdown("### 📊 核对统计")
            k1, k2, k3, k4 = st.columns([2, 2, 2, 3])
            k1.metric("🔢 BOM项", total)
            k2.metric("🟢 正常", total - err_cnt)
            k3.metric("🔴 异常", err_cnt)
            
            # 显示数据表
            df_res = pd.DataFrame(results)
            tab_err, tab_all = st.tabs([f"🚫 异常 ({err_cnt})", "📋 全量"])
            col_cfg = {
                "级别": st.column_config.TextColumn("级别", width="small"),
                "核对结果": st.column_config.TextColumn("状态", width="small"),
                "原始行号": st.column_config.TextColumn("行号", width="small"),
                "BOM料号": st.column_config.TextColumn("BOM料号", width="medium"),
                "BOM描述": st.column_config.TextColumn("BOM描述", width="large"),
                "站位备注": st.column_config.TextColumn("站位备注", width="large"),
                "差异说明": st.column_config.TextColumn("差异", width="large"),
                "站位号": st.column_config.TextColumn("站位", width="small"),
            }
            with tab_err:
                if err_cnt > 0:
                    st.error("请核实异常：")
                    st.dataframe(df_res[df_res["级别"]!="🟢 正常"], use_container_width=True, hide_index=True, column_config=col_cfg)
                else: st.success("🎉 无异常")
            with tab_all:
                st.dataframe(df_res, use_container_width=True, hide_index=True, column_config=col_cfg)
            
            del df_res, results; gc.collect()