import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

JSON_DIR = BASE_DIR / "outputs" / "week1_sample_json"
CLEAN_LOG_PATH = BASE_DIR / "logs" / "clean_v5_1_log.csv"


VALID_STAGE_STATUS = {"success", "partial", "fail"}


DIRTY_INVESTOR_KEYWORDS = [
    "不存在",
    "完成私募基金",
    "办理完成私募基金",
    "已办理基金",
    "发起设立基金",
    "13名股东",
    "13日",
    "4日",
    "日完成",
    "原因为该基金",
    "受托管理基金",
    "社会公众投资者道歉",
    "担任",
    "其管理人",
    "执行事务合伙人",
    "有限合伙人",
    "普通合伙人",
    "通过",
    "基金所投资",
    "日在中国证券投资基金",
    "聘任合伙人以外的人担任合伙企业",
    "公司员工",
    "核心员工",
    "定增对象",
    "承诺函",
    "道歉",
]


GENERIC_BAD_INVESTOR_NAMES = {
    "基金",
    "私募基金",
    "投资基金",
    "创业投资基金",
    "股权投资基金",
    "投资者",
    "社会公众投资者",
    "公司员工",
    "合伙企业",
    "发行人",
    "公司",
}


def normalize_stage_status(value, default="success"):
    value = str(value).strip()

    if value in VALID_STAGE_STATUS:
        return value

    if value in ["", "unchecked", "None", "none", "nan", "NaN", "null"]:
        return default

    return default


def normalize_investor_name(name):
    name = str(name).strip()

    prefixes = [
        "通过",
        "其管理人",
        "执行事务合伙人",
        "有限合伙人",
        "普通合伙人",
        "担任",
        "向",
        "由",
        "新股东",
        "外部投资者",
    ]

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                changed = True

    name = name.strip("，。、；：:（）()[]【】 ")

    if "（有限合伙" in name and "）" not in name:
        name = name + "）"

    return name


def is_dirty_investor_name(name):
    name = normalize_investor_name(name)

    if not name:
        return True

    if name in GENERIC_BAD_INVESTOR_NAMES:
        return True

    if len(name) < 2 or len(name) > 80:
        return True

    if any(keyword in name for keyword in DIRTY_INVESTOR_KEYWORDS):
        return True

    return False


def clean_event_investors(events):
    old_count = 0
    new_count = 0

    for event in events:
        investors = event.get("investors", [])

        if not isinstance(investors, list):
            event["investors"] = []
            continue

        old_count += len(investors)

        cleaned = []
        seen = set()

        for investor in investors:
            if not isinstance(investor, dict):
                continue

            name = normalize_investor_name(investor.get("investor_original_name", ""))

            if is_dirty_investor_name(name):
                continue

            if name in seen:
                continue

            investor["investor_original_name"] = name
            investor["investor_short_name"] = investor.get("investor_short_name") or name

            if not investor["investor_short_name"] or is_dirty_investor_name(investor["investor_short_name"]):
                investor["investor_short_name"] = name

            cleaned.append(investor)
            seen.add(name)

        event["investors"] = cleaned
        event["investor_disclosure_status"] = "已识别投资方名称" if cleaned else "未识别到投资方名称"

        new_count += len(cleaned)

    return old_count, new_count


def rebuild_investor_overview(events):
    """
    investor_overview 只从 financing_events 的干净 investors 重建。
    候选摘要里的投资方线索仍保留在 candidate_evidence_summary，不再混入 overview，
    这样可以避免 overview 出现“完成私募基金/不存在委托基金/社会公众投资者道歉”等脏名称。
    """
    investor_map = {}

    for event in events:
        event_order = event.get("event_order")

        for investor in event.get("investors", []):
            if not isinstance(investor, dict):
                continue

            name = normalize_investor_name(investor.get("investor_original_name", ""))

            if is_dirty_investor_name(name):
                continue

            if name not in investor_map:
                investor_map[name] = {
                    "investor_original_name": name,
                    "investor_short_name": investor.get("investor_short_name") or name,
                    "investor_type": investor.get("investor_type", "无法判断"),
                    "is_pevc": investor.get("is_pevc", "uncertain"),
                    "event_count": 0,
                    "related_event_orders": [],
                }

            investor_map[name]["event_count"] += 1

            if event_order is not None and event_order not in investor_map[name]["related_event_orders"]:
                investor_map[name]["related_event_orders"].append(event_order)

    return list(investor_map.values())


