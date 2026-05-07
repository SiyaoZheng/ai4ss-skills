# DDI-Lifecycle 3.3 Analysis for ddi-metadata.yaml Alignment

> Generated: 2026-04-30
> Source: DDI-Lifecycle 3.3 spec, 16 example XMLs, existing ddi-metadata.yaml instances (CGSS 2021, ABS 2019, PGRS 2014)

---

## 1. Core Elements for Survey Data Documentation

DDI-Lifecycle 3.3 organizes survey metadata across a hierarchy:

**StudyUnit** (top level) contains:
- `r:Citation` — title, creators, publication date
- `r:UniverseReference` — the study-wide population
- `s:DataCollection` — all data collection instruments and events
- `l:LogicalProduct` — variables, code lists, category schemes
- `pi:PhysicalInstance` — actual data file metadata (record count, case quantity)
- `r:Coverage` — temporal (date ranges) and geographic scope
- `r:FundingInformation` — grants and sponsors

**DataCollection** contains:
- `d:CollectionEvent` — specific data gathering episodes (mode, dates, interviewer instructions)
- `d:InstrumentScheme` — the actual questionnaire structure
- `d:ControlConstructScheme` — the flow/logic of the questionnaire (Sequences, IfThenElse, Loops)
- `d:ProcessingEvent` — post-collection data transformations

**LogicalProduct** contains:
- `l:VariableScheme` — all variables with their representations
- `l:CategoryScheme` — semantic categories (labels for coded values)
- `l:CodeListScheme` — mappings from codes to categories
- `l:LogicalRecord` — record structure definitions
- `l:DataRelationship` — links between records

---

## 2. Missing Code Representation

DDI-Lifecycle 3.3 provides a sophisticated missing value model via `ManagedMissingValuesRepresentation`, which combines two approaches:

### 2.1 Code-Based Missing Values (MissingCodeRepresentation)

Links to a CodeList that defines missing value codes and their semantic categories.

```xml
<!-- From RepresentationExamples_3_3.xml -->
<d:ManagedMissingValuesRepresentation>
  <r:URN>urn:ddi:int.example:MVR_1:1</r:URN>
  <r:Label>
    <r:Content xml:lang="en">Standard Missing Value Codes</r:Content>
  </r:Label>
  <d:MissingCodeRepresentation>
    <d:CodeListReference>
      <r:URN>urn:ddi:int.example:MVCL_1:1</r:URN>
      <r:TypeOfObject>CodeList</r:TypeOfObject>
    </d:CodeListReference>
  </d:MissingCodeRepresentation>
  <d:MissingNumericRepresentation>
    <d:NumberRange>
      <r:Low isInclusive="true">-1</r:Low>
      <r:High isInclusive="true">-1</r:High>
    </d:NumberRange>
    <r:Label>
      <r:Content xml:lang="en">No Response</r:Content>
    </r:Label>
  </d:MissingNumericRepresentation>
</d:ManagedMissingValuesRepresentation>
```

### 2.2 Range-Based Missing Values (MissingNumericRepresentation)

Defines a numeric range (e.g., -1 to -1 for single value, 95-99 for a block).

```xml
<d:MissingNumericRepresentation>
  <d:NumberRange>
    <r:Low isInclusive="true">-1</r:Low>
    <r:High isInclusive="true">-1</r:High>
  </d:NumberRange>
  <r:Label>
    <r:Content xml:lang="en">No Response</r:Content>
  </r:Label>
</d:MissingNumericRepresentation>
```

### 2.3 How Variables Reference Missing Values

Variables and RepresentedVariables link to `ManagedMissingValuesRepresentation` via reference:

```xml
<!-- From RepresentedVariableExample_3_3.xml -->
<l:Variable>
  <l:VariableName><r:String xml:lang="en">Age of Person</r:String></l:VariableName>
  <r:VariableRepresentation>
    <r:ManagedMissingValuesRepresentationReference>
      <r:URN>urn:ddi:int.example:MVR_1:1</r:URN>
      <r:TypeOfObject>ManagedMissingValuesRepresentation</r:TypeOfObject>
    </r:ManagedMissingValuesRepresentationReference>
  </r:VariableRepresentation>
</l:Variable>
```

