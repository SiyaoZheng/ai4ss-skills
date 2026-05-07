# DDI-CDI v1.0 Specification Analysis

> Analysis date: 2026-04-30
> Source files: `/Users/siyaozheng/Documents/ai4ss-skills/references/ddi/`
> Specification: DDI Cross-Domain Integration (DDI-CDI) v1.0 (2025)

---

## 1. Core Data Model

### 1.1 Variable Hierarchy (3-tier)

DDI-CDI uses a strict 3-tier variable hierarchy, each tier adding more specificity:

**ConceptualVariable** -- The most abstract level. Defines *what* is being measured conceptually.

```xml
<!-- From XSD (lines 5947-6027): extends ConceptXsdType -->
ConceptualVariableXsdType:
  descriptiveText
  unitOfMeasureKind
  takesSentinelConceptsFrom_SentinelConceptualDomain
  takesSubstantiveConceptsFrom_SubstantiveConceptualDomain
```

**RepresentedVariable** -- Adds representation details: data type, units of measure, and links to value domains.

```xml
<!-- From XSD (lines 14069-14180): extends ConceptualVariableXsdType -->
RepresentedVariableXsdType:
  describedUnitOfMeasure
  hasIntendedDataType          -- e.g. "F5.0", "F1.0"
  simpleUnitOfMeasure
  takesSentinelValuesFrom_SentinelValueDomain    (0..*)
  takesSubstantiveValuesFrom_SubstantiveValueDomain  (0..1)
```

**InstanceVariable** -- The concrete variable in a specific dataset. Adds physical data type, platform, source, and links to physical layout.

```xml
<!-- From XSD (lines 9453-9576): extends RepresentedVariableXsdType -->
InstanceVariableXsdType:
  physicalDataType
  platformType
  source                       -- provenance reference
  variableFunction
  InstanceVariable_has_PhysicalSegmentLayout
  InstanceVariable_has_ValueMapping
```

### 1.2 Value Domain Split (Substantive vs. Sentinel)

This is the most architecturally significant design choice in CDI. Every variable's value space is split into two domains:

**SubstantiveValueDomain** -- Values of primary research interest (the "clean" data).

```xml
<!-- From SPSS_Example.xml (line 5446): -->
<cdi:SubstantiveValueDomain>
  <cdi:identifier>
    <cdi:ddiIdentifier>
      <cdi:dataIdentifier>#substantiveValueDomain-nwspol</cdi:dataIdentifier>
    </cdi:ddiIdentifier>
  </cdi:identifier>
  <cdi:SubstantiveValueDomain_takesValuesFrom_EnumerationDomain>
    <cdi:ddiReference>
      <cdi:dataIdentifier>#substantiveCodelist-nwspol</cdi:dataIdentifier>
    </cdi:ddiReference>
    <cdi:validType>CodeList</cdi:validType>
  </cdi:SubstantiveValueDomain_takesValuesFrom_EnumerationDomain>
  <cdi:SubstantiveValueDomain_isDescribedBy_ValueAndConceptDescription>
    <cdi:ddiReference>
      <cdi:dataIdentifier>#substantiveValueAndConceptDescription-nwspol</cdi:dataIdentifier>
    </cdi:ddiReference>
    <cdi:validType>ValueAndConceptDescription</cdi:validType>
  </cdi:SubstantiveValueDomain_isDescribedBy_ValueAndConceptDescription>
</cdi:SubstantiveValueDomain>
```

**SentinelValueDomain** -- Missing codes, refusal codes, "don't know" -- values used for processing, not subject matter.

```xml
<!-- From SPSS_Example.xml (line 5688): -->
<cdi:SentinelValueDomain>
  <cdi:identifier>
    <cdi:ddiIdentifier>
      <cdi:dataIdentifier>#sentinelValueDomain-nwspol</cdi:dataIdentifier>
    </cdi:ddiIdentifier>
  </cdi:identifier>
  <cdi:SentinelValueDomain_takesValuesFrom_EnumerationDomain>
    <cdi:ddiReference>
      <cdi:dataIdentifier>#sentinelCodelist-nwspol</cdi:dataIdentifier>
    </cdi:ddiReference>
    <cdi:validType>CodeList</cdi:validType>
  </cdi:SentinelValueDomain_takesValuesFrom_EnumerationDomain>
</cdi:SentinelValueDomain>
```

