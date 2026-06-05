import csv
import json
import re
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

CANDIDATE_DIR = BASE_DIR / "outputs" / "week1_candidate_texts"
JSON_OUTPUT_DIR = BASE_DIR / "outputs" / "week1_sample_json"
EXTRACTION_LOG_PATH = BASE_DIR / "logs" / "extraction_log.csv"
COMPANY_LIST_PATH = BASE_DIR / "company_lists" / "week1_public_samples.csv"

MAX_EVENTS_PER_COMPANY = 8


# ============================================================
# 1. 关键词配置
# ============================================================

EVENT_ACTION_KEYWORDS = [
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
    "A+轮融资",
    "A轮融资",
    "B+轮融资",
    "B轮融资",
    "C+轮融资",
    "C轮融资",
    "战略投资",
    "战略融资",
]

INVESTOR_SIGNAL_KEYWORDS = [
    "创业投资",
    "创投",
    "股权投资",
    "投资基金",
    "私募基金",
    "产业基金",
    "合伙企业",
    "投资有限公司",
    "投资管理有限公司",
    "基金管理有限公司",
    "资产管理有限公司",
]

PEVC_ALIAS_KEYWORDS = [
    "创投",
    "创业投资",
    "股权投资",
    "投资基金",
    "产业基金",
    "私募基金",
    "基金",
    "深创投",
    "达晨",
    "东方富海",
    "金浦",
    "同华",
    "天健创投",
    "长泽创投",
    "稳正景明",
    "金浦临港基金",
    "金浦科创基金",
    "高新同华",
    "复星",
    "基石",
    "华金",
    "德朴",
    "睿泽",
    "中证投资",
    "源峰",
    "高瓴",
    "国药",
    "夏尔巴",
]

# 明确应该过滤的章节/语境
HARD_DROP_SECTION_KEYWORDS = [
    "股份支付",
    "股权激励",
    "其他权益工具投资",
    "经常性关联交易",
    "重大经常性关联交易",
    "一般经常性关联交易",
    "资金来源",
    "现金流量分析",
    "筹资活动现金流量分析",
    "募集资金使用情况",
    "募集资金用途",
    "股东权益总体分析",
    "主营业务成本",
    "商誉",
    "股利分配",
    "发行人板块定位情况",
    "发行人板块定位",
    "上市标准",
    "控股股东",
    "实际控制人",
    "一致行动人",
    "关联方",
    "董事",
    "监事",
    "高级管理人员",
    "承诺",
    "投资者保护",
]

# 有些标题比较泛，不能一刀切删除，但应降权
GENERIC_LOW_QUALITY_SECTIONS = [
    "科目具体情况及分析说明",
    "股本",
    "资本公积",
]

# 子公司、持股平台、非发行人本体相关主体
NON_ISSUER_ENTITY_HINTS = [
    "子公司",
    "深圳三协",
    "温州三联",
    "三连零部件",
    "黄山联鑫",
    "黄山广捷",
    "昆山谷捷",
    "上海亦我",
    "北京岚锋",
    "深圳岚锋",
    "香港岚锋",
    "岚烽管理",
    "岚沣管理",
    "共青城泽升",
    "知盛投资",
    "一路高飞",
]

TARGET_OR_ISSUER_NAMES = [
    "发行人",
    "公司",
    "谷捷有限",
    "黄山谷捷",
    "友升股份",
    "赛分科技",
    "赛分有限",
    "影石创新",
    "星图测控有限",
    "三联锻造",
    "常州三协",
    "云汉芯城",
]

BAD_EVIDENCE_KEYWORDS = [
    "前五大客户",
    "客户集中度",
    "营业收入",
    "采购总额",
    "主营业务",
    "毛利率",
    "原材料价格",
    "风险因素",
    "研发投入",
    "研发费用",
    "固定资产",
    "无形资产",
    "在建工程",
    "投资者关系",
    "利润分配",
    "同业竞争",
    "转贷",
    "贷款",
    "重大违法",
    "预计市值",
    "净利润",
    "净资产收益率",
]

IPO_STAGE_KEYWORDS = [
    "本次公开发行",
    "首次公开发行",
    "战略配售",
    "保荐人相关子公司",
    "跟投",
    "网下配售",
    "网上中签",
    "发行公告",
    "询价公告",
    "高级管理人员与核心员工",
    "专项资产管理计划",
    "员工资管计划",
]

NEGATIVE_KEYWORDS = [
    "不存在战略投资者",
    "不存在申报前十二个月内新增股东",
    "不存在私募投资基金",
    "不存在国有股份和外资股份",
    "不存在重大资产重组",
    "不存在委托基金",
    "亦不存在发起设立基金",
]

PREFERRED_SECTION_KEYWORDS = [
    "报告期内发行融资",
    "发行融资",
    "新增股东入股原因",
    "新增股东",
    "历史沿革",
    "股本演变",
    "股东变化",
    "股权转让",
    "股票发行",
    "定向发行",
    "股东权益",
    "发行人基本情况",
    "股本情况",
    "增资",
    "私募基金",
]

KNOWN_INVESTOR_ALIASES = [
    "稳正景明",
    "长泽创投",
    "高新同华",
    "天健创投",
    "丰利财富",
    "深创投",
    "达晨创投",
    "达晨创联基金",
    "东方富海",
    "金浦临港基金",
    "金浦科创基金",
    "上海骁墨",
    "中小企业基金",
    "国科瑞华",
    "CASREV FUND",
    "中科贵银",
    "南山富海",
    "珠海拓域",
    "富海节能",
    "临港投资",
    "鸿迪投资",
    "复星惟盈",
    "珠海睿泽创业投资基金",
    "领誉基石",
    "利得鑫投",
    "德朴投资",
    "华金创盈",
    "威明投资",
    "中证投资",
    "金石智娱",
    "赛格高技术",
    "上汽科技",
    "黄山佳捷",
    "源峰磐赛",
    "珠海峦恒",
    "高瓴祈睿",
    "国药中生",
    "圣成投资",
    "国药二期",
    "圣祁投资",
    "夏尔巴二期",
    "甘李药业",
    "吴征涛",
]


# ============================================================
# 2. 正则表达式
# ============================================================

DATE_PATTERN = re.compile(
    r"(?:19|20)\d{2}年\d{1,2}月\d{1,2}日|"
    r"(?:19|20)\d{2}年\d{1,2}月|"
    r"(?:19|20)\d{2}年"
)

AMOUNT_PATTERN = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万元|亿元|元)"
)

RATIO_PATTERN = re.compile(
    r"\d+(?:\.\d+)?\s*%"
)

