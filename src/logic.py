import pandas as pd
import re
from config.settings import SPLIT_PATTERN
from src.utils import (clean_text, parse_refs, parse_subs,
                       normalize_pn_value, normalize_ref_designator,
                       check_spec_conflict)

def run_smt_comparison(df_bom, df_station, config, ignore_nc=False):
    results = []
    error_count = 0
    
    # 1. 聚合站位表
    station_map = {}
    c_s_pn, c_s_ref, c_s_slot = config['st_pn'], config['st_ref'], config['st_slot']
    c_s_desc = config.get('st_desc')

    # 站位表内部表头/说明行关键字，需在聚合时忽略
    STATION_HEADER_TOKENS = {"安装号码", "元件名", "备注", "图样名", "总数", "VERSION", "安装号", "站位号"}

    for idx, row in df_station.iterrows():
        excel_row = idx + 2
        raw_pn = row[c_s_pn]
        pn = normalize_pn_value(raw_pn)

        # 忽略站位表内部的重复表头行 / 版本行，例如 "Version,1"、"安装号码,元件名,备注..."
        row_str_vals = [str(v).strip() for v in row.values if pd.notna(v)]
        upper_vals = {v.upper() for v in row_str_vals}
        if (
            str(raw_pn).strip() in STATION_HEADER_TOKENS
            or pn in STATION_HEADER_TOKENS
            or "VERSION" in upper_vals
            or STATION_HEADER_TOKENS & set(row_str_vals)
        ):
            continue
        # 合并位置号1（T面）和位置号2（B面）
        # 站位表可能有两种格式：
        # 1. 分两行：T面行（位置号1有值，位置号2为空）和B面行（位置号1为空，位置号2有值）
        # 2. 合并一行：位置号1和位置号2分别填入对应面的位号
        # 3. 多列位号：可能有多个位号列（如 T面位号、B面位号），需要拼接
        
        # 处理多列位号：遍历 c_s_ref（现在是列表），拼接各列的值
        ref_parts = []
        if isinstance(c_s_ref, list):
            for ref_col in c_s_ref:
                val = row[ref_col]
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str and val_str.upper() != 'NAN':  # 过滤空值和 NaN
                        ref_parts.append(val_str)
        else:
            # 兼容单列的情况（字符串）
            val = row[c_s_ref]
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str and val_str.upper() != 'NAN':
                    ref_parts.append(val_str)
        
        # 将多列位号拼接成一个字符串，用空格分隔
        combined_ref = " ".join(ref_parts)
        refs = parse_refs(combined_ref, SPLIT_PATTERN)
        st_desc_val = str(row[c_s_desc]).strip() if c_s_desc and pd.notna(row[c_s_desc]) else ""

        if not pn and refs:
            error_count += 1
            results.append({
                "级别": "🔴 严重", "核对结果": "数据错误", "原始行号": f"Station: {excel_row}",
                "BOM料号": "UNKNOWN", "差异说明": "❌ 站位表有位号无料号", "站位号": "", "BOM数量": 0, "实际数量": len(refs),
                "BOM描述": "", "站位备注": st_desc_val
            })
            continue
        if not pn: continue

        slot = str(row[c_s_slot]).strip() if c_s_slot else ""
        if pn not in station_map: station_map[pn] = {'refs': set(), 'slots': [], 'desc': st_desc_val, 'rows': []}
        station_map[pn]['refs'].update(refs)
        station_map[pn]['rows'].append(str(excel_row))
        if slot and slot not in station_map[pn]['slots']: station_map[pn]['slots'].append(slot)
        if st_desc_val and not station_map[pn]['desc']: station_map[pn]['desc'] = st_desc_val

    # 2. 聚合 BOM
    bom_aggregated = {}
    c_b_pn, c_b_ref = config['bom_pn'], config['bom_ref']
    c_b_sub, c_b_desc = config['bom_sub'], config['bom_desc']

    for idx, row in df_bom.iterrows():
        excel_row = idx + 2
        bom_pn = normalize_pn_value(row[c_b_pn])
        # 合并位置号1（T面）和位置号2（B面）
        # 同一物料可能分两行：T面（位置号1有值，位置号2为空）和B面（位置号1为空，位置号2有值）
        # 或者有多个位号列（如 T面位号、B面位号），需要拼接
        
        # 处理多列位号：遍历 c_b_ref（现在是列表），拼接各列的值
        ref_parts = []
        if isinstance(c_b_ref, list):
            for ref_col in c_b_ref:
                val = row[ref_col]
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str and val_str.upper() != 'NAN':  # 过滤空值和 NaN
                        ref_parts.append(val_str)
        else:
            # 兼容单列的情况（字符串）
            val = row[c_b_ref]
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str and val_str.upper() != 'NAN':
                    ref_parts.append(val_str)
        
        # 将多列位号拼接成一个字符串，用空格分隔
        combined_ref = " ".join(ref_parts)
        bom_refs = parse_refs(combined_ref, SPLIT_PATTERN)
        
        if ignore_nc and not bom_refs: pass
        
        if not bom_pn and bom_refs:
            error_count += 1
            results.append({
                "级别": "🔴 严重", "核对结果": "数据错误", "原始行号": f"BOM: {excel_row}",
                "BOM料号": "MISSING", "差异说明": "❌ BOM行缺失料号", "站位号": "", "BOM数量": len(bom_refs), "实际数量": 0,
                "BOM描述": "", "站位备注": ""
            })
            continue
        if not bom_pn: continue

        if bom_pn not in bom_aggregated:
            subs = parse_subs(row[c_b_sub], SPLIT_PATTERN) if c_b_sub else []
            desc = str(row[c_b_desc]).strip() if c_b_desc else ""
            bom_aggregated[bom_pn] = {'refs': set(), 'subs': set(subs), 'desc': desc, 'rows': []}
        
        if bom_refs: bom_aggregated[bom_pn]['refs'].update(bom_refs)
        bom_aggregated[bom_pn]['rows'].append(str(excel_row))
        if c_b_sub: bom_aggregated[bom_pn]['subs'].update(parse_subs(row[c_b_sub], SPLIT_PATTERN))

    # 3. 正向比对
    claimed_st_pns = set()
    for bom_pn, bom_data in bom_aggregated.items():
        bom_refs = bom_data['refs']
        bom_desc = bom_data['desc']
        bom_subs = list(bom_data['subs'])
        row_str = ",".join(bom_data['rows'][:3]) + ("..." if len(bom_data['rows'])>3 else "")
        
        if not bom_refs:
            if ignore_nc:
                results.append({
                    "级别": "⚪ 忽略", "核对结果": "NC/跳过", "原始行号": f"BOM: {row_str}",
                    "BOM料号": bom_pn, "差异说明": "ℹ️ NC", "站位号": "", "BOM数量": 0, "实际数量": 0,
                    "BOM描述": bom_desc, "站位备注": ""
                })
            else:
                error_count += 1
                results.append({
                    "级别": "🟠 警告", "核对结果": "位号为空", "原始行号": f"BOM: {row_str}",
                    "BOM料号": bom_pn, "差异说明": "⚠️ 位号为空", "站位号": "", "BOM数量": 0, "实际数量": 0,
                    "BOM描述": bom_desc, "站位备注": ""
                })
            continue 
        
        targets = [bom_pn] + bom_subs
        found_refs = set()
        found_slots = []
        matched_pns = []
        found_st_descs = []

        for target in targets:
            if target in station_map:
                matched_pns.append(target)
                found_refs.update(station_map[target]['refs'])
                found_slots.extend(station_map[target]['slots'])
                found_st_descs.append(station_map[target]['desc'])
                claimed_st_pns.add(target)

        slots_str = ",".join(sorted(list(set(found_slots))))
        st_desc_str = " | ".join([d for d in set(found_st_descs) if d])

        norm_bom = {normalize_ref_designator(r): r for r in bom_refs}
        norm_found = {normalize_ref_designator(r): r for r in found_refs}
        set_bom = set(norm_bom.keys())
        set_found = set(norm_found.keys())

        # 准备直观展示的位号明细（未经归一化，用于 UI 预览）
        bom_refs_display = ",".join(sorted(list(bom_refs))) if bom_refs else ""
        found_refs_display = ",".join(sorted(list(found_refs))) if found_refs else ""

        if not matched_pns:
            level = "🔴 严重"
            status = "缺料"
            detail = "❌ 站位表中未找到主料或替代料"
            error_count += 1
        else:
            missing = set_bom - set_found
            extra = set_found - set_bom
            if not missing and not extra:
                is_conf, conf_msg = check_spec_conflict(bom_desc, st_desc_str)
                if is_conf:
                    level, status, detail = "🟠 警告", "规格预警", f"⚠️ {conf_msg}"
                    error_count += 1
                else:
                    level, status, detail = "🟢 正常", "通过", "匹配成功"
                if bom_pn not in matched_pns: detail += " (使用替代料)"
            else:
                level, status = "🟠 警告", "位号不符"
                msgs = []
                if missing: msgs.append(f"漏贴({len(missing)}): {','.join([norm_bom[k] for k in missing])}")
                if extra: msgs.append(f"多贴({len(extra)}): {','.join([norm_found[k] for k in extra])}")
                detail = " | ".join(msgs)
                error_count += 1

        results.append({
            "级别": level,
            "核对结果": status,
            "原始行号": f"BOM: {row_str}",
            "BOM料号": bom_pn,
            "BOM描述": bom_desc,
            "站位备注": st_desc_str,
            "差异说明": detail,
            "站位号": slots_str,
            "BOM数量": len(bom_refs),
            "实际数量": len(found_refs),
            # 新增两列：用于在结果预览中直观对比 BOM vs Station 位号
            "BOM位号明细": bom_refs_display,
            "实装位号明细": found_refs_display,
        })

    # 4. 反向检测
    for extra_pn in (set(station_map.keys()) - claimed_st_pns):
        st_data = station_map[extra_pn]
        row_str = ",".join(st_data['rows'][:3])
        error_count += 1
        results.append({
            "级别": "🔴 严重",
            "核对结果": "错料/多余",
            "原始行号": f"Station: {row_str}...",
            "BOM料号": "N/A",
            "BOM描述": "",
            "站位备注": st_data['desc'],
            "差异说明": f"❌ 非法物料: {extra_pn}",
            "站位号": ",".join(set(st_data['slots'])),
            "BOM数量": 0,
            "实际数量": len(st_data['refs']),
            "BOM位号明细": "",
            "实装位号明细": ",".join(sorted(list(st_data['refs']))),
        })

    return results, error_count, len(bom_aggregated)