### 2.4 Gap with Our Schema

Our `ddi-metadata.yaml` already handles missing values well with:
```yaml
missing:
  schema_ref: null        # reference to shared_missing_schemas
  codes:
    99: {label: "拒绝回答", type: refused}
    88: {label: "不知道", type: dont_know}
  ranges: []
  blank_is_missing: true
```

The `type` field (refused, dont_know, inapplicable) maps to DDI Category semantics but is not natively expressed in DDI's `ManagedMissingValuesRepresentation` — it requires a separate CodeList with Category definitions. We already do this better by attaching semantic type directly.

---

## 3. Processing and Cleaning Operations

### 3.1 ProcessingEvent

DDI models data cleaning through `ProcessingEvent` within `ProcessingEventScheme`:

```xml
<!-- From QualityStatementExamples_3_3.xml -->
<d:ProcessingEventScheme>
  <r:URN>urn:ddi:us.archive:ProcEventSch_1:1</r:URN>
  <d:ProcessingEvent>
    <r:URN>urn:ddi:us.archive:ProcEventSch_1.PE_1:1</r:URN>
    <d:DataAppraisalInformation>
      <d:ResponseRate>
        <d:SampleSize>5000</d:SampleSize>
        <d:NumberOfResponses>3768</d:NumberOfResponses>
        <d:SpecificResponseRate>.7536</d:SpecificResponseRate>
      </d:ResponseRate>
    </d:DataAppraisalInformation>
  </d:ProcessingEvent>
</d:ProcessingEventScheme>
```

### 3.2 GenerationInstruction (Derived Variables)

Derived variables are created via `GenerationInstruction` with actual executable code:

```xml
<!-- From InOutBindingExample_3_3.xml -->
<d:GenerationInstruction>
  <r:URN>urn:ddi:int.example:GI:1</r:URN>
  <r:CommandCode>
    <r:Command>
      <r:ProgramLanguage>SPSS</r:ProgramLanguage>
      <r:InParameter>
        <r:URN>urn:ddi:int.example:GI_Age:1</r:URN>
        <r:Alias>AGE</r:Alias>
      </r:InParameter>
      <r:OutParameter>
        <r:URN>urn:ddi:int.example:GI_Age_Cohort:1</r:URN>
        <r:Alias>AGE_5</r:Alias>
      </r:OutParameter>
      <r:CommandContent>If (AGE &lt; 5) AGE_5=1; ...</r:CommandContent>
    </r:Command>
  </r:CommandCode>
</d:GenerationInstruction>
```

### 3.3 Gap with Our Schema

Our `processing_events` in ddi-metadata.yaml are minimal:
```yaml
processing_events:
  - event_id: pe001
    type: variable_rename
    timestamp: '2026-04-25T10:00:00'
    skill_version: '1.0'
    description: 'Renamed variables to standardized names'
    inputs: [原始变量]
    outputs: [标准化变量]
    operator: codebook-parse
```

DDI's model is richer — it supports:
- `DataAppraisalInformation` (response rates, sampling errors)
- `CommandCode` with `ProgramLanguage` and `CommandContent` (actual code)
- `InParameter`/`OutParameter` bindings for data flow tracking
- `TypeOfProcess` classification

Our schema captures provenance well but lacks the executable code storage and data flow binding that DDI supports.

---

## 4. Weighting and Sampling

### 4.1 Weighting

DDI represents weighting at multiple levels:

**Weight variable flag:**
```xml
<!-- From Example_Weighting_3_3.xml -->
<l:Variable isWeight="true">
  <r:URN>urn:ddi:int.example:WeightVar:1</r:URN>
  <l:VariableName><r:String>Person Weight</r:String></l:VariableName>
</l:Variable>
```