SHARES_PATTERN = re.compile(
    r"(?:发行股数|发行数量|实际发行|拟发行|共发行|发行普通股|新增股份|转让股份|受让股份|股份)"
    r"[^，。；\n]{0,80}?"
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万股|股)"
)

ROUND_PATTERN = re.compile(
    r"(?:Pre-A轮|Pre-A|A\+轮|A轮|B\+轮|B轮|C\+轮|C轮|D轮|天使轮|种子轮|战略融资|战略投资)"
)

INVESTMENT_TOTAL_PATTERN = re.compile(
    r"(?:募集资金总额|拟募集资金总额|投资总额|出资总额|认购金额|增资金额|转让价款|交易金额|出资款|对价)"
    r"[^，。；\n]{0,80}?"
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万元|亿元|元)"
)

PRICE_PER_SHARE_PATTERN = re.compile(
    r"(?:每股认购价格|每股发行价格|每股价格|认购价格|发行价格|增发价格|转让价格|每股价格约为|增资价格|增资作价)"
    r"[^，。；\n]{0,80}?"
    r"\d+(?:\.\d+)?\s*(?:元/股|元/注册资本|元)"
)

VALUATION_PATTERN = re.compile(
    r"(?:投前估值|投后估值|整体投后估值)"
    r"[^，。；\n]{0,80}?"
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万元|亿元|元)"
)

INVESTOR_SUFFIX_PATTERN = re.compile(
    r"[\u4e00-\u9fa5A-Za-z0-9（）()·]{2,80}"
    r"(?:"
    r"创业投资基金(?:（有限合伙）|\(有限合伙\))?|"
    r"股权投资基金(?:（有限合伙）|\(有限合伙\))?|"
    r"产业投资基金(?:（有限合伙）|\(有限合伙\))?|"
    r"投资基金(?:（有限合伙）|\(有限合伙\))?|"
    r"创业投资合伙企业(?:（有限合伙）|\(有限合伙\))?|"
    r"股权投资合伙企业(?:（有限合伙）|\(有限合伙\))?|"
    r"投资合伙企业(?:（有限合伙）|\(有限合伙\))?|"
    r"企业管理咨询合伙企业(?:（有限合伙）|\(有限合伙\))?|"
    r"合伙企业(?:（有限合伙）|\(有限合伙\))?|"
    r"创业投资有限公司|"
    r"股权投资有限公司|"
    r"投资有限公司|"
    r"投资管理有限公司|"
    r"资产管理有限公司|"
    r"基金管理有限公司|"
    r"创投|"
    r"基金"
    r")"
)

ALIAS_TRANSACTION_PATTERN = re.compile(
    r"(?:公司向|发行人与|已收到|收到|向|由新股东|新股东)"
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·、和及与，,]{2,260}?)"
    r"(?:缴纳|缴付|签署|定向发行|发行|认购|增资|转让|受让)"
)

INVESTOR_RESPECTIVELY_PATTERN = re.compile(
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·、和及与，,]{2,260}?)"
    r"分别以"
)

INVESTOR_BEFORE_EXISTING_SHAREHOLDER_PATTERN = re.compile(
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·、和及与，,]{2,260}?)"
    r"与本次增资前公司股东"
)

TRANSFER_TO_PATTERN = re.compile(
    r"转让(?:予|给)([\u4e00-\u9fa5A-Za-z0-9（）()·、和及与，,]{2,160})"
)

TRANSFER_AGREEMENT_PATTERN = re.compile(
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·]{2,80})"
    r"(?:与|和)"
    r"([\u4e00-\u9fa5A-Za-z0-9（）()·]{2,80})"
    r"签署.*?(?:股权转让协议|股份转让协议)"
)


# ============================================================
# 3. 基础函数
# ============================================================

def normalize_stock_code(stock_code: str) -> str:
    stock_code = str(stock_code).strip()
    if stock_code.isdigit() and len(stock_code) < 6:
        return stock_code.zfill(6)
    return stock_code


def normalize_space(text: str) -> str:
    text = str(text)
    text = re.sub(r"!\[\]\(images/[^)]*\)", " ", text)
    text = re.sub(r"!\[\]\([^)]*\)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_all(pattern, text: str):
    return sorted(set(m.group(0).strip() for m in pattern.finditer(text)))


def parse_amount_to_number(raw: str):
    if not raw:
        return None

    raw = str(raw).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(亿元|万元|元)", raw)

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2)

    if unit == "亿元":
        return value * 100000000
    if unit == "万元":
        return value * 10000
    if unit == "元":
        return value

    return None


def parse_price_to_number(raw: str):
    if not raw:
        return None

    raw = str(raw).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元/股|元/注册资本|元)", raw)

    if not match:
        return None

    return float(match.group(1))


def parse_shares_to_number(raw: str):
    if not raw:
        return None

    raw = str(raw).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万股|股)", raw)

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2)

    if unit == "万股":
        return value * 10000
    if unit == "股":
        return value

    return None


def infer_exchange(stock_code: str, board: str) -> str:
    stock_code = normalize_stock_code(stock_code)

    if board == "北交所" or stock_code.startswith(("83", "87", "88", "92")):
        return "北京证券交易所"
    if stock_code.startswith(("60", "68")):
        return "上海证券交易所"
    if stock_code.startswith(("00", "30")):
        return "深圳证券交易所"

    return "未披露"


def infer_prospectus_version(title: str) -> str:
    if "申报稿" in str(title):
        return "申报稿"
    return "未披露"


def parse_metadata(text: str) -> dict:
    metadata = {}

    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key in [
                "sample_id",
                "company_name",
                "stock_code",
                "board",
                "source_markdown",
                "prospectus_title",
                "prospectus_url",
            ]:
                metadata[key] = value

    if "stock_code" in metadata:
        metadata["stock_code"] = normalize_stock_code(metadata["stock_code"])

    return metadata