From the XSD (lines 14850-14863), sentinel values are defined per ISO 11404:

> "Sentinel values are defined in ISO 11404 as 'element of a value space that is not completely consistent with a datatype's properties and characterizing operations...'. A common example would be codes for missing values. Sentinel values are used for processing, not to describe subject matter."

The `platformType` on SentinelValueDomain specifies software-specific sentinel conventions:
- `Rstyle` -- NA, NaN, -Inf, +Inf
- `SASNumeric` -- ., .A-.Z
- `SPSSstyle` -- system missing (dot), individual values, ranges
- `StataNumeric` -- ., .A-.Z (sentinel > any substantive value)

### 1.3 Code-Category-Notation Chain

Value labels are represented through a 3-element chain:

**Code** -- Links a notation (the actual value) to a category (the label).

```xml
<!-- From SPSS_Example.xml (line 7071): -->
<cdi:Code>
  <cdi:identifier>
    <cdi:ddiIdentifier>
      <cdi:dataIdentifier>#code-7777.0-nwspol</cdi:dataIdentifier>
    </cdi:ddiIdentifier>
  </cdi:identifier>
  <cdi:Code_denotes_Category>
    <cdi:ddiReference>
      <cdi:dataIdentifier>#category-Refusal</cdi:dataIdentifier>
    </cdi:ddiReference>
    <cdi:validType>Category</cdi:validType>
  </cdi:Code_denotes_Category>
  <cdi:Code_uses_Notation>
    <cdi:ddiReference>
      <cdi:dataIdentifier>#notation-7777.0</cdi:dataIdentifier>
    </cdi:ddiReference>
    <cdi:validType>Notation</cdi:validType>
  </cdi:Code_uses_Notation>
</cdi:Code>
```

**Category** -- The human-readable label.

```xml
<!-- From SPSS_Example.xml (line 9196): -->
<cdi:Category>
  <cdi:displayLabel>
    <cdi:languageSpecificString>
      <cdi:content>Refusal</cdi:content>
    </cdi:languageSpecificString>
  </cdi:displayLabel>
  <cdi:identifier>
    <cdi:ddiIdentifier>
      <cdi:dataIdentifier>#category-Refusal</cdi:dataIdentifier>
    </cdi:ddiIdentifier>
  </cdi:identifier>
  <cdi:name>
    <cdi:name>Refusal</cdi:name>
  </cdi:name>
</cdi:Category>
```

**Notation** -- The actual alphanumeric value stored in the data.

```xml
<!-- From SPSS_Example.xml (line 9927): -->
<cdi:Notation>
  <cdi:content>
    <cdi:content>7777.0</cdi:content>
  </cdi:content>
  <cdi:identifier>
    <cdi:ddiIdentifier>
      <cdi:dataIdentifier>#notation-7777.0</cdi:dataIdentifier>
    </cdi:ddiIdentifier>
  </cdi:identifier>
</cdi:Notation>
```

The chain: `Code` --denotes--> `Category` (label) + `Code` --uses--> `Notation` (value). Notations are shared across variables (e.g., `#notation-9.0` is reused by multiple variables).

### 1.4 Classification Hierarchy

For standardized classification schemes (ISCO, ISCED, etc.):

```
ClassificationFamily
  -> ClassificationSeries
    -> StatisticalClassification
      -> ClassificationItem
        -> Level (levelNumber, isDefinedBy_Concept)
```

### 1.5 Identifier Structure

All CDI objects use a uniform `ddiIdentifier`:

```xml
<cdi:identifier>
  <cdi:ddiIdentifier>
    <cdi:dataIdentifier>#instanceVariable-idno</cdi:dataIdentifier>
    <cdi:registrationAuthorityIdentifier>int.esseric</cdi:registrationAuthorityIdentifier>
    <cdi:versionIdentifier>1</cdi:versionIdentifier>
  </cdi:ddiIdentifier>
</cdi:identifier>
```

Three components: `dataIdentifier` (local), `registrationAuthorityIdentifier` (agency), `versionIdentifier`.

### 1.6 Namespace

```
http://ddialliance.org/Specification/DDI-CDI/1.0/XMLSchema/
```

Prefix used in examples: `cdi:`

---

## 2. Data Structure Types

DDI-CDI supports four data structure paradigms, each with a corresponding DataStructure, DataSet, Key, and KeyMember:

### 2.1 WideDataStructure (Rectangular)