def normalize_processing(data):
    processing = data.setdefault("processing", {})

    events = data.get("financing_events", [])
    candidate_summary = data.get("candidate_evidence_summary", {})

    processing["download_status"] = normalize_stage_status(processing.get("download_status"), "success")
    processing["parse_status"] = normalize_stage_status(processing.get("parse_status"), "success")
    processing["locate_status"] = normalize_stage_status(processing.get("locate_status"), "success")

    if isinstance(events, list) and len(events) > 0:
        processing["extract_status"] = "success"
    else:
        processing["extract_status"] = "partial"

    processing["review_status"] = processing.get("review_status") or "unchecked"

    if processing["review_status"] not in ["unchecked", "pass", "revise", "fail"]:
        processing["review_status"] = "unchecked"

    processing["extracted_event_count"] = len(events) if isinstance(events, list) else 0

    if isinstance(candidate_summary, dict):
        if isinstance(candidate_summary.get("candidate_snippet_count"), int):
            processing["candidate_snippet_count"] = candidate_summary.get("candidate_snippet_count")
        else:
            processing["candidate_snippet_count"] = processing.get("candidate_snippet_count", 0)

        detected_keywords = candidate_summary.get("detected_keywords", [])
        processing["candidate_signal_count"] = len(detected_keywords) if isinstance(detected_keywords, list) else 0
    else:
        processing["candidate_snippet_count"] = processing.get("candidate_snippet_count", 0)
        processing["candidate_signal_count"] = processing.get("candidate_signal_count", 0)

    processing["notes"] = processing.get("notes", "") + " v5.1 clean: normalized processing status and rebuilt investor_overview from clean event investors."


def clean_one_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    company = data.get("company", {})
    company_name = company.get("company_name", "")
    stock_code = company.get("stock_code", "")

    old_locate_status = data.get("processing", {}).get("locate_status", "")

    events = data.get("financing_events", [])

    if not isinstance(events, list):
        events = []
        data["financing_events"] = events

    old_overview_count = len(data.get("investor_overview", [])) if isinstance(data.get("investor_overview", []), list) else 0

    old_event_investor_count, new_event_investor_count = clean_event_investors(events)

    data["investor_overview"] = rebuild_investor_overview(events)

    normalize_processing(data)

    new_locate_status = data.get("processing", {}).get("locate_status", "")
    new_overview_count = len(data.get("investor_overview", []))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "json_file": json_path.name,
        "company_name": company_name,
        "stock_code": stock_code,
        "old_locate_status": old_locate_status,
        "new_locate_status": new_locate_status,
        "old_overview_count": old_overview_count,
        "new_overview_count": new_overview_count,
        "old_event_investor_count": old_event_investor_count,
        "new_event_investor_count": new_event_investor_count,
        "status": "success",
        "error_message": "",
    }


def main():
    CLEAN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    json_files = sorted(JSON_DIR.glob("*.json"))

    if not json_files:
        print(f"未找到 JSON 文件，请检查目录：{JSON_DIR}")
        return

    rows = []

    print(f"待清洗 JSON 数量：{len(json_files)}")

    for json_path in json_files:
        print(f"正在清洗：{json_path.name}")

        try:
            row = clean_one_json(json_path)
            rows.append(row)
            print(
                f"完成：locate_status {row['old_locate_status']} -> {row['new_locate_status']}，"
                f"overview {row['old_overview_count']} -> {row['new_overview_count']}"
            )

        except Exception as e:
            rows.append({
                "json_file": json_path.name,
                "company_name": "",
                "stock_code": "",
                "old_locate_status": "",
                "new_locate_status": "",
                "old_overview_count": "",
                "new_overview_count": "",
                "old_event_investor_count": "",
                "new_event_investor_count": "",
                "status": "fail",
                "error_message": str(e),
            })
            print(f"失败：{json_path.name}，原因：{e}")

    with open(CLEAN_LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "json_file",
            "company_name",
            "stock_code",
            "old_locate_status",
            "new_locate_status",
            "old_overview_count",
            "new_overview_count",
            "old_event_investor_count",
            "new_event_investor_count",
            "status",
            "error_message",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\nv5.1 JSON 清洗完成")
    print(f"清洗日志：{CLEAN_LOG_PATH}")


if __name__ == "__main__":
    main()