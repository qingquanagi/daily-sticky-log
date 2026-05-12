# 日常问题便签 Windows 版

这是一个无依赖的 Windows 桌面便签，用 Python Tkinter 实现。适合一直放在桌面边缘，随手记录每天工作内容、问题、处理状态和复盘。

## 使用

推荐双击 `dist/DailyStickyLog.exe` 启动，不需要安装 Python。

开发调试时也可以双击 `run.bat` 启动。

数据保存在当前目录的 `records.json`，不会上传到网络。

## 功能

- 置顶窗口，适合当桌面便签使用。
- 新增记录区默认折叠，列表区也可折叠。
- 记录日期、类型、标题、内容、状态和标签。
- 支持待处理、处理中、已完成状态。
- 支持搜索和状态筛选。
- 支持一键完成、重开、删除、清理已完成。
- 支持导出当前筛选结果为 Markdown。

## 快捷键

- `Ctrl+N`：展开新增记录。
- `Ctrl+S`：保存当前记录。
- `Ctrl+L`：折叠或展开列表。
- `Esc`：清空新增表单。

## 文件

- `sticky_log.py`：桌面便签主程序。
- `run.bat`：Windows 启动脚本。
- `dist/DailyStickyLog.exe`：打包后的单文件 Windows 程序。
- `records.json`：运行后自动生成的数据文件。
