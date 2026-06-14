# infra_ping_checker

> 大规模 DevOps 基础设施网络拓扑存活状态并发检测与资产健康走查核心利器

基于 Python `asyncio` 的高并发 ICMP Ping 探测工具库，专为 DevOps 基础设施存活状态批量巡检场景设计。零生产依赖，开箱即用。

---

## 特性

- **高并发探测** — 基于 `asyncio` 信号量控制，支持数百目标同时扫描
- **零生产依赖** — 仅使用 Python 标准库，部署极简
- **跨平台兼容** — 自动适配 Windows / Linux / macOS 的 `ping` 参数差异
- **PEP 517/621** — 使用现代 Python 打包标准，兼容 `pip`、`build`、`uv` 等工具链
- **CLI 入口** — 安装后即提供 `infra-ping-cli` 命令行工具

---

## 环境要求

- Python >= 3.8

---

## 快速开始

### 1. 创建并激活本地虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活（Linux / macOS）
source .venv/bin/activate

# 激活（Windows CMD）
.venv\Scripts\activate.bat

# 激活（Windows PowerShell）
.venv\Scripts\Activate.ps1
```

### 2. 安装项目及开发依赖

```bash
# 以可编辑模式安装项目本体（零额外生产依赖）
pip install -e .

# 安装开发期测试依赖（pytest）
pip install -e ".[dev]"
```

### 3. 使用 CLI 工具

```bash
# 探测单个主机
infra-ping-cli 127.0.0.1

# 批量探测多个主机
infra-ping-cli 127.0.0.1 192.168.1.1 google.com
```

### 4. 在代码中调用

```python
from infra_ping_checker import concurrent_ping_hosts, is_valid_ip_address

# 校验 IP 地址合法性
print(is_valid_ip_address("192.168.1.1"))   # True
print(is_valid_ip_address("999.999.999"))   # False

# 高并发批量探测
results = concurrent_ping_hosts(
    hosts=["127.0.0.1", "192.168.1.1", "10.0.0.1"],
    concurrency=50,
    timeout=2.0,
)

for r in results:
    status = "UP" if r["alive"] else "DOWN"
    print(f"{r['host']}: {status}")
```

---

## 构建与打包

使用标准 `build` 前端将项目编译为 Wheel（`.whl`）与源码包（`.tar.gz`）：

```bash
# 安装构建工具
pip install build

# 在项目根目录执行构建
python -m build
```

构建完成后，产物位于 `dist/` 目录：

```
dist/
├── infra_ping_checker-0.1.0-py3-none-any.whl   # Wheel 二进制包
└── infra_ping_checker-0.1.0.tar.gz              # 源码分发包 (sdist)
```

### 发布到 PyPI（可选）

```bash
pip install twine
twine upload dist/*
```

---

## 运行测试

```bash
pytest
```

---

## 项目结构

```
infra_ping_checker/
├── pyproject.toml                  # PEP 517/621 项目配置
├── README.md                       # 本文档
└── src/
    └── infra_ping_checker/
        ├── __init__.py             # 包入口，导出公共 API
        └── net_util.py             # 网络探测核心模块
```

---

## 许可证

MIT
