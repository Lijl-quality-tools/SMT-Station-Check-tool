import json
import os
from config.mappings import ALIAS_CONFIG

DATA_FILE = "system_data.json"
RESET_TRIGGER_FILE = "RESET_ADMIN.txt"
DEFAULT_MAPPINGS = ALIAS_CONFIG
DEFAULT_DATA = {
    "inspectors": [],
    "admin_password": "admin",
    "mappings": DEFAULT_MAPPINGS
}


def load_data():
    """加载系统数据，处理重置和数据迁移"""
    if os.path.exists(RESET_TRIGGER_FILE):
        try:
            data = DEFAULT_DATA.copy()
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.remove(RESET_TRIGGER_FILE)
        except:
            pass
    
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 确保必要字段存在
        if "inspectors" not in data:
            data["inspectors"] = []
        if "admin_password" not in data:
            data["admin_password"] = "admin"
        if "mappings" not in data:
            data["mappings"] = DEFAULT_MAPPINGS
        
        save_data(data)
        return data
    except:
        return DEFAULT_DATA


def save_data(data):
    """保存系统数据到文件"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False


def get_inspector_list():
    """获取检验员姓名列表"""
    data = load_data()
    return data.get("inspectors", [])


def add_inspector(name):
    """添加新的检验员"""
    if not name or not isinstance(name, str):
        return False, "姓名不能为空"
    
    name = name.strip()
    if not name:
        return False, "姓名不能为空"
    
    data = load_data()
    inspectors = data.get("inspectors", [])
    
    if name in inspectors:
        return False, "检验员已存在"
    
    inspectors.append(name)
    data["inspectors"] = inspectors
    
    if save_data(data):
        return True, "成功添加"
    else:
        return False, "保存失败"


def delete_inspector(name):
    """删除检验员"""
    if not name or not isinstance(name, str):
        return False, "姓名不能为空"
    
    name = name.strip()
    data = load_data()
    inspectors = data.get("inspectors", [])
    
    if name not in inspectors:
        return False, "检验员不存在"
    
    inspectors.remove(name)
    data["inspectors"] = inspectors
    
    if save_data(data):
        return True, "成功删除"
    else:
        return False, "保存失败"


def verify_admin(pwd):
    """验证后台管理密码"""
    data = load_data()
    return data.get("admin_password", "admin") == pwd


def update_admin_password(pwd):
    """更新后台管理密码"""
    if not pwd or len(pwd) < 5:
        return False, "密码太短（至少5位）"
    
    data = load_data()
    data["admin_password"] = pwd
    
    if save_data(data):
        return True, "密码更新成功"
    else:
        return False, "保存失败"


def get_mappings():
    """获取当前映射配置字典"""
    data = load_data()
    mappings = data.get("mappings", DEFAULT_MAPPINGS)

    # 如果存储的映射不是字典（文件被意外修改或损坏），回退到默认并持久化修复
    if not isinstance(mappings, dict):
        mappings = DEFAULT_MAPPINGS.copy()
        data["mappings"] = mappings
        try:
            save_data(data)
        except:
            pass

    # 确保所有必要的键都存在，如果缺失则用默认值填充并保存修复
    changed = False
    for key in DEFAULT_MAPPINGS:
        if key not in mappings:
            mappings[key] = DEFAULT_MAPPINGS[key]
            changed = True

    if changed:
        data["mappings"] = mappings
        try:
            save_data(data)
        except:
            pass

    return mappings


def update_mappings(new_mappings):
    """更新映射配置"""
    if not isinstance(new_mappings, dict):
        return False, "映射必须是字典类型"
    
    data = load_data()
    data["mappings"] = new_mappings
    
    if save_data(data):
        return True, "映射更新成功"
    else:
        return False, "保存失败"


def reset_mappings():
    """重置映射配置为默认值"""
    data = load_data()
    data["mappings"] = DEFAULT_MAPPINGS
    
    if save_data(data):
        return True, "映射已重置为默认值"
    else:
        return False, "保存失败"