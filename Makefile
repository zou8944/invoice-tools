.PHONY: help install clean build run dev package

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make dev        - Run the application in development mode"
	@echo "  make build      - Build the application using PyInstaller"
	@echo "  make package    - Build and package the application for distribution"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make run        - Run the built application (macOS)"

install:
	uv sync --all-extras

dev:
	uv run python gui.py

build: clean
	@echo "Building application..."
	uv run pyinstaller build.spec
	@echo "Removing redundant executable..."
	rm -f dist/发票解析工具
	@echo "Build complete! Application is in dist/"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

package: build
	@echo "Packaging application for distribution..."
	@cd dist && zip -r 发票解析工具.zip 发票解析工具.app
	@echo "Package created: dist/发票解析工具.zip"
	@echo ""
	@echo "分享说明："
	@echo "1. 将 dist/发票解析工具.zip 发送给其他人"
	@echo "2. 接收者解压后，右键点击应用选择'打开'"
	@echo "3. 或者运行: xattr -cr 发票解析工具.app"

run:
	@if [ -d "dist/发票解析工具.app" ]; then \
		open "dist/发票解析工具.app"; \
	else \
		echo "Application not found. Run 'make build' first."; \
	fi
