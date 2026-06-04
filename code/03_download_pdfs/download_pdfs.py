import csv
import os
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path


# 项目根目录
BASE_DIR = Path(__file__).resolve().parents[2]

# 输入 CSV
COMPANY_LIST_PATH = BASE_DIR / "company_lists" / "week1_public_samples.csv"

# PDF 保存目录，不建议上传 GitHub
PDF_DIR = BASE_DIR / "data" / "raw_pdfs"

# 下载日志
LOG_PATH = BASE_DIR / "logs" / "download_log.csv"


def safe_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    name = str(name).strip()
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    return name


def get_value(row, possible_keys):
    """兼容英文表头和中文表头"""
    for key in possible_keys:
        if key in row and row[key]:
            return row[key].strip()
    return ""


def download_pdf(url: str, save_path: Path):
    """下载 PDF 文件"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read()

    save_path.write_bytes(content)
    return len(content)


def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_rows = []

    with open(COMPANY_LIST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sample_id = get_value(row, ["sample_id", "样本ID"])
            company_name = get_value(row, ["company_name", "公司名称"])
            stock_code = get_value(row, ["stock_code", "股票代码"])
            prospectus_url = get_value(row, ["prospectus_url", "招股说明书链接", "源页面网址", "source_page_url"])

            if not prospectus_url:
                log_rows.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "prospectus_url": "",
                    "file_name": "",
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "fail",
                    "file_size": "",
                    "error_message": "missing prospectus_url"
                })
                continue

            file_name = f"{sample_id}_{stock_code}_{safe_filename(company_name)}.pdf"
            save_path = PDF_DIR / file_name

            try:
                print(f"正在下载：{company_name} {stock_code}")
                file_size = download_pdf(prospectus_url, save_path)

                log_rows.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "prospectus_url": prospectus_url,
                    "file_name": file_name,
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                    "file_size": file_size,
                    "error_message": ""
                })

                print(f"下载成功：{file_name}")

                # 防止请求太快
                time.sleep(1)

            except Exception as e:
                log_rows.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "prospectus_url": prospectus_url,
                    "file_name": file_name,
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "fail",
                    "file_size": "",
                    "error_message": str(e)
                })

                print(f"下载失败：{company_name}，原因：{e}")

    with open(LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "company_name",
            "stock_code",
            "prospectus_url",
            "file_name",
            "download_time",
            "status",
            "file_size",
            "error_message"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    print("\n全部处理完成")
    print(f"PDF保存位置：{PDF_DIR}")
    print(f"下载日志位置：{LOG_PATH}")


if __name__ == "__main__":
    main()
