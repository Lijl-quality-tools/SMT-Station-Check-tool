import streamlit as st
from src.user_manager import (
    verify_admin, update_admin_password, get_inspector_list,
    add_inspector, delete_inspector, get_mappings, update_mappings, reset_mappings
)

def render_sidebar():
    # 数据导入区域
    with st.container(border=True):
        st.markdown("##### 📥 数据导入")
        bom_file = st.file_uploader("BOM", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
        st.caption("👆 上传 BOM 表")
        st.write("")
        station_file = st.file_uploader("Station", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
        st.caption("👆 上传 站位表")

    # 系统参数区域
    with st.container(border=True):
        st.markdown("##### ⚙️ 系统参数")
        st.caption("支持分隔符: `,` `/` `;` `空格`")
        st.markdown("---")
        st.info("✅ 已启用 NC/不贴件过滤")

    st.write("")
    
    # 技术支持区域
    # with st.container(border=True):
    #     st.markdown("##### 📞 技术支持")
    #     st.markdown("""<div style="font-size:0.85rem;color:#555;line-height:1.6">
    #     <strong>工程质量部 (SMT QE)</strong><br>📧 smt_support@company.com<br>☎️ 分机: <strong>8088</strong></div>""", unsafe_allow_html=True)

    st.write("")
    st.divider()

    # 管理员后台
    with st.expander("⚙️ 管理员后台"):
        st.caption("🔐 系统级权限 (仅管理员可见)")

        # 简化交互：使用会话状态记录是否已解锁，默认不显示完整管理表单
        if 'admin_unlocked' not in st.session_state:
            st.session_state['admin_unlocked'] = False

        if not st.session_state['admin_unlocked']:
            # 密码输入，回车解锁
            short_pwd = st.text_input("", type="password", placeholder="管理员密码（回车解锁）", label_visibility='collapsed', key='admin_pwd_input')
            
            # 检查输入并验证
            if short_pwd:
                if verify_admin(short_pwd):
                    st.session_state['admin_unlocked'] = True
                    st.success("✅ 解锁成功")
                    # 强制重新加载页面以立即进入管理员界面
                    import time
                    time.sleep(0.1)
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
                else:
                    st.error("❌ 密码错误，请重新输入")
        else:
            # 已解锁状态，显示精简控制面板并提供锁定按钮
            row_left, row_right = st.columns([4, 1], gap='small')
            with row_left:
                st.info("🔓 管理员已解锁")
            with row_right:
                if st.button("锁定", key='lock', use_container_width=True):
                    st.session_state['admin_unlocked'] = False
                    st.info("🔒 已锁定")
                    # 强制重新加载页面以显示密码框
                    import time
                    time.sleep(0.1)
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()

            # 管理员功能以标签页展示，但布局更紧凑：去掉多余说明，控件使用更紧凑的 label_visibility
            t1, t2, t3, t4, t5 = st.tabs(["检验员", "添加", "删除", "规则", "密码"])

            # Tab 1: 检验员列表（紧凑）
            with t1:
                inspectors = get_inspector_list()
                if inspectors:
                    rows = [{"序号": i, "姓名": name} for i, name in enumerate(inspectors, 1)]
                    st.dataframe(rows, hide_index=True)
                else:
                    st.info("暂无检验员")

            # Tab 2: 添加检验员（紧凑）
            with t2:
                new_name = st.text_input("姓名", placeholder="例如: 张三", label_visibility='collapsed')
                if st.button("添加", use_container_width=True):
                    if new_name.strip():
                        ok, msg = add_inspector(new_name.strip())
                        if ok:
                            st.success(msg)
                            return bom_file, station_file, True
                        else:
                            st.error(msg)
                    else:
                        st.error("姓名不能为空")

            # Tab 3: 删除检验员（紧凑）
            with t3:
                inspectors = get_inspector_list()
                if inspectors:
                    selected_to_delete = st.multiselect("选择", inspectors, label_visibility='collapsed')
                    if selected_to_delete and st.button(f"删除 ({len(selected_to_delete)})", use_container_width=True):
                        for name in selected_to_delete:
                            delete_inspector(name)
                        st.success("删除完成")
                        return bom_file, station_file, True
                else:
                    st.info("暂无可删除的检验员")

            # Tab 4: 规则管理（精简输入）
            with t4:
                mappings = get_mappings()
                col1, col2 = st.columns(2)
                with col1:
                    st.caption("**BOM 表字段**")
                    bom_pn_str = st.text_input("料号", value=", ".join(mappings.get("BOM_PN", [])), label_visibility='collapsed', help="用于匹配BOM表中的料号列名，多个别名用逗号分隔")
                    st.caption("🔹 料号别名")
                    bom_ref_str = st.text_input("位号", value=", ".join(mappings.get("BOM_REF", [])), label_visibility='collapsed', help="用于匹配BOM表中的位号列名，多个别名用逗号分隔")
                    st.caption("🔹 位号别名")
                    bom_desc_str = st.text_input("描述", value=", ".join(mappings.get("BOM_DESC", [])), label_visibility='collapsed', help="用于匹配BOM表中的描述/规格列名，多个别名用逗号分隔")
                    st.caption("🔹 描述别名")
                    bom_sub_str = st.text_input("替代料", value=", ".join(mappings.get("BOM_SUB", [])), label_visibility='collapsed', help="用于匹配BOM表中的替代料列名，多个别名用逗号分隔")
                    st.caption("🔹 替代料别名")
                with col2:
                    st.caption("**站位表字段**")
                    st_pn_str = st.text_input("料号", value=", ".join(mappings.get("ST_PN", [])), label_visibility='collapsed', key='st_pn', help="用于匹配站位表中的料号列名，多个别名用逗号分隔")
                    st.caption("🔹 料号别名")
                    st_ref_str = st.text_input("位号", value=", ".join(mappings.get("ST_REF", [])), label_visibility='collapsed', key='st_ref', help="用于匹配站位表中的位号列名，多个别名用逗号分隔")
                    st.caption("🔹 位号别名")
                    st_slot_str = st.text_input("安装号", value=", ".join(mappings.get("ST_SLOT", [])), label_visibility='collapsed', help="用于匹配站位表中的安装号/分盘位置列名，多个别名用逗号分隔")
                    st.caption("🔹 安装号别名")
                    st_desc_str = st.text_input("备注", value=", ".join(mappings.get("ST_DESC", [])), label_visibility='collapsed', help="用于匹配站位表中的备注/说明列名，多个别名用逗号分隔")
                    st.caption("🔹 备注别名")

                btn_col1, btn_col2 = st.columns([1, 1], gap='small')
                with btn_col1:
                    if st.button("保存", use_container_width=True):
                        try:
                            new_mappings = {
                                "BOM_PN": [x.strip() for x in bom_pn_str.split(",") if x.strip()],
                                "BOM_REF": [x.strip() for x in bom_ref_str.split(",") if x.strip()],
                                "BOM_DESC": [x.strip() for x in bom_desc_str.split(",") if x.strip()],
                                "BOM_SUB": [x.strip() for x in bom_sub_str.split(",") if x.strip()],
                                "ST_PN": [x.strip() for x in st_pn_str.split(",") if x.strip()],
                                "ST_REF": [x.strip() for x in st_ref_str.split(",") if x.strip()],
                                "ST_SLOT": [x.strip() for x in st_slot_str.split(",") if x.strip()],
                                "ST_DESC": [x.strip() for x in st_desc_str.split(",") if x.strip()],
                            }
                            ok, msg = update_mappings(new_mappings)
                            if ok:
                                st.success(msg)
                                return bom_file, station_file, True
                            else:
                                st.error(msg)
                        except Exception as e:
                            st.error(f"保存失败: {str(e)}")
                with btn_col2:
                    if st.button("恢复默认", use_container_width=True):
                        ok, msg = reset_mappings()
                        if ok:
                            st.success(msg)
                            return bom_file, station_file, True
                        else:
                            st.error(msg)
            # Tab 5: 管理员密码修改（独立选项卡）
            with t5:
                nap = st.text_input("新管理密码", type="password", placeholder="至少5位", label_visibility='collapsed')
                if st.button("更新密码", use_container_width=True):
                    if nap:
                        ok, msg = update_admin_password(nap)
                        if ok:
                            st.success(msg)
                            return bom_file, station_file, True
                        else:
                            st.error(msg)
                    else:
                        st.error("密码不能为空")

    return bom_file, station_file, True