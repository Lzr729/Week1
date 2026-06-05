import csv
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

JSON_DIR = BASE_DIR / "outputs" / "week1_sample_json"
VALIDATION_LOG_PATH = BASE_DIR / "logs" / "validation_log.csv"
VALIDATION_SUMMARY_PATH = BASE_DIR / "logs" / "validation_summary.csv"


REQUIRED_TOP_LEVEL_FIELDS = [
    "company",
    "financing_events",
    "investor_overview",
    "shareholding_and_exit_summary",
    "candidate_evidence_summary",
    "processing",
    "_meta",
]


REQUIRED_COMPANY_FIELDS = [
    "company_name",
    "stock_code",
    "exchange",
    "board",
    "listing_date",
    "prospectus_title",
    "prospectus_url",
    "prospectus_version",
    "prospectus_date",
]


REQUIRED_EVENT_FIELDS = [
    "event_order",
    "event_date",
    "date_type",
    "event_type",
    "event_nature",
    "pevc_relevance",
    "disclosed_round",
    "inferred_round",
    "round_inference_basis",
    "total_investment_amount",
    "currency",
    "share_price",
    "shares_issued_or_transferred",
    "pre_money_valuation",
    "post_money_valuation",
    "valuation_basis",
    "investors",
    "investor_disclosure_status",
    "source_section",
    "source_page",
    "evidence_text",
    "confidence",
    "source_candidate_file",
    "raw_amount_candidates",
    "raw_price_candidates",
    "raw_share_candidates",
    "raw_ratio_candidates",
]


REQUIRED_INVESTOR_FIELDS = [
    "investor_original_name",
    "investor_short_name",
    "investor_type",
    "is_pevc",
    "investment_amount",
    "shares_acquired",
    "shareholding_ratio_after_event",
    "exit_status_before_ipo",
]


REQUIRED_INVESTOR_OVERVIEW_FIELDS = [
    "investor_original_name",
    "investor_short_name",
    "investor_type",
    "is_pevc",
    "event_count",
    "related_event_orders",
]


REQUIRED_SUMMARY_FIELDS = [
    "summary_type",
    "source_section",
    "source_page",
    "evidence_text",
]


REQUIRED_CANDIDATE_SUMMARY_FIELDS = [
    "has_candidate_text",
    "candidate_snippet_count",
    "detected_keywords",
    "detected_investor_names",
    "detected_amount_or_price_values",
    "detected_ratio_values",
    "top_candidate_evidence",
]


REQUIRED_PROCESSING_FIELDS = [
    "download_status",
    "parse_status",
    "locate_status",
    "extract_status",
    "review_status",
    "candidate_snippet_count",
    "extracted_event_count",
    "candidate_signal_count",
    "notes",
]


REQUIRED_META_FIELDS = [
    "schema_name",
    "schema_version",
    "generated_at",
    "sample_id",
    "source_candidate_file",
]


DATE_TYPE_VALUES = [
    "协议签署日",
    "工商变更日",
    "股东会决议日",
    "出资到账日",
    "未说明",
]


EVENT_TYPE_VALUES = [
    "增资",
    "股权转让",
    "增资及股权转让",
    "其他",
]


EVENT_NATURE_VALUES = [
    "企业设立",
    "历史增资",
    "股权转让",
    "外部投资者进入",
    "股权结构调整",
    "代持解除",
    "员工持股平台",
    "IPO战略配售",
    "其他",
]


PEVC_RELEVANCE_VALUES = [
    "core",
    "related",
    "none",
    "uncertain",
]


INVESTOR_TYPE_VALUES = [
    "VC/PE",
    "产业资本",
    "自然人",
    "员工持股平台",
    "政府基金",
    "其他",
    "无法判断",
]


IS_PEVC_VALUES = [
    "yes",
    "no",
    "uncertain",
]


CONFIDENCE_VALUES = [
    "high",
    "medium",
    "low",
]


STATUS_VALUES = [
    "success",
    "partial",
    "fail",
]


REVIEW_STATUS_VALUES = [
    "unchecked",
    "pass",
    "revise",
    "fail",
]


SUMMARY_TYPE_VALUES = [
    "pre_ipo_shareholding",
    "lockup_arrangement",
    "exit_arrangement",
    "private_fund_check",
]