# --- 通用列表结构比对类（BOM_Data / Station_Data） ---

class SMTComparator:
    """
    通用 SMT 防错比对类。

    输入:
        BOM_Data: List[dict]，字段:
            - main_part: 主料号 (str)
            - alt_part:  替代料号 (str, 可为空)
            - description: 规格描述 (str)
            - refs: 原始位号字符串 (str, 逗号分隔，如 "C1,C2\\n")

        Station_Data: List[dict]，字段:
            - part_no: 料号 (str)
            - slot: 站位位置 (str)
            - comment: 机器备注 (str)
            - refs: 原始位号字符串 (str, 斜杠分隔，如 "C1/C2")

    compare() 返回:
        List[dict]，每条记录包含:
            - level:   'FAIL' / 'WARN' / 'PASS'
            - code:    'MISSING_FEEDER' / 'MISSING_REFS' /
                       'WARN_SPEC' / 'UNKNOWN_PART' / 'OK'
            - message: 文本说明
            - context: 附加信息 (字典)
    """

    SPEC_PATTERN = re.compile(r"\d+\s*[KkMmVv]")

    def _clean_refs(self, raw: str, sep: str) -> set:
        """按给定分隔符清洗位号 -> Set，使用项目统一的 clean_text 与 normalize_ref_designator。"""
        if raw is None:
            return set()
        # 基础清洗：去空、转大写、去不可见字符
        text = clean_text(raw)
        if not text:
            return set()
        # 去引号与换行
        text = text.replace('"', '').replace("\n", "").replace("\r", "")
        parts = [p.strip() for p in text.split(sep) if p.strip()]
        # 使用 normalize_ref_designator 做位号归一化，防止 C1 / C-1 不一致
        return set(normalize_ref_designator(p) for p in parts)

    def _standardize_bom(self, bom_list):
        """生成 BOM 标准化结构: [{'main', 'alt', 'desc', 'ref_set', 'raw_refs_map'}]"""
        std = []
        for item in bom_list or []:
            main = normalize_pn_value(item.get("main_part", ""))
            alt = normalize_pn_value(item.get("alt_part", ""))
            desc = str(item.get("description", "") or "").strip()
            raw_refs = str(item.get("refs", "") or "")

            ref_norm_set = self._clean_refs(raw_refs, sep=",")
            # 保存规范位号 -> 原始位号映射，用于后续报表展示
            raw_map = {}
            if raw_refs:
                text = clean_text(raw_refs).replace('"', '').replace("\n", "").replace("\r", "")
                for p in [p.strip() for p in text.split(",") if p.strip()]:
                    key = normalize_ref_designator(p)
                    raw_map[key] = p

            std.append(
                {
                    "main": main,
                    "alt": alt,
                    "desc": desc,
                    "ref_set": ref_norm_set,
                    "raw_refs_map": raw_map,
                }
            )
        return std

    def _aggregate_station(self, station_list):
        """
        生成站位聚合结构:
            {
              'PN1': {
                  'ref_set': {...},        # 规范化位号集合
                  'raw_refs_map': {...},   # 规范位号 -> 原始位号
                  'slots': [..],           # 所有分盘站位
                  'comments': set([...])   # 备注集合
              },
              ...
            }
        """
        agg = {}
        for item in station_list or []:
            pn = normalize_pn_value(item.get("part_no", ""))
            if not pn:
                continue

            slot = str(item.get("slot", "") or "").strip()
            comment = str(item.get("comment", "") or "").strip()
            raw_refs = str(item.get("refs", "") or "")

            ref_norm_set = self._clean_refs(raw_refs, sep="/")

            # 构造原始位号映射
            raw_map = {}
            if raw_refs:
                text = clean_text(raw_refs).replace('"', '').replace("\n", "").replace("\r", "")
                for p in [p.strip() for p in text.split("/") if p.strip()]:
                    key = normalize_ref_designator(p)
                    raw_map[key] = p

            if pn not in agg:
                agg[pn] = {
                    "ref_set": set(),
                    "raw_refs_map": {},
                    "slots": [],
                    "comments": set(),
                }

            agg[pn]["ref_set"].update(ref_norm_set)
            agg[pn]["raw_refs_map"].update(raw_map)
            if slot:
                agg[pn]["slots"].append(slot)
            if comment:
                agg[pn]["comments"].add(comment)

        return agg

    def _extract_spec_tokens(self, text: str):
        """从描述/备注里提取关键规格 token（如 10K / 4.7M / 25V）。"""
        if not text:
            return set()
        return set(self.SPEC_PATTERN.findall(text))

    def compare(self, bom_list, station_list):
        """
        主入口：执行正向+反向比对。
        返回 List[dict]，每条包含 level / code / message / context。
        """
        results = []

        bom_std = self._standardize_bom(bom_list)
        st_agg = self._aggregate_station(station_list)

        # --- 正向比对：遍历 BOM，查漏、规格预警 ---
        for item in bom_std:
            main = item["main"]
            alt = item["alt"]
            desc = item["desc"]
            bom_refs = item["ref_set"]

            # 1) 料号是否上料
            candidates = []
            if main:
                candidates.append(main)
            if alt:
                candidates.append(alt)

            installed_refs = set()
            comments_joined = ""
            used_parts = []

            for p in candidates:
                if p in st_agg:
                    used_parts.append(p)
                    installed_refs.update(st_agg[p]["ref_set"])

            if not used_parts:
                results.append(
                    {
                        "level": "FAIL",
                        "code": "MISSING_FEEDER",
                        "message": "站位表中未找到主料或替代料",
                        "context": {
                            "main_part": main,
                            "alt_part": alt,
                            "bom_desc": desc,
                        },
                    }
                )
                # 缺料已是严重错误，本条无需继续位号比对与规格预警
                continue

            # 汇总 remark，用于规格防呆
            all_comments = set()
            for p in used_parts:
                all_comments.update(st_agg[p]["comments"])
            comments_joined = " | ".join(all_comments)

            # 2) 位号集合运算：BOM - 实装 = 漏贴
            missing_refs = bom_refs - installed_refs
            if missing_refs:
                # 还原成原始位号用于展示
                raw_missing = [
                    item["raw_refs_map"].get(r, r) for r in sorted(missing_refs)
                ]
                results.append(
                    {
                        "level": "FAIL",
                        "code": "MISSING_REFS",
                        "message": f"存在漏贴位号: {','.join(raw_missing)}",
                        "context": {
                            "main_part": main,
                            "alt_part": alt,
                            "missing_refs": raw_missing,
                        },
                    }
                )

            # 3) 规格防呆：BOM 规格 token 需在站位备注中能找到至少一个
            bom_tokens = self._extract_spec_tokens(desc)
            if bom_tokens:
                st_tokens = self._extract_spec_tokens(comments_joined)
                if not (bom_tokens & st_tokens):
                    results.append(
                        {
                            "level": "WARN",
                            "code": "WARN_SPEC",
                            "message": "BOM 规格在站位备注中未匹配到关键参数",
                            "context": {
                                "main_part": main,
                                "alt_part": alt,
                                "bom_desc": desc,
                                "station_comment": comments_joined,
                                "bom_tokens": sorted(bom_tokens),
                                "station_tokens": sorted(st_tokens),
                            },
                        }
                    )

            # 若没有漏贴且没有规格告警，则给一条 PASS 记录（可选）
            if not missing_refs:
                results.append(
                    {
                        "level": "PASS",
                        "code": "OK",
                        "message": "BOM 与站位表比对通过",
                        "context": {
                            "main_part": main,
                            "alt_part": alt,
                            "bom_desc": desc,
                        },
                    }
                )

        # --- 反向比对：遍历站位表，查未知物料 ---
        valid_bom_parts = set()
        for item in bom_std:
            if item["main"]:
                valid_bom_parts.add(item["main"])
            if item["alt"]:
                valid_bom_parts.add(item["alt"])

        for part_no, data in st_agg.items():
            if part_no not in valid_bom_parts:
                results.append(
                    {
                        "level": "FAIL",
                        "code": "UNKNOWN_PART",
                        "message": "站位表发现 BOM 未声明的物料",
                        "context": {
                            "part_no": part_no,
                            "slots": sorted(set(data["slots"])),
                            "refs": [
                                data["raw_refs_map"].get(r, r)
                                for r in sorted(data["ref_set"])
                            ],
                        },
                    }
                )

        return results
