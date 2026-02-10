ALIAS_CONFIG = {
    # BOM表固定格式：优先匹配"编号"、"物料描述"、"位置号1"、"位置号2"
    'BOM_PN': ["编号", "料号", "Part", "PN", "Material", "物料编码"],
    'BOM_REF': ["位置号1", "位置", "位号", "Ref", "Designator", "Pos", "位置号"],
    'BOM_REF2': ["位置号2", "位号2", "Ref2", "Designator2", "Pos2", "B面位号"],
    'BOM_SUB': ["替代", "替料", "Sub", "Alt", "替代料"],
    'BOM_DESC': ["物料描述", "描述", "规格", "Desc", "Spec", "Value"],
    # 站位表：与BOM统一描述（物料编号、物料规格等）
    'ST_PN': ["编号", "元件", "料号", "Part", "Name", "元件名", "物料编号"],
    'ST_REF': ["位置号1", "图样", "位号", "Ref", "Designator", "图样名", "位置号"],
    'ST_REF2': ["位置号2", "位号2", "Ref2", "Designator2", "Pos2", "B面位号"],
    'ST_SLOT': ["安装", "站位", "Slot", "Feeder", "安装号"],
    'ST_QTY': ["总数", "数量", "Qty", "Count", "用量"],
    'ST_DESC': ["物料描述", "备注", "说明", "Remark", "Comment", "Desc", "物料规格"]
}

# 排除关键词列表，用于防止误选数量列
EXCLUDE_QTY_KEYWORDS = ['数量', 'Qty', 'Count', 'Amount', 'Total']