BANNER_HTML = """
<div style="background: linear-gradient(90deg, #005c97 0%, #363795 100%); padding: 15px 25px; border-radius: 10px; margin-bottom: 20px; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.15); display: flex; justify-content: space-between; align-items: center;">
    <div style="display: flex; align-items: center; gap: 15px;">
        <span style="font-size: 2rem;">🛡️</span>
        <div>
            <h2 style="margin:0; font-size: 1.4rem; color:white; font-weight:700;">SMT 生产防错比对系统</h2>
            <span style="font-size: 0.85rem; opacity: 0.9; font-weight:400;">Enterprise Edition v6.1</span>
        </div>
    </div>
    <div style="text-align: right; font-size: 0.9rem; opacity: 0.95;">
        <span style="background:rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; font-weight: 600;">
            ✅ 首件核对 / 换线防错
        </span>
    </div>
</div>
"""

CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.5rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    footer {visibility: hidden;}
    .stApp, .stMarkdown, p, div {font-family: "Microsoft YaHei", "Segoe UI", sans-serif;}
    .bom-header {
        background-color: #e3f2fd; border-left: 5px solid #2196f3;
        padding: 8px 15px; border-radius: 4px; margin-bottom: 10px;
        color: #0d47a1; font-weight: 700;
    }
    .station-header {
        background-color: #e8f5e9; border-left: 5px solid #4caf50;
        padding: 8px 15px; border-radius: 4px; margin-bottom: 10px;
        color: #1b5e20; font-weight: 700;
    }
    div.stButton > button {
        width: 100%; background-color: #0078d4; color: white; border: none;
        height: 45px; font-size: 16px; font-weight: bold; border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 10px;
    }
    div.stButton > button:hover {background-color: #005a9e; transform: translateY(-1px);}
    [data-testid="stDataFrame"] {border: 1px solid #eee;}
</style>
"""