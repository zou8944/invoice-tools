"""Configuration file for invoice extractor"""

import os
import sys
from pathlib import Path

import dotenv

# 处理 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    # 打包后的应用
    application_path = Path(sys._MEIPASS)  # type: ignore
else:
    # 开发环境
    application_path = Path(__file__).parent

# 加载 .env 文件
env_path = application_path / '.env'
dotenv.load_dotenv(env_path)

# DeepSeek API Configuration
# You can set these via environment variables or modify directly here
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

# Processing Configuration
MAX_WORKERS = 5  # Concurrent processing threads

# Default paths
DEFAULT_OUTPUT_FILENAME = "发票信息统计.xlsx"
