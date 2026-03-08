# Clinical Data Usage Policy
# 临床数据使用政策

**Version:** 1.0.0
**Generated:** 2026-03-07T14:28:49.411957
**Last Updated:** 2026-03-07

---

## Overview / 概述

This policy document outlines the guidelines and rules for using the clinical data processing system, including tool usage, data handling, and safety protocols.

本文档概述了使用临床数据处理系统的指导原则和规则，包括工具使用、数据处理和安全协议。

---

## 1. Data Privacy and Security / 数据隐私与安全

### 1.1 Protected Health Information (PHI) / 受保护健康信息

- **ALL patient identifiers must be anonymized** before data storage
  **所有患者标识符在存储前必须匿名化**

- Patient IDs should use hashed values, not real identifiers
  患者ID应使用哈希值，而非真实标识符

- Names, dates of birth, and contact information must be removed
  姓名、出生日期和联系信息必须删除

### 1.2 Data Handling / 数据处理

- Data must be encrypted at rest and in transit
  数据必须静态和传输加密

- Access logs must be maintained for all data operations
  必须维护所有数据操作的访问日志

- Regular security audits are required
  需要定期安全审计

---

## 2. Tool Usage Guidelines / 工具使用指南

### 2.1 Available Tools / 可用工具

The following clinical tools are available in this system:
本系统提供以下临床工具：


#### 1. egfr_calculator

**Description / 描述:** Calculates estimated Glomerular Filtration Rate (eGFR) using CKD-EPI formula. Used to assess kidney function and determine appropriate drug dosing.

**Parameters / 参数:**
- `creatinine` (number) - Serum creatinine level in mg/dL [Required]
- `age` (integer) - Patient age in years [Required]
- `gender` (string) - Patient gender [Required]
- `race` (string) - Patient race (optional, for adjusted calculation) [Optional]

#### 2. drug_dosing_calculator

**Description / 描述:** Calculates appropriate drug doses based on patient parameters (weight, renal function, hepatic function). Supports dose adjustments for special populations.

**Parameters / 参数:**
- `drug_name` (string) - Name of the medication [Required]
- `standard_dose` (number) - Standard dose in mg [Required]
- `weight` (number) - Patient weight in kg [Optional]
- `egfr` (number) - eGFR value for renal dose adjustment [Optional]
- `indication` (string) - Clinical indication for the drug [Optional]

#### 3. drug_interaction_checker

**Description / 描述:** Checks for potential drug-drug interactions and provides severity assessment and management recommendations.

**Parameters / 参数:**
- `drug_list` (array) - List of medications to check for interactions [Required]
- `patient_age` (integer) - Patient age for age-specific interactions [Optional]
- `comorbidities` (array) - Patient comorbidities for context [Optional]

#### 4. vital_signs_analyzer

**Description / 描述:** Analyzes vital signs (BP, HR, RR, Temp, SpO2) and identifies abnormalities, trends, and critical values requiring immediate attention.

**Parameters / 参数:**
- `blood_pressure_systolic` (integer) - Systolic blood pressure [Optional]
- `blood_pressure_diastolic` (integer) - Diastolic blood pressure [Optional]
- `heart_rate` (integer) - Heart rate/pulse [Optional]
- `respiratory_rate` (integer) - Respiratory rate [Optional]
- `temperature` (number) - Body temperature [Optional]
- `oxygen_saturation` (number) - Oxygen saturation (SpO2) [Optional]
- `age` (integer) - Patient age for age-specific ranges [Optional]

#### 5. lab_values_interpreter

**Description / 描述:** Interprets common laboratory values and identifies abnormalities, trends, and clinical significance. Includes CBC, CMP, coagulation studies, and cardiac markers.

**Parameters / 参数:**
- `test_name` (string) - Name of the laboratory test [Required]
- `value` (number) - Laboratory value [Required]
- `unit` (string) - Unit of measurement [Optional]
- `reference_range` (string) - Normal reference range [Optional]
- `patient_context` (object) - Additional patient context (age, gender, diagnosis) [Optional]

