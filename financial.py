import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from typing import Callable, Optional

import pandas as pd
from openai import OpenAI
from pdf2image import convert_from_path
from PIL import Image

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
    is_invoice: bool = True
    filename: str = ""
    page_number: int = 1


def image_to_base64(image: Image.Image) -> str:
    """将 PIL Image 转换为 base64 字符串"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def pdf_to_images(pdf_path: str) -> list[Image.Image]:
    """将 PDF 转换为图片列表，每页一张图片"""
    images = convert_from_path(pdf_path, dpi=200)
    return images


def parse_invoice_from_image(image_base64: str) -> InvoiceData:
    """使用 DeepSeek API 从图片中解析发票信息"""
    # 初始化 OpenAI 客户端，指向 DeepSeek API
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    # 构建 prompt
    prompt = """请分析这张图片，首先判断它是否是发票。如果是发票，提取所有相关信息；如果不是发票，只需要返回 is_invoice 为 false。

请返回以下格式的 JSON（日期格式统一为 YYYY-MM-DD）：
{
    "is_invoice": true/false,
    "invoice_type": "发票类型（如果不是发票则为空字符串）",
    "invoice_number": "发票号码",
    "invoice_date": "开票日期",
    "buyer_name": "购买方名称",
    "buyer_tax_id": "购买方税号",
    "seller_name": "销售方名称",
    "seller_tax_id": "销售方税号",
    "items": [
        {
            "project_name": "项目名称",
            "specification": "规格型号",
            "unit": "单位",
            "quantity": 数量,
            "unit_price": 单价,
            "amount": 金额,
            "tax_rate": 税率,
            "tax_amount": 税额
        }
    ],
    "total_price_and_tax": 价税合计,
    "comment": "备注",
    "issuer": "开票人"
}

注意：如果 is_invoice 为 false，其他字段可以填空字符串或0。"""

    # 调用 DeepSeek API with vision
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的发票信息提取助手，擅长从图片中识别并提取发票的各项信息。",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                ],
            },
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
    items = [InvoiceItem(**item) for item in result.get("items", [])]

    invoice_data = InvoiceData(
        is_invoice=result.get("is_invoice", False),
        invoice_type=result.get("invoice_type", ""),
        invoice_number=result.get("invoice_number", ""),
        invoice_date=result.get("invoice_date", ""),
        buyer_name=result.get("buyer_name", ""),
        buyer_tax_id=result.get("buyer_tax_id", ""),
        seller_name=result.get("seller_name", ""),
        seller_tax_id=result.get("seller_tax_id", ""),
        items=items,
        total_price_and_tax=result.get("total_price_and_tax", 0.0),
        comment=result.get("comment", ""),
        issuer=result.get("issuer", ""),
    )

    return invoice_data


class InvoiceExtractor:
    """PDF invoice data extractor"""

    def _process_single_page(self, image: Image.Image, page_num: int) -> Optional[InvoiceData]:
        """处理单页图片"""
        # 转换为 base64
        image_base64 = image_to_base64(image)

        # 调用 AI 解析
        invoice_data = parse_invoice_from_image(image_base64)

        # 检查是否是发票
        if not invoice_data.is_invoice:
            print(f"  → 第 {page_num} 页不是发票，已忽略")
            return None

        # 设置页码
        invoice_data.page_number = page_num

        return invoice_data

    def _extract_one(self, pdf_path: str) -> list[InvoiceData]:
        """提取单个 PDF 的发票数据，支持多页 PDF

        Returns:
            发票数据列表，每页一个 InvoiceData（如果是发票的话）
        """
        # 将 PDF 转换为图片列表
        images = pdf_to_images(pdf_path)
        print(f"  → PDF 共 {len(images)} 页")

        results = []

        # 并发处理所有页面，并发度为 5
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_page = {
                executor.submit(self._process_single_page, image, idx): idx
                for idx, image in enumerate(images, 1)
            }

            # 按完成顺序收集结果
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    invoice_data = future.result()
                    if invoice_data is not None:
                        results.append(invoice_data)
                        print(f"  ✓ 第 {page_num} 页处理完成，识别到发票")
                except Exception as e:
                    print(f"  ✗ 处理第 {page_num} 页时出错: {e}")

        return results

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
                    data_list = future.result()  # 现在返回的是列表
                    invoice_count = 0
                    for data in data_list:
                        if data.is_invoice:
                            # 为每个发票数据设置文件名（不再包含页码）
                            data.filename = filename
                            all_data.append(data)
                            invoice_count += 1

                    completed += 1
                    if invoice_count > 0:
                        print(f"✓ 已完成: {filename} - 识别到 {invoice_count} 张发票 ({completed}/{total})")
                    else:
                        print(f"✓ 已完成: {filename} - 未识别到发票 ({completed}/{total})")

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

        # 按文件名和页码排序
        all_data.sort(key=lambda x: (x.filename, x.page_number))

        # 展开数据：每个item独立成一行
        rows = []
        for invoice in all_data:
            # 基础发票信息（不包含items）
            base_info = {
                "发票文件": invoice.filename,
                "页码": invoice.page_number,
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
            "/Users/zouguodong/Downloads/深圳福克森-李雨霏报销2025.10.14_20251014153857.pdf",
            "/Users/zouguodong/Downloads/零食发票 6.pdf",
        ],
        excel_path="/Users/zouguodong/Downloads/发票信息统计.xlsx",
    )