**WeightingMethodology:**
```xml
<r:WeightingMethodology>
  <r:URN>urn:ddi:int.example:WM_1:1</r:URN>
  <r:TypeOfWeightingMethodology>Standard Weight</r:TypeOfWeightingMethodology>
  <r:Description>
    <r:Content>Design weight adjusted for non-response...</r:Content>
  </r:Description>
</r:WeightingMethodology>
```

**StandardWeight in ProcessingEvent:**
```xml
<d:ProcessingEvent>
  <d:Weighting>
    <d:WeightingMethodologyReference>
      <r:URN>urn:ddi:int.example:WM_1:1</r:URN>
    </d:WeightingMethodologyReference>
    <d:AnalysisUnit>Person</d:AnalysisUnit>
    <d:StandardWeight>
      <r:VariableReference>
        <r:URN>urn:ddi:int.example:WeightVar:1</r:URN>
      </r:VariableReference>
    </d:StandardWeight>
  </d:Weighting>
</d:ProcessingEvent>
```

**Weighted statistics reference:**
```xml
<!-- From StatisticsExample_3_3.xml -->
<l:VariableStatistics>
  <r:StandardWeightReference>
    <r:URN>urn:ddi:int.example:WeightVar:1</r:URN>
  </r:StandardWeightReference>
  <l:SummaryStatistic>
    <l:TypeOfSummaryStatistic>wtCount</l:TypeOfSummaryStatistic>
    <r:Statistic isWeighted="true" computationBase="validOnly">234567.89</r:Statistic>
  </l:SummaryStatistic>
</l:VariableStatistics>
```

### 4.2 Sampling

DDI defines sampling through:

```xml
<!-- From Example_Sampling_3_3.xml -->
<r:SamplingProcedure>
  <r:URN>urn:ddi:int.example:SP_1:1</r:URN>
  <r:TypeOfSamplingProcedure>Probability</r:TypeOfSamplingProcedure>
  <r:Description>
    <r:Content>Multi-stage stratified probability sampling...</r:Content>
  </r:Description>
</r:SamplingProcedure>

<r:Sample>
  <r:URN>urn:ddi:int.example:S_1:1</r:URN>
  <r:PopulationOfConcern>
    <r:UniverseReference>
      <r:URN>urn:ddi:int.example:U_1:1</r:URN>
    </r:UniverseReference>
  </r:PopulationOfConcern>
  <r:OverallTargetSampleSize>10000</r:OverallTargetSampleSize>
</r:Sample>

<r:SampleFrame>
  <r:URN>urn:ddi:int.example:SF_1:1</r:URN>
  <r:UnitsOfFrame>
    <r:PrimaryPopulation>
      <r:Content>Households in urban areas</r:Content>
    </r:PrimaryPopulation>
  </r:UnitsOfFrame>
  <r:FrameLimitations>
    <r:Content>Excludes institutional populations...</r:Content>
  </r:FrameLimitations>
</r:SampleFrame>
```

### 4.3 Gap with Our Schema

Our `ddi-metadata.yaml` currently has:
```yaml
study:
  analysis_unit: Person

variables:
  - id: var001
    is_weight: true   # only flag, no methodology
```

We lack:
- `WeightingMethodology` (type, description)
- `StandardWeight` linkage (which variable is the standard weight)
- `SamplingProcedure` description
- `Sample` with target sample size
- `SampleFrame` with population and limitations
- `AnalysisUnit` at the weighting level (we only have it at study level)

---

## 5. Questionnaire Structure

### 5.1 ControlConstructScheme

DDI models questionnaire flow through a scheme of control constructs:

