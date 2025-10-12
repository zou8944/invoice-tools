import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd
import pdfplumber
from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MAX_WORKERS


@dataclass
class InvoiceItem:
    project_name: str
    specification: str
    unit: str
    quantity: float
    unit_price: float
    amount: float
    tax_rate: float
    tax_amount: float


@dataclass
class InvoiceData:
    invoice_type: str
    invoice_number: str
    invoice_date: str
    buyer_name: str
    buyer_tax_id: str
    seller_name: str
    seller_tax_id: str
    items: list[InvoiceItem]
    total_price_and_tax: float
    comment: str
    issuer: str
    filename: str = ""


def parse_invoice_text(text: str) -> InvoiceData:
    """使用 DeepSeek API 解析发票文本"""
    # 初始化 OpenAI 客户端，指向 DeepSeek API
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    # 构建 prompt
    prompt = f"""请解析以下发票文本，提取所有相关信息并以 JSON 格式返回。其中，日期格式统一为 YYYY-MM-DD。

发票文本：
{text}

请返回以下格式的 JSON：
{{
    "invoice_type": "发票类型",
    "invoice_number": "发票号码",
    "invoice_date": "开票日期",
    "buyer_name": "购买方名称",
    "buyer_tax_id": "购买方税号",
    "seller_name": "销售方名称",
    "seller_tax_id": "销售方税号",
    "items": [
        {{
            "project_name": "项目名称",
            "specification": "规格型号",
            "unit": "单位",
            "quantity": 数量,
            "unit_price": 单价,
            "amount": 金额,
            "tax_rate": 税率,
            "tax_amount": 税额
        }}
    ],
    "total_price_and_tax": 价税合计,
    "comment": "备注",
    "issuer": "开票人"
}}
"""

    # 调用 DeepSeek API
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "你是一个专业的发票信息提取助手，擅长从文本中准确提取发票的各项信息。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    # 解析响应
    content = response.choices[0].message.content
    if not content:
        raise ValueError("DeepSeek API 返回的内容为空")
    result = json.loads(content)

    # 转换为 InvoiceData 对象
    items = [InvoiceItem(**item) for item in result["items"]]

    invoice_data = InvoiceData(
        invoice_type=result["invoice_type"],
        invoice_number=result["invoice_number"],
        invoice_date=result["invoice_date"],
        buyer_name=result["buyer_name"],
        buyer_tax_id=result["buyer_tax_id"],
        seller_name=result["seller_name"],
        seller_tax_id=result["seller_tax_id"],
        items=items,
        total_price_and_tax=result["total_price_and_tax"],
        comment=result["comment"],
        issuer=result["issuer"],
    )

    return invoice_data


class InvoiceExtractor:
    """PDF invoice data extractor"""

    def _extract_text(self, pdf_path: str) -> str:
        """Extract text content from PDF"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text

    def _extract_one(self, pdf_path: str) -> InvoiceData:
        text = self._extract_text(pdf_path)
        invoice_data = parse_invoice_text(text)
        return invoice_data

    def _extract_many(
        self, pdf_paths: list[str], progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> list[InvoiceData]:
        """并发提取多个PDF的发票数据，并发度为5

        Args:
            pdf_paths: PDF文件路径列表
            progress_callback: 进度回调函数，参数为(文件名, 已完成数量, 总数量)
        """
        all_data = []
        total = len(pdf_paths)
        completed = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_path = {executor.submit(self._extract_one, pdf_path): pdf_path for pdf_path in pdf_paths}

            # 按完成顺序收集结果
            for future in as_completed(future_to_path):
                pdf_path = future_to_path[future]
                filename = pdf_path.split("/")[-1]
                try:
                    data = future.result()
                    data.filename = filename
                    all_data.append(data)
                    completed += 1
                    print(f"✓ 已完成: {filename} ({completed}/{total})")
                    if progress_callback:
                        progress_callback(filename, completed, total)
                except Exception as e:
                    completed += 1
                    print(f"✗ 处理 {filename} 时出错: {e}")
                    if progress_callback:
                        progress_callback(filename, completed, total)

        return all_data

    def extract_to_excel(
        self,
        pdf_paths: list[str],
        excel_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """提取多个PDF的发票数据并保存为Excel，items列表会展开为多行

        Args:
            pdf_paths: PDF文件路径列表
            excel_path: 输出Excel文件路径
            progress_callback: 进度回调函数，参数为(文件名, 已完成数量, 总数量)
        """
        print(f"开始处理 {len(pdf_paths)} 个PDF文件...")
        all_data = self._extract_many(pdf_paths, progress_callback)

        # 展开数据：每个item独立成一行
        rows = []
        for invoice in all_data:
            # 基础发票信息（不包含items）
            base_info = {
                "发票文件": invoice.filename,
                "发票类型": invoice.invoice_type,
                "发票号码": invoice.invoice_number,
                "开票日期": invoice.invoice_date,
                "购买方名称": invoice.buyer_name,
                "购买方税号": invoice.buyer_tax_id,
                "销售方名称": invoice.seller_name,
                "销售方税号": invoice.seller_tax_id,
                "价税合计": invoice.total_price_and_tax,
                "备注": invoice.comment,
                "开票人": invoice.issuer,
            }

            # 如果有items，每个item创建一行
            if invoice.items:
                for item in invoice.items:
                    row = base_info.copy()
                    row.update(
                        {
                            "项目名称": item.project_name,
                            "规格型号": item.specification,
                            "单位": item.unit,
                            "数量": item.quantity,
                            "单价": item.unit_price,
                            "金额": item.amount,
                            "税率": item.tax_rate,
                            "税额": item.tax_amount,
                        }
                    )
                    rows.append(row)
            else:
                # 如果没有items，也保留发票基础信息
                rows.append(base_info)

        # 创建DataFrame并保存
        df = pd.DataFrame(rows)
        df.to_excel(excel_path, index=False)
        print(f"✓ Excel文件已保存到: {excel_path}")


if __name__ == "__main__":
    extractor = InvoiceExtractor()
    extractor.extract_to_excel(
        pdf_paths=[
            "/Users/zouguodong/Downloads/零食发票 6.pdf",
            "/Users/zouguodong/Downloads/阿里云前正式账号 6 月发票.pdf",
            "/Users/zouguodong/Downloads/阿里云测试账号 6 月发票.pdf",
            "/Users/zouguodong/Downloads/电a子发票 - 90 购买域名.pdf",
            "/Users/zouguodong/Downloads/20cb94a6-683e-4dfc-a6ef-757d6aedf596.pdf",
        ],
        excel_path="/Users/zouguodong/Downloads/发票信息统计.xlsx",
    )
