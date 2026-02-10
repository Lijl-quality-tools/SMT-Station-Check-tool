## SMT 首件核对 / 生产防错比对系统

> A production-grade SMT first-article inspection & BOM vs Station comparison tool, built with Streamlit.

### ✨ 项目简介

**SMT 首件核对工具**是面向电子制造现场（SMT 车间）的首件核对与换线防错系统，用于对比 **BOM 表** 与 **贴片机站位表**，自动识别以下问题：

- **缺料 / 错料**：BOM 中声明的物料在站位表未上料，或站位表出现 BOM 未声明物料  
- **位号不符**：BOM 位号与实装位号不一致（漏贴 / 多贴）  
- **规格不匹配预警**：根据描述字段提取封装、耐压等关键参数，在备注中做交叉校验  
- **NC / 不贴件**：支持按位号为空、备注等规则忽略 NC 物料  

系统通过 Web 界面运行，无需安装复杂客户端。

---

### 🧩 功能特性概览

- **智能表头识别**：无需固定模板，自动从 Excel 中检测表头行并清洗空行/空列（`src/data_loader.py`）  
- **多格式 Excel 兼容**：优先使用 `pandas`，失败时自动回退到 `xlwings` + 本机 Excel 解析，适应复杂格式  
- **料号与位号归一化**：修复科学计数法料号（如 `3.00E+13`）、归一化位号（如 `LED-1` → `LED1`），减少人为格式差异带来的误判（`src/utils.py`）  
- **一料多站 / 多列位号支持**：支持 T/B 面位号分列、多列位号自动合并与去重（`src/logic.py`）  
- **替代料 / 替代关系处理**：BOM 中的主料 + 替代料一起参与匹配，避免误报缺料  
- **规则可视化配置**：通过左侧「管理员后台」维护字段别名映射，无需改代码即可适配不同格式的 BOM / 站位表（`config/mappings.py` + `system_data.json`）  
- **首件报告一键导出**：按照工单信息自动生成带有条件格式、保护和追溯信息的 Excel 报告（`ui/main_content.py`）  
- **轻量用户管理**：内置检验员名单与管理员密码管理，帮助规范操作流程（`src/user_manager.py`）  


---

### 🛠 技术栈与工程实践

- **语言 / 框架**：Python 3.10 + Streamlit
- **数据处理**：Pandas，用于 Excel/CSV 清洗与结果表格生成
- **Excel 兼容层**：xlwings + 本机 Excel（作为回退方案处理复杂格式）
- **前端 UI**：Streamlit 原生组件 + 自定义 CSS（`config/styles.py`），宽屏布局、扁平化卡片风格
- **配置与持久化**：JSON (`system_data.json`) + 简单配置映射字典 (`config/mappings.py`)

**工程实践亮点：**

- 使用 `@st.cache_data` + 自定义缓存 TTL，减少重复解析大 Excel 带来的性能开销  
- Excel 解析采用 **“pandas → 失败再回退到 xlwings”** 的多级兜底方案，提高现场可用性  
- 通过 **别名映射 + 智能列名猜测**（`guess_column_index` / `guess_column_names`），适配不同客户/产线的表头风格  
- 将 UI（`ui/*`）、业务逻辑（`src/logic.py`）、数据层（`src/data_loader.py`、`src/user_manager.py`）和配置（`config/*`）分层，结构清晰、便于后续扩展  

---

### 📂 目录结构

```text
SMT首件核对工具/
├─ app.py                 # Streamlit 入口，拼装整体布局（左侧栏 + 右侧主区域）
├─ requirements.txt       # Python 依赖列表
├─ SMT首件核对.bat        # Windows 一键启动脚本
├─ system_data.json       # 运行时配置与检验员数据
├─ src/
│  ├─ data_loader.py      # Excel/CSV 安全加载、表头自动检测与清洗
│  ├─ logic.py            # BOM vs Station 核心比对逻辑与通用比较类
│  ├─ user_manager.py     # 检验员、管理员密码、映射配置持久化
│  └─ utils.py            # 文本清洗、位号/料号归一化、规格提取等工具函数
├─ ui/
│  ├─ sidebar.py          # 左侧文件上传、系统参数与管理员后台
│  └─ main_content.py     # 右侧业务流程：配置映射、比对、结果展示与报告导出
├─ config/
│  ├─ settings.py         # 页面设置、分隔符、规格提取正则、缓存配置
│  ├─ styles.py           # 顶部横幅与全局 CSS 样式
│  └─ mappings.py         # 默认列名别名映射与数量列排除规则
├─ Demo_Docs/             # 示例 BOM / 站位表与操作截图（可自行补充）
└─ python_embed/          # 嵌入式 Python 运行时（用于做成免安装版本）
```

---

### 🚀 如何运行（开发环境）

#### 1. 准备环境

```bash
pip install -r requirements.txt
```

建议使用 Python 3.9+。如果在公司环境没有安装 Python，可使用项目自带的 `python_embed` 目录打包为免安装版本。

#### 2. 启动 Web 应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`（如未自动打开，可手动访问该地址）。

> Windows 用户也可以直接双击 `SMT首件核对.bat` 启动（适合非技术人员使用）。

---

### 📘 使用说明（业务视角）

1. **准备文件**
   - BOM 与站位表分别导出为 `xlsx / xls / csv`  
   - **文件名需以机种编号开头**，例如：`8088_BOM.xlsx` 与 `8088_Station.xlsx`，以便系统校验两份文件是否属于同一机种  

2. **上传数据**
   - 左侧栏中上传 BOM 文件与 Station 文件  
   - 系统会自动尝试识别表头行、清洗空列/空行  

3. **确认字段映射**
   - 右侧主区会自动根据当前别名配置，推荐 BOM/站位表的料号列、位号列、描述列、替代料列等  
   - 如自动识别不准确，可手动从下拉框中重新选择（仅影响当前会话）  

4. **执行比对**
   - 点击「🚀 执行自动化比对」，系统会清洗数据并执行 BOM vs Station 比对  
   - 下方会展示统计指标及异常明细，可在「🚫 异常」与「📋 全量」两个 Tab 中切换查看  

5. **填写工单信息并导出报告**
   - 在「📦 工单信息」区域选择检验人、录入订单号和数量  
   - 填写完整后，会自动出现「📥 导出报告」按钮，生成带条件格式和保护的核对报告 Excel  

更多关于字段映射、规格预警等实现细节，可参考 `docs/技术说明_架构设计.md`。

---

### 🔐 管理员后台与配置映射

- 左侧栏底部的「⚙️ 管理员后台」用于：
  - 维护检验员名单（便于统计与追溯）  
  - 配置 BOM / 站位表的字段别名（例如「料号」「物料编码」「Part No.」都映射为同一逻辑字段）  
  - 修改管理员密码  
- 相关逻辑集中在：
  - `src/user_manager.py`：负责 `system_data.json` 的读写和字段容错  
  - `config/mappings.py`：定义字段别名的默认值  

---