**Sequence (ordered list of constructs):**
```xml
<!-- From InOutBindingExample_3_3.xml -->
<d:Sequence>
  <r:URN>urn:ddi:int.example:SEQ:1</r:URN>
  <d:ControlConstructReference>
    <r:URN>urn:ddi:int.example:QC_1:1</r:URN>
    <r:TypeOfObject>QuestionConstruct</r:TypeOfObject>
  </d:ControlConstructReference>
  <d:ControlConstructReference>
    <r:URN>urn:ddi:int.example:QC_2:1</r:URN>
    <r:TypeOfObject>QuestionConstruct</r:TypeOfObject>
  </d:ControlConstructReference>
</d:Sequence>
```

**QuestionConstruct (wraps a question with parameter bindings):**
```xml
<d:QuestionConstruct>
  <r:URN>urn:ddi:int.example:QC_1:1</r:URN>
  <r:OutParameter>
    <r:URN>urn:ddi:int.example:QC_OUT_1:1</r:URN>
  </r:OutParameter>
  <r:Binding>
    <r:SourceParameterReference>
      <r:URN>urn:ddi:int.example:Q1_Name:1</r:URN>
      <r:TypeOfObject>OutParameter</r:TypeOfObject>
    </r:SourceParameterReference>
    <r:TargetParameterReference>
      <r:URN>urn:ddi:int.example:QC_OUT_1:1</r:URN>
      <r:TypeOfObject>OutParameter</r:TypeOfObject>
    </r:TargetParameterReference>
  </r:Binding>
  <r:QuestionReference>
    <r:URN>urn:ddi:int.example:Q1:1</r:URN>
    <r:TypeOfObject>QuestionItem</r:TypeOfObject>
  </r:QuestionReference>
</d:QuestionConstruct>
```

### 5.2 QuestionItem with Dynamic Text

Questions can embed conditional text that references prior answers:

```xml
<!-- From InOutBindingExample_3_3.xml -->
<d:QuestionItem>
  <r:URN>urn:ddi:int.example:Q2:1</r:URN>
  <r:InParameter>
    <r:URN>urn:ddi:int.example:Q2_Name:1</r:URN>
  </r:InParameter>
  <d:QuestionText>
    <d:LiteralText>
      <d:Text xml:lang="en" xml:space="preserve">How old is </d:Text>
    </d:LiteralText>
    <d:ConditionalText>
      <r:SourceParameterReference>
        <r:URN>urn:ddi:int.example:Q2_Name:1</r:URN>
        <r:TypeOfObject>InParameter</r:TypeOfObject>
      </r:SourceParameterReference>
    </d:ConditionalText>
    <d:LiteralText>
      <d:Text xml:lang="en" xml:space="preserve"> ?</d:Text>
    </d:LiteralText>
  </d:QuestionText>
</d:QuestionItem>
```

### 5.3 Question Response Domains

Questions specify their response format via domain references:

```xml
<!-- From QuestionExample_3_3.xml: CodeDomain for categorical -->
<d:QuestionItem>
  <d:QuestionText>
    <d:LiteralText><d:Text>What is your marital status?</d:Text></d:LiteralText>
  </d:QuestionText>
  <d:CodeDomain>
    <d:CodeListReference>
      <r:URN>urn:ddi:int.example:CL_Marital:1</r:URN>
      <r:TypeOfObject>CodeList</r:TypeOfObject>
    </d:CodeListReference>
  </d:CodeDomain>
</d:QuestionItem>
```

### 5.4 Gap with Our Schema

Our schema has no questionnaire structure at all. Variables carry `name` and `label` but not the original question text, response domain type, or questionnaire flow. For codebook-parse, this is acceptable since we parse from post-collection documentation rather than questionnaire design. However, if we want to track original question wording, we could add:

```yaml
variables:
  - name: Q1
    question_text: "What is your marital status?"  # not currently captured
    response_domain: code                           # already in representation.type
```

---

## 6. Universe Concept

### 6.1 Definition and Hierarchy

Universe in DDI defines the population to which a variable applies. It is defined in a `UniverseScheme` and referenced by Variables:

```xml
<!-- From RepresentedVariableExample_3_3.xml -->
<r:UniverseScheme>
  <r:Universe>
    <r:URN>urn:ddi:int.example:U_Persons:1</r:URN>
    <r:UniverseName><r:String>Persons in US</r:String></r:UniverseName>
    <r:HumanReadable>
      <r:Content>All persons living in the United States</r:Content>
    </r:HumanReadable>
  </r:Universe>
  <r:Universe>
    <r:URN>urn:ddi:int.example:U_Teens:1</r:URN>
    <r:UniverseName><r:String>Persons Age 13-19</r:String></r:UniverseName>
    <r:HumanReadable>
      <r:Content>Persons aged 13 to 19 inclusive</r:Content>
    </r:HumanReadable>
    <r:ParentUniverseReference>
      <r:URN>urn:ddi:int.example:U_Persons:1</r:URN>
    </r:ParentUniverseReference>
  </r:Universe>
</r:UniverseScheme>
```

**Key features:**
- Universes form a hierarchy (ParentUniverseReference)
- Variables reference specific universes, enabling reuse across studies
- `isInclusive` flag on universe membership
- Study-level universe vs. variable-level universe (variable can be more restrictive)

### 6.2 Gap with Our Schema

Our schema has `study.universe: null` and no variable-level universe. DDI allows each variable to declare its own universe (e.g., "only for married respondents"), which we don't capture. We could add:

```yaml
study:
  universe: "Adult residents of China aged 18+"

variables:
  - name: Q_mariage_satisfaction
    universe: "Married respondents only"  # restricted subset
```

---

## 7. Statistics and Data Quality

### 7.1 VariableStatistics

DDI stores actual computed statistics alongside variables:

```xml
<!-- From StatisticsExample_3_3.xml -->
<l:VariableStatistics>
  <r:VariableReference>
    <r:URN>urn:ddi:int.example:V1:1</r:URN>
  </r:VariableReference>
  <r:TotalResponses>5000</r:TotalResponses>
  <r:StandardWeightReference>
    <r:URN>urn:ddi:int.example:WeightVar:1</r:URN>
  </r:StandardWeightReference>
  <r:MissingValuesReference>
    <r:URN>urn:ddi:int.example:MVR_1:1</r:URN>
  </r:MissingValuesReference>
  <l:SummaryStatistic>
    <l:TypeOfSummaryStatistic>wtCount</l:TypeOfSummaryStatistic>
    <r:Statistic isWeighted="true" computationBase="validOnly">234567.89</r:Statistic>
  </l:SummaryStatistic>
  <l:UnfilteredCategoryStatistics>
    <l:VariableCategory>
      <l:CategoryValue>1</l:CategoryValue>
      <l:CategoryStatistic>
        <l:TypeOfCategoryStatistic>wtCount</l:TypeOfCategoryStatistic>
        <r:Statistic isWeighted="true">12345.67</r:Statistic>
      </l:CategoryStatistic>
      <l:CategoryStatistic>
        <l:TypeOfCategoryStatistic>weightedPct</l:TypeOfCategoryStatistic>
        <r:Statistic>24.5</r:Statistic>
      </l:CategoryStatistic>
    </l:VariableCategory>
  </l:UnfilteredCategoryStatistics>
</l:VariableStatistics>
```

**Statistic types:** wtCount, Count, weightedPct, colPct, Mean, Median, StdDev, etc.

### 7.2 Quality Statements

```xml
<!-- From QualityStatementExamples_3_3.xml -->
<r:QualityStatement>
  <r:QualityStandard>
    <r:StandardUsed>
      <r:OtherMaterial>
        <r:TypeOfMaterial>Standard</r:TypeOfMaterial>
        <r:Citation>
          <r:Title><r:String>OAIS Recommended Practice</r:String></r:Title>
        </r:Citation>
      </r:OtherMaterial>
    </r:StandardUsed>
  </r:QualityStandard>
  <r:ComplianceStatement>
    <r:Content>The archive complies with the OAIS model...</r:Content>
  </r:ComplianceStatement>
</r:QualityStatement>
```

