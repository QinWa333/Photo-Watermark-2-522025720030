@echo off
title 水印处理工具 - 一键打包
color 0A
chcp 65001 > nul

echo.
echo ========================================
echo         水印处理工具 - 一键打包        
echo ========================================
echo.

:: 检查Python环境
echo [1/6] 检查Python环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo    请先安装Python 3.7或更高版本
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

:: 安装依赖
echo.
echo [2/6] 安装打包依赖...
echo    正在检查pathlib冲突...
pip uninstall pathlib -y 2>nul
echo    正在安装PyInstaller...
pip install pyinstaller pillow
if errorlevel 1 (
    echo ❌ 依赖安装失败，尝试使用国内镜像...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller pillow
    if errorlevel 1 (
        echo ❌ 安装失败，请手动执行: pip install pyinstaller pillow
        pause
        exit /b 1
    )
)
echo ✅ 依赖安装完成

:: 清理旧文件
echo.
echo [3/6] 清理旧文件...
if exist "build" rmdir /s /q "build" > nul 2>&1
if exist "dist" rmdir /s /q "dist" > nul 2>&1
if exist "*.spec" del /q "*.spec" > nul 2>&1
if exist "水印处理工具_发布版" rmdir /s /q "水印处理工具_发布版" > nul 2>&1
echo ✅ 清理完成

:: 开始打包
echo.
echo [4/6] 开始打包应用程序...
echo    这可能需要几分钟时间，请耐心等待...
pyinstaller --onefile --windowed --name="水印处理工具" --distpath="./dist" --workpath="./build" watermark_app.py

if not exist "dist\水印处理工具.exe" (
    echo ❌ 打包失败！
    echo    请检查上方的错误信息
    pause
    exit /b 1
)
echo ✅ 应用程序打包完成

:: 创建发布文件夹
echo.
echo [5/6] 创建发布包...
mkdir "水印处理工具_发布版" > nul 2>&1

:: 复制主程序
copy "dist\水印处理工具.exe" "水印处理工具_发布版\" > nul
echo ✅ 主程序复制完成

:: 复制文档
copy "使用指南.md" "水印处理工具_发布版\" > nul 2>&1
copy "操作说明.txt" "水印处理工具_发布版\" > nul 2>&1
copy "README.md" "水印处理工具_发布版\" > nul 2>&1

:: 创建启动脚本
echo @echo off > "水印处理工具_发布版\启动水印工具.bat"
echo title 水印处理工具 >> "水印处理工具_发布版\启动水印工具.bat"
echo chcp 65001 ^> nul >> "水印处理工具_发布版\启动水印工具.bat"
echo echo 正在启动水印处理工具... >> "水印处理工具_发布版\启动水印工具.bat"
echo echo 请稍候... >> "水印处理工具_发布版\启动水印工具.bat"
echo start "" "水印处理工具.exe" >> "水印处理工具_发布版\启动水印工具.bat"

:: 创建用户说明
echo 水印处理工具 - 使用说明 > "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo ======================================= >> "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo 快速开始： >> "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo 1. 双击"水印处理工具.exe"启动程序 >> "水印处理工具_发布版\使用说明.txt"
echo    或双击"启动水印工具.bat" >> "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo 2. 操作步骤： >> "水印处理工具_发布版\使用说明.txt"
echo    1 导入图片 - 点击"选择图片"或"选择文件夹" >> "水印处理工具_发布版\使用说明.txt"
echo    2 设置水印 - 选择"文本水印"或"图片水印" >> "水印处理工具_发布版\使用说明.txt"
echo    3 调整位置 - 使用预设位置或直接拖拽 >> "水印处理工具_发布版\使用说明.txt"
echo    4 配置导出 - 选择输出文件夹和格式 >> "水印处理工具_发布版\使用说明.txt"
echo    5 开始处理 - 点击"开始批量导出" >> "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo 重要提示： >> "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo - 中文水印请选择"微软雅黑"字体 >> "水印处理工具_发布版\使用说明.txt"
echo - 输出文件夹必须与原图片文件夹不同 >> "水印处理工具_发布版\使用说明.txt"
echo - 推荐使用PNG格式保持最佳质量 >> "水印处理工具_发布版\使用说明.txt"
echo - 程序内有"帮助"按钮可查看详细说明 >> "水印处理工具_发布版\使用说明.txt"
echo. >> "水印处理工具_发布版\使用说明.txt"
echo 系统要求：Windows 7/8/10/11，无需Python环境 >> "水印处理工具_发布版\使用说明.txt"

:: 完成
echo.
echo [6/6] 打包完成！
echo.
echo ========================================
echo               打包成功！            
echo ========================================
echo.
echo 📁 发布文件夹: 水印处理工具_发布版
echo 📦 文件大小: 约50-80MB
echo.
echo 用户使用方法:
echo    1. 下载"水印处理工具_发布版"文件夹
echo    2. 双击"水印处理工具.exe"运行
echo    3. 或双击"启动水印工具.bat"运行
echo.
echo 注意事项:
echo    - 首次启动可能需要几秒钟
echo    - 某些杀毒软件可能误报，请添加信任
echo    - 建议在不同Windows系统上测试
echo.
echo 按任意键打开发布文件夹...
pause > nul
explorer "水印处理工具_发布版"