TRANSACTION_ACTION_KEYWORDS = [
    "股票定向发行",
    "定向发行",
    "股票发行",
    "发行股票",
    "新增注册资本",
    "增加注册资本",
    "增资",
    "认购",
    "缴纳的出资款",
    "缴付的出资款",
    "出资款",
    "股权转让",
    "股份转让",
    "转让协议",
    "受让",
    "融资",
    "投资协议",
]


BAD_EVENT_SECTION_KEYWORDS = [
    "发行人板块定位",
    "股份支付",
    "股权激励",
    "其他权益工具投资",
    "经常性关联交易",
    "重大经常性关联交易",
    "资金来源",
    "现金流量分析",
    "筹资活动现金流量分析",
    "主营业务成本",
    "商誉",
    "股利分配",
    "上市标准",
    "投资者保护",
]


WEAK_SECTION_KEYWORDS = [
    "科目具体情况及分析说明",
    "股本",
    "资本公积",
    "募集资金使用情况",
]


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
]


GENERIC_BAD_INVESTOR_NAMES = [
    "基金",
    "投资者",
    "社会公众投资者",
    "公司员工",
    "合伙企业",
    "私募基金",
    "投资基金",
]


NUMBER_PATTERN = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万元|亿元|元|万股|股|%)"
)


def add_log(log_rows, json_file, company_name, stock_code, level, check_item, message):
    log_rows.append({
        "json_file": json_file,
        "company_name": company_name,
        "stock_code": stock_code,
        "level": level,
        "check_item": check_item,
        "message": message,
    })


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def is_number_or_null(value):
    return value is None or isinstance(value, (int, float))


def has_transaction_action(text: str) -> bool:
    return any(keyword in text for keyword in TRANSACTION_ACTION_KEYWORDS)


def has_number_evidence(text: str) -> bool:
    return bool(NUMBER_PATTERN.search(text))


def is_dirty_investor_name(name: str) -> bool:
    if not name:
        return True

    name = str(name).strip()

    if name in GENERIC_BAD_INVESTOR_NAMES:
        return True

    if len(name) < 2 or len(name) > 80:
        return True

    if any(keyword in name for keyword in DIRTY_INVESTOR_KEYWORDS):
        return True

    return False


def validate_enum(value, allowed_values, log_rows, json_file, company_name, stock_code, level, check_item, message_prefix):
    if value not in allowed_values:
        add_log(
            log_rows,
            json_file,
            company_name,
            stock_code,
            level,
            check_item,
            f"{message_prefix} 取值异常：{value}",
        )


def validate_company(data, log_rows, json_file):
    company = data.get("company", {})

    company_name = ""
    stock_code = ""

    if not isinstance(company, dict):
        add_log(log_rows, json_file, "", "", "ERROR", "company_type", "company 不是对象。")
        return company_name, stock_code

    company_name = company.get("company_name", "")
    stock_code = str(company.get("stock_code", ""))

    for field in REQUIRED_COMPANY_FIELDS:
        if field not in company:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "company_field_missing", f"company 缺少字段：{field}")
        elif is_empty(company.get(field)):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "company_field_empty", f"company 字段为空：{field}")

    if stock_code:
        if not stock_code.isdigit() or len(stock_code) != 6:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "stock_code_format", f"股票代码应为 6 位数字：{stock_code}")

    return company_name, stock_code


def validate_investor(investor, log_rows, json_file, company_name, stock_code, event_idx, investor_idx, evidence_text):
    if not isinstance(investor, dict):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_type", f"第 {event_idx} 条事件第 {investor_idx} 个 investor 不是对象。")
        return

    for field in REQUIRED_INVESTOR_FIELDS:
        if field not in investor:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_field_missing", f"第 {event_idx} 条事件第 {investor_idx} 个 investor 缺少字段：{field}")

    name = investor.get("investor_original_name", "")

    if is_empty(name):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_original_name_empty", f"第 {event_idx} 条事件第 {investor_idx} 个 investor_original_name 为空。")
    elif is_dirty_investor_name(name):
        add_log(log_rows, json_file, company_name, stock_code, "WARNING", "dirty_investor_name", f"第 {event_idx} 条事件第 {investor_idx} 个 investor_original_name 疑似脏名称：{name}")

    validate_enum(
        investor.get("investor_type"),
        INVESTOR_TYPE_VALUES,
        log_rows,
        json_file,
        company_name,
        stock_code,
        "ERROR",
        "investor_type_value",
        f"第 {event_idx} 条事件 investor_type",
    )

    validate_enum(
        investor.get("is_pevc"),
        IS_PEVC_VALUES,
        log_rows,
        json_file,
        company_name,
        stock_code,
        "ERROR",
        "is_pevc_value",
        f"第 {event_idx} 条事件 is_pevc",
    )

    for numeric_field in [
        "investment_amount",
        "shares_acquired",
        "shareholding_ratio_after_event",
    ]:
        value = investor.get(numeric_field)
        if value is not None and not isinstance(value, (int, float)):
            add_log(
                log_rows,
                json_file,
                company_name,
                stock_code,
                "ERROR",
                "investor_numeric_field_type",
                f"第 {event_idx} 条事件第 {investor_idx} 个 {numeric_field} 应为数字或 null。",
            )

    if name and name not in evidence_text:
        add_log(
            log_rows,
            json_file,
            company_name,
            stock_code,
            "WARNING",
            "investor_not_in_evidence",
            f"第 {event_idx} 条事件投资方名称未出现在 evidence_text 中：{name}",
        )