### 7.3 Gap with Our Schema

We currently store no statistics or quality statements. If needed:

```yaml
variables:
  - name: age
    statistics:
      total_responses: 5000
      mean: 42.3
      std_dev: 15.2
      weighted_count: 234567.89
      category_statistics:
        1: {count: 1234, pct: 24.5}
```

---

## 8. Mapping to ddi-metadata.yaml SSOT

### 8.1 Current Schema Structure

Our ddi-metadata.yaml has:
```yaml
schema_version: '1.0'
ddi_version: '3.3'
study: {name, id, agency, universe, analysis_unit, data_source, wave}
shared_category_schemes: {scheme_NNN: {code: label}}
shared_missing_schemas: {name: {codes: {val: {label, type}}, ranges, blank_is_missing}}
variables:
  - {id, name, label, is_temporal, is_geographic, is_weight,
     concept, unit_type,
     representation: {type, storage_type, category_scheme_ref, codes, min, max},
     missing: {schema_ref, codes, ranges, blank_is_missing},
     source_variables, derivation_rule, _parse_flags}
processing_events:
  - {event_id, type, timestamp, skill_version, description, inputs, outputs, operator}
```

### 8.2 Field-by-Field Mapping

| ddi-metadata.yaml field | DDI-Lifecycle 3.3 equivalent | Status |
|---|---|---|
| `study.name` | `s:StudyUnit/r:Citation/r:Title` | OK |
| `study.id` | `s:StudyUnit/r:URN` | Partial (we use null) |
| `study.agency` | `r:URN` agency component | Partial |
| `study.universe` | `s:StudyUnit/r:UniverseReference` | Gap (usually null) |
| `study.analysis_unit` | `r:AnalysisUnit` / `d:Weighting/d:AnalysisUnit` | OK |
| `study.data_source` | Custom (not in DDI natively) | Our addition |
| `study.wave` | `s:StudyUnit/r:Coverage/r:TemporalCoverage` | Partial |
| `shared_category_schemes` | `l:CategoryScheme` + `l:CodeListScheme` | Different structure (see below) |
| `shared_missing_schemas` | `d:ManagedMissingValuesRepresentation` | Our improvement (type annotation) |
| `variable.name` | `l:Variable/l:VariableName/r:String` | OK |
| `variable.label` | `l:Variable/r:Label/r:Content` | OK |
| `variable.is_weight` | `l:Variable[@isWeight="true"]` | OK |
| `variable.concept` | `l:Variable/l:ConceptReference` / `c:Concept` | Gap (usually null) |
| `variable.unit_type` | `l:Variable/r:UnitTypeReference` | Gap (usually null) |
| `variable.representation.type` | `r:Representation` subtype (CodeDomain, NumericRepresentation, etc.) | OK |
| `variable.representation.storage_type` | `r:StorageType` / physical data model | OK |
| `variable.representation.category_scheme_ref` | `d:CodeDomain/d:CodeListReference` | OK |
| `variable.missing` | `r:ManagedMissingValuesRepresentationReference` | OK + enhanced |
| `variable.source_variables` | `r:SourceParameterReference` (via GenerationInstruction) | Partial |
| `variable.derivation_rule` | `d:GenerationInstruction/r:CommandCode` | Gap (usually null) |
| `processing_events` | `d:ProcessingEventScheme/d:ProcessingEvent` | Minimal |
| (absent) `questionnaire` | `d:InstrumentScheme`, `d:ControlConstructScheme` | Not captured |
| (absent) `sampling` | `r:SamplingProcedure`, `r:Sample`, `r:SampleFrame` | Not captured |
| (absent) `statistics` | `l:VariableStatistics` | Not captured |
| (absent) `quality` | `r:QualityScheme`, `r:QualityStatement` | Not captured |
| (absent) `notes` | `r:Note` with `r:ProprietaryInfo` | Not captured |

### 8.3 Structural Differences

