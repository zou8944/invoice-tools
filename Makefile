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
	uv run python excel_renamer.py

build: clean
	@echo "Building application..."
	uv run pyinstaller excel_renamer.spec
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
	@cd dist && zip -r "Excel Sheet Renamer.zip" "Excel Sheet Renamer.app"
	@echo "Package created: dist/Excel Sheet Renamer.zip"
	@echo ""
	@echo "分享说明："
	@echo "1. 将 dist/Excel Sheet Renamer.zip 发送给其他人"
	@echo "2. 接收者解压后，右键点击应用选择'打开'"
	@echo "3. 或者运行: xattr -cr 'Excel Sheet Renamer.app'"

run:
	@if [ -d "dist/Excel Sheet Renamer.app" ]; then \
		open "dist/Excel Sheet Renamer.app"; \
	else \
		echo "Application not found. Run 'make build' first."; \
	fi
