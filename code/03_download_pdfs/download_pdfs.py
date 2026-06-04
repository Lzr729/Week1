import csv
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

COMPANY_LIST_PATH = BASE_DIR / "company_lists" / "week1_public_samples.csv"
PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
LOG_PATH = BASE_DIR / "logs" / "download_log.csv"


def safe_filename(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    return name


def normalize_stock_code(stock_code: str) -> str:
    stock_code = str(stock_code).strip()
    if stock_code.isdigit() and len(stock_code) < 6:
        stock_code = stock_code.zfill(6)
    return stock_code


def get_value(row, possible_keys):
    for key in possible_keys:
        if key in row and row[key] not in [None, ""]:
            return str(row[key]).strip()
    return ""


def download_pdf_by_urllib(url: str, save_path: Path) -> int:
    """普通方式下载，适合巨潮资讯等直接PDF链接"""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()

    if len(content) < 1000:
        raise ValueError("downloaded file is too small, may not be a valid PDF")

    if not content.startswith(b"%PDF"):
        raise ValueError("downloaded content is not a PDF file")

    save_path.write_bytes(content)
    return len(content)


def wait_for_new_pdf(download_dir: Path, before_files: set, timeout: int = 90) -> Path:
    """等待浏览器下载完成，并返回新下载的PDF路径"""

    start_time = time.time()

    while time.time() - start_time < timeout:
        current_pdfs = set(download_dir.glob("*.pdf"))
        new_pdfs = list(current_pdfs - before_files)

        temp_files = list(download_dir.glob("*.crdownload"))

        if new_pdfs and not temp_files:
            newest_pdf = max(new_pdfs, key=lambda p: p.stat().st_mtime)
            return newest_pdf

        time.sleep(1)

    raise TimeoutError("browser download timeout, no new PDF file detected")


def download_pdf_by_selenium(url: str, save_path: Path) -> int:
    """用Chrome浏览器自动化下载，适合北交所原始链接"""

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    PDF_DIR.mkdir(parents=True, exist_ok=True)

    before_files = set(PDF_DIR.glob("*.pdf"))

    chrome_options = Options()

    # 不使用 headless，避免某些电脑无头模式无法下载 PDF
    prefs = {
        "download.default_directory": str(PDF_DIR.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)

        downloaded_pdf = wait_for_new_pdf(PDF_DIR, before_files, timeout=90)

        if save_path.exists():
            save_path.unlink()

        downloaded_pdf.rename(save_path)

        content = save_path.read_bytes()

        if len(content) < 1000:
            raise ValueError("downloaded file is too small, may not be a valid PDF")

        if not content.startswith(b"%PDF"):
            raise ValueError("downloaded content is not a PDF file")

        return len(content)

    finally:
        driver.quit()


def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_rows = []

    with open(COMPANY_LIST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sample_id = get_value(row, ["sample_id", "样本ID", "样本 ID"])
            company_name = get_value(row, ["company_name", "公司名称"])
            stock_code = get_value(row, ["stock_code", "股票代码"])
            stock_code = normalize_stock_code(stock_code)

            prospectus_url = get_value(
                row,
                [
                    "prospectus_url",
                    "招股说明书链接",
                    "source_page_url",
                    "源页面网址",
                    "PDF链接",
                ],
            )

            if not sample_id:
                sample_id = stock_code

            file_name = f"{sample_id}_{stock_code}_{safe_filename(company_name)}.pdf"
            save_path = PDF_DIR / file_name

            print(f"\n正在处理：{sample_id} {company_name} {stock_code}")

            if not prospectus_url:
                log_rows.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "prospectus_url": "",
                    "used_url": "",
                    "file_name": file_name,
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "fail",
                    "file_size": "",
                    "download_method": "",
                    "error_message": "missing prospectus_url"
                })
                continue

            try:
                if "bse.cn" in prospectus_url:
                    print("检测到北交所链接，使用 Selenium 浏览器自动化下载")
                    file_size = download_pdf_by_selenium(prospectus_url, save_path)
                    download_method = "selenium_original_url"
                else:
                    print("使用 urllib 直接下载")
                    file_size = download_pdf_by_urllib(prospectus_url, save_path)
                    download_method = "urllib_original_url"

                log_rows.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "prospectus_url": prospectus_url,
                    "used_url": prospectus_url,
                    "file_name": file_name,
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                    "file_size": file_size,
                    "download_method": download_method,
                    "error_message": ""
                })

                print(f"下载成功：{file_name}，大小：{file_size} bytes")

            except Exception as e:
                log_rows.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "prospectus_url": prospectus_url,
                    "used_url": prospectus_url,
                    "file_name": file_name,
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "fail",
                    "file_size": "",
                    "download_method": "original_url_failed",
                    "error_message": str(e)
                })

                print(f"下载失败：{company_name}，原因：{e}")

            time.sleep(1)

    with open(LOG_PATH, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "company_name",
            "stock_code",
            "prospectus_url",
            "used_url",
            "file_name",
            "download_time",
            "status",
            "file_size",
            "download_method",
            "error_message",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    print("\n全部处理完成")
    print(f"PDF 保存位置：{PDF_DIR}")
    print(f"下载日志位置：{LOG_PATH}")


if __name__ == "__main__":
    main()