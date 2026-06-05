Week 1 工作周报：招股书 PE/VC 信息抽取流程搭建
一、本周工作目标

本周主要目标是完成第一周样本数据的获取、解析、章节定位、PE/VC 相关信息抽取与结果校验，形成一套可以复用的招股说明书结构化处理流程。

本周重点关注以下任务：

1、建立第一周公开样本公司清单；
2、下载样本公司招股说明书 PDF；
3、将 PDF 解析为 Markdown 文本；
4、从解析文本中定位 PE/VC 研究相关章节；
5、抽取上市前融资、增资、股权转让、外部投资者进入等事件；
6、生成结构化 JSON；
7、对 JSON 结果进行程序化校验。
二、本周完成情况
1、样本公司清单整理
已建立第一周公开样本公司清单文件：
company_lists/week1_public_samples.csv
2、数据来源与下载方法说明
已补充数据来源说明文档：
source_notes/data_sources.md
source_notes/prospectus_download_method.md
其中：
data_sources.md
用于说明招股说明书数据来源、获取路径和数据使用方式。
prospectus_download_method.md
用于说明 PDF 文件下载方法、保存路径和下载过程中的注意事项。
3、PDF 下载流程
已完成第 3 步 PDF 下载代码：
code/03_download_pdfs/
下载日志保存于：
logs/download_log.csv
该日志记录了每个 PDF 的下载状态、文件路径、是否成功、错误信息等。
4、PDF 解析为 Markdown
已完成第 4 步 PDF 解析代码：
code/04_parse_pdf_to_markdown/
本阶段使用 MinerU 对招股说明书 PDF 进行解析，并将解析结果转为 Markdown 文本。
解析日志保存于：
logs/parse_log.csv
解析结果用于后续章节定位和信息抽取。
5、相关章节定位
已完成第 5 步章节定位代码：
code/05_locate_relevant_sections/
该步骤从 Markdown 文本中定位与 PE/VC 研究相关的章节和段落
outputs/week1_candidate_texts/
章节定位日志保存于：
logs/locate_log.csv
6、 PE/VC 相关信息抽取
已完成第 6 步 PE/VC 信息抽取代码：
code/06_extract_pevc_info/
本步骤从第五步定位出的候选文本中抽取 PE/VC 研究相关事件池
生成的 JSON 文件保存在：
outputs/week1_sample_json/
同时，针对第六步生成结果进行了 v5.1 清洗，主要修正了：
locate_status 状态值不规范问题；
investor_overview 中的脏投资方名称；
processing 中统计字段与实际 JSON 结果不一致的问题；
个别事件中的投资方名称冗余问题。
相关代码文件包括：
code/06_extract_pevc_info/extract_pevc_info.py
code/06_extract_pevc_info/clean_v5_outputs.py
抽取日志保存于：
logs/extraction_log.csv
logs/clean_v5_1_log.csv
7、JSON 结果校验
已完成第 7 步 JSON 校验代码：
code/07_validate_outputs/
校验对象为：
outputs/week1_sample_json/
校验日志保存于：
logs/validation_log.csv
logs/validation_summary.csv
最终校验结果为：
PASS = 8
ERROR = 0
WARNING = 0
INFO = 3
说明 8 个 JSON 文件均通过结构校验，没有错误和警告。
三、本周关键结果
本周完成了从招股说明书 PDF 到结构化 JSON 的完整流程，形成了以下处理链路：
公司样本清单
→ PDF 下载
→ PDF 解析为 Markdown
→ PE/VC 相关章节定位
→ 候选文本生成
→ PE/VC 事件池 JSON 抽取
→ JSON 结果清洗
→ JSON 校验
最终输出了 8 家样本公司的结构化 JSON 文件。JSON 中保留了公司基础信息、融资相关事件、投资方信息、发行前股东结构和退出锁定相关摘要，并保留了每条事件的原文证据。
四、本周遇到的问题及解决
1、PDF 解析耗时较长
部分招股说明书页数较多，且包含大量表格，MinerU 在执行 OCR 或表格识别时耗时较长。后续通过跳过不必要 OCR、分批测试样本和查看任务管理器状态来确认程序是否仍在运行。
2、JSON 初始结果过空
早期抽取规则过于严格，导致部分公司 financing_events 为空。后续将第六步改为“PE/VC 研究事件池”思路，不只抽取确定 PE/VC 事件，也抽取与 PE/VC 研究相关的增资、股权转让、外部投资者进入等事件，并通过 event_nature 和 pevc_relevance 区分事件性质。