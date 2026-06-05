import csv
import re
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

PARSE_LOG_PATH = BASE_DIR / "logs" / "parse_log.csv"
COMPANY_LIST_PATH = BASE_DIR / "company_lists" / "week1_public_samples.csv"

OUTPUT_DIR = BASE_DIR / "outputs" / "week1_candidate_texts"
LOCATE_LOG_PATH = BASE_DIR / "logs" / "locate_log.csv"


# 重点章节关键词
SECTION_KEYWORDS = [
    "发行人基本情况",
    "历史沿革",
    "股本演变",
    "股本形成",
    "设立及报告期内股本演变",
    "历次增资",
    "历次股权转让",
    "股权结构",
    "股东情况",
    "主要股东",
    "发行前股本结构",
    "发行人股本情况",
    "上市前投资者",
]


# PE/VC 信息关键词
PEVC_KEYWORDS = [
    "增资",
    "股权转让",
    "出资",
    "认购",
    "入股",
    "投资者",
    "外部投资者",
    "财务投资者",
    "风险投资",
    "私募股权",
    "创投",
    "创业投资",
    "产业基金",
    "股权投资基金",
    "合伙企业",
    "员工持股平台",
    "投前估值",
    "投后估值",
    "估值",
    "每股价格",
    "认购价格",
    "持股比例",
    "股份锁定",
    "退出",
    "对赌",
    "特殊投资条款",
]


ALL_KEYWORDS = SECTION_KEYWORDS + PEVC_KEYWORDS


def normalize_stock_code(stock_code: str) -> str:
    """修复 001282 这类股票代码被 Excel 吃掉前导 0 的问题"""
    stock_code = str(stock_code).strip()
    if stock_code.isdigit() and len(stock_code) < 6:
        return stock_code.zfill(6)
    return stock_code


def extract_sample_id(file_name: str) -> str:
    """从文件名中提取样本编号，如 MB001、GEM001"""
    match = re.match(r"^(MB\d+|GEM\d+|STAR\d+|BSE\d+)", file_name)
    if match:
        return match.group(1)
    return ""