def validate_event(event, log_rows, json_file, company_name, stock_code, idx):
    if not isinstance(event, dict):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "event_type", f"第 {idx} 条 financing_event 不是对象。")
        return

    for field in REQUIRED_EVENT_FIELDS:
        if field not in event:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "event_field_missing", f"第 {idx} 条事件缺少字段：{field}")

    if event.get("event_order") != idx:
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "event_order", f"第 {idx} 条事件 event_order 应为 {idx}，当前为 {event.get('event_order')}。")

    validate_enum(event.get("date_type"), DATE_TYPE_VALUES, log_rows, json_file, company_name, stock_code, "ERROR", "date_type_value", f"第 {idx} 条事件 date_type")
    validate_enum(event.get("event_type"), EVENT_TYPE_VALUES, log_rows, json_file, company_name, stock_code, "ERROR", "event_type_value", f"第 {idx} 条事件 event_type")
    validate_enum(event.get("event_nature"), EVENT_NATURE_VALUES, log_rows, json_file, company_name, stock_code, "WARNING", "event_nature_value", f"第 {idx} 条事件 event_nature")
    validate_enum(event.get("pevc_relevance"), PEVC_RELEVANCE_VALUES, log_rows, json_file, company_name, stock_code, "ERROR", "pevc_relevance_value", f"第 {idx} 条事件 pevc_relevance")
    validate_enum(event.get("confidence"), CONFIDENCE_VALUES, log_rows, json_file, company_name, stock_code, "ERROR", "confidence_value", f"第 {idx} 条事件 confidence")

    if is_empty(event.get("disclosed_round")):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "disclosed_round_empty", f"第 {idx} 条事件 disclosed_round 为空。未披露时应填“未披露”。")

    if not is_empty(event.get("inferred_round")) and is_empty(event.get("round_inference_basis")):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "inferred_round_basis_missing", f"第 {idx} 条事件填写了 inferred_round，但 round_inference_basis 为空。")

    for numeric_field in [
        "total_investment_amount",
        "share_price",
        "shares_issued_or_transferred",
        "pre_money_valuation",
        "post_money_valuation",
    ]:
        value = event.get(numeric_field)
        if not is_number_or_null(value):
            add_log(
                log_rows,
                json_file,
                company_name,
                stock_code,
                "ERROR",
                "event_numeric_field_type",
                f"第 {idx} 条事件 {numeric_field} 应为数字或 null，当前为：{value}",
            )

    if event.get("currency") != "CNY":
        add_log(log_rows, json_file, company_name, stock_code, "WARNING", "currency", f"第 {idx} 条事件 currency 当前为 {event.get('currency')}，建议统一为 CNY。")

    evidence_text = event.get("evidence_text", "")

    if is_empty(evidence_text):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "evidence_text_empty", f"第 {idx} 条事件 evidence_text 为空。")
    else:
        if not has_transaction_action(evidence_text):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "evidence_no_transaction_action", f"第 {idx} 条事件 evidence_text 缺少交易动作。")

        if not has_number_evidence(evidence_text):
            add_log(log_rows, json_file, company_name, stock_code, "WARNING", "evidence_no_number", f"第 {idx} 条事件 evidence_text 缺少金额/价格/股数/比例证据。")

    source_section = event.get("source_section", "")

    if is_empty(source_section) and is_empty(event.get("source_page")):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "source_missing", f"第 {idx} 条事件缺少 source_section/source_page。")

    if any(keyword in source_section for keyword in BAD_EVENT_SECTION_KEYWORDS):
        add_log(
            log_rows,
            json_file,
            company_name,
            stock_code,
            "WARNING",
            "bad_source_section",
            f"第 {idx} 条事件 source_section 疑似低质量或误抽章节：{source_section}",
        )

    if any(keyword in source_section for keyword in WEAK_SECTION_KEYWORDS):
        add_log(
            log_rows,
            json_file,
            company_name,
            stock_code,
            "INFO",
            "weak_source_section",
            f"第 {idx} 条事件 source_section 为泛化章节，建议后续优先用更具体章节替代：{source_section}",
        )

    investors = event.get("investors")

    if not isinstance(investors, list):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investors_type", f"第 {idx} 条事件 investors 不是列表。")
    else:
        if event.get("pevc_relevance") == "core" and len(investors) == 0:
            add_log(
                log_rows,
                json_file,
                company_name,
                stock_code,
                "WARNING",
                "core_event_without_investor",
                f"第 {idx} 条事件 pevc_relevance=core，但 investors 为空。",
            )

        for investor_idx, investor in enumerate(investors, start=1):
            validate_investor(investor, log_rows, json_file, company_name, stock_code, idx, investor_idx, evidence_text)

    for list_field in [
        "raw_amount_candidates",
        "raw_price_candidates",
        "raw_share_candidates",
        "raw_ratio_candidates",
    ]:
        if list_field in event and not isinstance(event.get(list_field), list):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "raw_candidate_type", f"第 {idx} 条事件 {list_field} 应为列表。")