**Category Schemes:** DDI separates Category (semantic label) from Code (numeric mapping) via two schemes. Our schema flattens this into `{code: label}` dictionaries. This works for simple cases but loses:
- Category-level metadata (e.g., classification of a category)
- Code-to-Category reuse across CodeLists
- Hierarchical categories

**Variable Tiers:** DDI has 3 tiers (ConceptualVariable -> RepresentedVariable -> Variable). We have a flat Variable with optional `concept` and `unit_type` references. This is adequate for post-collection documentation.

---

## 9. Specific XML Examples — Key Patterns

### 9.1 Variable with Coded Representation

```xml
<!-- From RepresentedVariableExample_3_3.xml -->
<l:Variable>
  <r:URN>urn:ddi:int.example:V1:1</r:URN>
  <l:VariableName><r:String xml:lang="en">Age of Person</r:String></l:VariableName>
  <r:RepresentedVariableReference>
    <r:URN>urn:ddi:int.example:RV_Age:1</r:URN>
    <r:TypeOfObject>RepresentedVariable</r:TypeOfObject>
  </r:RepresentedVariableReference>
  <r:UniverseReference>
    <r:URN>urn:ddi:int.example:U_Persons:1</r:URN>
    <r:TypeOfObject>Universe</r:TypeOfObject>
  </r:UniverseReference>
  <r:VariableRepresentation>
    <r:NumericRepresentationDefinitionReference>
      <r:URN>urn:ddi:int.example:NR_Age:1</r:URN>
      <r:TypeOfObject>ManagedNumericRepresentation</r:TypeOfObject>
    </r:NumericRepresentationDefinitionReference>
  </r:VariableRepresentation>
</l:Variable>
```

### 9.2 CategoryScheme + CodeList Pattern

```xml
<!-- From QuestionExample_3_3.xml -->
<l:CategoryScheme>
  <l:Category>
    <r:URN>urn:ddi:int.example:Cat_Married:1</r:URN>
    <l:CategoryName><r:String>Married</r:String></l:CategoryName>
    <r:Label><r:Content xml:lang="en">Currently married</r:Content></r:Label>
  </l:Category>
  <!-- more categories... -->
</l:CategoryScheme>

<l:CodeListScheme>
  <l:CodeList>
    <l:Code>
      <r:URN>urn:ddi:int.example:Code_1:1</r:URN>
      <l:CategoryReference>
        <r:URN>urn:ddi:int.example:Cat_Married:1</r:URN>
        <r:TypeOfObject>Category</r:TypeOfObject>
      </l:CategoryReference>
      <l:Value>1</l:Value>
    </l:Code>
  </l:CodeList>
</l:CodeListScheme>
```

### 9.3 IsWeight Variable

```xml
<!-- From Example_Weighting_3_3.xml -->
<l:Variable isWeight="true">
  <r:URN>urn:ddi:int.example:WeightVar:1</r:URN>
  <l:VariableName><r:String>Person Weight</r:String></l:VariableName>
  <r:VariableRepresentation>
    <r:WeightVariableReference>
      <r:URN>urn:ddi:int.example:WM_1:1</r:URN>
      <r:TypeOfObject>WeightingMethodology</r:TypeOfObject>
    </r:WeightVariableReference>
  </r:VariableRepresentation>
</l:Variable>
```

### 9.4 Conditional/Filtered Statistics

```xml
<!-- From StatisticsExample_3_3.xml -->
<l:FilteredCategoryStatistics>
  <r:FilterVariableReference>
    <r:URN>urn:ddi:int.example:FilterVar:1</r:URN>
  </r:FilterVariableReference>
  <l:FilterVariableCategory>
    <l:CategoryValue>1</l:CategoryValue>
  </l:FilterVariableCategory>
  <l:VariableCategory>
    <l:CategoryValue>1</l:CategoryValue>
    <l:CategoryStatistic>
      <l:TypeOfCategoryStatistic>colPct</l:TypeOfCategoryStatistic>
      <r:Statistic>45.2</r:Statistic>
    </l:CategoryStatistic>
  </l:VariableCategory>
</l:FilteredCategoryStatistics>
```

