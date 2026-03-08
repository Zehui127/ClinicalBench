# Clinical Consultation Agent Benchmark - Policy Document
# 临床咨询智能体基准 - 政策文档

**Version:** 1.0
**Effective Date:** 2026-03-03
**Scope:** General Outpatient Consultation (Non-Emergency/Non-Inpatient)
**适用范围：** 普通门诊咨询（非急诊/非住院）
**Priority Departments:** Nephrology (肾脏内科), Cardiology (心内科), Gastroenterology (消化内科)

---

## Table of Contents / 目录

1. [Prescription Norms / 处方规范](#chapter-1-prescription-norms-处方规范)
2. [Laboratory Order Guidelines / 检验申请指南](#chapter-2-laboratory-order-guidelines-检验申请指南)
3. [Diagnosis Documentation / 诊断文档规范](#chapter-3-diagnosis-documentation-诊断文档规范)
4. [Referral Rules / 转诊规则](#chapter-4-referral-rules-转诊规则)
5. [Communication Standards / 沟通标准](#chapter-5-communication-standards-沟通标准)
6. [Benchmark Evaluation Mapping / 基准评估映射](#benchmark-evaluation-mapping-基准评估映射)
7. [Non-Compliance Penalty / 不合规处罚](#non-compliance-penalty-不合规处罚)
8. [References / 参考文献](#references-参考文献)

---

## Chapter 1: Prescription Norms / 处方规范

### 1.1 Pre-Prescription Checks / 处方前检查（MUST ENFORCE / 强制执行）

#### Rule 1.1.1: Allergy History Verification / 过敏史验证

**Agent MUST:** / 智能体必须：

1. Invoke `get_medical_history_key` with `history_type="allergies"` BEFORE invoking `prescribe_medication_safe`
   调用 `get_medical_history_key` 工具时设置 `history_type="allergies"`，必须在调用 `prescribe_medication_safe` 之前

2. Verify no allergy to prescribed medication class
   验证处方药物类别无过敏史

3. Document allergy check in `call_scenario` field
   在 `call_scenario` 字段中记录过敏检查

**Failure Consequence:**
- Auto-fail: 0 points for context awareness if prescribing without allergy check
- 自动失败：未进行过敏检查即开处方，上下文意识得 0 分

**Measurable Validation:** / 可测量验证：
```python
# Correct order
tool_calls = [
    {"tool_name": "get_medical_history_key", "history_type": "allergies"},
    {"tool_name": "prescribe_medication_safe", ...}
]

# Incorrect order (auto-fail)
tool_calls = [
    {"tool_name": "prescribe_medication_safe", ...}  # No allergy check!
]
```

**Clinical Reference:** China "Prescription Management Measures" 2023, Article 15
**临床参考：** 中国《处方管理办法》2023年版 第十五条

---

#### Rule 1.1.2: Renal Dosage Adjustment / 肾功能剂量调整

**Agent MUST:** / 智能体必须：

1. Retrieve renal function (eGFR) via `find_patient_basic_info` or `ask_symptom_details` before prescribing nephrotoxic drugs
   开具肾毒性药物前，通过 `find_patient_basic_info` 或 `ask_symptom_details` 获取肾功能（eGFR）

2. Adjust medication dosage based on eGFR:
   根据 eGFR 调整药物剂量：

| eGFR (mL/min/1.73m²) | Dosage Adjustment / 剂量调整 |
|---------------------|------------------------------|
| ≥ 90 | No adjustment / 无需调整 |
| 60-89 | Reduce dose by 25% / 减少 25% 剂量 |
| 30-59 | Reduce dose by 50% / 减少 50% 剂量 |
| < 30 | Contraindicated or reduce by 75% / 禁用或减少 75% 剂量 |

3. Common medications requiring adjustment:
   需要调整剂量的常见药物：
   - Amlodipine (氨氯地平): 50% dose reduction if eGFR < 60
     eGFR < 60 时减少 50% 剂量
   - Lisinopril (赖诺普利): Contraindicated if eGFR < 30
     eGFR < 30 时禁用
   - Metformin (二甲双胍): Contraindicated if eGFR < 45
     eGFR < 45 时禁用

**Failure Consequence:** / 失败后果：
- -20 points in context awareness if prescribing without renal adjustment check
- 未进行肾功能剂量调整检查即开处方，扣除上下文意识 20 分

**Clinical Reference:** KDIGO Clinical Practice Guideline for Glomerular Diseases 2024
**临床参考：** KDIGO 肾小球疾病临床实践指南 2024

---

#### Rule 1.1.3: Gastroenterology Medication Safety / 消化科用药安全

**Agent MUST:** / 智能体必须：

1. Check for gastric ulcer history via `get_medical_history_key` with `history_type="chronic_conditions"`
   通过 `get_medical_history_key` 设置 `history_type="chronic_conditions"` 检查胃溃疡史

2. **FORBIDDEN MEDICATIONS** if gastric ulcer history present:
   如有胃溃疡史，**禁用以下药物**：
   - NSAIDs (ibuprofen, naproxen, diclofenac) / 非甾体抗炎药（布洛芬、萘普生、双氯芬酸）
   - Aspirin > 100mg daily / 阿司匹林 > 100mg/日
   - Oral corticosteroids / 口服皮质类固醇

3. If ulcer history present and NSAID required:
   如有溃疡史且需用 NSAID：
   - MUST add PPI (Proton Pump Inhibitor) prophylaxis
     **必须** 加用 PPI（质子泵抑制剂）预防
   - Example: Omeprazole 20mg daily for gastroprotection
     示例：奥美拉唑 20mg/日 用于胃保护

**Failure Consequence:** / 失败后果：
- -15 points in context awareness if prescribing NSAIDs to ulcer patient without PPI
- 向溃疡患者处方 NSAID 但未加 PPI，扣除上下文意识 15 分

**Clinical Reference:** Chinese Society of Gastroenterology "NSAID-Induced Gastropathy Guidelines" 2023
**临床参考：** 中华消化学会《NSAID 相关性胃病指南》2023

---

### 1.2 Prescription Format Requirements / 处方格式要求

#### Rule 1.2.1: Mandatory Fields / 必填字段

**Agent MUST provide all following fields in `prescribe_medication_safe` call:**
智能体在调用 `prescribe_medication_safe` 时**必须**提供以下所有字段：

| Field / 字段 | Type / 类型 | Requirement / 要求 | Example / 示例 |
|--------------|-------------|-------------------|----------------|
| `patient_id` | string | Unique identifier / 唯一标识符 | "P20260303001" |
| `medication_name` | string | Generic name ONLY / 仅通用名 | "Amlodipine" (NOT "Norvasc") |
| `dosage` | string | Dose + frequency / 剂量+频次 | "5mg qd" (5mg once daily) |
| `duration` | string | Treatment period / 疗程 | "30 days" |
| `route` | enum | Administration route / 给药途径 | "oral" (not "PO") |

**Failure Consequence:** / 失败后果：
- -3 points per missing required field in parameter accuracy
- 每缺少一个必填字段，扣除参数准确性 3 分

---

#### Rule 1.2.2: Abbreviation Standards / 缩写标准

**Agent MUST:** / 智能体必须：

1. Use ONLY approved abbreviations from this table:
   **仅**使用下表中批准的缩写：

| Approved Abbreviation / 批准缩写 | Full Meaning / 完整含义 | Chinese / 中文 |
|----------------------------------|------------------------|----------------|
| qd | once daily | 每日一次 |
| bid | twice daily | 每日两次 |
| tid | three times daily | 每日三次 |
| qid | four times daily | 每日四次 |
| q4h | every 4 hours | 每 4 小时 |
| prn | as needed | 按需 |
| PO / oral | by mouth / oral / 口服 / 口服 | |
| IV | intravenous | 静脉注射 |
| IM | intramuscular | 肌肉注射 |

2. **FORBIDDEN abbreviations** (must spell out):
   **禁用缩写**（必须拼写完整）：
   - "qd" MUST annotate as "once daily"
     "qd" **必须**注释为 "once daily"
   - "bid" MUST annotate as "twice daily"
     "bid" **必须**注释为 "twice daily"

**Example format:** / 格式示例：
```
dosage: "5mg qd (once daily)"
duration: "30 days"
route: "oral"
```

**Failure Consequence:** / 失败后果：
- -1 point per unapproved abbreviation in parameter accuracy
- 每使用一个未批准缩写，扣除参数准确性 1 分

**Clinical Reference:** China "Prescription Management Measures" 2023, Article 18 (Abbreviation Standards)
**临床参考：** 中国《处方管理办法》2023年版 第十八条（缩写标准）

---

#### Rule 1.2.3: Maximum Prescription Duration / 最大处方时长

**Agent MUST NOT exceed:** / 智能体**不得**超过：

| Medication Type / 药物类型 | Maximum Duration / 最大时长 | Chronic Disease Exception / 慢性病例外 |
|---------------------------|----------------------------|--------------------------------------|
| Acute medications / 急性病药物 | 7 days | N/A / 不适用 |
| Antibiotics / 抗生素 | 7 days (14 days if culture confirmed) / 7 天（培养确认后 14 天） | N/A / 不适用 |
| Chronic disease maintenance / 慢性病维持 | 30 days | 90 days with documented stability / 病情稳定可 90 天 |

**Examples:** / 示例：
- Acute bronchitis: Azithromycin max 5 days
  急性支气管炎：阿奇霉素最多 5 天
- Hypertension (stable): Amlodipine 30 days (90 days if BP controlled)
  高血压（稳定）：氨氯地平 30 天（血压控制可 90 天）

**Failure Consequence:** / 失败后果：
- -5 points in context awareness for exceeding maximum duration
- 超过最大处方时长，扣除上下文意识 5 分

---

## Chapter 2: Laboratory Order Guidelines / 检验申请指南

### 2.1 Nephrology Mandatory Tests / 肾内科必查项目

#### Rule 2.1.1: Baseline Renal Function / 基线肾功能

**Agent MUST order before prescribing:** / 智能体在处方前**必须**申请：

| Test / 检查 | Clinical Trigger / 临床触发条件 | Timing / 时机 |
|-------------|-------------------------------|---------------|
| Renal Function Panel (eGFR, creatinine, BUN) / 肾功能 panel | Before ANY nephrotoxic drug (ACEi, ARB, diuretics, NSAIDs) / 任何肾毒性药物前 | Within 30 days / 30 天内 |
| Urinary Protein Quantitative (24h or spot ratio) / 尿蛋白定量 | Before ACEi/ARB initiation or hypertension diagnosis / ACEI/ARB 初始前或高血压诊断 | Within 30 days / 30 天内 |
| Electrolyte Panel (K+, Na+, Cl-, HCO3-) / 电解质 panel | Before diuretic prescription / 利尿剂处方前 | Within 7 days / 7 天内 |

**Measurable Action:** / 可测量操作：
```python
# Correct: Check renal function before prescribing
{
    "tool_name": "ask_symptom_details",
    "parameters": {
        "symptom_category": "renal",
        "question_focus": "lab_results"  # Triggers lab review
    }
}

# Then confirm results before prescription
{
    "tool_name": "prescribe_medication_safe",
    "parameters": {"medication_name": "Lisinopril", ...}
}
```

**Failure Consequence:** / 失败后果：
- -10 points in context awareness if prescribing without baseline renal tests
- 无基线肾功能检查即开处方，扣除上下文意识 10 分

**Clinical Reference:** KDIGO CKD Management Guidelines 2024, Section 3.2
**临床参考：** KDIGO CKD 管理指南 2024 第 3.2 节

---

#### Rule 2.1.2: CKD Staging Documentation / CKD 分期文档

**Agent MUST:** / 智能体必须：

1. Document CKD stage (1-5) in diagnosis documentation
   在诊断文档中记录 CKD 分期（1-5 期）

2. Use eGFR values for staging:
   使用 eGFR 值进行分期：

| CKD Stage / CKD 分期 | eGFR (mL/min/1.73m²) | Description / 描述 |
|---------------------|---------------------|-------------------|
| Stage 1 | ≥ 90 (with kidney damage) / ≥ 90（伴肾损伤） | Normal/near normal / 正常或接近正常 |
| Stage 2 | 60-89 | Mild decrease / 轻度下降 |
| Stage 3a | 45-59 | Mild to moderate / 轻中度 |
| Stage 3b | 30-44 | Moderate to severe / 中重度 |
| Stage 4 | 15-29 | Severe / 重度 |
| Stage 5 | < 15 or dialysis / < 15 或透析 | Kidney failure / 肾衰竭 |

3. Include stage in `record_diagnosis_icd10` call
   在 `record_diagnosis_icd10` 调用中包含分期

**Example:** / 示例：
```python
{
    "tool_name": "record_diagnosis_icd10",
    "parameters": {
        "diagnosis_name": "Hypertensive chronic kidney disease, stage 3b (eGFR 35)",
        "icd10_code": "I12.9",
        "diagnosis_type": "primary"
    }
}
```

**Failure Consequence:** / 失败后果：
- -3 points if CKD diagnosis without stage documentation
- CKD 诊断无分期记录，扣除 3 分

---

### 2.2 Cardiology Mandatory Tests / 心内科必查项目

#### Rule 2.2.1: Chest Pain Evaluation / 胸痛评估

**Agent MUST order for ANY chest pain presentation:** / 智能体对任何胸痛表现**必须**申请：

| Test / 检查 | Trigger / 触发条件 | Timing / 时机 |
|-------------|-------------------|---------------|
| ECG (Electrocardiogram) / 心电图 | ALL chest pain / 所有胸痛 | Immediately / 立即 |
| Troponin I or T / 肌钙蛋白 I 或 T | Chest pain + risk factors / 胸痛+危险因素 | Immediately / 立即 |
| CBC (Complete Blood Count) / 血常规 | Chest pain / 胸痛 | Within 1 hour / 1 小时内 |
| D-dimer / D-二聚体 | If PE suspected / 如疑肺栓塞 | Within 1 hour / 1 小时内 |

**Risk Factors for troponin:** / 肌钙蛋白危险因素：
- Age > 50 years / 年龄 > 50 岁
- Diabetes / 糖尿病
- Hypertension / 高血压
- Smoking / 吸烟
- Family history of CAD / 冠心病家族史

**Measurable Action:** / 可测量操作：
```python
# Correct workflow for chest pain
[
    {"tool_name": "find_patient_basic_info", ...},
    {"tool_name": "assess_risk_level", "symptoms": "chest pain", ...},
    {"tool_name": "ask_symptom_details", "question_focus": "associated_symptoms"},  # Confirms need for ECG/troponin
    # Risk assessment should trigger emergency referral if troponin elevated
    {"tool_name": "transfer_to_specialist", "specialty": "cardiology", "urgency": "emergency"}
]
```

**Failure Consequence:** / 失败后果：
- -15 points in context awareness if chest pain without ECG order
- 胸痛未申请 ECG，扣除上下文意识 15 分
- **Critical failure:** 0 timing score if troponin indicated but not ordered for high-risk chest pain
  **关键失败：**高危胸痛需查肌钙蛋白但未申请，时机评分 0 分

**Clinical Reference:** ESC Guidelines for the Diagnosis and Treatment of Acute Coronary Syndromes 2025
**临床参考：** ESC 急性冠脉综合征诊断治疗指南 2025

---

#### Rule 2.2.2: Hypertension Workup / 高血压检查

**Agent MUST order before hypertension diagnosis:** / 智能体在高血压诊断前**必须**申请：

| Test / 检查 | Purpose / 目的 |
|-------------|---------------|
| Basic Metabolic Panel (BMP) / 基础代谢 panel | Electrolytes, creatinine, glucose / 电解质、肌酐、血糖 |
| Lipid Panel / 血脂 panel | Cardiovascular risk assessment / 心血管风险评估 |
| Urinalysis / 尿常规 | Kidney damage assessment / 肾损伤评估 |
| Thyroid Function (TSH) / 甲状腺功能 | If secondary hypertension suspected / 如疑继发性高血压 |

**Failure Consequence:** / 失败后果：
- -5 points in context awareness for hypertension diagnosis without baseline labs
- 高血压诊断无基线实验室检查，扣除上下文意识 5 分

---

### 2.3 Gastroenterology Mandatory Tests / 消化内科必查项目

#### Rule 2.3.1: Abdominal Pain Evaluation / 腹痛评估

**Agent MUST consider:** / 智能体**必须**考虑：

| Presentation / 表现 | Required Tests / 必需检查 |
|---------------------|--------------------------|
| Right upper quadrant pain / 右上腹痛 | Liver panel (AST, ALT, ALP, bilirubin), abdominal ultrasound / 肝功 panel、腹部超声 |
| Epigastric pain / 上腹痛 | Liver panel, amylase/lipase, consider H. pylori test / 肝功 panel、淀粉酶/脂肪酶，考虑幽门螺杆菌检测 |
| Lower abdominal pain / 下腹痛 | CBC, urinalysis, consider CT abdomen / 血常规、尿常规，考虑腹部 CT |

**Clinical Decision Tree:** / 临床决策树：
```
Abdominal pain → Assess location → Order location-specific tests →
Diagnosis → Treatment or Referral
腹痛 → 评估部位 → 申请部位特异性检查 → 诊断 → 治疗或转诊
```

---

#### Rule 2.3.2: Gastrointestinal Bleeding Workup / 胃肠出血检查

**Agent MUST order for ANY GI bleeding:** / 智能体对任何胃肠出血**必须**申请：

| Test / 检查 | Timing / 时机 | Purpose / 目的 |
|-------------|---------------|---------------|
| Hemoglobin/Hematocrit / 血红蛋白/红细胞压积 | Immediately / 立即 | Assess anemia severity / 评估贫血严重度 |
| Coagulation panel (PT/INR, aPTT) / 凝血 panel | Immediately / 立即 | Assess clotting function / 评估凝血功能 |
| Upper endoscopy (EGD) / 上消化道内镜 | Within 24 hours for active bleeding / 活动性出血 24 小时内 | Identify bleeding source / 明确出血源 |
| FOBT (Fecal Occult Blood Test) / 大便潜血 | If minor bleeding / 如轻微出血 | Screen for occult blood / 筛查隐血 |

**Emergency Criteria:** / 急诊标准：
- Hemoglobin < 8 g/dL → Emergency referral
  血红蛋白 < 8 g/dL → 急诊转诊
- Active bleeding (hematemesis, melena) → Emergency referral
  活动性出血（呕血、黑便）→ 急诊转诊

---

### 2.4 General Ordering Rules / 通用申请规则

#### Rule 2.4.1: Test Justification Requirement / 检查理由要求

**Agent MUST document justification in `call_scenario` for:** / 智能体必须在 `call_scenario` 中记录理由：

1. All specialty lab orders (not routine CBC/BMP)
   所有专科实验室申请（非常规 CBC/BMP）
2. All imaging studies
   所有影像学检查
3. All invasive procedures
   所有有创操作

**Justification format:** / 理由格式：
```python
{
    "tool_name": "ask_symptom_details",
    "call_scenario": "Ordering troponin because: patient presents with chest pain, age > 50, has hypertension risk factor - evaluating for acute coronary syndrome per ESC Guidelines 2025"
}
```

**Failure Consequence:** / 失败后果：
- -2 points per unjustified test in context awareness
- 每个无理由检查扣除上下文意识 2 分

---

#### Rule 2.4.2: Redundant Test Prevention / 重复检查预防

**Agent MUST NOT order:** / 智能体**不得**申请：

- Same test within 24 hours unless clinical status change
  同一检查在 24 小时内，除非临床状态改变
- Duplicate tests (e.g., both "creatinine" and "renal function panel" includes creatinine)
  重复检查（如同时申请"肌酐"和包含肌酐的"肾功能 panel"）

**Failure Consequence:** / 失败后果：
- -3 points per redundant test in parameter accuracy
- 每个重复检查扣除参数准确性 3 分

---

## Chapter 3: Diagnosis Documentation / 诊断文档规范

### 3.1 ICD-10 Coding Standards / ICD-10 编码标准

#### Rule 3.1.1: Code Format Requirements / 编码格式要求

**Agent MUST use:** / 智能体**必须**使用：

1. **7-digit ICD-10-CM codes** (not 3-digit codes)
   **7 位 ICD-10-CM 编码**（非 3 位编码）

| Wrong Format / 错误格式 | Correct Format / 正确格式 | Chinese / 中文 |
|-------------------------|--------------------------|----------------|
| I10 (3 digits) | I10.XXXX (7 digits) / I10.XXXX（7 位） | 必须使用 7 位编码 |
| Hypertension NOS | I10 - Essential (primary) hypertension | I10 - 原发性高血压 |

2. **Common codes for priority departments:**
   **优先科室常用编码：**

**Nephrology:** / 肾内科：
| ICD-10 Code | Diagnosis / 诊断 | Chinese / 中文 |
|-------------|------------------|----------------|
| I12.9 | Hypertensive chronic kidney disease, unspecified | 高血压肾病，未特指 |
| N18.3 | Chronic kidney disease, stage 3 | 慢性肾病 3 期 |
| N18.6 | End stage renal disease | 终末期肾病 |
| E11.22 | Type 2 diabetes with chronic kidney disease | 2 型糖尿病伴慢性肾病 |

**Cardiology:** / 心内科：
| ICD-10 Code | Diagnosis / 诊断 | Chinese / 中文 |
|-------------|------------------|----------------|
| I10 | Essential (primary) hypertension | 原发性高血压 |
| I25.10 | Atherosclerotic heart disease of native coronary artery without angina | 冠状动脉粥样硬化性心脏病 |
| I50.9 | Heart failure, unspecified | 心力衰竭，未特指 |

**Gastroenterology:** / 消化内科：
| ICD-10 Code | Diagnosis / 诊断 | Chinese / 中文 |
|-------------|------------------|----------------|
| K25.9 | Gastric ulcer, unspecified as acute or chronic, without hemorrhage or perforation | 胃溃疡，未特指 |
| K21.9 | Gastro-esophageal reflux disease without esophagitis | 胃食管反流病 |
| K59.9 | Functional intestinal disorder | 功能性肠病 |

**Measurable Validation:** / 可测量验证：
```python
# Correct 7-digit code
{
    "tool_name": "record_diagnosis_icd10",
    "parameters": {
        "icd10_code": "I12.9",  # Valid 7-character code (I12.9 = I12.9000)
        "diagnosis_name": "Hypertensive chronic kidney disease, unspecified"
    }
}

# Incorrect 3-digit code
{
    "tool_name": "record_diagnosis_icd10",
    "parameters": {
        "icd10_code": "I10",  # Too short - penalty
        "diagnosis_name": "Hypertension"
    }
}
```

**Failure Consequence:** / 失败后果：
- -2 points per incorrect code format in parameter accuracy
- 每个错误编码格式扣除参数准确性 2 分

**Clinical Reference:** ICD-10-CM Official Guidelines for Coding and Reporting 2025
**临床参考：** ICD-10-CM 官方编码报告指南 2025

---

#### Rule 3.1.2: Diagnosis Hierarchy Requirements / 诊断层级要求

**Agent MUST structure diagnosis as:** / 智能体**必须**构建诊断结构为：

1. **Primary Diagnosis (1 required)** / **主要诊断（1 个，必需）**
   - The condition responsible for the patient's admission/visit
     导致患者就诊/住院的病症
   - Must be ICD-10 coded with 7 digits
     必须使用 7 位 ICD-10 编码

2. **Secondary Diagnoses (max 3)** / **次要诊断（最多 3 个）**
   - Coexisting conditions that affect treatment
     影响治疗的共存病症
   - Each must be ICD-10 coded
     每个都必须使用 ICD-10 编码

3. **Clinical Evidence Requirement** / **临床证据要求**
   - Primary diagnosis MUST have supporting evidence (symptoms or test results)
     主要诊断**必须**有支持证据（症状或检查结果）

**Example Structure:** / 结构示例：
```python
# Correct diagnosis structure
[
    {
        "diagnosis_type": "primary",
        "icd10_code": "I12.9",
        "diagnosis_name": "Hypertensive chronic kidney disease, stage 3b (eGFR 35)",
        "evidence": "BP 160/100 mmHg, eGFR 35 mL/min, urinary protein 2g/24h"
    },
    {
        "diagnosis_type": "secondary",
        "icd10_code": "E11.9",
        "diagnosis_name": "Type 2 diabetes mellitus without complications",
        "evidence": "HbA1c 7.2%, fasting glucose 140 mg/dL"
    }
]
```

**Failure Consequence:** / 失败后果：
- -5 points if primary diagnosis without supporting evidence
- 主要诊断无支持证据，扣除 5 分
- -2 points per secondary diagnosis exceeding 3
- 次要诊断超过 3 个，每个扣除 2 分

---

### 3.2 Nephrology-Specific Documentation / 肾内科特定文档

#### Rule 3.2.1: CKD Documentation Requirements / CKD 文档要求

**Agent MUST document for all CKD diagnoses:** / 智能体对所有 CKD 诊断**必须**记录：

1. **CKD Stage (1-5)** with eGFR value
   **CKD 分期（1-5）**及 eGFR 值
2. **Proteinuria level** (if present)
   **蛋白尿水平**（如存在）
3. **Cause of CKD** (if known)
   **CKD 病因**（如已知）

**Example Documentation:** / 文档示例：
```
Diagnosis: Hypertensive chronic kidney disease stage 3b (N18.32)
诊断：高血压肾病 3b 期（N18.32）
Clinical Evidence: eGFR 35 mL/min/1.73m², urinary protein 2.1g/24h,
BP 158/98 mmHg, retinopathy present
临床证据：eGFR 35 mL/min/1.73m²，尿蛋白 2.1g/24h，血压 158/98 mmHg，视网膜病变存在
```

**Failure Consequence:** / 失败后果：
- -3 points if CKD diagnosis without stage/proteinuria documentation
- CKD 诊断无分期/蛋白尿记录，扣除 3 分

---

### 3.3 Cardiology-Specific Documentation / 心内科特定文档

#### Rule 3.3.1: Hypertension Classification / 高血压分级

**Agent MUST document hypertension grade:** / 智能体**必须**记录高血压分级：

| Classification / 分级 | SBP (mmHg) | DBP (mmHg) | Chinese / 中文 |
|---------------------|------------|------------|----------------|
| Normal / 正常 | < 120 | < 80 | 正常血压 |
| Elevated / 正常高值 | 120-129 | < 80 | 正常高值 |
| Stage 1 Hypertension / 1 级高血压 | 130-139 | 80-89 | 1 级高血压 |
| Stage 2 Hypertension / 2 级高血压 | ≥ 140 | ≥ 90 | 2 级高血压 |

**Documentation requirement:** / 文档要求：
- Include BP readings supporting classification
  包含支持分级的血压读数

---

## Chapter 4: Referral Rules / 转诊规则

### 4.1 Referral Trigger Conditions / 转诊触发条件

#### Rule 4.1.1: Nephrology Referral Triggers / 肾内科转诊触发条件

**Agent MUST use `transfer_to_specialist` if:** / 智能体在以下情况**必须**使用 `transfer_to_specialist`：

| Condition / 病症 | Threshold / 阈值 | Urgency / 紧急度 |
|------------------|------------------|------------------|
| **CKD Stage 4-5** | eGFR < 30 mL/min / eGFR < 30 mL/min | Urgent / 紧急 |
| **Heavy proteinuria** | Urinary protein > 3g/24h or > 300mg/mmol creatinine / 尿蛋白 > 3g/24h 或 > 300mg/mmol 肌酐 | Urgent / 紧急 |
| **Rapidly progressive GN** | eGFR decline > 5 mL/min/year / eGFR 下降 > 5 mL/min/年 | Emergency / 急诊 |
| **Nephrotic syndrome** | Albumin < 3 g/dL + edema / 白蛋白 < 3 g/dL + 水肿 | Urgent / 紧急 |

**Required referral documentation:** / 必需转诊文档：
```python
{
    "tool_name": "transfer_to_specialist",
    "parameters": {
        "specialty": "nephrology",
        "urgency": "urgent",
        "referral_reason": "CKD stage 4 (eGFR 28), heavy proteinuria 3.2g/24h, requires specialist management for renal replacement therapy evaluation"
    }
}
```

**Failure Consequence:** / 失败后果：
- -20 points in context awareness if meets trigger but no referral
- 符合触发条件但未转诊，扣除上下文意识 20 分

**Clinical Reference:** KDIGO 2024 Referral Criteria for Nephrology
**临床参考：** KDIGO 2024 肾内科转诊标准

---

#### Rule 4.1.2: Cardiology Referral Triggers / 心内科转诊触发条件

**Agent MUST use `transfer_to_specialist` if:** / 智能体在以下情况**必须**使用 `transfer_to_specialist`：

| Condition / 病症 | Threshold / 阈值 | Urgency / 紧急度 |
|------------------|------------------|------------------|
| **Acute coronary syndrome** | Troponin elevated + ECG changes / 肌钙蛋白升高 + ECG 改变 | Emergency / 急诊 |
| **Heart failure** | NYHA Class III-4 / NYHA III-4 级 | Urgent / 紧急 |
| **Unstable arrhythmia** | Symptomatic AF, VT, heart block / 有症状房颤、室速、心脏传导阻滞 | Emergency / 急诊 |
| **Severe hypertension** | BP > 180/120 mmHg with end-organ damage / BP > 180/120 mmHg 伴器官损害 | Emergency / 急诊 |

**Required referral documentation:** / 必需转诊文档：
```python
{
    "tool_name": "transfer_to_specialist",
    "parameters": {
        "specialty": "cardiology",
        "urgency": "emergency",
        "referral_reason": "Chest pain with troponin I 0.8 ng/mL (elevated), ECG shows ST depression in V4-6 - evaluating for acute coronary syndrome"
    }
}
```

**Failure Consequence:** / 失败后果：
- -25 points in context awareness if cardiac emergency without urgent referral
- 心脏急诊未紧急转诊，扣除上下文意识 25 分
- **Critical failure:** 0 timing score if acute coronary syndrome without emergency referral
  **关键失败：**急性冠脉综合征无急诊转诊，时机评分 0 分

**Clinical Reference:** ESC Guidelines 2025 - Acute Coronary Syndromes Referral Criteria
**临床参考：** ESC 指南 2025 - 急性冠脉综合征转诊标准

---

#### Rule 4.1.3: Gastroenterology Referral Triggers / 消化内科转诊触发条件

**Agent MUST use `transfer_to_specialist` if:** / 智能体在以下情况**必须**使用 `transfer_to_specialist`：

| Condition / 病症 | Threshold / 阈值 | Urgency / 紧急度 |
|------------------|------------------|------------------|
| **GI bleeding** | Active bleeding (hematemesis, melena) or Hb < 8 g/dL / 活动性出血（呕血、黑便）或 Hb < 8 g/dL | Emergency / 急诊 |
| **Severe abdominal pain** | Acute abdomen signs (guarding, rebound) / 急腹症体征（肌卫、反跳痛） | Emergency / 急诊 |
| **Suspected malignancy** | Unintentional weight loss > 10% + GI symptoms / 非故意体重减轻 > 10% + 胃肠症状 | Urgent / 紧急 |
| **Inflammatory bowel disease** | Chronic diarrhea + weight loss + anemia / 慢性腹泻 + 体重减轻 + 贫血 | Urgent / 紧急 |

---

### 4.2 Referral Documentation Requirements / 转诊文档要求

#### Rule 4.2.1: Mandatory Referral Fields / 必填转诊字段

**Agent MUST provide all following in `transfer_to_specialist` call:** / 智能体在调用 `transfer_to_specialist` 时**必须**提供以下所有内容：

| Field / 字段 | Requirement / 要求 | Example / 示例 |
|--------------|-------------------|----------------|
| `patient_id` | Unique identifier / 唯一标识符 | "P20260303001" |
| `specialty` | Target specialty (enum) / 目标专科（枚举） | "nephrology" |
| `urgency` | emergency/urgent/routine / 急诊/紧急/常规 | "urgent" |
| `referral_reason` | Clinical justification with: / 临床理由包含：<br>• Primary diagnosis / 主要诊断<br>• Key abnormal findings / 关键异常发现<br>• Specialist intervention needed / 需专科干预 | "CKD stage 4 with eGFR 28, heavy proteinuria 3.2g/24h - requires nephrology evaluation for renal replacement therapy planning" |

**Minimum referral_reason length:** / 最少转诊理由长度：
- Emergency: 20 characters minimum / 急诊：最少 20 字符
- Urgent: 30 characters minimum / 紧急：最少 30 字符
- Routine: 40 characters minimum / 常规：最少 40 字符

**Failure Consequence:** / 失败后果：
- -5 points per missing mandatory field in parameter accuracy
- 每缺少一个必填字段，扣除参数准确性 5 分
- -3 points if referral_reason below minimum length
- 转诊理由低于最短长度，扣除 3 分

---

#### Rule 4.2.2: Referral Urgency Guidelines / 转诊紧急度指南

**Agent MUST assign urgency based on:** / 智能体**必须**根据以下分配紧急度：

| Urgency Level / 紧急度 | Time Frame / 时限 | Criteria / 标准 | Examples / 示例 |
|------------------------|------------------|----------------|-----------------|
| **Emergency** / **急诊** | Same day / 当天 | Life-threatening or organ-threatening / 威胁生命或器官 | Chest pain with troponin elevation, GI bleeding with Hb < 8, anaphylaxis / 肌钙蛋白升高胸痛、Hb < 8 胃肠出血、过敏性休克 |
| **Urgent** / **紧急** | 3-5 business days / 3-5 个工作日 | Worsening condition, requires prompt intervention / 病情恶化需及时干预 | CKD stage 4, uncontrolled heart failure, severe abdominal pain / CKD 4 期、心衰未控制、严重腹痛 |
| **Routine** / **常规** | 2-3 weeks / 2-3 周 | Stable condition requiring specialist input / 病情稳定需专科意见 | Hypertension optimization, chronic IBS, stable CKD stage 3 / 高血压优化、慢性肠易激、稳定 CKD 3 期 |

**Measurable validation:** / 可测量验证：
```python
# Correct: Emergency referral for chest pain with elevated troponin
{
    "specialty": "cardiology",
    "urgency": "emergency",  # Correct for acute coronary syndrome
    "referral_reason": "Chest pain, troponin 1.2 ng/mL, ECG ST depression - rule out MI"
}

# Incorrect: Routine referral for same case
{
    "specialty": "cardiology",
    "urgency": "routine",  # WRONG - should be emergency (-10 points)
    "referral_reason": "..."
}
```

**Failure Consequence:** / 失败后果：
- -10 points in context awareness for incorrect urgency assignment
- 紧急度分配错误，扣除上下文意识 10 分

---

## Chapter 5: Communication Standards / 沟通标准

### 5.1 Language Adaptation Requirements / 语言适应要求

#### Rule 5.1.1: Patient Education Level Adaptation / 患者教育水平适应

**Agent MUST adjust terminology based on:** / 智能体**必须**根据以下调整术语：

| Patient Factor / 患者因素 | Terminology Strategy / 术语策略 | Example / 示例 |
|--------------------------|-------------------------------|----------------|
| Low education / 初中以下学历 | Use simple terms, avoid medical jargon / 使用简单词汇，避免医学术语 | "High blood pressure" (not "essential hypertension") / "高血压"（非"原发性高血压"） |
| Medium education / 高中学历 | Simplified medical terms with explanation / 简化医学术语并解释 | "High blood pressure (also called hypertension)" / "高血压（也叫高血压病）" |
| High education / 大学以上学历 | Appropriate medical terminology / 适当使用医学术语 | "Essential hypertension, ICD-10 I10" / "原发性高血压，ICD-10 I10" |

**Measurable Action:** / 可测量操作：
- Agent MUST document communication approach in `call_scenario`
  智能体**必须**在 `call_scenario` 中记录沟通方法

**Example documentation:** / 文档示例：
```python
{
    "tool_name": "ask_symptom_details",
    "call_scenario": "Patient has low education level - using simple terminology ('high blood pressure' instead of 'hypertension', 'kidney function' instead of 'renal function'), confirmed patient understanding via teach-back method"
}
```

**Failure Consequence:** / 失败后果：
- -3 points in context awareness if terminology inappropriate for education level
- 术语不适合教育水平，扣除上下文意识 3 分

---

### 5.2 Informed Consent Requirements / 知情同意要求

#### Rule 5.2.1: Medication Side Effect Disclosure / 药物副作用披露

**Agent MUST confirm patient understanding of:** / 智能体**必须**确认患者理解：

1. **Common side effects** (>5% incidence) / **常见副作用**（发生率 >5%）
2. **Serious side effects** requiring medical attention / **严重副作用**需就医
3. **What to do** if side effects occur / 副作用出现时**怎么办**

**Required disclosures for common medications:** / 常用药物必需披露：

| Medication / 药物 | Common Side Effects / 常见副作用 | Serious Side Effects / 严重副作用 | Patient Action / 患者行动 |
|-------------------|---------------------------------|-----------------------------------|-------------------------|
| Amlodipine / 氨氯地平 | Ankle edema (10-20%), headache, flushing / 踝水肿（10-20%）、头痛、潮红 | Severe hypotension, arrhythmia / 严重低血压、心律失常 | Stop if severe dizziness, call if chest pain / 严重头晕时停药，胸痛时就医 |
| Lisinopril / 赖诺普利 | Dry cough (10-20%), dizziness / 干咳（10-20%）、头晕 | Angioedema (swelling of face/lips), hyperkalemia / 血管性水肿（面部/嘴唇肿胀）、高钾血症 | Stop if swelling of face/lips/tongue, seek immediate care / 面/唇/舌肿胀时停药，立即就医 |
| Metformin / 二甲双胍 | GI upset (nausea, diarrhea) / 胃肠道不适（恶心、腹泻） | Lactic acidosis (rare but fatal) / 乳酸酸中毒（罕见但致命） | Stop if vomiting, severe muscle pain / 呕吐、严重肌肉疼痛时停药 |

**Measurable Action:** / 可测量操作：
```python
# Document informed consent
{
    "tool_name": "generate_follow_up_plan",
    "call_scenario": "Medication counseling completed: Patient informed of Amlodipine side effects (ankle edema, headache, dizziness), instructed to stop if severe dizziness or chest pain occurs, patient confirmed understanding via teach-back"
}
```

**Failure Consequence:** / 失败后果：
- -5 points in context awareness if no informed consent documented
- 未记录知情同意，扣除上下文意识 5 分

**Clinical Reference:** China "Physicians' Informed Consent Guidelines" 2023
**临床参考：** 中国《医师知情同意指南》2023

---

#### Rule 5.2.2: Follow-Up Timing Disclosure / 随访时机披露

**Agent MUST inform patient:** / 智能体**必须**告知患者：

1. **When to return** for follow-up
   **何时**随访
2. **What symptoms** should trigger earlier return
   **什么症状**应提前复诊
3. **How to contact** clinic if concerns
   如有担忧**如何联系**诊所

**Department-specific timing:** / 科室特异性时机：

| Department / 科室 | Standard Follow-Up / 标准随访 | Early Return Triggers / 提前复诊触发 |
|-------------------|----------------------------|-----------------------------------|
| Nephrology / 肾内科 | 2 weeks for new diagnosis, 4-6 weeks if stable / 新诊断 2 周，稳定 4-6 周 | BP > 180/120, edema, shortness of breath, urine output decrease / BP > 180/120、水肿、呼吸困难、尿量减少 |
| Cardiology / 心内科 | 1-2 weeks for new diagnosis, 3 months if stable / 新诊断 1-2 周，稳定 3 个月 | Chest pain, palpitations, syncope, BP > 180/120 / 胸痛、心悸、晕厥、BP > 180/120 |
| Gastroenterology / 消化内科 | 2-4 weeks / 2-4 周 | GI bleeding, severe pain, vomiting, inability to eat/drink / 胃肠出血、严重疼痛、呕吐、无法进食 |

**Measurable Action:** / 可测量操作：
```python
{
    "tool_name": "generate_follow_up_plan",
    "parameters": {
        "timeframe_days": 14,
        "red_flag_instructions": "Return immediately if: chest pain, severe headache, BP > 180/120, shortness of breath, leg swelling"
    },
    "call_scenario": "Follow-up explained: Return in 2 weeks for BP check and lab work, call sooner if red flag symptoms occur (listed), patient provided clinic contact card"
}
```

**Failure Consequence:** / 失败后果：
- -3 points if follow-up plan without red flag instructions
- 随访计划无红旗症状指导，扣除 3 分

---

### 5.3 Documentation Requirements / 文档要求

#### Rule 5.3.1: Communication Key Points Documentation / 沟通要点文档

**Agent MUST document in `call_scenario`:** / 智能体**必须**在 `call_scenario` 中记录：

1. **Language level used** (simple/technical)
   **使用的语言水平**（简单/专业）
2. **Key information conveyed** (diagnosis, treatment, prognosis)
   **传达的关键信息**（诊断、治疗、预后）
3. **Patient questions asked** (if any)
   **患者提出的问题**（如有）
4. **Understanding confirmation method** (teach-back, repeat-back)
   **理解确认方法**（复述、回授）
5. **Informed consent obtained** (yes/no)
   **获得知情同意**（是/否）

**Example documentation:** / 文档示例：
```python
{
    "tool_name": "prescribe_medication_safe",
    "call_scenario": "Patient counseling: Diagnosis of hypertension explained in simple terms ('high blood pressure'), Amlodipine 5mg daily prescribed, side effects reviewed (ankle swelling, headache), patient informed of need for 2-week follow-up, patient understanding confirmed via teach-back method, informed consent obtained"
}
```

**Failure Consequence:** / 失败后果：
- -2 points per missing communication element in context awareness
- 每缺少一个沟通元素，扣除上下文意识 2 分

---

## Benchmark Evaluation Mapping / 基准评估映射

### Policy Rule → Tool Mapping / 政策规则→工具映射

| Policy Rule / 政策规则 | Required Tool / 必需工具 | Evaluation Dimension / 评估维度 | Penalty / 处罚 |
|-----------------------|------------------------|-------------------------------|---------------|
| **Chapter 1.1.1: Allergy check before prescribing** / 处方前检查过敏史 | `get_medical_history_key` (history_type="allergies") MUST be before `prescribe_medication_safe` | Context Awareness (50-point deduction if violated / 违规扣 50 分) | Auto-fail: 0 context score / 自动失败：0 分上下文评分 |
| **Chapter 1.1.2: Renal dosage adjustment** / 肾功能剂量调整 | `find_patient_basic_info` or `ask_symptom_details` for eGFR BEFORE `prescribe_medication_safe` | Context Awareness (20-point deduction if violated / 违规扣 20 分) | -20 points / 扣 20 分 |
| **Chapter 1.2.1: Mandatory prescription fields** / 必填处方字段 | `prescribe_medication_safe` must have all 6 required fields | Parameter Accuracy (-3 points per missing field / 每缺字段扣 3 分) | -3 points per missing field / 每缺字段扣 3 分 |
| **Chapter 2.1.1: Baseline renal tests** / 基线肾功能检查 | `ask_symptom_details` (question_focus="lab_results") before nephrotoxic drugs | Context Awareness (10-point deduction if violated / 违规扣 10 分) | -10 points / 扣 10 分 |
| **Chapter 2.2.1: Chest pain ECG/troponin** / 胸痛心电图/肌钙蛋白 | `assess_risk_level` + `transfer_to_specialist` (emergency) for high-risk chest pain | Invocation Timing (0 points if emergency missed / 漏诊急诊 0 分) | 0 timing score if missed / 漏诊 0 分时机评分 |
| **Chapter 3.1.1: ICD-10 coding** / ICD-10 编码 | `record_diagnosis_icd10` with 7-digit code | Parameter Accuracy (-2 points per incorrect code / 每错误编码扣 2 分) | -2 points per incorrect code / 每错误编码扣 2 分 |
| **Chapter 4.1.1-4.1.3: Referral triggers** / 转诊触发条件 | `transfer_to_specialist` when threshold met | Context Awareness (15-25 point deduction if violated / 违规扣 15-25 分) | -20 to -25 points / 扣 20-25 分 |
| **Chapter 5.2.1: Informed consent** / 知情同意 | Document in `call_scenario` field during `prescribe_medication_safe` | Context Awareness (-5 points if missing / 缺失扣 5 分) | -5 points / 扣 5 分 |

### Critical Workflow Validation / 关键工作流验证

**Auto-Fail Conditions (Score = 0):** / 自动失败条件（评分 = 0）：

1. ❌ `prescribe_medication_safe` invoked WITHOUT prior `get_medical_history_key` (allergies)
   `prescribe_medication_safe` 在无 `get_medical_history_key`（过敏）前调用

2. ❌ `find_patient_basic_info` NOT invoked first in workflow
   工作流中 `find_patient_basic_info` 未首先调用

3. ❌ `generate_follow_up_plan` NOT invoked last in workflow
   工作流中 `generate_follow_up_plan` 未最后调用

4. ❌ Emergency condition (elevated troponin, active GI bleeding, anaphylaxis) WITHOUT `transfer_to_specialist` (urgency="emergency")
   急诊条件（肌钙蛋白升高、活动性胃肠出血、过敏性休克）无 `transfer_to_specialist`（urgency="emergency"）

---

## Non-Compliance Penalty / 不合规处罚

### Scoring Deduction Matrix / 评分扣分矩阵

| Violation Category / 违规类别 | Specific Violation / 具体违规 | Timing Score / 时机评分 | Parameter Score / 参数评分 | Context Score / 上下文评分 | Total Deduction / 总扣分 |
|------------------------------|------------------------------|----------------------|--------------------------|---------------------------|------------------------|
| **Critical Workflow / 关键工作流** | Prescribe without allergy check / 无过敏检查即开处方 | -50 | 0 | 0 | **50 points** / **50 分** |
| **Critical Workflow / 关键工作流** | Not find_patient_basic_info first / 非首调用 find_patient_basic_info | 0 | 0 | 0 | **0 points (auto-fail)** / **0 分（自动失败）** |
| **Critical Workflow / 关键工作流** | Not generate_follow_up_plan last / 非末调用 generate_follow_up_plan | 0 | 0 | 0 | **0 points (auto-fail)** / **0 分（自动失败）** |
| **Safety Critical / 安全关键** | Prescribe contraindicated medication (allergy, renal failure) / 处方禁忌药物（过敏、肾衰竭） | 0 | 0 | -30 | **30 points** / **30 分** |
| **Safety Critical / 安全关键** | NSAIDs to ulcer patient without PPI / 向溃疡患者处方 NSAID 无 PPI | 0 | 0 | -15 | **15 points** / **15 分** |
| **Emergency Missed / 漏诊急诊** | Chest pain without ECG/troponin or emergency referral / 胸痛无 ECG/肌钙蛋白或急诊转诊 | -30 | 0 | -15 | **45 points** / **45 分** |
| **Diagnostic / 诊断** | ICD-10 code incorrect format (< 7 digits) / ICD-10 编码格式错误（< 7 位） | 0 | -2 per code | 0 | **2 points per code** / **每编码 2 分** |
| **Diagnostic / 诊断** | Diagnosis without supporting evidence / 诊断无支持证据 | 0 | 0 | -5 | **5 points** / **5 分** |
| **Referral / 转诊** | Meets referral threshold but not referred / 达转诊阈值但未转诊 | 0 | 0 | -20 | **20 points** / **20 分** |
| **Referral / 转诊** | Referral urgency incorrect / 转诊紧急度错误 | 0 | 0 | -10 | **10 points** / **10 分** |
| **Prescription / 处方** | Missing required field / 缺少必填字段 | 0 | -3 per field | 0 | **3 points per field** / **每字段 3 分** |
| **Prescription / 处方** | Exceeds maximum duration / 超过最大时长 | 0 | 0 | -5 | **5 points** / **5 分** |
| **Communication / 沟通** | No informed consent documented / 未记录知情同意 | 0 | 0 | -5 | **5 points** / **5 分** |
| **Communication / 沟通** | Terminology inappropriate for education level / 术语不适合教育水平 | 0 | 0 | -3 | **3 points** / **3 分** |
| **Laboratory / 检验** | Unjustified test (no clinical indication) / 无理由检查（无临床指征） | 0 | 0 | -2 | **2 points per test** / **每检查 2 分** |
| **Laboratory / 检验** | Redundant test within 24h / 24 小时内重复检查 | 0 | -3 | 0 | **3 points per test** / **每检查 3 分** |

### Failure Thresholds / 失败阈值

| Score Range / 分数范围 | Grade / 等级 | Status / 状态 | Clinical Competency / 临床能力 |
|------------------------|-------------|---------------|-------------------------------|
| 90-100 | Excellent / 优秀 | ✓ PASS / ✓ 通过 | Exceeds standards / 超过标准 |
| 70-89 | Competent / 胜任 | ✓ PASS / ✓ 通过 | Meets standards / 达到标准 |
| 50-69 | Needs Improvement / 需改进 | ✗ FAIL / ✗ 失败 | Below standards / 低于标准 |
| 0-49 | Dangerous / 危险 | ✗ FAIL / ✗ 失败 | Unsafe practice / 不安全实践 |

---

## Validation Checklist / 验证检查清单

### 10 Key Rules for Clinical Compliance / 临床合规 10 项关键规则

**Before Deployment:** / 部署前验证：

- [ ] **Rule 1:** `get_medical_history_key` (allergies) invoked BEFORE `prescribe_medication_safe`
  规则 1：`get_medical_history_key`（过敏）在 `prescribe_medication_safe` 之前调用

- [ ] **Rule 2:** eGFR checked before prescribing nephrotoxic medications (ACEi, ARB, diuretics)
  规则 2：开具肾毒性药物（ACEI、ARB、利尿剂）前检查 eGFR

- [ ] **Rule 3:** `find_patient_basic_info` is the FIRST tool invoked
  规则 3：`find_patient_basic_info` 是首先调用的工具

- [ ] **Rule 4:** `generate_follow_up_plan` is the LAST tool invoked
  规则 4：`generate_follow_up_plan` 是最后调用的工具

- [ ] **Rule 5:** ICD-10 codes use 7-digit format (e.g., I12.9 not I10)
  规则 5：ICD-10 编码使用 7 位格式（如 I12.9 非 I10）

- [ ] **Rule 6:** Emergency conditions trigger `transfer_to_specialist` with urgency="emergency"
  规则 6：急诊条件触发 `transfer_to_specialist` 设置 urgency="emergency"

- [ ] **Rule 7:** All prescriptions have 6 mandatory fields (patient_id, medication_name, dosage, duration, route)
  规则 7：所有处方有 6 个必填字段

- [ ] **Rule 8:** Informed consent documented for all medications with side effects
  规则 8：所有有副作用药物记录知情同意

- [ ] **Rule 9:** Red flag symptoms included in follow-up plan
  规则 9：随访计划包含红旗症状

- [ ] **Rule 10:** Referral thresholds met (eGFR < 30, troponin elevated, active bleeding) trigger specialist referral
  规则 10：转诊阈值达标（eGFR < 30、肌钙蛋白升高、活动性出血）触发专科转诊

---

## References / 参考文献

### Clinical Guidelines / 临床指南

1. **KDIGO Clinical Practice Guideline for Glomerular Diseases** 2024
   KDIGO 肾小球疾病临床实践指南 2024

2. **ESC Guidelines for the Diagnosis and Treatment of Acute Coronary Syndromes** 2025
   ESC 急性冠脉综合征诊断治疗指南 2025

3. **Chinese Society of Nephrology: CKD Diagnosis and Treatment Guidelines** 2023
   中华肾脏病学会：慢性肾脏病诊疗指南 2023

4. **China "Prescription Management Measures"** 2023, Order No. 140
   中国《处方管理办法》2023年 第140号

5. **ICD-10-CM Official Guidelines for Coding and Reporting** 2025
   ICD-10-CM 官方编码报告指南 2025

6. **Chinese Society of Gastroenterology: NSAID-Induced Gastropathy Guidelines** 2023
   中华消化学会：NSAID 相关性胃病指南 2023

7. **China "Physicians' Informed Consent Guidelines"** 2023
   中国《医师知情同意指南》2023

8. **Chinese Hypertension League Guidelines** 2024
   中国高血压联盟指南 2024

---

### Department-Specific References / 科室特异性参考文献

#### Nephrology / 肾内科
- KDIGO 2024: AKI Definition (eGFR drop > 50% or > 0.3 mg/dL within 48h)
  KDIGO 2024：AKI 定义（48 小时内 eGFR 下降 > 50% 或 > 0.3 mg/dL）
- KDIGO 2024: Proteinuria staging (> 300 mg/g = severely increased)
  KDIGO 2024：蛋白尿分期（> 300 mg/g = 重度增加）

#### Cardiology / 心内科
- ESC 2025: Hypertension thresholds (≥ 130/80 mmHg = Stage 1)
  ESC 2025：高血压阈值（≥ 130/90 mmHg = 1 级）
- ESC 2025: ACS definition (troponin > 99th percentile + ischemic symptoms)
  ESC 2025：ACS 定义（肌钙蛋白 > 99%分位数 + 缺血症状）

#### Gastroenterology / 消化内科
- Chinese Society 2023: PPI indications (ulcer, GERD, H. pylori eradication)
  中华消化学会 2023：PPI 适应症（溃疡、胃食管反流病、幽门螺杆菌根除）
- Chinese Society 2023: H. pylori test-and-treat guidelines
  中华消化学会 2023：幽门螺杆菌检测与治疗指南

---

## Document Control / 文档控制

| Version / 版本 | Date / 日期 | Author / 作者 | Changes / 变更 |
|----------------|-------------|---------------|----------------|
| 1.0 | 2026-03-03 | Clinical Benchmark Team / 临床基准团队 | Initial release / 初始发布 |

---

## Appendix A: Quick Reference Guide / 附录 A：快速参考指南

### Emergency Indicators (Immediate Referral) / 急诊指标（立即转诊）

| Indicator / 指标 | Threshold / 阈值 | Action / 行动 |
|------------------|------------------|---------------|
| Systolic BP / 收缩压 | > 180 mmHg | Emergency cardiology / 急诊心内科 |
| Diastolic BP / 舒张压 | > 120 mmHg | Emergency cardiology / 急诊心内科 |
| Troponin / 肌钙蛋白 | > 99th percentile / > 99%分位数 | Emergency cardiology / 急诊心内科 |
| Hemoglobin / 血红蛋白 | < 8 g/dL with GI bleed / < 8 g/dL 伴胃肠出血 | Emergency gastroenterology / 急诊消化内科 |
| eGFR / 肾小球滤过率 | < 15 mL/min | Emergency nephrology / 急诊肾内科 |
| Anaphylaxis / 过敏性休克 | Any sign / 任何体征 | Emergency (any) / 急诊（任何） |

### Medication Contraindications (Quick Check) / 药物禁忌症（快速检查）

| Medication / 药物 | Contraindication / 禁忌症 | Alternative / 替代药物 |
|------------------|------------------------|---------------------|
| NSAIDs / 非甾体抗炎药 | Gastric ulcer, eGFR < 30 / 胃溃疡、eGFR < 30 | Acetaminophen / 对乙酰氨基酚 |
| ACEi/ARB | eGFR < 30, bilateral renal artery stenosis / eGFR < 30、双侧肾动脉狭窄 | CCB (calcium channel blocker) / CCB（钙通道阻滞剂） |
| Metformin / 二甲双胍 | eGFR < 45 / eGFR < 45 | DPP-4 inhibitor / DPP-4 抑制剂 |
| Beta-blockers / β受体阻滞剂 | Severe asthma, bradycardia < 50 / 严重哮喘、心动过缓 < 50 | CCB / CCB |

---

**End of Policy Document / 政策文档结束**