def validate_investor_overview(data, log_rows, json_file, company_name, stock_code):
    overview = data.get("investor_overview", [])

    if not isinstance(overview, list):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_overview_type", "investor_overview 不是列表。")
        return

    seen_names = set()

    for idx, investor in enumerate(overview, start=1):
        if not isinstance(investor, dict):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_overview_item_type", f"investor_overview 第 {idx} 项不是对象。")
            continue

        for field in REQUIRED_INVESTOR_OVERVIEW_FIELDS:
            if field not in investor:
                add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_overview_field_missing", f"investor_overview 第 {idx} 项缺少字段：{field}")

        name = investor.get("investor_original_name", "")

        if is_empty(name):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_overview_name_empty", f"investor_overview 第 {idx} 项名称为空。")
        else:
            if name in seen_names:
                add_log(log_rows, json_file, company_name, stock_code, "WARNING", "investor_overview_duplicate", f"investor_overview 投资方重复：{name}")
            seen_names.add(name)

            if is_dirty_investor_name(name):
                add_log(log_rows, json_file, company_name, stock_code, "WARNING", "dirty_investor_overview_name", f"investor_overview 疑似脏名称：{name}")

        validate_enum(
            investor.get("investor_type"),
            INVESTOR_TYPE_VALUES,
            log_rows,
            json_file,
            company_name,
            stock_code,
            "ERROR",
            "investor_overview_type_value",
            f"investor_overview 第 {idx} 项 investor_type",
        )

        validate_enum(
            investor.get("is_pevc"),
            IS_PEVC_VALUES,
            log_rows,
            json_file,
            company_name,
            stock_code,
            "ERROR",
            "investor_overview_is_pevc_value",
            f"investor_overview 第 {idx} 项 is_pevc",
        )

        if not isinstance(investor.get("event_count"), int):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_overview_event_count_type", f"investor_overview 第 {idx} 项 event_count 应为整数。")

        if not isinstance(investor.get("related_event_orders"), list):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "investor_overview_related_orders_type", f"investor_overview 第 {idx} 项 related_event_orders 应为列表。")


def validate_shareholding_summary(data, log_rows, json_file, company_name, stock_code):
    summary_items = data.get("shareholding_and_exit_summary", [])

    if not isinstance(summary_items, list):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "shareholding_summary_type", "shareholding_and_exit_summary 不是列表。")
        return

    for idx, item in enumerate(summary_items, start=1):
        if not isinstance(item, dict):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "shareholding_summary_item_type", f"shareholding_and_exit_summary 第 {idx} 项不是对象。")
            continue

        for field in REQUIRED_SUMMARY_FIELDS:
            if field not in item:
                add_log(log_rows, json_file, company_name, stock_code, "ERROR", "shareholding_summary_field_missing", f"shareholding_and_exit_summary 第 {idx} 项缺少字段：{field}")

        summary_type = item.get("summary_type")
        if summary_type not in SUMMARY_TYPE_VALUES:
            add_log(log_rows, json_file, company_name, stock_code, "WARNING", "summary_type_value", f"shareholding_and_exit_summary 第 {idx} 项 summary_type 取值异常：{summary_type}")

        evidence_text = item.get("evidence_text", "")
        source_section = item.get("source_section", "")

        if is_empty(evidence_text):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "summary_evidence_empty", f"shareholding_and_exit_summary 第 {idx} 项 evidence_text 为空。")

        if summary_type == "exit_arrangement":
            if not any(keyword in evidence_text for keyword in ["退出", "减持", "转让", "锁定", "限售"]):
                add_log(
                    log_rows,
                    json_file,
                    company_name,
                    stock_code,
                    "INFO",
                    "weak_exit_summary",
                    f"exit_arrangement 摘要可能只是普通风险或业务文本，source_section={source_section}",
                )