The classic "wide" format: one row per case, columns = variables.

```xml
<!-- From XSD (lines 17778-17793): -->
WideDataStructureXsdType extends DataStructureXsdType
  -- no additional elements beyond base
```

Components: `IdentifierComponent` (e.g., idno), `MeasureComponent` (e.g., nwspol, netusoft), `AttributeComponent`.

From SPSS_Example.xml (lines 4616-4729):
```xml
<cdi:WideDataStructure>
  <cdi:DataStructure_has_DataStructureComponent>
    <!-- IdentifierComponent for idno -->
    <cdi:DataStructureComponent>
      <cdi:identifier><cdi:ddiIdentifier>
        <cdi:dataIdentifier>#identifierComponent-idno</cdi:dataIdentifier>
      </cdi:ddiIdentifier></cdi:identifier>
      <cdi:type>IdentifierComponent</cdi:type>
    </cdi:DataStructureComponent>
  </cdi:DataStructure_has_DataStructureComponent>
  <cdi:DataStructure_has_DataStructureComponent>
    <!-- MeasureComponent for nwspol -->
    <cdi:DataStructureComponent>
      <cdi:identifier><cdi:ddiIdentifier>
        <cdi:dataIdentifier>#measureComponent-nwspol</cdi:dataIdentifier>
      </cdi:ddiIdentifier></cdi:identifier>
      <cdi:type>MeasureComponent</cdi:type>
    </cdi:DataStructureComponent>
  </cdi:DataStructure_has_DataStructureComponent>
  <!-- ... more MeasureComponents for netusoft, netustm, ppltrst, etc. -->
</cdi:WideDataStructure>
```

Example: `[Unit id, Income, Province]` -- Unit id identifies a statistical unit, Income and Province capture characteristics.

### 2.2 LongDataStructure (Event/Long)

The "long" format: multiple rows per case, with variable descriptor and value columns.

```xml
<!-- From XSD (lines 10946-10961): -->
LongDataStructureXsdType extends DataStructureXsdType
  -- no additional elements beyond base
```

Components: `IdentifierComponent`, `MeasureComponent`, `AttributeComponent`, **`DescriptorVariable`** (variable name column), **`ReferenceVariable`** (variable value column).

Example: `[Unit id, Income, Province, Variable name, Variable value]` where Variable name and Variable value represent all other instance variables in long format.

### 2.3 DimensionalDataStructure (Cube/Multi-Dimensional)

For OLAP-style data cubes.

```xml
<!-- From XSD (lines 8387-8434): -->
DimensionalDataStructureXsdType extends DataStructureXsdType
  DimensionalDataStructure_uses_DimensionGroup  (0..*)
```

Components: `DimensionComponent`, `MeasureComponent`, `AttributeComponent`.

Example: `[City, Average Income, Total Population]` where City is a dimension and Average Income and Total Population are measures.

Supporting classes:
- `DimensionalKey` -- Collection of data instances identifying data points (e.g., "male", "Ontario", "married")
- `DimensionalKeyDefinition` -- Collection of concepts defining data points (e.g., [Male], [Ontario], [Married])

### 2.4 KeyValueStructure (NoSQL)

For key-value datastores.

```xml
<!-- From XSD (lines 10168-10183): -->
KeyValueStructureXsdType extends DataStructureXsdType
  -- no additional elements beyond base
```

Components: `IdentifierComponent`, contextual, `SyntheticIdComponent`, `DimensionComponent`, variable descriptor, variable value.

Example: `[Income distribution, Unit id, Period, Income]` where Income distribution is the contextual component.

### 2.5 Data Structure Components

All structures share a common component base:

| Component Type | Purpose | Used In |
|---------------|---------|---------|
| `IdentifierComponent` | Unique row identifier (e.g., idno) | All |
| `MeasureComponent` | The variable of interest | All |
| `AttributeComponent` | Descriptive metadata | All |
| `DimensionComponent` | Cube dimension axis | Dimensional |
| `DescriptorVariable` | Variable name column | Long |
| `ReferenceVariable` | Variable value column | Long |
| `SyntheticIdComponent` | Generated key | KeyValue |

---

## 3. Process/Provenance Model

DDI-CDI has a rich process model for describing data provenance at any level of granularity.

### 3.1 Process Hierarchy