### 9.5 Notes with ProprietaryInfo (Extensibility Mechanism)

```xml
<!-- From NoteExample_3_3.xml -->
<r:Note>
  <r:Relationship>
    <r:RelatedToReference>
      <r:Agency>int.example</r:Agency>
      <r:ID>Concept1</r:ID>
      <r:TypeOfObject>Concept</r:TypeOfObject>
    </r:RelatedToReference>
  </r:Relationship>
  <r:ProprietaryInfo>
    <r:ProprietaryProperty>
      <r:AttributeKey>CustomProperty1</r:AttributeKey>
      <r:AttributeValue>Custom value 1</r:AttributeValue>
    </r:ProprietaryProperty>
  </r:ProprietaryInfo>
</r:Note>
```

This is DDI's extension mechanism — any custom metadata can be attached via `ProprietaryInfo` on Notes.

---

## 10. Recommendations for ddi-metadata.yaml Schema Evolution

### 10.1 Keep As-Is (Already Adequate)
- `shared_category_schemes` flat dict — simpler than DDI's Category+CodeList split, sufficient for post-collection
- `missing.codes` with `type` annotation — actually better than DDI's model
- `variable.is_weight` flag — clear and compact
- `variable.representation.type` — good mapping to DDI domain types

### 10.2 Consider Adding (Low Effort, High Value)
- `study.universe` — currently always null; should be populated from codebook intro text
- `variable.universe` — restricted universe per variable (e.g., "married only")
- `variable.question_text` — original question wording from codebook; invaluable for interpretation
- `variable.source_reference` — original variable name/code in source data (already have `source_variables` but underused)

### 10.3 Consider Adding (Medium Effort)
- `weighting` section — which variable is the standard weight, what methodology
- `sampling` section — procedure description, sample frame, target size
- `study.temporal_coverage` — collection date range

### 10.4 Defer (Not Needed for codebook-parse)
- `questionnaire` flow — we parse post-collection docs, not questionnaire designs
- `statistics` — can be computed on demand from data
- `quality` statements — relevant for archives, not for cleaning-contract pipeline
- `notes/proprietary_info` — DDI's extensibility; our `_parse_flags` serve similar purpose

---

## Appendix: File Index

| File | Content |
|---|---|
| `RepresentedVariableExample_3_3.xml` | 3-tier variable model, Universe hierarchy |
| `RepresentationExamples_3_3.xml` | All representation types, ManagedMissingValuesRepresentation |
| `QuestionExample_3_3.xml` | QuestionItem, QuestionGrid, CategoryScheme, CodeListScheme |
| `InOutBindingExample_3_3.xml` | Parameter bindings, GenerationInstruction with SPSS code |
| `Example_Weighting_3_3.xml` | WeightingMethodology, isWeight, StandardWeight |
| `Example_Sampling_3_3.xml` | SamplingProcedure, Sample, SampleFrame |
| `StatisticsExample_3_3.xml` | VariableStatistics, SummaryStatistic, CategoryStatistic |
| `QualityStatementExamples_3_3.xml` | QualityStatement, DataAppraisalInformation, ResponseRate |
| `NoteExample_3_3.xml` | Note types, ProprietaryInfo extensibility |
| `ArchiveExample_3_3.xml` | ArchiveSpecific, DefaultAccess, LifecycleInformation |
| `DateExamples_3_3.xml` | TemporalCoverage, ReferenceDate |
| `Example_QuestionnaireDevelopment_3_3.xml` | DevelopmentPlan, TranslationActivity |
| `SPSS_Example.xml` | DDI-CDI format (different model, not DDI-Lifecycle) |
| `ZA4586_ddi-l_3_2.xml` | Full DDI-L 3.2 study (large, study-level metadata) |
| `ICPSR2079variables_3_2.xml` | DDI-L 3.2 variable-level content |
