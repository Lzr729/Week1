import argparse
import csv
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
TMP_PDF_DIR = BASE_DIR / "data" / "tmp_ascii_pdfs"
PARSED_DIR = BASE_DIR / "data" / "parsed_texts_full"
LOG_PATH = BASE_DIR / "logs" / "parse_log.csv"

MINERU_EXE = BASE_DIR / ".venv" / "Scripts" / "mineru.exe"


def get_pdf_page_count(pdf_path: Path):
    """读取 PDF 总页数。pypdf 未安装或读取失败时返回空。"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return ""


def extract_sample_and_code(pdf_path: Path):
    """
    从 PDF 文件名中提取 sample_id 和 stock_code。
    支持：
    MB001_001282.pdf
    MB001_001282_芜湖三联锻造股份有限公司.pdf
    """
    name = pdf_path.stem
    pattern = r"^(MB\d+|GEM\d+|STAR\d+|BSE\d+)_(\d{6})"
    match = re.match(pattern, name)

    if match:
        return match.group(1), match.group(2)

    return name, ""


def prepare_ascii_pdf(pdf_path: Path):
    """
    复制一份英文/数字文件名 PDF，避免 Windows 中文文件名影响 MinerU。
    原始 PDF 不会被删除。
    """
    sample_id, stock_code = extract_sample_and_code(pdf_path)

    if stock_code:
        ascii_name = f"{sample_id}_{stock_code}.pdf"
    else:
        ascii_name = f"{sample_id}.pdf"

    TMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
    ascii_pdf_path = TMP_PDF_DIR / ascii_name

    shutil.copy2(pdf_path, ascii_pdf_path)

    return ascii_pdf_path, sample_id, stock_code


def find_markdown_file(output_dir: Path):
    """递归查找 MinerU 输出的 Markdown 文件。"""
    md_files = list(output_dir.rglob("*.md"))

    if not md_files:
        return None

    auto_md_files = [p for p in md_files if "auto" in str(p).lower()]
    if auto_md_files:
        return auto_md_files[0]

    return md_files[0]


def run_mineru_for_pdf(pdf_path: Path, output_dir: Path):
    """
    使用 MinerU 完整解析单个 PDF。
    不使用 -e 参数，因此会解析完整 PDF。
    解析过程会实时显示在 VS Code 终端。
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if not MINERU_EXE.exists():
        raise FileNotFoundError(f"未找到 MinerU 可执行文件：{MINERU_EXE}")

    command = [
    str(MINERU_EXE),
    "-p",
    str(pdf_path.resolve()),
    "-o",
    str(output_dir.resolve()),
    "-b",
    "pipeline",
    "--table",
    "false",
    "--formula",
    "false",
    "--image-analysis",
    "false",
]

    print("\n执行 MinerU 命令：")
    print(" ".join(command))
    print("\n开始解析，解析过程中请不要关闭 VS Code 或终端。\n")

    env = os.environ.copy()
    env["PATH"] = str(MINERU_EXE.parent) + ";" + env.get("PATH", "")
    env["MINERU_MODEL_SOURCE"] = "modelscope"

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore",
        env=env,
        bufsize=1,
    )

    output_lines = []

    if process.stdout is not None:
        for line in process.stdout:
            print(line, end="")
            output_lines.append(line)

    process.wait()

    return process.returncode, "".join(output_lines)


