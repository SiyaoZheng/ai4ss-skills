Adrian，交付物：文献证据矩阵启动包。

**研究范围**

核心问题：local AI / digital-government adoption 是否改变 firm innovation 与 public-sector productivity。先不写综述，只建立可核验文献库。

**检索分层**

1. AI adoption → firm innovation/productivity  
Query: `"AI adoption" firm innovation patents productivity DID OR "difference-in-differences"`  
Query: `"artificial intelligence adoption" "direction of innovation" firm`

2. Digital government → firm innovation/TFP  
Query: `"digital government" firm innovation China patents DID`  
Query: `"government digital transformation" enterprise innovation listed companies China`

3. Digital government / e-government → public-sector productivity  
Query: `"e-government" "public sector productivity" empirical OECD`  
Query: `"digital transformation" "public sector productivity" local government`

4. AI → public-sector productivity  
Query: `"artificial intelligence" "public sector productivity" local government empirical`  
Query: `"AI adoption" local government productivity public sector`

**纳入规则**

纳入：有稳定来源页或 PDF；研究 AI、digital government、e-government 或 government digital transformation；结果变量包括 patent、innovation、R&D、TFP、public service productivity、administrative efficiency；能提取 setting/sample、data、method、outcome。

排除：纯评论、新闻、咨询报告中无方法和数据的 claims；无法确认作者/年份/题名；只在二手摘要中出现的 finding。政策报告可进入「背景与测量」表，但不进入 causal evidence 表，除非有明确 empirical design。

**本轮候选源队列**

| candidate_id | source | initial status | next action |
|---|---|---|---|
| chen_2024_digital_gov_tfp | Chen et al., PLOS ONE, digital government and corporate TFP, DOI visible | include_after_extraction | 从 PLOS 页面/PDF 抽取样本、DID 设定、robustness、表格定位。 |
| gan_2024_digital_regional_innovation | Economics Letters/RePEc record, digital government and regional innovation, DOI visible | needs_primary_pdf | 需打开 ScienceDirect 或机构 PDF；RePEc 只能作 metadata pointer。 |
| tan_2024_green_innovation | Economic Analysis and Policy/RePEc record, digital government and corporate green innovation, DOI visible | needs_primary_pdf | 需核验 publisher PDF 后再提 findings。 |
| acharya_shao_xu_2026_ai_productivity | SSRN/NYU author PDF, AI adoption, innovation, productivity | working_paper_check | 记录版本；确认是否仍为 working paper。 |
| deng_2026_ai_direction | SSRN record found but access restricted in this pass | unverified_pointer | 不进 evidence table；先找 SSRN page/author PDF。 |
| jordens_hampton_alayande_2024_public_productivity | Productivity Institute public-sector productivity review | background_measurement | 用于概念和测量问题，不作 adoption effect evidence。 |
| dippoliti_2010_egov_oecd | MPRA e-government/public-sector productivity paper | maybe | 核验 PDF、方法和数据后决定是否进入 empirical table。 |
| hoskins_2025_ai_public_sector | Productivity Institute AI/public-sector productivity paper | background_or_maybe | 先判断是 conceptual/policy paper 还是 empirical study。 |

Sources already located for primary checking include PLOS ONE, IDEAS/RePEc, SSRN/author PDF, MPRA, and The Productivity Institute pages/PDFs.

**矩阵字段**

`paper_id, citation, authors, year, status, venue_or_series, doi, url, verification_level, research_question, setting_sample, treatment_or_exposure, outcomes, data_sources, identification_strategy, fixed_effects_controls, validation_checks, main_findings, claim_source_section, claim_source_locator, limitations, relevance_to_project, open_questions, verified_from, access_date, version_used, included_in_synthesis`

**筛选日志字段**

`candidate_id, title, authors, year, source_url, source_type, query_used, status, reason, screened_at, screened_by`

**不确定来源处理**

Search snippets、ResearchGate 摘要、新闻、博客、二手引用一律标为 `secondary_only` 或 `unverified`。它们只能用于找 DOI、作者页或 publisher page，不能支撑综述判断。SSRN、working paper、preprint 必须保留 `version_used`；同一论文不同版本不合并 finding，只在 `version_notes` 记录。若 abstract 提供 finding 但正文/PDF未核验，`claim_source_section=abstract_only`，`included_in_synthesis=false`。

**抽取顺序**

先抽 firm-side causal papers：AI adoption → patents/innovation/productivity；digital government → firm innovation/TFP。再抽 public-sector productivity measurement 与 AI/local-government implementation papers。最后按四个 evidence clusters 交给作者判断：firm innovation channel、firm productivity channel、government digitalization as business environment、public-sector productivity measurement/adoption constraints。

**作者需决定**

1. 是否限定中国地方政府场景，还是纳入 OECD/local government 比较研究。  
2. Green innovation 是否作为 innovation 主结果，还是单列机制/异质性。  
3. Public-sector productivity 是结果变量，还是作为政策背景与测量框架。  
4. Working papers 是否可进入正文综述，或只放 appendix/search log。