def load_company_info():
    """读取 company_list，用 sample_id 映射公司信息"""
    company_map = {}

    if not COMPANY_LIST_PATH.exists():
        return company_map

    with open(COMPANY_LIST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            stock_code = normalize_stock_code(row.get("stock_code", ""))
            company_name = row.get("company_name", "").strip()
            board = row.get("board", "").strip()
            prospectus_title = row.get("prospectus_title", "").strip()
            prospectus_url = row.get("prospectus_url", "").strip()

            if sample_id:
                company_map[sample_id] = {
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "board": board,
                    "prospectus_title": prospectus_title,
                    "prospectus_url": prospectus_url,
                }

    return company_map


def load_parse_log():
    """读取 parse_log，找到每家公司对应的 Markdown 路径"""
    rows = []

    with open(PARSE_LOG_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            status = row.get("status", "").strip()
            markdown_path = row.get("markdown_path", "").strip()

            if status not in ["success", "success_existing"]:
                continue

            if not markdown_path:
                continue

            rows.append(row)

    return rows


def read_markdown(markdown_path: Path) -> str:
    """读取 Markdown 内容"""
    return markdown_path.read_text(encoding="utf-8", errors="ignore")


def find_nearest_heading(text: str, position: int) -> str:
    """找到当前位置前最近的 Markdown 标题"""
    before_text = text[:position]
    headings = re.findall(r"^#{1,6}\s+(.+)$", before_text, flags=re.MULTILINE)

    if headings:
        return headings[-1].strip()

    return ""


def make_snippet(text: str, position: int, window: int = 3000):
    """根据关键词位置截取上下文"""
    start = max(position - window, 0)
    end = min(position + window, len(text))
    return start, end, text[start:end]


def merge_ranges(ranges, min_gap=1500):
    """
    合并距离较近的文本区间，避免同一章节被重复截取太多次。
    ranges: [(start, end, keyword, section)]
    """
    if not ranges:
        return []

    ranges = sorted(ranges, key=lambda x: x[0])
    merged = []

    cur_start, cur_end, cur_keywords, cur_sections = ranges[0][0], ranges[0][1], {ranges[0][2]}, {ranges[0][3]}

    for start, end, keyword, section in ranges[1:]:
        if start <= cur_end + min_gap:
            cur_end = max(cur_end, end)
            cur_keywords.add(keyword)
            cur_sections.add(section)
        else:
            merged.append((cur_start, cur_end, cur_keywords, cur_sections))
            cur_start, cur_end = start, end
            cur_keywords = {keyword}
            cur_sections = {section}

    merged.append((cur_start, cur_end, cur_keywords, cur_sections))

    return merged


def locate_candidate_text(text: str):
    """定位候选文本区间"""
    ranges = []

    for keyword in ALL_KEYWORDS:
        for match in re.finditer(re.escape(keyword), text):
            position = match.start()
            section = find_nearest_heading(text, position)
            start, end, _ = make_snippet(text, position)
            ranges.append((start, end, keyword, section))

    merged = merge_ranges(ranges)

    # 限制候选片段数量，避免输出文件过大
    return merged[:20]


def write_candidate_file(output_path: Path, metadata: dict, text: str, merged_ranges):
    """写入候选文本文件"""
    parts = []

    parts.append("# 候选文本截取结果\n")
    parts.append(f"sample_id: {metadata.get('sample_id', '')}\n")
    parts.append(f"company_name: {metadata.get('company_name', '')}\n")
    parts.append(f"stock_code: {metadata.get('stock_code', '')}\n")
    parts.append(f"board: {metadata.get('board', '')}\n")
    parts.append(f"source_markdown: {metadata.get('source_markdown', '')}\n")
    parts.append(f"prospectus_title: {metadata.get('prospectus_title', '')}\n")
    parts.append(f"prospectus_url: {metadata.get('prospectus_url', '')}\n")
    parts.append("\n---\n\n")

    for idx, (start, end, keywords, sections) in enumerate(merged_ranges, start=1):
        snippet = text[start:end]

        parts.append(f"## 候选片段 {idx}\n\n")
        parts.append(f"- matched_keywords: {', '.join(sorted(keywords))}\n")
        parts.append(f"- source_sections: {', '.join([s for s in sorted(sections) if s])}\n")
        parts.append(f"- start_position: {start}\n")
        parts.append(f"- end_position: {end}\n\n")
        parts.append("```text\n")
        parts.append(snippet.strip())
        parts.append("\n```\n\n")
        parts.append("---\n\n")

    output_path.write_text("".join(parts), encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOCATE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    company_map = load_company_info()
    parse_rows = load_parse_log()

    locate_log_rows = []

    if not parse_rows:
        print("没有在 parse_log.csv 中找到成功解析的 Markdown 记录。")
        return

    for row in parse_rows:
        file_name = row.get("file_name", "").strip()
        markdown_path_str = row.get("markdown_path", "").strip()

        sample_id = extract_sample_id(file_name)
        company_info = company_map.get(sample_id, {})

        markdown_path = BASE_DIR / markdown_path_str

        print("\n" + "=" * 80)
        print(f"正在定位：{sample_id} {company_info.get('company_name', '')}")
        print(f"Markdown：{markdown_path}")
        print("=" * 80)

        if not markdown_path.exists():
            locate_log_rows.append({
                "company_name": company_info.get("company_name", ""),
                "stock_code": company_info.get("stock_code", ""),
                "matched_keyword": "",
                "source_section": "",
                "start_position": "",
                "end_position": "",
                "candidate_text_path": "",
                "status": "fail",
                "error_message": f"markdown file not found: {markdown_path_str}",
            })
            print("Markdown 文件不存在。")
            continue

        try:
            text = read_markdown(markdown_path)
            merged_ranges = locate_candidate_text(text)

            if not merged_ranges:
                locate_log_rows.append({
                    "company_name": company_info.get("company_name", ""),
                    "stock_code": company_info.get("stock_code", ""),
                    "matched_keyword": "",
                    "source_section": "",
                    "start_position": "",
                    "end_position": "",
                    "candidate_text_path": "",
                    "status": "fail",
                    "error_message": "no candidate text found",
                })
                print("没有定位到候选文本。")
                continue

            stock_code = company_info.get("stock_code", row.get("stock_code", ""))
            stock_code = normalize_stock_code(stock_code)

            output_file_name = f"{sample_id}_{stock_code}_candidate.txt"
            output_path = OUTPUT_DIR / output_file_name

            metadata = {
                "sample_id": sample_id,
                "company_name": company_info.get("company_name", ""),
                "stock_code": stock_code,
                "board": company_info.get("board", ""),
                "source_markdown": markdown_path_str,
                "prospectus_title": company_info.get("prospectus_title", ""),
                "prospectus_url": company_info.get("prospectus_url", ""),
            }

            write_candidate_file(output_path, metadata, text, merged_ranges)

            # 每个合并片段写一条日志
            for start, end, keywords, sections in merged_ranges:
                locate_log_rows.append({
                    "company_name": company_info.get("company_name", ""),
                    "stock_code": stock_code,
                    "matched_keyword": "|".join(sorted(keywords)),
                    "source_section": "|".join([s for s in sorted(sections) if s]),
                    "start_position": start,
                    "end_position": end,
                    "candidate_text_path": str(output_path.relative_to(BASE_DIR)),
                    "status": "success",
                    "error_message": "",
                })

            print(f"定位成功：{output_path}")
            print(f"候选片段数量：{len(merged_ranges)}")

        except Exception as e:
            locate_log_rows.append({
                "company_name": company_info.get("company_name", ""),
                "stock_code": company_info.get("stock_code", ""),
                "matched_keyword": "",
                "source_section": "",
                "start_position": "",
                "end_position": "",
                "candidate_text_path": "",
                "status": "fail",
                "error_message": str(e),
            })
            print(f"定位失败：{e}")

    with open(LOCATE_LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "company_name",
            "stock_code",
            "matched_keyword",
            "source_section",
            "start_position",
            "end_position",
            "candidate_text_path",
            "status",
            "error_message",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(locate_log_rows)

    print("\n章节定位完成")
    print(f"候选文本目录：{OUTPUT_DIR}")
    print(f"定位日志：{LOCATE_LOG_PATH}")


if __name__ == "__main__":
    main()