```
Sequence
  -> SequencePosition (indexes Activities with integer value)
  -> ControlLogic
    -> invokes Activity
    -> informs ProcessingAgent
  -> Activity
    -> has SubActivities (recursive)
    -> has Steps (recursive)
    -> entityUsed (input references with URI)
    -> entityProduced (output references with URI)
  -> Step (extends Activity)
    -> script (CommandCode with URI)
    -> scriptingLanguage (ControlledVocabularyEntry)
    -> produces Parameter
    -> receives Parameter
    -> hasSubStep_Step (recursive)
```

### 3.2 Activity

An Activity is a conceptual-level task. From the XSD (lines 702-715):

> "An activity is a task described at a conceptual level. It is not parameterized and as such is less reusable. For more logical/physical, fine-grained, reusable description there is a sub-type called step."

From Process_Example_CDI.xml (lines 440-460):
```xml
<cdi:Activity>
  <cdi:description>ERA5 data processing</cdi:description>
  <cdi:displayLabel>
    <cdi:languageSpecificString>
      <cdi:content>ERA5 data processing</cdi:content>
      <cdi:language>en</cdi:language>
    </cdi:languageSpecificString>
  </cdi:displayLabel>
  <cdi:entityProduced>
    <cdi:description>Integratable datafile for ERA5 (era5-regions)</cdi:description>
    <cdi:uri>https://doi.org/10.21338/era5-regions</cdi:uri>
  </cdi:entityProduced>
  <cdi:entityUsed>
    <cdi:description>ERA5 interim data</cdi:description>
    <cdi:uri>https://doi.org/10.21338/era5-interim</cdi:uri>
  </cdi:entityUsed>
  <cdi:Activity_has_Step>
    <cdi:ddiReference><cdi:dataIdentifier>...</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:Activity_has_Step>
  <!-- ... 26 Step references -->
</cdi:Activity>
```

Activities can nest: the top-level "Integrate climate and air quality data with ESS" has sub-activities for ERA5, EEA, and ESS data, each with their own sub-activities (Get raw input, Marshalling data, Data Processing).

### 3.3 Step

A Step extends Activity with executable script and parameter support. From the XSD (lines 15702-15715):

> "Step is a reusable, parameterized activity associated to information flows. One or more steps perform an activity."

From Process_Example_CDI.xml (lines 2025-2056):
```xml
<cdi:Step>
  <cdi:description>Compute target variable 'date' based on variable 'time'
    and 'region' to convert from UTC to local time zones</cdi:description>
  <cdi:identifier>
    <cdi:ddiIdentifier>
      <cdi:dataIdentifier>4fd913d0-c3b2-4e95-8a3b-90a5d34a56d3</cdi:dataIdentifier>
    </cdi:ddiIdentifier>
  </cdi:identifier>
  <cdi:name>
    <cdi:name>Create variable date</cdi:name>
  </cdi:name>
  <cdi:script>
    <cdi:commandFile>
      <cdi:uri>https://github.com/sikt-no/ess-labs-data-sp9/blob/master/era5-prepare.py#L14</cdi:uri>
    </cdi:commandFile>
  </cdi:script>
  <cdi:scriptingLanguage>
    <cdi:entryValue>Python3</cdi:entryValue>
  </cdi:scriptingLanguage>
  <cdi:Step_produces_Parameter>
    <cdi:ddiReference><cdi:dataIdentifier>a4c5a88e-...</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:Step_produces_Parameter>
  <cdi:Step_receives_Parameter>
    <cdi:ddiReference><cdi:dataIdentifier>fa27c73e-...</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:Step_receives_Parameter>
  <!-- ... more receives -->
</cdi:Step>
```

Key properties:
- `script` -- executable code URI (can point to GitHub with line anchors)
- `scriptingLanguage` -- e.g., "Python3"
- `Step_produces_Parameter` / `Step_receives_Parameter` -- input/output data flow
- `Step_hasSubStep_Step` -- recursive decomposition

### 3.4 ProcessingAgent

Agents that perform activities. Three subtypes:

| Agent Type | Example |
|-----------|---------|
| `Organization` | Sikt, CODATA, DDI Alliance |
| `Individual` | A researcher |
| `Machine` | SAS program, photocopier |