#### 6. clinical_calculator

**Description / 描述:** Multi-purpose clinical calculator including BMI, risk scores, decision rules, and diagnostic criteria. Supports FRAX, CHA2DS2-VASc, HAS-BLED, Wells criteria, etc.

**Parameters / 参数:**
- `calculator_type` (string) - Type of calculator to use [Required]
- `parameters` (object) - Calculator-specific parameters [Required]

#### 7. fhir_get_condition

**Description / 描述:** Condition.Search (Problems) This web service retrieves problems from a patient's chart. This includes any data found in the patient's problem list across all encounters. This resource can be queried by a combination of patient ID and status.

Note that this resource retrieves only data stored in problem list records. As a result, medical history data documented outside of a patient's problem list isn't available to applications using this service unless that data is retrieved using another method.

This resource does not return unconfirmed Condition resources in the "holding tank" that drives the EpicCare Reconcile Outside Data Activity. Note - once a clinician reconciles a problem, a new Condition resource associated with the reconciled problem will be available in the normal Condition.Search results.

**Parameters / 参数:**
- `category` (string) - Always "problem-list-item" for this API. [Optional]
- `patient` (string) - Reference to a patient resource the condition is for. [Required]

#### 8. fhir_get_observation

**Description / 描述:** Observation.Search (Labs) The Observation (Labs) resource returns component level data for lab results. 

**Parameters / 参数:**
- `code` (string) - The observation identifier (base name). [Required]
- `date` (string) - Date when the specimen was obtained. [Optional]
- `patient` (string) - Reference to a patient resource the condition is for. [Required]

#### 9. fhir_get_observation

**Description / 描述:** Observation.Search (Vitals) This web service will retrieve vital sign data from a patient's chart, as well as any other non-duplicable data found in the patient's flowsheets across all encounters.

This resource requires the use of encoded flowsheet IDs. Work with each organization to obtain encoded flowsheet IDs. Note that encoded flowsheet IDs will be different for each organization. Encoded flowsheet IDs are also different across production and non-production environments.

**Parameters / 参数:**
- `category` (string) - Use "vital-signs" to search for vitals observations. [Required]
- `date` (string) - The date range for when the observation was taken. [Optional]
- `patient` (string) - Reference to a patient resource the condition is for. [Required]

#### 10. fhir_post_observation

**Description / 描述:** Observation.Create (Vitals) The FHIR Observation.Create (Vitals) resource can file to all non-duplicable flowsheet rows, including vital signs. This resource can file vital signs for all flowsheets.

**Parameters / 参数:**
- `resourceType` (string) - Use "Observation" for vitals observations. [Required]
- `category` (array) -  [Required]
- `code` (object) -  [Required]
- `effectiveDateTime` (string) - The date and time the observation was taken, in ISO format. [Required]
- `status` (string) - The status of the observation. Only a value of "final" is supported. We do not support filing data that isn't finalized. [Required]
- `valueString` (string) - Measurement value [Required]
- `subject` (object) -  [Required]

#### 11. fhir_get_medicationrequest

**Description / 描述:** MedicationRequest.Search (Signed Medication Order) You can use the search interaction to query for medication orders based on a patient and optionally status or category.

This resource can return various types of medications, including inpatient-ordered medications, clinic-administered medications (CAMS), patient-reported medications, and reconciled medications from Care Everywhere and other external sources.

The R4 version of this resource also returns patient-reported medications. Previously, patient-reported medications were not returned by the STU3 version of MedicationRequest and needed to be queried using the STU3 MedicationStatement resource. This is no longer the case. The R4 version of this resource returns patient-reported medications with the reportedBoolean element set to True. If the informant is known, it is also specified in the reportedReference element.

**Parameters / 参数:**
- `category` (string) - The category of medication orders to search for. By default all categories are searched.

