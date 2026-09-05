# DIKWP FutureValue Ark OS v1.0.0

**AI文明时代个人资产保值与投资韧性决策支持系统**

运行标识：

```text
MESH95_REAL_WEALTH_FLOOR_PLURAL_WORLDS_NO_LEVERAGE_REBALANCE_CLOSURE
```

FutureValue Ark 不是行情预测软件，也不推荐具体证券。它把个人资产配置重构为一个可审计的多世界决策问题：先声明生活责任、应急资金、近期支出和不可承受风险，再在多个互相冲突的通胀、通缩、AI生产率、AI估值反转、多Agent控制面、供应链碎片化和相关性失效世界中寻找有硬护栏的资产类别区间。

## 最快使用

无需安装：双击根目录中的：

```text
DIKWP_FUTURE_VALUE_ARK_v1.0.0.html
```

该页面完全离线，不加载网络脚本，不连接券商，不上传输入，也不执行交易。

## Python 运行

```bash
python -m pip install -e .
valueark demo --workspace .valueark-demo --reset
```

或者：

```bash
PYTHONPATH=src python -m dikwp_valueark demo \
  --workspace .valueark-demo \
  --reset
```

输出：

```text
analysis.json
valueark-report.md
valueark-report.html
futurevalue-ark.html
```

## 输入逻辑

用户输入：

- 当前广泛资产类别金额；
- 计价货币和主要法域；
- 每月必要支出；
- 应急储备月数；
- 未来二十四个月确定支出；
- 每月新增可投资金额；
- 目标期限；
- 存款保险声明容量；
- 高成本债务；
- 多世界重要性权重；
- 各情景压力回报和长期实际回报假设。

## 输出逻辑

系统输出：

- 当前组合的多世界压力结果；
- 应急流动性底线；
- 存款保险容量缺口；
- 权益、AI主题和投机仓硬上限检查；
- 多约束目标配置；
- 近优候选形成的目标区间；
- 再平衡金额和“先用新增资金纠偏”方案；
- 声明情景中的最差回报和尾部25%均值；
- 可导出的 JSON、CSV 和 Markdown 报告。

## 不可覆盖的边界

```text
automatic_trade_authority = 0
automatic_broker_connection = 0
leverage_allowed = false
short_selling_allowed = false
derivatives_recommendation = false
specific_security_recommendation = false
scenario_numbers_are_forecasts = false
```

## 项目结构

```text
src/dikwp_valueark/       Python参考内核
src/.../resources/        默认情景与离线HTML应用
examples/                 合成组合和CSV模板
schemas/                  JSON Schema
tests/                    自动化测试
tools/                    静态审计和发布工具
formal/                   有限状态检查和TLA+草案
docs/                     方法、使用、来源和边界
```

## 重要限制

- 所有回报数值都是可编辑压力测试假设，不是预测。
- “声明情景财富底线”只覆盖当前输入的情景集合，不是现实保证下限。
- 软件不处理个体税务、福利、养老金、继承、跨境资金、具体产品信用和托管风险。
- 存款保险结果依赖机构资格、账户类别、所有权结构、应计利息和法域；软件不验证账户。
- 任何实际调整均由使用者决定；高影响或复杂事项应由适用法域的持牌专业人士复核。
- HTML 与 Python 内核分别使用各自的固定种子伪随机实现；硬约束和评分结构相同，但可能从近优集合中选出不同目标点。

## 许可证

Apache License 2.0。见 `LICENSE`。