From Process_Example_CDI.xml (lines 205-230):
```xml
<cdi:ProcessingAgent>
  <cdi:Agent_possesses_ProductionEnvironment>
    <cdi:ddiReference><cdi:dataIdentifier>...</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:Agent_possesses_ProductionEnvironment>
  <cdi:purpose>Integrate climate data from ERA5 and air quality data
    from EEA with ESS survey data</cdi:purpose>
  <cdi:ProcessingAgent_performs_Activity>
    <cdi:ddiReference><cdi:dataIdentifier>...</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:ProcessingAgent_performs_Activity>
</cdi:ProcessingAgent>
```

### 3.5 ControlLogic and Sequence

ControlLogic orchestrates the flow:
- `ControlLogic_invokes_Activity` -- launches an activity
- `ControlLogic_informs_ProcessingAgent` -- notifies an agent
- `Sequence` contains `SequencePosition` elements that index activities with integer values

### 3.6 ProductionEnvironment

The platform where processing occurs.

```xml
<!-- From Process_Example_CDI.xml: -->
<cdi:ProductionEnvironment>
  <cdi:description>ESS Dataportal</cdi:description>
  <cdi:uri>https://dataportal.ess.nsd.uib.no/</cdi:uri>
</cdi:ProductionEnvironment>
```

---

## 4. CategoryScheme / Missing Codes

### 4.1 How CDI Represents Value Labels

The complete chain for a substantive value label (e.g., netusoft = 1 "Never"):

1. **CodeList** references Code objects:
   ```xml
   <cdi:CodeList>
     <cdi:dataIdentifier>#substantiveCodelist-netusoft</cdi:dataIdentifier>
     <cdi:CodeList_has_Code>
       <cdi:ddiReference><cdi:dataIdentifier>#code-1.0-netusoft</cdi:dataIdentifier></cdi:ddiReference>
     </cdi:CodeList_has_Code>
     <!-- ... more codes -->
   </cdi:CodeList>
   ```

2. **Code** links notation to category:
   ```xml
   <cdi:Code>
     <cdi:dataIdentifier>#code-1.0-netusoft</cdi:dataIdentifier>
     <cdi:Code_denotes_Category>
       <cdi:ddiReference><cdi:dataIdentifier>#category-Never</cdi:dataIdentifier></cdi:ddiReference>
     </cdi:Code_denotes_Category>
     <cdi:Code_uses_Notation>
       <cdi:ddiReference><cdi:dataIdentifier>#notation-1.0</cdi:dataIdentifier></cdi:ddiReference>
     </cdi:Code_uses_Notation>
   </cdi:Code>
   ```

3. **Category** holds the label:
   ```xml
   <cdi:Category>
     <cdi:displayLabel>
       <cdi:languageSpecificString>
         <cdi:content>Never</cdi:content>
       </cdi:languageSpecificString>
     </cdi:displayLabel>
     <cdi:name><cdi:name>Never</cdi:name></cdi:name>
   </cdi:Category>
   ```

4. **Notation** holds the actual value:
   ```xml
   <cdi:Notation>
     <cdi:content><cdi:content>1.0</cdi:content></cdi:content>
   </cdi:Notation>
   ```

### 4.2 How CDI Represents Missing/Sentinel Codes

Missing codes follow the exact same Code-Category-Notation chain, but are grouped in a **sentinel CodeList** referenced by a **SentinelValueDomain**.

From SPSS_Example.xml, the variable `nwspol` has sentinel codes:

| Notation Value | Category Label | Purpose |
|---------------|---------------|---------|
| 7777.0 | Refusal | Respondent refused to answer |
| 8888.0 | Don't know | Respondent didn't know |
| 9999.0 | No answer | No answer recorded |

```xml
<!-- Sentinel Code for Refusal: -->
<cdi:Code>
  <cdi:dataIdentifier>#code-7777.0-nwspol</cdi:dataIdentifier>
  <cdi:Code_denotes_Category>
    <cdi:ddiReference><cdi:dataIdentifier>#category-Refusal</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:Code_denotes_Category>
  <cdi:Code_uses_Notation>
    <cdi:ddiReference><cdi:dataIdentifier>#notation-7777.0</cdi:dataIdentifier></cdi:ddiReference>
  </cdi:Code_uses_Notation>
</cdi:Code>
```

For `netusoft`, sentinel codes are 7.0, 8.0, 9.0. For `netustm`, sentinel codes are 6666.0, 7777.0, 8888.0. The same Notation objects (e.g., `#notation-7777.0`) are reused across variables.

### 4.3 ValueAndConceptDescription

