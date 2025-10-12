"""Configuration file for invoice extractor"""

import os

import dotenv

dotenv.load_dotenv()

# DeepSeek API Configuration
# You can set these via environment variables or modify directly here
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL")

# Processing Configuration
MAX_WORKERS = 5  # Concurrent processing threads

# Default paths
DEFAULT_OUTPUT_FILENAME = "发票信息统计.xlsx"
