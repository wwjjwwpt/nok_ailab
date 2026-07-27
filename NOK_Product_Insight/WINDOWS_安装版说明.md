# Windows 安装版说明

## 最终生成文件

在 Windows 10/11 64位电脑上双击：

```text
build_windows_installer.bat
```

构建完成后，`release` 文件夹会出现：

```text
NOK_Product_Insight_Setup_v1.1.0_x64.exe
NOK_Product_Insight_Portable_v1.1.0_x64.exe
```

- `Setup` 是正式安装版，提供安装向导、桌面快捷方式、开始菜单和卸载入口。
- `Portable` 是免安装单文件版，可以直接双击运行。

## 构建电脑要求

- Windows 10 或 Windows 11，64位；
- Python 3.11 或 Python 3.12，64位；
- 能访问互联网以安装 Python 打包依赖；
- Inno Setup 6。

脚本找不到 Inno Setup 时，会询问是否通过 Windows `winget` 自动安装。也可以从以下地址手动安装：

```text
https://jrsoftware.org/isdl.php
```

## 安装后的功能

- 安装到当前用户目录，不强制要求管理员权限；
- 创建开始菜单快捷方式；
- 默认勾选创建桌面快捷方式；
- 在 Windows“已安装的应用”中提供卸载入口；
- 用户导入 Excel 后自动解析产品、月度销量、库存、采购和客户数据；
- 展示总览、产品多指标清单、产品详情、风险预警和指标说明；
- 支持导出8个工作表的经营分析报告。

## 注意

Windows 安装包需要在 Windows 上生成。PyInstaller 会调用当前系统的 Windows 引导程序和动态库，因此不能在 macOS 上可靠地直接生成 Windows EXE。

如果要对外分发，建议购买代码签名证书并对安装包签名，这样可以降低 Windows SmartScreen 的未知发布者提示。
