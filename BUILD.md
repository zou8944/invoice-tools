# 打包说明文档

## 环境准备

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv sync
uv pip install pyinstaller pyqt6

# 或使用 pip
pip install -r requirements.txt
pip install pyinstaller pyqt6
```

### 2. 配置 API 密钥

在 [config.py](config.py) 中配置你的 DeepSeek API 密钥，或通过环境变量设置：

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-chat"
```

## 开发测试

### 运行 GUI 应用

```bash
# 使用 uv
uv run python gui.py

# 或直接运行
python gui.py
```

### 运行命令行版本

```bash
python financial.py
```

## 打包应用

### macOS 打包

```bash
# 方式1: 使用 spec 文件（推荐）
pyinstaller build.spec

# 方式2: 使用命令行参数
pyinstaller --onefile \
            --windowed \
            --name="invoice-tools" \
            --hidden-import=pdfplumber \
            --hidden-import=pdfminer \
            --hidden-import=PIL \
            --hidden-import=pandas \
            --hidden-import=openpyxl \
            --hidden-import=openai \
            gui.py
```

**输出位置:**
- 使用 spec 文件: `dist/invoice-tools.app`
- 使用命令行: `dist/invoice-tools.app`

**运行打包后的应用:**
```bash
open dist/invoice-tools.app
```

### Windows 打包

在 Windows 系统上执行:

```bash
# 使用命令行参数
pyinstaller --onefile ^
            --windowed ^
            --name="invoice-tools" ^
            --hidden-import=pdfplumber ^
            --hidden-import=pdfminer ^
            --hidden-import=PIL ^
            --hidden-import=pandas ^
            --hidden-import=openpyxl ^
            --hidden-import=openai ^
            gui.py
```

**输出位置:** `dist/invoice-tools.exe`

**注意事项:**
- Windows Defender 可能会误报，需要添加信任
- 首次运行可能需要管理员权限

### Linux 打包

在 Linux 系统上执行:

```bash
# 使用命令行参数
pyinstaller --onefile \
            --windowed \
            --name="invoice-tools" \
            --hidden-import=pdfplumber \
            --hidden-import=pdfminer \
            --hidden-import=PIL \
            --hidden-import=pandas \
            --hidden-import=openpyxl \
            --hidden-import=openai \
            gui.py
```

**输出位置:** `dist/invoice-tools`

**运行:**
```bash
chmod +x dist/invoice-tools
./dist/invoice-tools
```

## 常见问题

### 1. 打包后体积过大

- 使用虚拟环境打包，避免打包不必要的依赖
- 使用 `--exclude-module` 排除不需要的模块
- 考虑使用 UPX 压缩（已在 spec 文件中启用）

### 2. 打包后无法运行

- 检查是否缺少隐藏导入（hidden imports）
- 查看 `build/` 目录下的日志文件
- 使用 `--console` 参数查看错误信息

### 3. macOS 安全提示

首次运行可能提示"无法验证开发者"：

```bash
# 移除隔离属性
xattr -cr dist/invoice-tools.app
```

或在"系统偏好设置 > 安全性与隐私"中允许运行

### 4. API 密钥安全

**不要**在打包的应用中硬编码 API 密钥！建议：

1. 使用环境变量
2. 让用户在 GUI 中输入
3. 使用配置文件（不包含在版本控制中）

## 跨平台打包方案

由于 PyInstaller 无法真正跨平台打包，需要：

### 方案1: 在各平台分别打包

1. 在 macOS 上打包生成 `.app`
2. 在 Windows 上打包生成 `.exe`
3. 在 Linux 上打包生成可执行文件

### 方案2: 使用 CI/CD 自动打包

使用 GitHub Actions 等 CI/CD 工具在云端自动打包：

```yaml
# .github/workflows/build.yml 示例
name: Build
on: [push]
jobs:
  build-macos:
    runs-on: macos-latest
    # ... 打包步骤
  build-windows:
    runs-on: windows-latest
    # ... 打包步骤
  build-linux:
    runs-on: ubuntu-latest
    # ... 打包步骤
```

### 方案3: Web 应用替代

如果需要真正的跨平台支持，考虑将应用改为 Web 应用：

- 使用 Flask/FastAPI 作为后端
- 使用 HTML/CSS/JS 作为前端
- 打包为本地服务器，浏览器访问


## 优化建议

1. **减小体积**: 使用虚拟环境，只安装必要依赖
2. **提升启动速度**: 延迟导入大型库
3. **增强安全性**: 不在代码中硬编码密钥
4. **改善用户体验**: 添加应用图标、启动画面
5. **错误处理**: 完善异常捕获和用户提示