def load_company_list():
    result = {}

    if not COMPANY_LIST_PATH.exists():
        return result

    with open(COMPANY_LIST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            if not sample_id:
                continue

            stock_code = normalize_stock_code(row.get("stock_code", ""))

            result[sample_id] = {
                "company_name": row.get("company_name", "").strip(),
                "stock_code": stock_code,
                "board": row.get("board", "").strip(),
                "listing_date": row.get("listing_date", "").strip(),
                "prospectus_title": row.get("prospectus_title", "").strip(),
                "prospectus_url": row.get("prospectus_url", "").strip(),
                "prospectus_date": row.get("prospectus_date", "").strip(),
                "download_status": row.get("download_status", "").strip() or "success",
                "parse_status": row.get("parse_status", "").strip() or "success",
                "locate_status": row.get("locate_status", "").strip() or "success",
            }

    return result


def split_candidate_snippets(text: str):
    blocks = re.findall(
        r"## 候选片段\s+(\d+)(.*?)(?=## 候选片段|\Z)",
        text,
        flags=re.S,
    )

    snippets = []

    for snippet_id, block in blocks:
        matched_keywords = ""
        source_sections = ""
        body = ""

        keyword_match = re.search(r"- matched_keywords:\s*(.+)", block)
        section_match = re.search(r"- source_sections:\s*(.+)", block)
        body_match = re.search(r"```text\s*(.*?)\s*```", block, flags=re.S)

        if keyword_match:
            matched_keywords = keyword_match.group(1).strip()
        if section_match:
            source_sections = section_match.group(1).strip()
        if body_match:
            body = body_match.group(1).strip()

        if body:
            snippets.append({
                "snippet_id": int(snippet_id),
                "matched_keywords": matched_keywords,
                "source_sections": source_sections,
                "text": body,
            })

    return snippets


def split_by_markdown_headings(text: str):
    lines = text.splitlines()
    chunks = []
    current_heading = "未定位"
    current_lines = []

    for line in lines:
        if re.match(r"^\s*#{1,6}\s+", line):
            if current_lines:
                chunks.append({
                    "heading": current_heading,
                    "text": "\n".join(current_lines),
                })
                current_lines = []

            current_heading = re.sub(r"^\s*#{1,6}\s+", "", line).strip()
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append({
            "heading": current_heading,
            "text": "\n".join(current_lines),
        })

    if not chunks:
        return [{"heading": "未定位", "text": text}]

    return chunks


def split_event_subchunks(chunk_text: str):
    pattern = (
        r"(?=(?:①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩)\s*(?:19|20)\d{2}年|"
        r"(?:\(|（)[一二三四五六七八九十]+(?:\)|）)\s*(?:19|20)\d{2}年|"
        r"(?:\d+、)\s*(?:19|20)\d{2}年)"
    )
    parts = re.split(pattern, chunk_text)
    cleaned = [p.strip() for p in parts if p and p.strip()]
    return cleaned if cleaned else [chunk_text]


# ============================================================
# 4. 投资方识别与清洗
# ============================================================

def clean_investor_name(name: str) -> str:
    name = normalize_space(name)

    prefixes = [
        "公司向",
        "向",
        "由新股东",
        "新股东",
        "股东",
        "任",
        "为",
        "系",
        "以及",
        "和",
        "及",
        "与",
        "在",
        "已收到",
        "收到",
        "转让给",
        "转让予",
        "受让方",
        "新增股东",
        "认购人",
        "本次增资前公司股东",
        "新增注册资本由",
        "约定",
        "外部投资者",
        "月外部投资者",
        "4月外部投资者",
        "2020年9月外部投资者",
        "通过",
        "其管理人",
        "执行事务合伙人",
        "有限合伙人",
        "普通合伙人",
    ]

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                changed = True

    suffix_noise = [
        "定向",
        "公开",
        "发行",
        "认购",
        "增资",
        "受让",
        "转让",
        "缴纳",
        "缴付",
        "出资",
        "缴纳的出资款",
        "缴付的出资款",
        "主营业务为创业投资",
        "就上述股权转让事宜",
        "的承诺函",
    ]

    for noise in suffix_noise:
        if name.endswith(noise):
            name = name[: -len(noise)].strip()

    name = name.strip("，。、；：:（）()[]【】 ")

    if "（有限合伙" in name and "）" not in name:
        name = name + "）"

    return name


def is_noise_investor_name(name: str) -> bool:
    if not name:
        return True

    bad_parts = [
        "注册资本",
        "资本公积",
        "资本化",
        "价格",
        "取得了中国证券投资基金",
        "私募投资基金",
        "不存在私募投资基金",
        "不特定合格投资者",
        "本合伙企业",
        "全体合伙人",
        "万元将持有",
        "发行人股东中不存在",
        "出资情况",
        "验资报告",
        "工商登记",
        "募集资金",
        "基金所投资",
        "入股云汉有限时的投资",
        "年入股",
        "转让给",
        "受让了",
        "曾用名为",
        "刘靖康间接持股",
        "权益的合伙企业",
        "承担",
        "公司员工",
        "的承诺函",
        "资金来源",
        "发行的",
        "定增对象",
        "核心员工",
        "公司董事",
        "购买并持有持股平台",
        "已办理基金",
        "完成私募基金",
        "办理完成私募基金",
        "不存在委托基金",
        "亦不存在发起设立基金",
        "13名股东",
        "13日完成",
        "4日完成",
        "日在中国证券投资基金",
    ]

    if any(bad in name for bad in bad_parts):
        return True

    if name in TARGET_OR_ISSUER_NAMES:
        return True

    bad_short_words = {
        "承担",
        "公司员工",
        "承诺函",
        "合伙人",
        "发行人",
        "实际控制人",
        "关联方",
        "发行的",
        "核心员工",
        "定增对象",
        "不存在委托基金",
    }

    if name in bad_short_words:
        return True

    if len(name) < 2 or len(name) > 80:
        return True

    return False


def is_institution_name(name: str) -> bool:
    words = [
        "基金",
        "创投",
        "投资",
        "资本",
        "合伙企业",
        "资产管理",
        "投资管理",
        "稳正景明",
        "长泽创投",
        "高新同华",
        "天健创投",
        "丰利财富",
        "东方富海",
        "金浦",
        "上海骁墨",
        "深创投",
        "达晨",
        "淡马锡",
        "韦豪",
        "复星",
        "基石",
        "华金",
        "德朴",
        "知盛",
        "睿泽",
        "领誉",
        "利得",
        "金石",
        "中证投资",
        "赛格高技术",
        "上汽科技",
        "源峰磐赛",
        "珠海峦恒",
        "高瓴祈睿",
        "国药中生",
        "圣成投资",
        "国药二期",
        "圣祁投资",
        "夏尔巴二期",
        "甘李药业",
    ]
    return any(word in name for word in words)


def is_chinese_person_name(name: str) -> bool:
    if not re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", name):
        return False

    bad_names = {
        "公司",
        "发行人",
        "股东",
        "董事",
        "监事",
        "万元",
        "普通股",
        "认购人",
        "注册",
        "资本",
        "基金",
        "创投",
    }

    return name not in bad_names


def split_name_list(raw: str):
    raw = normalize_space(raw)
    raw = raw.replace("以及", "、").replace("及", "、").replace("和", "、").replace("与", "、")
    raw = raw.replace(",", "、").replace("，", "、")
    parts = []

    for p in raw.split("、"):
        name = clean_investor_name(p)
        if name:
            parts.append(name)

    return parts


def extract_investor_names(text: str):
    names = []

    # 1. 带明显机构后缀的名称
    for raw in find_all(INVESTOR_SUFFIX_PATTERN, text):
        raw = clean_investor_name(raw)

        # 如果正则抓到了“稳正景明和长泽创投”这种合并名称，继续拆分
        if any(connector in raw for connector in ["、", "和", "与", "及", "，", ","]):
            candidates = split_name_list(raw)
        else:
            candidates = [raw]

        for name in candidates:
            if not is_noise_investor_name(name) and (is_institution_name(name) or is_chinese_person_name(name)):
                names.append(name)

    # 2. 句式抽取
    for pattern in [
        ALIAS_TRANSACTION_PATTERN,
        INVESTOR_RESPECTIVELY_PATTERN,
        INVESTOR_BEFORE_EXISTING_SHAREHOLDER_PATTERN,
        TRANSFER_TO_PATTERN,
    ]:
        for match in pattern.finditer(text):
            raw = match.group(1)
            for name in split_name_list(raw):
                if is_noise_investor_name(name):
                    continue
                if is_institution_name(name) or is_chinese_person_name(name):
                    names.append(name)

    # 3. 股权转让协议双方
    for match in TRANSFER_AGREEMENT_PATTERN.finditer(text):
        for raw in [match.group(1), match.group(2)]:
            name = clean_investor_name(raw)
            if is_noise_investor_name(name):
                continue
            if is_institution_name(name) or is_chinese_person_name(name):
                names.append(name)

    # 4. 已知简称补充
    for alias in KNOWN_INVESTOR_ALIASES:
        if alias in text:
            names.append(alias)

    unique = []
    seen = set()

    for name in names:
        name = clean_investor_name(name)

        if not name:
            continue
        if is_noise_investor_name(name):
            continue
        if name in TARGET_OR_ISSUER_NAMES:
            continue
        if name not in seen:
            unique.append(name)
            seen.add(name)

    return unique


def infer_investor_type(name: str, evidence_text: str = "") -> str:
    if any(k in name for k in ["员工持股", "持股平台", "员工资管"]):
        return "员工持股平台"

    if any(k in name for k in ["政府", "国资", "财政", "引导基金"]):
        return "政府基金"

    if any(k in name for k in PEVC_ALIAS_KEYWORDS):
        return "VC/PE"

    if any(k in name for k in ["产业", "实业", "控股", "淡马锡", "上汽科技", "赛格高技术", "甘李药业"]):
        return "产业资本"

    if any(k in name for k in ["投资", "资本", "合伙企业", "资产管理", "上海骁墨", "汇智同裕", "知盛投资", "德朴投资"]):
        return "无法判断"

    if is_chinese_person_name(name):
        return "自然人"

    return "无法判断"


def infer_is_pevc(investor_type: str, name: str, evidence_text: str = "") -> str:
    if investor_type == "VC/PE":
        return "yes"

    if investor_type in ["自然人", "员工持股平台", "产业资本", "政府基金"]:
        return "no"

    if any(k in name for k in ["基金", "创投", "股权投资"]):
        return "yes"

    if "私募基金" in evidence_text and name in evidence_text:
        return "yes"

    return "uncertain"


def extract_parallel_investor_amounts(evidence_text: str, investor_names: list):
    """
    处理：
    A、B和C分别以7,000万元、3,000万元和1,500万元认购……
    """
    result = {}

    pattern = re.compile(
        r"([\u4e00-\u9fa5A-Za-z0-9（）()·、和及与，,]{2,260}?)"
        r"分别以"
        r"(.{0,220}?)"
        r"(?:认购|增资|受让|取得)"
    )

    for match in pattern.finditer(evidence_text):
        names_raw = match.group(1)
        amounts_raw = match.group(2)

        names = [
            name for name in split_name_list(names_raw)
            if name in investor_names
        ]

        amounts = find_all(AMOUNT_PATTERN, amounts_raw)
        amounts_num = [parse_amount_to_number(a) for a in amounts]
        amounts_num = [a for a in amounts_num if a is not None]

        if len(names) == len(amounts_num):
            for name, amount in zip(names, amounts_num):
                result[name] = amount

    return result


def extract_investor_amount(name: str, evidence_text: str, amount_map=None):
    if amount_map and name in amount_map:
        return amount_map[name]

    if not name or name not in evidence_text:
        return None

    pattern = re.compile(
        re.escape(name)
        + r"[^。；，,]{0,80}?"
        + r"(?:出资|认购|增资|投资|缴纳|以现金)"
        + r"[^。；，,]{0,50}?"
        + r"(\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万元|亿元|元))"
    )

    match = pattern.search(evidence_text)

    if not match:
        return None

    return parse_amount_to_number(match.group(1))


def extract_investor_ratio(name: str, evidence_text: str):
    pos = evidence_text.find(name)
    if pos < 0:
        return None

    window = evidence_text[pos: pos + 180]
    ratio_match = RATIO_PATTERN.search(window)

    if ratio_match:
        raw = ratio_match.group(0).replace("%", "")
        try:
            return float(raw)
        except ValueError:
            return None

    return None


def build_investors(investor_names: list, evidence_text: str):
    investors = []
    amount_map = extract_parallel_investor_amounts(evidence_text, investor_names)

    for name in investor_names:
        investor_type = infer_investor_type(name, evidence_text)

        investors.append({
            "investor_original_name": name,
            "investor_short_name": name,
            "investor_type": investor_type,
            "is_pevc": infer_is_pevc(investor_type, name, evidence_text),
            "investment_amount": extract_investor_amount(name, evidence_text, amount_map),
            "shares_acquired": None,
            "shareholding_ratio_after_event": extract_investor_ratio(name, evidence_text),
            "exit_status_before_ipo": "无法判断",
        })

    return investors


# ============================================================
# 5. 过滤与证据
# ============================================================

def has_action(text: str) -> bool:
    return any(k in text for k in EVENT_ACTION_KEYWORDS)


def has_number_signal(text: str) -> bool:
    return bool(
        find_all(INVESTMENT_TOTAL_PATTERN, text)
        or find_all(PRICE_PER_SHARE_PATTERN, text)
        or find_all(SHARES_PATTERN, text)
        or find_all(RATIO_PATTERN, text)
        or find_all(AMOUNT_PATTERN, text)
    )


def is_bad_evidence(text: str) -> bool:
    if any(k in text for k in NEGATIVE_KEYWORDS):
        return True

    if any(k in text for k in IPO_STAGE_KEYWORDS):
        return True

    if "不特定合格投资者" in text:
        return True

    if any(k in text for k in BAD_EVIDENCE_KEYWORDS):
        strong = any(good in text for good in ["股票发行", "定向发行", "股权转让", "增资", "出资款", "投资协议"])
        if not strong:
            return True

    return False


def should_drop_event_by_section(source_section: str, evidence_text: str) -> bool:
    combined = source_section + " " + evidence_text[:800]

    if "发行人板块定位情况" in combined or "发行人板块定位" in combined:
        return True

    # 股份支付、资金来源、关联交易、现金流、商誉等章节不进入事件池
    if any(k in combined for k in HARD_DROP_SECTION_KEYWORDS):
        allow = any(good in combined for good in [
            "新增股东入股原因",
            "历史沿革",
            "股本演变",
            "股票发行",
            "定向发行",
            "股权转让",
            "报告期内第一次股权转让",
            "报告期内第二次增资",
        ])

        if not allow:
            return True

    # 泛化章节如果只是财务科目解释，且没有硬融资证据，则过滤
    if any(k in source_section for k in GENERIC_LOW_QUALITY_SECTIONS):
        hard_financing = any(k in evidence_text for k in ["定向发行", "股票发行", "募集资金总额", "每股价格", "每股发行价格"])
        if not hard_financing:
            return True

    # 非发行人本体或子公司/平台类事件，除非明确是外部机构投资者进入发行人
    if any(k in combined for k in NON_ISSUER_ENTITY_HINTS):
        has_external_investor = any(k in evidence_text for k in PEVC_ALIAS_KEYWORDS)
        has_hard_financing = any(k in evidence_text for k in ["股票发行", "定向发行", "投资协议", "认购价格", "募集资金总额", "新增注册资本"])

        if not (has_external_investor and has_hard_financing):
            return True

    return False


def is_weak_or_non_issuer_context(source_section: str, evidence_text: str) -> bool:
    combined = source_section + " " + evidence_text[:800]

    if should_drop_event_by_section(source_section, evidence_text):
        return True

    if any(k in combined for k in ["本次公开发行", "战略配售", "上市标准"]):
        return True

    return False


def get_primary_source_section(source_sections: str, chunk_heading: str):
    if chunk_heading and chunk_heading != "未定位":
        return chunk_heading

    if not source_sections:
        return "未定位"

    parts = [p.strip() for p in source_sections.split(",") if p.strip()]

    for keyword in PREFERRED_SECTION_KEYWORDS:
        for part in parts:
            if keyword in part:
                return part

    return parts[0] if parts else "未定位"


def make_evidence_text(chunk_text: str, max_len: int = 1800):
    text = normalize_space(chunk_text)

    if len(text) <= max_len:
        return text

    positions = []

    for keyword in EVENT_ACTION_KEYWORDS:
        pos = text.find(keyword)
        if pos >= 0:
            positions.append(pos)

    focus = min(positions) if positions else 0
    half = max_len // 2
    start = max(focus - half, 0)
    end = min(focus + half, len(text))

    evidence = text[start:end]

    if start > 0:
        evidence = "..." + evidence
    if end < len(text):
        evidence = evidence + "..."

    return evidence


# ============================================================
# 6. 事件字段抽取与评分
# ============================================================

def detect_event_type(text: str):
    has_capital = any(k in text for k in ["增资", "认购", "定向发行", "股票发行", "发行股票", "募集资金总额", "出资款"])
    has_transfer = any(k in text for k in ["股权转让", "股份转让", "转让协议", "受让"])

    if has_capital and has_transfer:
        return "增资及股权转让"
    if has_capital:
        return "增资"
    if has_transfer:
        return "股权转让"
    return "其他"


def extract_disclosed_round(text: str) -> str:
    match = ROUND_PATTERN.search(text)
    if match:
        return match.group(0)
    return "未披露"


def extract_event_date(text: str):
    dates = find_all(DATE_PATTERN, text)
    if dates:
        return dates[0]
    return "未披露"


def infer_date_type(text: str):
    if any(k in text for k in ["缴纳的出资款", "收到", "出资款"]):
        return "出资到账日"
    if any(k in text for k in ["协议", "签署"]):
        return "协议签署日"
    if any(k in text for k in ["工商变更", "完成工商", "办理工商", "换发营业执照"]):
        return "工商变更日"
    if any(k in text for k in ["股东大会", "股东会", "董事会", "临时股东大会", "审议通过"]):
        return "股东会决议日"
    return "未说明"


def extract_total_investment_amount(text: str):
    values = find_all(INVESTMENT_TOTAL_PATTERN, text)

    preferred = [
        v for v in values
        if any(k in v for k in ["募集资金总额", "拟募集资金总额", "出资款", "认购金额", "增资金额", "交易金额", "转让价款", "对价"])
    ]

    if preferred:
        return parse_amount_to_number(preferred[0])

    match = re.search(r"分别以(.{0,220}?)(?:认购|增资|取得)", text)
    if match:
        part = match.group(1)
        amounts = find_all(AMOUNT_PATTERN, part)
        nums = [parse_amount_to_number(a) for a in amounts]
        nums = [n for n in nums if n is not None]
        if nums:
            return sum(nums)

    return None


def extract_share_price(text: str):
    values = find_all(PRICE_PER_SHARE_PATTERN, text)
    if not values:
        return None

    parsed = []
    for value in values:
        number = parse_price_to_number(value)
        if number is not None:
            parsed.append(number)

    if not parsed:
        return None

    # 同一段同时有员工激励 1 元和外部融资价格 29.13 元时，优先取较高价格
    return max(parsed)


def extract_shares_issued_or_transferred(text: str):
    values = find_all(SHARES_PATTERN, text)
    if not values:
        return None
    return parse_shares_to_number(values[0])


def extract_valuation(text: str, valuation_type: str):
    values = find_all(VALUATION_PATTERN, text)

    if not values:
        return None

    if valuation_type == "pre":
        pre_values = [v for v in values if "投前估值" in v]
        return parse_amount_to_number(pre_values[0]) if pre_values else None

    if valuation_type == "post":
        post_values = [v for v in values if "投后估值" in v or "整体投后估值" in v]
        return parse_amount_to_number(post_values[0]) if post_values else None

    return None


def build_valuation_basis(text: str):
    values = find_all(VALUATION_PATTERN, text)
    if values:
        return "；".join(values)
    return "招股书未披露投前估值或投后估值"


def detect_event_nature(text: str, source_section: str, investors: list):
    combined = source_section + " " + text

    if "代持" in combined:
        return "代持解除"

    if "设立" in source_section and "注册资本" in text:
        return "企业设立"

    if any(k in combined for k in ["股票发行", "股票定向发行", "定向发行"]):
        if any(inv.get("is_pevc") == "yes" for inv in investors):
            return "外部投资者进入"
        return "历史增资"

    if "增资" in combined:
        if any(inv.get("is_pevc") == "yes" for inv in investors):
            return "外部投资者进入"
        return "历史增资"

    if any(k in combined for k in ["股权转让", "股份转让", "转让协议", "受让"]):
        if "0 元" in text or "零对价" in text or "架构调整" in text:
            return "股权结构调整"
        if any(inv.get("is_pevc") == "yes" for inv in investors):
            return "外部投资者进入"
        return "股权转让"

    return "其他"


def detect_pevc_relevance(event_nature: str, investors: list, evidence_text: str):
    if event_nature in ["代持解除", "股权结构调整", "企业设立"]:
        return "related"

    if any(inv.get("is_pevc") == "yes" for inv in investors):
        if any(k in evidence_text for k in ["增资", "认购", "投资协议", "股票发行", "定向发行", "股权转让"]):
            return "core"

    if any(k in evidence_text for k in ["私募基金", "创业投资", "创投", "股权投资基金"]):
        return "core"

    if event_nature in ["历史增资", "股权转让"]:
        return "related"

    return "uncertain"


def confidence_label(evidence_text: str, investors: list):
    score = 0

    if investors:
        score += 1
    if extract_total_investment_amount(evidence_text) is not None:
        score += 1
    if extract_share_price(evidence_text) is not None:
        score += 1
    if has_action(evidence_text):
        score += 1

    if score >= 3:
        return "high"
    if score == 2:
        return "medium"
    return "low"


def score_event(event: dict):
    source_section = event.get("source_section", "")
    evidence_text = event.get("evidence_text", "")
    event_nature = event.get("event_nature", "")

    if should_drop_event_by_section(source_section, evidence_text):
        return -100

    score = 0

    if event.get("pevc_relevance") == "core":
        score += 6
    elif event.get("pevc_relevance") == "related":
        score += 2

    if event.get("total_investment_amount") is not None:
        score += 2
    if event.get("share_price") is not None:
        score += 2
    if event.get("shares_issued_or_transferred") is not None:
        score += 1
    if event.get("investors"):
        score += 2

    if any(k in source_section for k in ["股票发行", "定向发行", "增资", "股权转让", "历史沿革", "股本演变", "新增股东"]):
        score += 2

    if event_nature == "外部投资者进入":
        score += 4
    elif event_nature == "历史增资":
        score += 2
    elif event_nature in ["代持解除", "股权结构调整", "企业设立"]:
        score -= 2

    if any(k in source_section for k in ["股份支付", "其他权益工具投资", "经常性关联交易", "资金来源", "一致行动人", "实际控制人", "现金流量", "商誉", "股利分配", "发行人板块定位"]):
        score -= 10

    if any(k in source_section for k in GENERIC_LOW_QUALITY_SECTIONS):
        score -= 3

    if event.get("investors") and any(inv.get("is_pevc") == "yes" for inv in event.get("investors", [])):
        score += 2

    return score


# ============================================================
# 7. 单片段抽取
# ============================================================

def extract_events_from_snippet(snippet: dict, source_file: str):
    text = snippet.get("text", "")
    source_sections = snippet.get("source_sections", "")
    events = []

    chunks = split_by_markdown_headings(text)

    for chunk in chunks:
        chunk_heading = chunk.get("heading", "未定位")
        chunk_text = chunk.get("text", "")
        subchunks = split_event_subchunks(chunk_text)

        for subchunk_text in subchunks:
            raw_text = normalize_space(subchunk_text)

            if not raw_text:
                continue

            source_section = get_primary_source_section(source_sections, chunk_heading)

            if should_drop_event_by_section(source_section, raw_text):
                continue

            if not has_action(raw_text):
                continue

            if not has_number_signal(raw_text):
                continue

            if is_bad_evidence(raw_text):
                continue

            evidence_text = make_evidence_text(raw_text)

            if is_weak_or_non_issuer_context(source_section, evidence_text):
                continue

            investor_names = extract_investor_names(evidence_text)
            investors = build_investors(investor_names, evidence_text)

            event_type = detect_event_type(evidence_text)
            event_nature = detect_event_nature(evidence_text, source_section, investors)
            pevc_relevance = detect_pevc_relevance(event_nature, investors, evidence_text)

            # 没有机构投资方、没有金额/价格的普通自然人转让，不进入事件池
            if event_nature in ["股权转让", "股权结构调整", "代持解除"] and not any(inv.get("is_pevc") == "yes" for inv in investors):
                if extract_total_investment_amount(evidence_text) is None and extract_share_price(evidence_text) is None:
                    continue

            event = {
                "event_order": 0,
                "event_date": extract_event_date(evidence_text),
                "date_type": infer_date_type(evidence_text),
                "event_type": event_type,
                "event_nature": event_nature,
                "pevc_relevance": pevc_relevance,

                "disclosed_round": extract_disclosed_round(evidence_text),
                "inferred_round": "",
                "round_inference_basis": "",

                "total_investment_amount": extract_total_investment_amount(evidence_text),
                "currency": "CNY",
                "share_price": extract_share_price(evidence_text),
                "shares_issued_or_transferred": extract_shares_issued_or_transferred(evidence_text),
                "pre_money_valuation": extract_valuation(evidence_text, "pre"),
                "post_money_valuation": extract_valuation(evidence_text, "post"),
                "valuation_basis": build_valuation_basis(evidence_text),

                "investors": investors,
                "investor_disclosure_status": "已识别投资方名称" if investors else "未识别到投资方名称",

                "source_section": source_section,
                "source_page": "未定位",
                "evidence_text": evidence_text,
                "confidence": confidence_label(evidence_text, investors),

                "source_candidate_file": source_file,
                "raw_amount_candidates": find_all(AMOUNT_PATTERN, evidence_text),
                "raw_price_candidates": find_all(PRICE_PER_SHARE_PATTERN, evidence_text),
                "raw_share_candidates": find_all(SHARES_PATTERN, evidence_text),
                "raw_ratio_candidates": find_all(RATIO_PATTERN, evidence_text),
            }

            event["_score"] = score_event(event)

            if event["_score"] >= 4:
                events.append(event)

    return events


# ============================================================
# 8. 汇总
# ============================================================

def collect_candidate_evidence_summary(snippets):
    all_text = "\n".join(snippet.get("text", "") for snippet in snippets)
    all_text_norm = normalize_space(all_text)

    detected_keywords = []
    for keyword in EVENT_ACTION_KEYWORDS + INVESTOR_SIGNAL_KEYWORDS:
        if keyword in all_text_norm and keyword not in detected_keywords:
            detected_keywords.append(keyword)

    investor_names = extract_investor_names(all_text_norm)
    amounts = find_all(AMOUNT_PATTERN, all_text_norm)[:30]
    ratios = find_all(RATIO_PATTERN, all_text_norm)[:30]

    top_candidate_evidence = []

    for snippet in snippets:
        chunks = split_by_markdown_headings(snippet.get("text", ""))

        for chunk in chunks:
            heading = chunk.get("heading", "")
            text = normalize_space(chunk.get("text", ""))

            if should_drop_event_by_section(heading, text):
                continue
            if not has_action(text):
                continue
            if not has_number_signal(text):
                continue
            if is_bad_evidence(text):
                continue

            evidence = make_evidence_text(text, max_len=700)
            key = evidence[:200]

            if evidence and key not in [e[:200] for e in top_candidate_evidence]:
                top_candidate_evidence.append(evidence)

    return {
        "has_candidate_text": len(snippets) > 0,
        "candidate_snippet_count": len(snippets),
        "detected_keywords": detected_keywords[:50],
        "detected_investor_names": investor_names[:40],
        "detected_amount_or_price_values": amounts,
        "detected_ratio_values": ratios,
        "top_candidate_evidence": top_candidate_evidence[:8],
    }


def is_valid_overview_investor(name: str) -> bool:
    if not name:
        return False

    name = clean_investor_name(name)

    if is_noise_investor_name(name):
        return False

    if name in TARGET_OR_ISSUER_NAMES:
        return False

    if any(bad in name for bad in [
        "不存在",
        "完成私募基金",
        "办理完成私募基金",
        "已办理基金",
        "发起设立基金",
        "13名股东",
        "13日",
        "4日",
        "日完成",
        "其管理人",
        "执行事务合伙人",
        "有限合伙人",
        "普通合伙人",
        "通过",
    ]):
        return False

    # overview 只收机构或明确已知投资方，不收普通自然人噪声
    if is_institution_name(name):
        return True

    if name in KNOWN_INVESTOR_ALIASES:
        return True

    return False


def build_investor_overview(events, candidate_summary):
    investor_map = {}

    for event in events:
        for investor in event.get("investors", []):
            name = clean_investor_name(investor.get("investor_original_name", ""))

            if not is_valid_overview_investor(name):
                continue

            if name not in investor_map:
                investor_map[name] = {
                    "investor_original_name": name,
                    "investor_short_name": name,
                    "investor_type": investor.get("investor_type", "无法判断"),
                    "is_pevc": investor.get("is_pevc", "uncertain"),
                    "event_count": 0,
                    "related_event_orders": [],
                }

            investor_map[name]["event_count"] += 1
            investor_map[name]["related_event_orders"].append(event.get("event_order"))

    # 候选摘要只补充干净机构投资方
    for name in candidate_summary.get("detected_investor_names", []):
        name = clean_investor_name(name)

        if name in investor_map:
            continue

        if not is_valid_overview_investor(name):
            continue

        investor_type = infer_investor_type(name)
        investor_map[name] = {
            "investor_original_name": name,
            "investor_short_name": name,
            "investor_type": investor_type,
            "is_pevc": infer_is_pevc(investor_type, name),
            "event_count": 0,
            "related_event_orders": [],
        }

    return list(investor_map.values())


def collect_shareholding_and_exit_summary(snippets):
    result = []

    keywords_map = {
        "pre_ipo_shareholding": ["前十名股东", "发行前股本结构", "本次发行前", "股东情况", "持股比例"],
        "lockup_arrangement": ["锁定", "限售", "减持", "股份锁定", "锁定期限"],
        "exit_arrangement": ["退出", "转让", "减持", "退出安排", "上市前退出"],
        "private_fund_check": ["私募基金", "基金备案", "基金管理人"],
    }

    seen = set()

    for snippet in snippets:
        source_sections = snippet.get("source_sections", "")
        chunks = split_by_markdown_headings(snippet.get("text", ""))

        for chunk in chunks:
            heading = chunk.get("heading", "未定位")
            text = normalize_space(chunk.get("text", ""))

            combined = heading + " " + text[:1200]

            for summary_type, keywords in keywords_map.items():
                if any(k in combined for k in keywords):
                    evidence = make_evidence_text(text, max_len=900)
                    key = summary_type + "::" + heading + "::" + evidence[:150]

                    if key in seen:
                        continue

                    seen.add(key)

                    result.append({
                        "summary_type": summary_type,
                        "source_section": get_primary_source_section(source_sections, heading),
                        "source_page": "未定位",
                        "evidence_text": evidence,
                    })

    return result[:15]


def build_processing_section(company_info, snippets, events, candidate_summary):
    extracted_event_count = len(events)

    return {
        "download_status": company_info.get("download_status") or "success",
        "parse_status": company_info.get("parse_status") or "success",
        "locate_status": company_info.get("locate_status") or "success",
        "extract_status": "success" if extracted_event_count > 0 else "partial",
        "review_status": "unchecked",
        "candidate_snippet_count": len(snippets),
        "extracted_event_count": extracted_event_count,
        "candidate_signal_count": len(candidate_summary.get("detected_keywords", [])),
        "notes": (
            "第六步从第五步定位章节中抽取 PE/VC 研究相关的股权融资事件池。"
            "v5 版本加强了重复事件去重、投资方名称清洗、低质量章节过滤和并列投资金额识别；"
            "未披露字段不编造，保留为 null 或“未披露”。"
        ),
    }


# ============================================================
# 9. 构建 JSON
# ============================================================

def event_quality_score_for_dedup(event: dict):
    score = event.get("_score", 0)

    # 优先保留有投资方的
    if event.get("investors"):
        score += 5

    # 优先保留 source_section 更具体的
    section = event.get("source_section", "")
    if any(k in section for k in ["股票发行", "定向发行", "增资", "股权转让", "新增股东入股原因"]):
        score += 4

    # 降低泛化财务科目说明
    if any(k in section for k in GENERIC_LOW_QUALITY_SECTIONS):
        score -= 4

    if event.get("confidence") == "high":
        score += 2

    return score


def deduplicate_events(all_events):
    best_by_key = {}

    for event in all_events:
        event_type = event.get("event_type", "")
        amount = event.get("total_investment_amount")
        price = event.get("share_price")
        shares = event.get("shares_issued_or_transferred")
        date = event.get("event_date", "")

        investor_key = "|".join(
            sorted(
                investor.get("investor_original_name", "")
                for investor in event.get("investors", [])
                if investor.get("investor_original_name", "")
            )
        )

        # 金额、价格、股数高度相似的发行/增资事件，视为同一事件
        if amount is not None or price is not None or shares is not None:
            key = (
                "financial",
                round(amount, 2) if isinstance(amount, (int, float)) else None,
                round(price, 6) if isinstance(price, (int, float)) else None,
                round(shares, 2) if isinstance(shares, (int, float)) else None,
            )
        else:
            evidence_key = event.get("evidence_text", "")[:180]
            key = (
                "textual",
                event_type,
                date,
                investor_key,
                evidence_key,
            )

        if key not in best_by_key:
            best_by_key[key] = event
        else:
            old = best_by_key[key]
            if event_quality_score_for_dedup(event) > event_quality_score_for_dedup(old):
                best_by_key[key] = event

    return list(best_by_key.values())


def build_company_json(candidate_file: Path, company_map: dict):
    text = candidate_file.read_text(encoding="utf-8", errors="ignore")

    metadata = parse_metadata(text)
    snippets = split_candidate_snippets(text)

    sample_id = metadata.get("sample_id", candidate_file.stem.split("_")[0])
    company_info = company_map.get(sample_id, {})

    company_name = company_info.get("company_name") or metadata.get("company_name", "")
    stock_code = normalize_stock_code(company_info.get("stock_code") or metadata.get("stock_code", ""))
    board = company_info.get("board") or metadata.get("board", "")
    listing_date = company_info.get("listing_date") or "未披露"
    prospectus_title = company_info.get("prospectus_title") or metadata.get("prospectus_title", "")
    prospectus_url = company_info.get("prospectus_url") or metadata.get("prospectus_url", "")
    prospectus_date = company_info.get("prospectus_date") or "未披露"

    all_events = []

    for snippet in snippets:
        events = extract_events_from_snippet(
            snippet,
            str(candidate_file.relative_to(BASE_DIR)).replace("\\", "/"),
        )
        all_events.extend(events)

    unique_events = deduplicate_events(all_events)

    # 优先保留核心 PE/VC 和外部投资者进入事件
    unique_events.sort(key=lambda e: event_quality_score_for_dedup(e), reverse=True)
    unique_events = unique_events[:MAX_EVENTS_PER_COMPANY]
    unique_events.sort(key=lambda e: e.get("event_date", ""))

    for idx, event in enumerate(unique_events, start=1):
        event["event_order"] = idx
        event.pop("_score", None)

    candidate_summary = collect_candidate_evidence_summary(snippets)
    investor_overview = build_investor_overview(unique_events, candidate_summary)
    shareholding_and_exit_summary = collect_shareholding_and_exit_summary(snippets)

    result = {
        "company": {
            "company_name": company_name,
            "stock_code": stock_code,
            "exchange": infer_exchange(stock_code, board),
            "board": board,
            "listing_date": listing_date,
            "prospectus_title": prospectus_title,
            "prospectus_url": prospectus_url,
            "prospectus_version": infer_prospectus_version(prospectus_title),
            "prospectus_date": prospectus_date,
        },
        "financing_events": unique_events,
        "investor_overview": investor_overview,
        "shareholding_and_exit_summary": shareholding_and_exit_summary,
        "candidate_evidence_summary": candidate_summary,
        "processing": build_processing_section(company_info, snippets, unique_events, candidate_summary),
        "_meta": {
            "schema_name": "pevc_research_event_pool",
            "schema_version": "v5_refined",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sample_id": sample_id,
            "source_candidate_file": str(candidate_file.relative_to(BASE_DIR)).replace("\\", "/"),
        },
    }

    return result


# ============================================================
# 10. 主程序
# ============================================================

def main():
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    company_map = load_company_list()
    candidate_files = sorted(CANDIDATE_DIR.glob("*_candidate.txt"))

    if not candidate_files:
        print(f"未找到候选文本文件，请检查目录：{CANDIDATE_DIR}")
        return

    log_rows = []

    for candidate_file in candidate_files:
        print("\n" + "=" * 80)
        print(f"正在生成 PE/VC 研究事件池 JSON：{candidate_file.name}")
        print("=" * 80)

        try:
            result = build_company_json(candidate_file, company_map)

            stock_code = normalize_stock_code(result["company"].get("stock_code", ""))
            sample_id = result["_meta"].get("sample_id", "")

            if sample_id and stock_code:
                json_name = f"{sample_id}_{stock_code}.json"
            else:
                json_name = candidate_file.stem.replace("_candidate", "") + ".json"

            json_path = JSON_OUTPUT_DIR / json_name

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            log_rows.append({
                "company_name": result["company"].get("company_name", ""),
                "stock_code": stock_code,
                "candidate_text_path": str(candidate_file.relative_to(BASE_DIR)).replace("\\", "/"),
                "model_name": "rule_based_regex_pevc_event_pool_v5_refined",
                "prompt_version": "none",
                "json_path": str(json_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "status": "success",
                "event_count": len(result.get("financing_events", [])),
                "investor_count": len(result.get("investor_overview", [])),
                "candidate_signal_count": len(result.get("candidate_evidence_summary", {}).get("detected_keywords", [])),
                "error_message": "",
            })

            print(f"生成成功：{json_path}")
            print(f"融资相关事件数量：{len(result['financing_events'])}")
            print(f"投资方线索数量：{len(result['investor_overview'])}")
            print(f"候选信号数量：{len(result['candidate_evidence_summary']['detected_keywords'])}")

        except Exception as e:
            log_rows.append({
                "company_name": "",
                "stock_code": "",
                "candidate_text_path": str(candidate_file.relative_to(BASE_DIR)).replace("\\", "/"),
                "model_name": "rule_based_regex_pevc_event_pool_v5_refined",
                "prompt_version": "none",
                "json_path": "",
                "status": "fail",
                "event_count": "",
                "investor_count": "",
                "candidate_signal_count": "",
                "error_message": str(e),
            })

            print(f"抽取失败：{candidate_file.name}")
            print(e)

    with open(EXTRACTION_LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "company_name",
            "stock_code",
            "candidate_text_path",
            "model_name",
            "prompt_version",
            "json_path",
            "status",
            "event_count",
            "investor_count",
            "candidate_signal_count",
            "error_message",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    print("\nPE/VC 研究事件池 JSON 生成完成")
    print(f"JSON 输出目录：{JSON_OUTPUT_DIR}")
    print(f"抽取日志：{EXTRACTION_LOG_PATH}")


if __name__ == "__main__":
    main()