For described (non-enumerated) value domains, CDI uses `ValueAndConceptDescription` to specify value ranges. The SubstantiveValueDomain for `idno` uses this instead of a CodeList:

```xml
<cdi:SubstantiveValueDomain>
  <cdi:dataIdentifier>#substantiveValueDomain-idno</cdi:dataIdentifier>
  <cdi:SubstantiveValueDomain_isDescribedBy_ValueAndConceptDescription>
    <cdi:ddiReference>
      <cdi:dataIdentifier>#substantiveValueAndConceptDescription-idno</cdi:dataIdentifier>
    </cdi:ddiReference>
  </cdi:SubstantiveValueDomain_isDescribedBy_ValueAndConceptDescription>
</cdi:SubstantiveValueDomain>
```

This allows describing ranges like "real numbers between 0 and 3, represented to two Arabic decimal places" in a machine-actionable way.

### 4.4 CategoryRelationCode

From the XSD (lines 17857-17889), categories can be typed:

| Value | Meaning |
|-------|---------|
| `Nominal` | No order (categorical/discrete) |
| `Ordinal` | Rank order |
| `Interval` | Equal intervals, no true zero |
| `Ratio` | Equal intervals with true zero |
| `Continuous` | Both interval and ratio |

---

## 5. Key Differences from DDI-Lifecycle

### 5.1 Scope and Orientation

| Aspect | DDI-Lifecycle 3.3 | DDI-CDI 1.0 |
|--------|-------------------|-------------|
| **Orientation** | Study-centric (surveys, questionnaires) | Data-centric (the datum itself) |
| **Domain** | Survey/statistical research | Any domain (cross-domain) |
| **Granularity** | Study unit, data file, variable | Individual datum |
| **Primary focus** | Metadata management over time | Data structure description + process provenance |
| **Version** | V3.3 (2020) | V1.0 (2025) |
| **UML** | XML Schema driven | UML model-driven (Canonical XMI) |

### 5.2 Structural Differences

**DDI-Lifecycle** is organized around the data lifecycle:
- Study Unit, Data Collection, Logical Records, Physical Records, Physical Instances, Archiving, Groups, Resources, Comparison
- Supports questionnaires, instruments, sampling procedures
- Has repeated survey support and metadata reuse between studies

**DDI-CDI** is organized around data structures:
- Wide, Long, Dimensional, KeyValue data structures
- Process model (Sequence, ControlLogic, Activity, Step)
- Agent model (ProcessingAgent, Organization, Individual, Machine)
- Classification model (ClassificationFamily, ClassificationSeries, StatisticalClassification)

### 5.3 Variable Model Differences

DDI-Lifecycle has a simpler variable model:
- `Variable` with `CodeScheme` references
- `CategoryScheme` as a flat list
- Missing values embedded in variable definition

DDI-CDI has the 3-tier hierarchy (ConceptualVariable -> RepresentedVariable -> InstanceVariable) with the Substantive/Sentinel value domain split.

### 5.4 Process Model

DDI-Lifecycle has limited process description (mostly in the "Processing" module). DDI-CDI has a comprehensive process model with:
- Activity decomposition (SubActivities, Steps)
- Script attachment (with URI to code)
- Parameter flow (produces/receives)
- Agent orchestration
- Production environment tracking

### 5.5 Encoding

DDI-Lifecycle: Single XML Schema entry point (`instance.xsd`)
DDI-CDI: Multiple encodings -- W3C XML Schema, JSON-LD, Ontology (Turtle)

---

## 6. Relevance to Survey Data Cleaning

### 6.1 CGSS/CFPS/ABS Pipeline Mapping

DDI-CDI's architecture maps well to survey data cleaning workflows:

| Cleaning Concept | CDI Equivalent |
|-----------------|----------------|
| Source data file | `PhysicalDataSet` (physicalFileName: "CGSS2021.dta") |
| Variable definition | `InstanceVariable` with `hasIntendedDataType` |
| Value labels | `CodeList` -> `Code` -> `Category` + `Notation` chain |
| Missing codes (97/98/99) | `SentinelValueDomain` with sentinel `CodeList` |
| Valid values | `SubstantiveValueDomain` with substantive `CodeList` |
| Recoding/cleaning step | `Step` with `script` (URI to R/Python code) |
| Data transformation | `Activity` with `entityUsed`/`entityProduced` |
| Cleaning pipeline | `Sequence` with `ControlLogic` ordering |
| Who ran the pipeline | `ProcessingAgent` (Organization/Individual/Machine) |
| Platform used | `ProductionEnvironment` |