def write_parse_log(log_rows):
    """写入解析日志。"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

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
            "error_message",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)


def main():
    parser = argparse.ArgumentParser(description="Use MinerU to parse prospectus PDFs into Markdown.")
    parser.add_argument(
        "--sample",
        default="",
        help="只解析某一个样本，例如 MB001；不填则解析全部 PDF。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="如果输出目录已存在，是否删除后重新解析。",
    )

    args = parser.parse_args()

    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    TMP_PDF_DIR.mkdir(parents=True, exist_ok=True)

    all_pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if args.sample:
        pdf_files = [
            p for p in all_pdf_files
            if p.name.startswith(args.sample)
        ]
    else:
        pdf_files = all_pdf_files

    if not pdf_files:
        print(f"未找到 PDF 文件，请检查目录：{PDF_DIR}")
        return

    log_rows = []

    print(f"项目根目录：{BASE_DIR}")
    print(f"PDF 输入目录：{PDF_DIR}")
    print(f"完整解析输出目录：{PARSED_DIR}")
    print(f"本次待解析 PDF 数量：{len(pdf_files)}")

    for original_pdf_path in pdf_files:
        ascii_pdf_path, sample_id, stock_code = prepare_ascii_pdf(original_pdf_path)
        page_count = get_pdf_page_count(ascii_pdf_path)

        output_dir = PARSED_DIR / ascii_pdf_path.stem

        print("\n" + "=" * 80)
        print(f"样本编号：{sample_id}")
        print(f"股票代码：{stock_code}")
        print(f"原始 PDF：{original_pdf_path.name}")
        print(f"临时英文 PDF：{ascii_pdf_path.name}")
        print(f"PDF 页数：{page_count}")
        print(f"输出目录：{output_dir}")
        print("=" * 80)

        parse_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if output_dir.exists() and args.force:
            print(f"检测到已有输出目录，--force 已启用，删除旧目录：{output_dir}")
            shutil.rmtree(output_dir)

        existing_md = find_markdown_file(output_dir) if output_dir.exists() else None

        if existing_md is not None and not args.force:
            print(f"已存在 Markdown，跳过解析：{existing_md}")

            log_rows.append({
                "company_name": "",
                "stock_code": stock_code,
                "file_name": original_pdf_path.name,
                "parser": "MinerU",
                "parse_time": parse_time,
                "page_count": page_count,
                "markdown_path": str(existing_md.relative_to(BASE_DIR)),
                "status": "success_existing",
                "error_message": "Markdown already exists. Use --force to reparse.",
            })

            continue

        try:
            return_code, mineru_output = run_mineru_for_pdf(ascii_pdf_path, output_dir)
            md_file = find_markdown_file(output_dir)

            if return_code == 0 and md_file is not None:
                status = "success"
                markdown_path = str(md_file.relative_to(BASE_DIR))
                error_message = ""
                print(f"\n解析成功：{markdown_path}")

            elif return_code == 0 and md_file is None:
                status = "partial"
                markdown_path = ""
                error_message = "MinerU finished, but no markdown file was found."
                print("\nMinerU 执行完成，但没有找到 Markdown 文件。")

            else:
                status = "fail"
                markdown_path = ""
                error_message = mineru_output[-3000:]
                print("\n解析失败。请查看 logs/parse_log.csv 中的 error_message。")

            log_rows.append({
                "company_name": "",
                "stock_code": stock_code,
                "file_name": original_pdf_path.name,
                "parser": "MinerU",
                "parse_time": parse_time,
                "page_count": page_count,
                "markdown_path": markdown_path,
                "status": status,
                "error_message": error_message,
            })

            write_parse_log(log_rows)

        except KeyboardInterrupt:
            print("\n用户中断了解析。当前已完成样本会写入 parse_log.csv。")
            write_parse_log(log_rows)
            raise

        except Exception as e:
            log_rows.append({
                "company_name": "",
                "stock_code": stock_code,
                "file_name": original_pdf_path.name,
                "parser": "MinerU",
                "parse_time": parse_time,
                "page_count": page_count,
                "markdown_path": "",
                "status": "fail",
                "error_message": str(e),
            })

            write_parse_log(log_rows)

            print(f"\n解析异常：{original_pdf_path.name}")
            print(e)

    write_parse_log(log_rows)

    print("\n全部 PDF 解析流程结束")
    print(f"完整解析结果目录：{PARSED_DIR}")
    print(f"解析日志：{LOG_PATH}")


if __name__ == "__main__":
    main()