def validate_candidate_summary(data, log_rows, json_file, company_name, stock_code):
    summary = data.get("candidate_evidence_summary", {})

    if not isinstance(summary, dict):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "candidate_summary_type", "candidate_evidence_summary 不是对象。")
        return

    for field in REQUIRED_CANDIDATE_SUMMARY_FIELDS:
        if field not in summary:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "candidate_summary_field_missing", f"candidate_evidence_summary 缺少字段：{field}")

    if "has_candidate_text" in summary and not isinstance(summary.get("has_candidate_text"), bool):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "has_candidate_text_type", "candidate_evidence_summary.has_candidate_text 应为布尔值。")

    if "candidate_snippet_count" in summary and not isinstance(summary.get("candidate_snippet_count"), int):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "candidate_snippet_count_type", "candidate_evidence_summary.candidate_snippet_count 应为整数。")

    for list_field in [
        "detected_keywords",
        "detected_investor_names",
        "detected_amount_or_price_values",
        "detected_ratio_values",
        "top_candidate_evidence",
    ]:
        if list_field in summary and not isinstance(summary.get(list_field), list):
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "candidate_summary_list_type", f"candidate_evidence_summary.{list_field} 应为列表。")


def validate_processing(data, log_rows, json_file, company_name, stock_code, event_count):
    processing = data.get("processing", {})

    if not isinstance(processing, dict):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "processing_type", "processing 不是对象。")
        return

    for field in REQUIRED_PROCESSING_FIELDS:
        if field not in processing:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "processing_field_missing", f"processing 缺少字段：{field}")

    for field in ["download_status", "parse_status", "locate_status", "extract_status"]:
        validate_enum(
            processing.get(field),
            STATUS_VALUES,
            log_rows,
            json_file,
            company_name,
            stock_code,
            "ERROR",
            "processing_status_value",
            field,
        )

    validate_enum(
        processing.get("review_status"),
        REVIEW_STATUS_VALUES,
        log_rows,
        json_file,
        company_name,
        stock_code,
        "ERROR",
        "review_status_value",
        "review_status",
    )

    extracted_event_count = processing.get("extracted_event_count")

    if isinstance(extracted_event_count, int):
        if extracted_event_count != event_count:
            add_log(
                log_rows,
                json_file,
                company_name,
                stock_code,
                "ERROR",
                "event_count_match",
                f"processing.extracted_event_count={extracted_event_count}，但 financing_events 实际数量={event_count}。",
            )
    else:
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "extracted_event_count_type", "processing.extracted_event_count 应为整数。")

    if event_count == 0 and processing.get("extract_status") != "partial":
        add_log(log_rows, json_file, company_name, stock_code, "WARNING", "empty_events_status", "financing_events 为空时，extract_status 建议为 partial。")

    if event_count > 0 and processing.get("extract_status") != "success":
        add_log(log_rows, json_file, company_name, stock_code, "WARNING", "non_empty_events_status", "financing_events 非空时，extract_status 建议为 success。")


def validate_meta(data, log_rows, json_file, company_name, stock_code):
    meta = data.get("_meta", {})

    if not isinstance(meta, dict):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "meta_type", "_meta 不是对象。")
        return

    for field in REQUIRED_META_FIELDS:
        if field not in meta:
            add_log(log_rows, json_file, company_name, stock_code, "ERROR", "meta_field_missing", f"_meta 缺少字段：{field}")

    schema_version = meta.get("schema_version", "")
    if schema_version and not str(schema_version).startswith("v"):
        add_log(log_rows, json_file, company_name, stock_code, "WARNING", "schema_version_format", f"_meta.schema_version 建议以 v 开头，当前为：{schema_version}")


