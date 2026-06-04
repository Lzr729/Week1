import csv
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
PARSED_DIR = BASE_DIR / "data" / "parsed_texts"
LOG_PATH = BASE_DIR / "logs" / "parse_log.csv"


def find_markdown_file(output_dir: Path):
    """在 MinerU 输出目录中查找 markdown 文件"""
    md_files = list(output_dir.rglob("*.md"))
    if md_files:
        return md_files[0]
    return None


def run_mineru_for_pdf(pdf_path: Path, output_dir: Path):
    """
    使用 MinerU 命令行解析单个 PDF。
    输出目录为 data/parsed_texts/公司文件名/
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "mineru",
        "-p", str(pdf_path),
        "-o", str(output_dir),
        "-b", "pipeline"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    return result


def main():
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"未找到 PDF 文件，请检查目录：{PDF_DIR}")
        return

    log_rows = []

    for pdf_path in pdf_files:
        print(f"\n正在用 MinerU 解析：{pdf_path.name}")

        output_dir = PARSED_DIR / pdf_path.stem
        parse_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = run_mineru_for_pdf(pdf_path, output_dir)

            md_file = find_markdown_file(output_dir)

            if result.returncode == 0 and md_file is not None:
                status = "success"
                markdown_path = str(md_file.relative_to(BASE_DIR))
                error_message = ""
                print(f"解析成功：{markdown_path}")

            elif result.returncode == 0 and md_file is None:
                status = "partial"
                markdown_path = ""
                error_message = "MinerU finished, but no markdown file was found."
                print("解析部分成功，但未找到 markdown 文件。")

            else:
                status = "fail"
                markdown_path = ""
                error_message = result.stderr.strip() or result.stdout.strip()
                print(f"解析失败：{pdf_path.name}")

            log_rows.append({
                "company_name": "",
                "stock_code": "",
                "file_name": pdf_path.name,
                "parser": "MinerU",
                "parse_time": parse_time,
                "page_count": "",
                "markdown_path": markdown_path,
                "status": status,
                "error_message": error_message[:500]
            })

        except Exception as e:
            log_rows.append({
                "company_name": "",
                "stock_code": "",
                "file_name": pdf_path.name,
                "parser": "MinerU",
                "parse_time": parse_time,
                "page_count": "",
                "markdown_path": "",
                "status": "fail",
                "error_message": str(e)[:500]
            })

            print(f"解析异常：{pdf_path.name}，原因：{e}")

    with open(LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "company_name",
            "stock_code",
            "file_name",
            "parser",
            "parse_time",
            "page_count",
            "markdown_path",
            "status",
            "error_message"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    print("\n全部 PDF 解析流程完成")
    print(f"解析结果目录：{PARSED_DIR}")
    print(f"解析日志：{LOG_PATH}")


if __name__ == "__main__":
    main()
