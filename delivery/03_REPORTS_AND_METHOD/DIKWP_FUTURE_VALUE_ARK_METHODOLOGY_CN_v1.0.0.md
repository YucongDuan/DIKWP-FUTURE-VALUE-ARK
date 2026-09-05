# FutureValue Ark 数学与决策方法

## 1. 目标函数不是“收益最大化”

设资产类别集合为 \(A\)，条件世界集合为 \(W\)，资产权重为：

\[
\mathbf x=(x_1,\ldots,x_n),\qquad x_i\ge0,\quad \sum_i x_i=1
\]

系统禁止负权重、杠杆和做空。每个世界 \(w\) 给出一组可编辑的实际回报压力值 \(r_{iw}\)。组合在该世界的净实际回报为：

\[
R_w(\mathbf x)=\sum_i x_i r_{iw}-Fee(\mathbf x)
\]

系统计算：

\[
R_{min}=\min_w R_w
\]

\[
CVaR_{25}=\text{重要性加权的最差25%世界均值}
\]

\[
\bar R=\sum_w q_wR_w
\]

其中 \(q_w\) 是决策重要性权重，不被解释为真实概率。

评分函数为：

\[
J(\mathbf x)=
\alpha R_{min}
+\beta CVaR_{25}
+\gamma \bar R
-\delta\sigma_W
-\eta Turnover
-\kappa HHI
\]

不同风险档案使用不同参数。系统先满足硬约束，再比较评分，因此高平均回报不能洗白流动性缺口、主题集中或投机上限违反。

## 2. 真实购买力底线

应急资金需求：

\[
L=MonthlyEssentialExpense\times ReserveMonths+NearTermOutflows
\]

流动性权重下限：

\[
\ell_{min}=\min\left(0.95,\frac{L}{PortfolioValue}\right)
\]

现金和短期主权工具权重必须满足：

\[
x_{cash}+x_{short\_gov}\ge\ell_{min}
\]

这是一项生活约束，不是市场观点。

## 3. 风险档案硬约束

### 保值优先

\[
Equity\le30\%,\quad AI\le8\%,\quad Speculative=0,\quad InflationHedge\ge20\%
\]

### 平衡韧性

\[
Equity\le55\%,\quad AI\le12\%,\quad Speculative\le3\%,\quad InflationHedge\ge15\%
\]

### 增长有护栏

\[
Equity\le75\%,\quad AI\le18\%,\quad Speculative\le5\%,\quad InflationHedge\ge10\%
\]

这些只是软件默认边界，使用者可以在源码中改变；改变边界不等于获得更高真实收益。

## 4. 目标区间

系统对满足全部硬约束的候选组合排序，在近优集合中计算每一资产的第10和第90百分位，并与档案的无交易带合并，形成：

\[
[Lower_i,Target_i,Upper_i]
\]

这比输出一个看似精确的百分比更诚实，也减少因微小模型变化产生的过度交易。

## 5. 声明情景财富底线

\[
WealthFloor_{declared}=V_0(1+R_{min})
\]

它必须始终被称为“声明情景财富底线”，因为现实可能出现未输入的损失、信用违约、账户冻结、汇率错配、税费或操作失败。它不是本金保证。

## 6. 长期实际价值

每个资产类别带有可编辑的长期实际回报假设 \(g_i\)：

\[
g_p=\sum_i x_ig_i-Fee(\mathbf x)
\]

\[
V_H=V_0(1+g_p)^H
\]

该值只用于敏感性讨论，不构成预期收益或概率预测。

## 7. 搜索方法

参考内核采用固定种子的构造式随机搜索：

1. 在流动性下限上方抽取流动性总量；
2. 满足通胀对冲下限；
3. 在权益、AI主题、稳定资产和投机仓上限内拆分；
4. 计算多世界指标和目标函数；
5. 保留最优及近优样本。

它在同一实现、相同输入和相同种子下可重放、易审计、无第三方运行依赖，但不能证明已经找到数学上的全局最优。HTML 与 Python 使用不同的确定性伪随机实现，因此可能从同一近优区域选出不同目标点；这不应被解释为任一结果更“真实”。

## 8. 为什么加入相关性失效情景

若模型中的每个世界都有一个资产恰好上涨，优化器可能构造出“所有声明世界都盈利”的假象。相关性失效与托管可达性情景强制承认：危机时多个资产可能同时下跌，账户或支付也可能短期不可达。该情景仍然只是压力假设，不是完整的现实风险上界。
