# B1 Pipeline

[![Tests](https://github.com/ysonglala/b1-pipeline/actions/workflows/tests.yml/badge.svg)](https://github.com/ysonglala/b1-pipeline/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](./pyproject.toml)

B1 半自动选股流水线。

这是一个面向 **A 股日线级别 B1 机会挖掘** 的半自动研究/筛选项目，目标不是全自动下单，而是把“抓数 → 特征加工 → 候选筛选 → 图表导出 → review 打分 → 最终 shortlist”这条链路稳定下来，帮助人工决策更快、更一致。

## 项目定位

这个项目当前更接近：

- **研究型选股工程**，不是量化交易执行系统
- **半自动 shortlist 生成器**，不是黑盒买卖信号机
- **持续迭代的策略工程骨架**，不是最终定版产品

当前核心目标是：

> 每天产出一个质量足够高的 top list，帮助人工从中挑出更值得重点审查的 1~2 个机会。

---

## 当前流水线

目前已经打通的主要阶段：

1. **fetch**：拉取股票基础信息、日线数据、市值快照
2. **preprocess**：计算指标与结构特征
3. **preselect**：做第一轮 B1 海选/候选池构建
4. **export_charts**：导出 review 图表和 review 输入
5. **review**：对候选池做二次打分与排序
6. **summary**：输出最终 shortlist 供人工判断

---

## 设计原则

### 1. 宁可在前面少做误杀，也不要把强票早早筛掉

当前 preselect 层更强调 **减少漏票**，而不是一开始就用过严条件强砍。

### 2. 更严格的质量判断，尽量后移到 review 层

也就是说：

- 海选层偏召回
- review 层偏排序
- 最终决策仍然保留给人工

### 3. 这是辅助判断系统，不是假装“自动赚钱”的神棍脚本

项目当前明确不是：

- 自动交易系统
- 收益承诺工具
- 投资建议产品

---

## 当前策略理解（简版）

当前 B1 方向更重视这些特征：

- J 值低位，尤其深低位 / 负值
- 价格回踩后仍保有结构支撑
- 白线 / 黄线位置与距离关系
- 缩量回调、时间换空间、小 K 消化
- 靠近白线、黄线或关键支撑区域
- 回调阶段的量价关系优于前期拉升阶段

当前系统的判断理念大致是：

> 好的 B1 不一定长得完全一样，但通常都有“趋势未死、回调可控、量能收敛、位置不差、盈亏比还在”这些共性。

---

## 项目结构

```text
b1_pipeline/
├─ config/          # 策略参数与流程配置
├─ scripts/         # 可直接运行的入口脚本
├─ src/             # 核心代码
├─ tests/           # 测试
├─ examples/        # 脱敏示例输出
├─ data/            # 本地数据（已被 git ignore）
├─ logs/            # 本地日志（已被 git ignore）
├─ docs/            # 额外说明文档
├─ .github/         # CI workflows
├─ CHANGELOG.md     # 变更记录
├─ ROADMAP.md       # 迭代路线图
├─ CONTRIBUTING.md  # 贡献说明
├─ pyproject.toml   # 项目元数据与测试配置
├─ LICENSE          # 开源许可
└─ README.md
```

补充文档：

- [CHANGELOG](./CHANGELOG.md)
- [ROADMAP](./ROADMAP.md)
- [Contributing](./CONTRIBUTING.md)
- [Development Notes](./docs/development.md)
- [Sample Outputs Guide](./docs/sample_outputs.md)
- [Sanitized Example Artifacts](./examples/README.md)

---

## 环境准备

推荐：

- Python 3.11+
- Windows PowerShell / macOS / Linux 均可

安装依赖：

```bash
pip install -r requirements.txt
```

或者使用可编辑安装：

```bash
pip install -e .
pip install pytest
```

---

## Tushare Token 配置

项目默认优先从环境变量读取：`TUSHARE_TOKEN`

### Windows PowerShell

```powershell
$env:TUSHARE_TOKEN="your_token_here"
```

### macOS / Linux

```bash
export TUSHARE_TOKEN="your_token_here"
```

说明：

- 不要把真实 token 提交进 git
- 当前仓库中的 `config/fetch.yaml` 使用的是占位符写法
- `.env.example` 仅作示意，不应存放真实私钥

---

## 推荐日常跑法

经过目前的工程实践，日常更推荐：

- **增量抓取**，而不是每天 full refetch
- **staged preprocess**，而不是一上来全市场 heavy full preprocess

### 默认日常流程

```bash
py scripts/run_fetch.py --end-date YYYY-MM-DD
py scripts/run_preprocess.py --stage light --date YYYY-MM-DD
py scripts/run_preprocess.py --stage full --codes-from .\data\light_candidates\light_candidates_YYYY-MM-DD.json
py scripts/run_preselect.py --date YYYY-MM-DD
py scripts/run_export_charts.py --date YYYY-MM-DD
py scripts/run_review.py --date YYYY-MM-DD
```

### Fetch 模式

```bash
py scripts/run_fetch.py --mode incremental --end-date YYYY-MM-DD
py scripts/run_fetch.py --mode full --start-date 2025-01-01 --end-date YYYY-MM-DD
```

说明：

- `incremental`：默认模式，适合日常运行
- `full`：适合修库、补历史、排障
- 正常场景下，优先走 `incremental`

---

## 示例输出

如果你只是想先快速理解这个项目会产出什么，而不是立刻跑全流程，可以先看：

- [examples/sample_review_result.json](./examples/sample_review_result.json)
- [examples/sample_summary.md](./examples/sample_summary.md)

这些文件是 **脱敏示例**，用于展示 review 输出的大致结构，不代表真实交易建议。

---

## 测试

```bash
pytest tests
```

当前测试仍然偏基础，后续应继续补：

- 特征计算单测
- 配置驱动测试
- 关键评分逻辑回归测试
- 样本 case 验证测试

---

## 工程经验 / 坑点

### 1. 工作目录必须对

部分脚本使用项目相对路径。如果从错误目录启动，数据可能会被写进错误的 `data/` 目录。

**建议：始终在项目根目录下运行脚本。**

### 2. `market_cap.csv` 应保持为全市场快照

历史上，subset fetch 曾有覆盖全市场市值快照的问题，进而导致后续筛选阶段大量股票 `market_cap` 变成 NaN。

当前处理原则：

- 子集抓取（`--codes` / `--limit`）时，不重写全市场 `market_cap.csv`
- 全市场日常增量流程可正常刷新快照

---

## 安全说明

仓库当前有这些保护：

- `data/` 已忽略，不上传本地大数据
- `logs/` 已忽略，不上传本地日志
- token 默认从环境变量读取，不建议写死到版本库

如果你要把仓库分享给其他人，建议继续遵守：

1. 不提交真实 token
2. 不提交本地数据快照
3. 不提交私有实验日志
4. 对外展示前先做一次公开内容审查

---

## 当前状态

项目仍在持续迭代中。

当前阶段的重点不是“再加更多规则”，而是：

- 提升前排 shortlist 的真实质量
- 更准确地下调脏结构、低盈亏比、过度修复后的候选
- 让 top list 更接近真实人工审美和实际出手意愿

---

## 免责声明

本项目仅用于个人研究、策略工程整理和流程验证，不构成任何投资建议。