def validate_duplicate_events(events, log_rows, json_file, company_name, stock_code):
    seen = {}

    for idx, event in enumerate(events, start=1):
        key = (
            event.get("event_type"),
            event.get("total_investment_amount"),
            event.get("share_price"),
            event.get("shares_issued_or_transferred"),
        )

        if key in seen and any(value is not None for value in key[1:]):
            add_log(
                log_rows,
                json_file,
                company_name,
                stock_code,
                "WARNING",
                "possible_duplicate_event",
                f"第 {idx} 条事件与第 {seen[key]} 条事件金额/价格/股数相同，疑似重复。",
            )
        else:
            seen[key] = idx


def validate_json_file(json_path: Path):
    log_rows = []

    json_file = json_path.name

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        add_log(log_rows, json_file, "", "", "ERROR", "json_parse", f"JSON 无法读取：{e}")
        return log_rows

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in data:
            add_log(log_rows, json_file, "", "", "ERROR", "top_level_field_missing", f"缺少顶层字段：{field}")

    company_name, stock_code = validate_company(data, log_rows, json_file)

    financing_events = data.get("financing_events", [])

    if not isinstance(financing_events, list):
        add_log(log_rows, json_file, company_name, stock_code, "ERROR", "financing_events_type", "financing_events 不是列表。")
        financing_events = []

    for idx, event in enumerate(financing_events, start=1):
        validate_event(event, log_rows, json_file, company_name, stock_code, idx)

    validate_duplicate_events(financing_events, log_rows, json_file, company_name, stock_code)
    validate_investor_overview(data, log_rows, json_file, company_name, stock_code)
    validate_shareholding_summary(data, log_rows, json_file, company_name, stock_code)
    validate_candidate_summary(data, log_rows, json_file, company_name, stock_code)
    validate_processing(data, log_rows, json_file, company_name, stock_code, len(financing_events))
    validate_meta(data, log_rows, json_file, company_name, stock_code)

    error_count = sum(1 for row in log_rows if row["level"] == "ERROR")
    warning_count = sum(1 for row in log_rows if row["level"] == "WARNING")

    if error_count == 0:
        if warning_count == 0:
            add_log(log_rows, json_file, company_name, stock_code, "PASS", "all_checks", "新版 PE/VC 事件池 JSON 校验通过。")
        else:
            add_log(log_rows, json_file, company_name, stock_code, "PASS", "structure_pass", "结构校验通过，但存在 WARNING，建议查看质量预警。")

    return log_rows


def main():
    VALIDATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    json_files = sorted(JSON_DIR.glob("*.json"))

    if not json_files:
        print(f"未找到 JSON 文件，请检查目录：{JSON_DIR}")
        return

    all_rows = []

    print(f"待校验 JSON 数量：{len(json_files)}")

    for json_path in json_files:
        print(f"正在校验：{json_path.name}")
        rows = validate_json_file(json_path)
        all_rows.extend(rows)

    with open(VALIDATION_LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "json_file",
            "company_name",
            "stock_code",
            "level",
            "check_item",
            "message",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    summary = {}

    for row in all_rows:
        json_file = row["json_file"]
        level = row["level"]

        if json_file not in summary:
            summary[json_file] = {
                "json_file": json_file,
                "PASS": 0,
                "INFO": 0,
                "WARNING": 0,
                "ERROR": 0,
            }

        if level in summary[json_file]:
            summary[json_file][level] += 1

    with open(VALIDATION_SUMMARY_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "json_file",
            "PASS",
            "INFO",
            "WARNING",
            "ERROR",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary.values())

    error_count = sum(1 for row in all_rows if row["level"] == "ERROR")
    warning_count = sum(1 for row in all_rows if row["level"] == "WARNING")
    info_count = sum(1 for row in all_rows if row["level"] == "INFO")

    print("\n新版 PE/VC 事件池 JSON 校验完成")
    print(f"校验日志：{VALIDATION_LOG_PATH}")
    print(f"校验汇总：{VALIDATION_SUMMARY_PATH}")
    print(f"ERROR 数量：{error_count}")
    print(f"WARNING 数量：{warning_count}")
    print(f"INFO 数量：{info_count}")

    if error_count == 0:
        print("结果：结构校验通过。若存在 WARNING，请根据 validation_log.csv 判断是否需要继续优化第六步。")
    else:
        print("结果：存在 ERROR，请根据 validation_log.csv 修改第六步输出或第七步校验规则。")


if __name__ == "__main__":
    main()