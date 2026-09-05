# FutureValue Ark 直接使用指南

## 路径一：无需安装

双击：

```text
DIKWP_FUTURE_VALUE_ARK_v1.0.0.html
```

现代 Chrome、Edge、Firefox 或 Safari 均可使用。页面不需要互联网。

### 操作顺序

1. 在“目标、现金流与约束”中填写必要支出、储备月数和近期支出。
2. 选择风险档案和 ACEVO 警戒预设。
3. 在“当前资产类别”中填写各类资产当前市值。
4. 核对存款保险声明上限和机构数量。
5. 展开情景矩阵，修改您不同意的压力回报假设。
6. 点击“分析并生成资产区间”。
7. 先处理 HIGH 风险提示，再查看目标区间和新增资金计划。
8. 导出 JSON、CSV 或 Markdown，保留本次决策依据。

### 导入 CSV

支持最简单的两列 CSV：

```csv
asset_id,amount
cash,300000
short_gov,160000
inflation_linked,90000
quality_bonds,90000
global_equity,250000
ai_tech,120000
gold,70000
commodities,20000
real_assets,30000
foreign_reserve,0
speculative,0
```

## 路径二：Python 命令行

```bash
python -m pip install dikwp_valueark-1.0.0-py3-none-any.whl
valueark demo --workspace .valueark-demo --reset
```

分析自己的 JSON：

```bash
valueark analyze my-portfolio.json \
  --workspace .valueark-run \
  --reset
```

输出本地交互应用：

```bash
valueark export-html DIKWP_FUTURE_VALUE_ARK.html
```

本地启动：

```bash
valueark serve --directory .valueark-app --port 8765
```

服务器只绑定 `127.0.0.1`。

## 结果解释

- **声明情景最差回报**：只在当前输入的情景集合中成立。
- **尾部25%均值**：把权重最差的一组世界按重要性汇总。
- **声明情景财富底线**：不是现实保证下限。
- **目标换手率**：当前组合变到目标组合所需的单边权重变化。
- **目标区间**：近优组合形成的可容忍范围；区间内通常不需要精确调整。
- **新增资金方案**：把当月新增资金优先配置给低于下限的资产类别。

## 复核频率

默认建议是每六至十二个月或越过区间时复核；出现失业、退休、婚姻、照护、医疗、住房、迁移、税务或重大收入变化时应立即重算。