Supported categories:
Inpatient
Outpatient (those administered in the clinic - CAMS)
Community (prescriptions)
Discharge [Optional]
- `date` (string) - The medication administration date. This parameter corresponds to the dosageInstruction.timing.repeat.boundsPeriod element. Medication orders that do not have start and end dates within the search parameter dates are filtered. If the environment supports multiple time zones, the search dates are adjusted one day in both directions, so more medications might be returned than expected. Use caution when filtering a medication list by date as it is possible to filter out important active medications. Starting in the November 2022 version of Epic, this parameter is respected. In May 2022 and earlier versions of Epic, this parameter is allowed but is ignored and no date filtering is applied. [Optional]
- `patient` (string) - The FHIR patient ID. [Required]

#### 12. fhir_post_medicationrequest

**Description / 描述:** MedicationRequest.Create

**Parameters / 参数:**
- `resourceType` (string) - Use "MedicationRequest" for medication requests. [Required]
- `medicationCodeableConcept` (object) -  [Required]
- `authoredOn` (string) - The date the prescription was written. [Required]
- `dosageInstruction` (array) -  [Required]
- `status` (string) - The status of the medication request. Use "active"  [Required]
- `intent` (string) - Use "order"  [Required]
- `subject` (object) -  [Required]

#### 13. fhir_get_procedure

**Description / 描述:** Procedure.Search (Orders) The FHIR Procedure resource defines an activity performed on or with a patient as part of the provision of care. It corresponds with surgeries and procedures performed, including endoscopies and biopsies, as well as less invasive actions like counseling and physiotherapy.

This resource is designed for a high-level summarization around the occurrence of a procedure, and not for specific procedure log documentation - a concept that does not yet have a defined FHIR Resource. When searching, only completed procedures are returned.


**Parameters / 参数:**
- `code` (string) - External CPT codes associated with the procedure. [Optional]
- `date` (string) - Date or period that the procedure was performed, using the FHIR date parameter format. [Required]
- `patient` (string) - Reference to a patient resource the condition is for. [Required]

#### 14. fhir_post_servicerequest

**Description / 描述:** ServiceRequest.Create

**Parameters / 参数:**
- `resourceType` (string) - Use "ServiceRequest" for service requests. [Required]
- `code` (object) - The standard terminology codes mapped to the procedure, which can include LOINC, SNOMED, CPT, CBV, THL, or Kuntalitto codes. [Required]
- `authoredOn` (string) - The order instant. This is the date and time of when an order is signed or signed and held. [Required]
- `status` (string) - The status of the service request. Use "active"  [Required]
- `intent` (string) - Use "order"  [Required]
- `priority` (string) - Use "stat"  [Required]
- `subject` (object) -  [Required]
- `note` (object) -  [Optional]
- `occurrenceDateTime` (string) - The date and time for the service request to be conducted, in ISO format. [Optional]

#### 15. fhir_get_patient

**Description / 描述:** Patient.Search This web service allows filtering or searching for patients based on a number of parameters, and retrieves patient demographic information from a patient's chart for each matching patient record. This service also does not respect the same filtering as MyChart, with the exception of the careProvider parameter.

**Parameters / 参数:**
- `address` (string) - The patient's street address. [Optional]
- `address-city` (string) - The city for patient's home address. [Optional]
- `address-postalcode` (string) - The postal code for patient's home address. [Optional]
- `address-state` (string) - The state for the patient's home address. [Optional]
- `birthdate` (string) - The patient's date of birth in the format YYYY-MM-DD. [Optional]
- `family` (string) - The patient's family (last) name. [Optional]
- `gender` (string) - The patient's legal sex. Starting in the August 2021 version of Epic, the legal-sex parameter is preferred. [Optional]
- `given` (string) - The patient's given name. May include first and middle names. [Optional]
- `identifier` (string) - The patient's identifier. [Optional]
- `legal-sex` (string) - The patient’s legal sex. Takes precedence over the gender search parameter. Available starting in the August 2021 version of Epic. [Optional]
- `name` (string) - Any part of the patient's name. When discrete name parameters are used, such as family or given, this parameter is ignored. [Optional]
- `telecom` (string) - The patient's phone number or email. [Optional]

