#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Output Generator for Clinical Data ETL
临床数据 ETL 的输出生成器

Generates standardized output files:
- tasks.json: Clinical task definitions
- db.json: Clinical knowledge database
- tools.json: Tool definitions
- policy.md: Usage policy document
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class OutputGenerator:
    """
    Generator for ETL output files.
    ETL 输出生成器。

    Generates all required output files from transformed clinical data.
    """

    def __init__(self, output_dir: str):
        """
        Initialize the output generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        # Metadata
        self.generated_at = datetime.now().isoformat()
        self.version = "1.0.0"

    def generate_tasks(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate tasks.json file.

        Args:
            data: Transformed clinical data

        Returns:
            Path to generated file
        """
        tasks = []

        for record in data:
            task = {
                "id": record.get("id", ""),
                "department": record.get("department", ""),
                "difficulty": record.get("difficulty", "moderate"),
                "description": record.get("description", ""),
                "clinical_scenario": record.get("clinical_scenario", {}),
                "tool_call_requirements": record.get("tool_call_requirements", {}),
                "expected_outcome": record.get("expected_outcome", ""),
                "metadata": {
                    **record.get("metadata", {}),
                    "generated_at": self.generated_at,
                },
            }
            tasks.append(task)

        output_path = self.output_dir / "tasks.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def generate_db(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate db.json file (clinical knowledge database).

        Args:
            data: Transformed clinical data

        Returns:
            Path to generated file
        """
        db = {
            "metadata": {
                "version": self.version,
                "generated_at": self.generated_at,
                "total_records": len(data),
            },
            "records": [],
            "indexes": {
                "by_department": {},
                "by_difficulty": {},
                "by_diagnosis": {},
            },
        }

        # Process records and build indexes
        for record in data:
            db_record = {
                "id": record.get("id", ""),
                "department": record.get("department", ""),
                "difficulty": record.get("difficulty", ""),
                "clinical_scenario": record.get("clinical_scenario", {}),
                "keywords": self._extract_keywords(record),
            }
            db["records"].append(db_record)

            # Build department index
            dept = record.get("department", "unknown")
            if dept not in db["indexes"]["by_department"]:
                db["indexes"]["by_department"][dept] = []
            db["indexes"]["by_department"][dept].append(db_record["id"])

            # Build difficulty index
            diff = record.get("difficulty", "unknown")
            if diff not in db["indexes"]["by_difficulty"]:
                db["indexes"]["by_difficulty"][diff] = []
            db["indexes"]["by_difficulty"][diff].append(db_record["id"])

            # Build diagnosis index
            diagnosis = record.get("clinical_scenario", {}).get("diagnosis", "")
            if diagnosis:
                if diagnosis not in db["indexes"]["by_diagnosis"]:
                    db["indexes"]["by_diagnosis"][diagnosis] = []
                db["indexes"]["by_diagnosis"][diagnosis].append(db_record["id"])

        output_path = self.output_dir / "db.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def _extract_keywords(self, record: Dict[str, Any]) -> List[str]:
        """Extract keywords from record for searching."""
        keywords = []

        # Add department
        dept = record.get("department", "")
        if dept:
            keywords.append(dept.lower())

        # Add difficulty
        diff = record.get("difficulty", "")
        if diff:
            keywords.append(diff.lower())

        # Add diagnosis keywords
        scenario = record.get("clinical_scenario", {})
        diagnosis = scenario.get("diagnosis", "")
        if diagnosis:
            keywords.extend(diagnosis.lower().split())

        # Add symptom keywords
        symptoms = scenario.get("patient_info", {}).get("symptoms", [])
        if symptoms:
            for symptom in symptoms:
                keywords.extend(str(symptom).lower().split())

        # Remove duplicates
        return list(set(keywords))

    def generate_tools(self, tools: List[Dict[str, Any]]) -> str:
        """
        Generate tools.json file.

        Args:
            tools: List of tool definitions

        Returns:
            Path to generated file
        """
        output_data = {
            "metadata": {
                "version": self.version,
                "generated_at": self.generated_at,
                "total_tools": len(tools),
            },
            "tools": tools,
        }

        output_path = self.output_dir / "tools.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def generate_policy(self, tools: List[Dict[str, Any]]) -> str:
        """
        Generate policy.md file.

        Args:
            tools: List of tool definitions

        Returns:
            Path to generated file
        """
        policy_content = self._generate_policy_content(tools)

        output_path = self.output_dir / "policy.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(policy_content)

        return str(output_path)

    def _generate_policy_content(self, tools: List[Dict[str, Any]]) -> str:
        """Generate policy document content."""
        content = f"""# Clinical Data Usage Policy
# 临床数据使用政策

**Version:** {self.version}
**Generated:** {self.generated_at}
**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

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

"""

        # Add tool descriptions
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get("name", "Unknown")
            tool_desc = tool.get("description", "No description")
            tool_params = tool.get("parameters", [])

            content += f"""
#### {i}. {tool_name}

**Description / 描述:** {tool_desc}

**Parameters / 参数:**
"""
            if tool_params:
                for param in tool_params:
                    param_name = param.get("name", "unknown")
                    param_type = param.get("type", "any")
                    param_desc = param.get("description", "")
                    required = "Required" if param.get("required", False) else "Optional"
                    content += f"- `{param_name}` ({param_type}) - {param_desc} [{required}]\n"
            else:
                content += "- No specific parameters required\n"

        content += """
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
"""
        return content

    def generate_summary(
        self,
        result: "ETLResult",
        stats: Dict[str, Any],
        tools: List[Dict[str, Any]]
    ) -> str:
        """
        Generate summary report (JSON format).

        Args:
            result: ETL operation result
            stats: Processing statistics
            tools: Tool definitions

        Returns:
            Path to generated file
        """
        summary = {
            "metadata": {
                "version": self.version,
                "generated_at": self.generated_at,
                "pipeline_version": "1.0.0",
            },
            "etl_result": {
                "success": result.success,
                "start_time": result.start_time.isoformat() if result.start_time else None,
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration_seconds": (
                    (result.end_time - result.start_time).total_seconds()
                    if result.start_time and result.end_time else 0
                ),
                "records_processed": result.records_processed,
                "records_failed": result.records_failed,
                "tasks_generated": result.tasks_generated,
                "db_records": result.db_records,
                "tools_count": result.tools_count,
                "errors": result.errors,
                "warnings": result.warnings,
                "output_files": result.output_files,
            },
            "statistics": stats,
            "tools_summary": {
                "total_tools": len(tools),
                "tool_names": [t.get("name", "unknown") for t in tools],
                "departments_covered": list(set(
                    t.get("department", "") for t in tools if t.get("department")
                )),
            },
        }

        output_path = self.output_dir / "etl_summary.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return str(output_path)
