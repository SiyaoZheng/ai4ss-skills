Adrian，下面是我会交付给研究者的 city-year 数据构建交付件草案。

## 交付包

1. `derived/city_year_panel_2010_2021.csv`  
   一行一个 `city_id × year`，覆盖 2010-2021。包含：
   - `city_id`, `city_name`, `year`
   - `pilot_start_year_clean`
   - `treated_city`
   - `post`
   - `event_time`
   - `green_patent_count_city`
   - `gdp_pc`, `population`, `fiscal_exp`
   - 样本限制标记：`in_balanced_city_year_panel`, `has_controls`, `has_outcome`, `analysis_sample`

2. `derived/policy_timing_clean.csv`  
   清洗后的政策时间表，一城一行。保留原始重复记录的处理说明：
   - 若同一城市有多个公告年份，默认使用最早 `pilot_start_year` 作为首次处理时间。
   - 另保留 `pilot_start_year_all` 或 `n_policy_records`，方便稳健性检查。
   - 对同城不同年份公告生成 `policy_timing_conflict_flag`。

3. `derived/sample_flow.csv`  
   记录每一步样本变化，但不在未看数据前填具体数字：
   - 原始城市列表
   - 去重后的政策城市
   - 2010-2021 city-year 框架
   - 合并专利后的 city-year
   - 合并控制变量后的 city-year
   - 主分析样本

4. `derived/merge_audit.csv`  
   每次合并的审计表：
   - `merge_step`
   - `left_key`
   - `right_key`
   - `expected_grain`
   - `unmatched_left_flag`
   - `unmatched_right_flag`
   - `duplicate_key_flag`
   - `action_taken`

5. `docs/data_build_log.md`  
   用自然语言记录所有关键决定、排除规则、变量定义和未解决问题，供论文附录或 replication package 使用。

## 数据处理逻辑

| 输入 | 主要问题 | 处理规则 |
|---|---|---|
| `city_policy_list.csv` | 城市重复、多个公告日期 | 先按 `city_id` 标准化；主规格取最早公告年；保留冲突标记 |
| `patents.csv` | firm-year 粒度、部分 `city_id` 缺失 | 优先使用专利表内 `city_id`；缺失时可用 `firms.csv` 的 `firm_id → city_id` 补齐，并生成来源标记 |
| `firms.csv` | 企业进入、退出年份 | 用于补齐 firm city，并检查专利年份是否落在企业存续期内 |
| `city_controls.csv` | 七个城市缺 2012 控制变量 | 不默认插值；主样本将缺控制的 city-year 标为 `has_controls = 0`，另列稳健性方案 |

## 核心变量定义

| 变量 | 定义 |
|---|---|
| `treated_city` | 城市曾被列为 digital-government pilot，则为 1 |
| `pilot_start_year_clean` | 清洗后的首次试点年份；未处理城市为空 |
| `post` | `treated_city == 1` 且 `year >= pilot_start_year_clean` |
| `event_time` | `year - pilot_start_year_clean`；未处理城市为空 |
| `green_patent_count_city` | 按 `city_id × application_year` 汇总企业绿色专利数 |
| `analysis_sample` | 满足年份范围、城市键有效、控制变量齐备、结果变量定义清楚的 city-year |

## 关键检查

1. 粒度检查  
   确认最终面板中每个 `city_id × year` 只有一行。

2. 政策时间检查  
   列出所有同一城市多个 `pilot_start_year` 的案例，要求作者确认主规格是否使用最早公告年。

3. 专利归属检查  
   对 `patents.csv` 中缺失 `city_id` 的 firm-year，区分：
   - 可由 `firms.csv` 唯一补齐；
   - firm_id 不存在；
   - firm_id 对应多个城市或迁移信息不清楚。

4. 控制变量缺失检查  
   单独列出缺 2012 控制变量的七个城市。主规格不做自动填补；可准备两个稳健性版本：
   - 删除缺控制的 city-year；
   - 对控制变量做城市内线性插值，并明确标记为辅助规格。

5. 样本限制检查  
   明确是否排除：
   - 没有有效 `city_id` 的专利记录；
   - 企业申请年早于 `entry_year` 或晚于 `exit_year` 的记录；
   - 从未出现在 firms 表中的专利 firm_id；
   - 缺控制变量的 city-year。

## 需要作者确认的问题

1. 多次公告的城市，主处理时间应取「首次公告」还是「正式实施」年份？
2. 企业城市归属应按专利记录城市、企业注册城市，还是申请年份对应的实际城市？
3. 缺 2012 控制变量的城市是否进入主样本？
4. 绿色专利结果变量使用总数、`log(1 + count)`，还是人均/企业数标准化指标？
5. 是否需要构造平衡面板，还是允许因控制变量缺失形成非平衡样本？