### 2.2 Tool Safety Rules / 工具安全规则

- **Always validate input parameters** before tool invocation
  **始终在工具调用前验证输入参数**

- **Check for drug interactions** before prescribing medications
  **在开具药物前检查药物相互作用**

- **Verify dosage calculations** using clinical judgment
  **使用临床判断验证剂量计算**

- **Document all tool usage** in the clinical record
  **在临床记录中记录所有工具使用**

---

## 3. Clinical Decision Making / 临床决策

### 3.1 AI-Assisted Decisions / AI辅助决策

- AI tools provide **supportive information**, not final decisions
  AI工具提供**支持性信息**，而非最终决策

- **Clinical judgment** always takes precedence
  **临床判断**始终优先

- Verify AI recommendations with clinical guidelines
  使用临床指南验证AI建议

### 3.2 Error Handling / 错误处理

- Report all system errors to technical support
  向技术支持报告所有系统错误

- Document workaround procedures used
  记录使用的变通程序

- Do not use erroneous results in patient care
  不要在患者护理中使用错误结果

---

## 4. Department-Specific Guidelines / 部门特定指南

### 4.1 Cardiology / 心内科

- ECG interpretations require physician confirmation
  心电图解释需要医生确认

- Drug dosing must consider cardiac function
  药物剂量必须考虑心功能

### 4.2 Nephrology / 肾内科

- eGFR calculations require current creatinine values
  eGFR计算需要当前肌酐值

- Dose adjustments for renal impairment are mandatory
  肾功能损害的剂量调整是强制性的

### 4.3 Gastroenterology / 消化内科

- Consider drug-induced effects on GI system
  考虑药物对胃肠道的影响

- Screen for contraindications before prescribing
  在开药前筛查禁忌症

---

## 5. Quality Assurance / 质量保证

### 5.1 Data Validation / 数据验证

- All input data must be validated against schema
  所有输入数据必须根据架构进行验证

- Out-of-range values must be flagged for review
  超出范围的值必须标记以供审查

- Missing required fields must be reported
  必须报告缺失的必填字段

### 5.2 Performance Monitoring / 性能监控

- Monitor tool accuracy rates
  监控工具准确率

- Track processing times
  跟踪处理时间

- Document system performance metrics
  记录系统性能指标

---

## 6. Compliance and Auditing / 合规与审计

### 6.1 Regulatory Compliance / 监管合规

- Comply with HIPAA regulations (US)
  遵守HIPAA法规（美国）

- Follow GDPR requirements (EU)
  遵循GDPR要求（欧盟）

- Adhere to local medical data regulations
  遵守当地医疗数据法规

### 6.2 Audit Trail / 审计跟踪

- Maintain complete audit logs
  维护完整的审计日志

- Log all data access and modifications
  记录所有数据访问和修改

- Regular audit reviews are mandatory
  定期审计审查是强制性的

---

## 7. Support and Contact / 支持与联系

### 7.1 Technical Support / 技术支持

- **Email:** support@clinicalengine.example.com
- **Response Time:** Within 24 hours

### 7.2 Clinical Questions / 临床问题

- Contact the appropriate medical department
  联系相应的医疗部门
- Use official clinical guidelines
  使用官方临床指南

---

## 8. Version History / 版本历史

| Version | Date | Changes |
|---------|------|---------|
| {self.version} | {datetime.now().strftime('%Y-%m-%d')} | Initial release |

---

## 9. Acknowledgments / 确认

This clinical data processing system is designed to assist healthcare professionals in their daily work. Always prioritize patient safety and follow established clinical protocols.

本临床数据处理系统旨在协助医疗专业人员完成日常工作。始终将患者安全放在首位，并遵循既定的临床方案。

---

*This policy is subject to change. Always refer to the latest version.*
*本政策如有更改。请始终参考最新版本。*

*For questions or concerns, contact the system administrator.*
*如有疑问或顾虑，请联系系统管理员。*