### 6.2 Missing Code Handling

The Substantive/Sentinel split is directly relevant to survey cleaning. For CGSS variables with missing codes like 97/98/99:

- **SubstantiveValueDomain**: References the substantive CodeList (e.g., 1-5 for Likert)
- **SentinelValueDomain**: References the sentinel CodeList (e.g., 97=Refusal, 98=Don't know, 99=No answer)
- Each sentinel code has its own Category with a human-readable label

This is cleaner than DDI-Lifecycle's approach where missing values are mixed into the variable definition.

### 6.3 Process Documentation

The Step model directly supports documenting cleaning operations:

```xml
<cdi:Step>
  <cdi:name>Recode missing values</cdi:name>
  <cdi:description>Recode 97/98/99 to NA for Likert-scale variables</cdi:description>
  <cdi:script>
    <cdi:commandFile>
      <cdi:uri>https://github.com/.../clean.R#L42</cdi:uri>
    </cdi:commandFile>
  </cdi:script>
  <cdi:scriptingLanguage>
    <cdi:entryValue>R</cdi:entryValue>
  </cdi:scriptingLanguage>
  <cdi:Step_receives_Parameter><!-- input dataset --></cdi:Step_receives_Parameter>
  <cdi:Step_produces_Parameter><!-- cleaned dataset --></cdi:Step_produces_Parameter>
</cdi:Step>
```

---

## 7. Mapping to ddi-metadata.yaml SSOT

The `ddi-metadata.yaml` file (generated by codebook-parse skill) uses a flat structure. Here is how each field maps to CDI:

### 7.1 Study Level

| ddi-metadata.yaml | CDI Equivalent | Notes |
|-------------------|---------------|-------|
| `study.name` | `DataSet` / `WideDataSet` name | CDI doesn't have a "study" concept; data-centric |
| `study.universe` | `Universe` class | Direct match |
| `study.analysis_unit` | `UnitType` class | Direct match |
| `study.data_source` | `PhysicalDataSet.physicalFileName` | File path |
| `study.wave` | No direct equivalent | CDI is domain-neutral; wave is survey-specific |

### 7.2 Variables

| ddi-metadata.yaml | CDI Equivalent | Notes |
|-------------------|---------------|-------|
| `variables[].name` | `InstanceVariable.name` | Direct match |
| `variables[].label` | `InstanceVariable.displayLabel` | Direct match |
| `variables[].concept` | `ConceptualVariable.descriptiveText` | CDI has full 3-tier hierarchy |
| `variables[].representation.type` | `RepresentedVariable.hasIntendedDataType` | CDI uses format strings like "F5.0" |
| `variables[].representation.storage_type` | `InstanceVariable.physicalDataType` | Direct match |
| `variables[].representation.category_scheme_ref` | `CodeList` reference via `SubstantiveValueDomain_takesValuesFrom_EnumerationDomain` | CDI uses dataIdentifier references |
| `variables[].is_temporal` | No direct equivalent | CDI is domain-neutral |
| `variables[].is_geographic` | No direct equivalent | CDI is domain-neutral |
| `variables[].is_weight` | `InstanceVariable.variableFunction` | Could be encoded here |

### 7.3 Missing Codes

| ddi-metadata.yaml | CDI Equivalent | Notes |
|-------------------|---------------|-------|
| `variables[].missing.codes` | `SentinelValueDomain` -> sentinel `CodeList` -> `Code` -> `Category` + `Notation` | CDI has richer structure with separate Category labels per code |
| `variables[].missing.ranges` | `ValueAndConceptDescription` on `SentinelValueDomain` | CDI can describe ranges formally |
| `variables[].missing.blank_is_missing` | Implied by `SentinelValueDomain.platformType` (e.g., `BlankString`) | CDI has explicit platform typing |
| `variables[].missing.schema_ref` | `SentinelValueDomain_takesConceptsFrom_SentinelConceptualDomain` | Links to conceptual domain |

### 7.4 Category Schemes

| ddi-metadata.yaml | CDI Equivalent | Notes |
|-------------------|---------------|-------|
| `shared_category_schemes` | `CodeList` objects (reusable across variables) | CDI CodeLists are naturally shared via dataIdentifier references |
| `shared_category_schemes.scheme_N.code: label` | `Code` -> `Category.name` + `Notation.content` | CDI separates code value (Notation) from label (Category) |

### 7.5 Processing Events

| ddi-metadata.yaml | CDI Equivalent | Notes |
|-------------------|---------------|-------|
| `processing_events[].event_id` | `Activity.identifier` | Direct match |
| `processing_events[].type` | Activity type/subtype | CDI uses Activity hierarchy |
| `processing_events[].description` | `Activity.description` | Direct match |
| `processing_events[].inputs` | `Activity.entityUsed` with URI | CDI uses URI references |
| `processing_events[].outputs` | `Activity.entityProduced` with URI | CDI uses URI references |
| `processing_events[].operator` | `ProcessingAgent` | CDI has full agent model |
| `processing_events[].timestamp` | No direct equivalent | CDI process model doesn't have built-in timestamps |
| `processing_events[].skill_version` | No direct equivalent | Tool-specific metadata |

### 7.6 Key Gaps

1. **Domain neutrality vs. survey specificity**: CDI doesn't have `is_temporal`, `is_geographic`, `is_weight`, `wave` -- these are survey-specific concerns that would need custom extensions or use of `variableFunction`.

2. **Flat vs. hierarchical**: ddi-metadata.yaml uses a flat variable list; CDI requires the full 3-tier hierarchy (ConceptualVariable -> RepresentedVariable -> InstanceVariable). This adds significant XML verbosity.

3. **Shared category schemes**: ddi-metadata.yaml uses `scheme_N` references; CDI uses `dataIdentifier` references to CodeList objects. Functionally equivalent but CDI is more verbose.

4. **Processing events**: ddi-metadata.yaml has simple event records; CDI has the full Activity/Step/Agent/Sequence model. CDI is much richer but much more complex.

5. **Missing code representation**: ddi-metadata.yaml uses `codes: {97: "Refusal", 98: "Don't know", 99: "No answer"}`. CDI requires 4 objects per code (Code + Category + Notation + CodeList entry). This is the most significant verbosity difference.

### 7.7 Practical Implications

For the codebook-parse skill, a full CDI encoding of ddi-metadata.yaml would be approximately 10-20x more verbose. The CDI model is designed for machine-to-machine interoperability and formal semantic precision, not for human-readable metadata files.

The ddi-metadata.yaml SSOT is well-designed as a practical intermediate representation. If CDI output is ever needed, the mapping is straightforward but requires generating the ConceptualVariable/RepresentedVariable/InstanceVariable hierarchy, the SubstantiveValueDomain/SentinelValueDomain split, and the Code/Category/Notation chain for every coded variable.

---

## Appendix A: Physical Data Layer

CDI separates logical and physical descriptions:

```
PhysicalDataSet
  -> PhysicalRecordSegment
    -> PhysicalSegmentLayout
      -> isDelimited (boolean)
      -> isFixedWidth (boolean)
      -> ValueMapping (one per variable)
        -> DataPoint
          -> DataPointPosition (start/end positions for fixed-width)
```

From SPSS_Example.xml:
```xml
<cdi:PhysicalDataSet>
  <cdi:physicalFileName>SPSS_Example.sav</cdi:physicalFileName>
</cdi:PhysicalDataSet>

<cdi:PhysicalSegmentLayout>
  <cdi:isDelimited>false</cdi:isDelimited>
  <cdi:isFixedWidth>false</cdi:isFixedWidth>
</cdi:PhysicalSegmentLayout>
```

## Appendix B: InstanceVariableMap

CDI supports key-value relationships for connecting logical records across datasets via `InstanceVariableMap`. This is useful for linking variables across data files (e.g., linking a respondent ID in a survey dataset to a geographic code in a regional dataset).

## Appendix C: Measurement Level

The `CategoryRelationCode` enumeration provides measurement theory typing:

```xml
<xs:enumeration value="Nominal"/>    <!-- no order -->
<xs:enumeration value="Ordinal"/>    <!-- rank order -->
<xs:enumeration value="Interval"/>   <!-- equal intervals -->
<xs:enumeration value="Ratio"/>      <!-- true zero -->
<xs:enumeration value="Continuous"/> <!-- interval or ratio -->
```

This can be used to annotate value domains with their statistical measurement level, which is relevant for choosing appropriate cleaning operations and statistical methods.
