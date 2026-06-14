# pipeline_yaml_parser

> DevOps CI/CD 流水线配置文件静态走查与解析工具

`pipeline_yaml_parser` 是一个基于现代 Python 打包标准（PEP 517 / PEP 621）构建的基础设施工具，用于对 CI/CD 流水线 YAML 配置文件进行加载、结构化解析及语法合规性校验。

---

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
  - [1. 激活本地 venv 隔离环境](#1-激活本地-venv-隔离环境)
  - [2. 一键部署开发依赖](#2-一键部署开发依赖)
- [构建产物](#构建产物)
- [命令行工具](#命令行工具)
- [项目结构](#项目结构)

---

## 环境要求

| 依赖项       | 最低版本 |
| ------------ | -------- |
| Python       | ≥ 3.8    |
| pip          | ≥ 21.3   |
| build        | ≥ 0.7    |

---

## 快速开始

### 1. 激活本地 venv 隔离环境

在项目根目录下创建并激活虚拟环境：

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD)**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 一键部署开发依赖

以可编辑模式安装项目本身及其运行时依赖，并附加安装 `dev` 可选依赖组（含 `black` 等开发工具）：

```bash
pip install --upgrade pip build
pip install -e ".[dev]"
```

> **说明**：`-e` 表示可编辑安装（editable install），代码修改后无需重新安装即可立即生效。`[dev]` 段落包含 `black` 等仅开发阶段需要的工具，不会污染生产运行时环境。

---

## 构建产物

使用官方推荐的 `build` 前端，执行以下标准打包命令即可同时生成干净的 `.whl`（Wheel 产物）与 `.tar.gz`（sdist 源码包），且不会产生编译警告：

```bash
python -m build
```

构建完成后，产物位于 `dist/` 目录：

```
dist/
├── pipeline_yaml_parser-0.1.0-py3-none-any.whl
└── pipeline_yaml_parser-0.1.0.tar.gz
```

> **提示**：若希望分别构建，可使用 `python -m build --wheel` 或 `python -m build --sdist`。

---

## 命令行工具

安装后，终端中将自动注册 `pipeline-lint-cli` 命令：

```bash
pipeline-lint-cli path/to/pipeline.yml [path/to/another.yml ...]
```

该命令会对指定的 YAML 文件执行：
1. 加载并结构化解析
2. 逐个 Stage 语法合规性校验
3. 输出校验结果，失败时以非零退出码终止

---

## 项目结构

```
.
├── pyproject.toml                          # PEP 517/621 项目元数据与构建配置
├── README.md                               # 项目说明文档
├── src/
│   └── pipeline_yaml_parser/
│       ├── __init__.py                     # 包入口，导出公共 API
│       └── parser.py                       # 核心解析与校验模块
└── dist/                                   # 构建产物目录（由 python -m build 生成）
```
