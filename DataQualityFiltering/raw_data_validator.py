#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raw Data Validator
原始数据验证器 - 阶段1测试

在数据转换之前验证原始医患对话数据，确保数据适合转换为tasks。

功能：
1. 验证对话结构（是否有患者主诉、医生回答）
2. 验证对话长度（是否足够生成有意义的task）
3. 验证医学相关性（是否是医学咨询内容）
4. 验证科室信息（科室是否明确）
5. 验证数据完整性（必填字段是否存在）

作者：Tau2 Data Quality Team
版本：1.0
日期：2025-03
"""

import json
import re
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    dialogue_id: str
    department: str
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "passed": self.passed,
            "dialogue_id": self.dialogue_id,
            "department": self.department,
            "issues": self.issues,
            "warnings": self.warnings,
            "metrics": self.metrics
        }


@dataclass
class ValidationReport:
    """验证报告"""
    total_dialogues: int = 0
    passed_dialogues: int = 0
    failed_dialogues: int = 0
    pass_rate: float = 0.0

    # 统计信息
    department_distribution: Dict[str, int] = field(default_factory=dict)
    failure_reasons: Counter = field(default_factory=Counter)
    warning_distribution: Counter = field(default_factory=Counter)

    # 详细结果
    details: List[ValidationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "summary": {
                "total": self.total_dialogues,
                "passed": self.passed_dialogues,
                "failed": self.failed_dialogues,
                "pass_rate": f"{self.pass_rate:.1%}"
            },
            "statistics": {
                "department_distribution": dict(self.department_distribution),
                "failure_reasons": dict(self.failure_reasons),
                "warning_distribution": dict(self.warning_distribution)
            },
            "details": [r.to_dict() for r in self.details]
        }


class RawDataValidator:
    """
    原始医患对话数据验证器

    在数据转换之前验证原始对话数据的质量。
    """

    # 医学关键词（用于验证医学相关性）
    MEDICAL_KEYWORDS_ZH = [
        # 症状
        "疼痛", "发烧", "头痛", "恶心", "呕吐", "咳嗽", "头晕", "乏力",
        "失眠", "腹泻", "便秘", "胸闷", "气短", "心悸", "水肿", "麻木",
        "胃痛", "腹痛", "腹胀", "反酸", "食欲不振", "痒", "皮疹",

        # 医学名词
        "医生", "患者", "症状", "诊断", "治疗", "药物", "手术", "血压",
        "心率", "检查", "化验", "住院", "门诊", "复查", "预约", "挂号",

        # 科室
        "内科", "外科", "妇科", "儿科", "肿瘤科", "神经科", "心脏科",
        "消化科", "内分泌", "肾病", "男科", "骨科", "眼科", "耳鼻喉",

        # 常见疾病
        "高血压", "糖尿病", "感冒", "炎症", "过敏", "肿瘤", "癌症",
        "心脏病", "中风", "癫痫", "哮喘", "胃炎", "肝炎", "肾炎",
    ]

    # 最小对话长度
    MIN_PATIENT_LENGTH = 5  # 患者主诉最小字符数
    MIN_DOCTOR_LENGTH = 10  # 医生回答最小字符数
    MIN_TOTAL_TURNS = 2     # 最少对话轮数

    # 必需字段（CSV格式）
    REQUIRED_FIELDS = ["department", "dialogue_id", "role", "content"]

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化验证器

        Args:
            config: 配置参数
                - min_patient_length: 患者主诉最小长度
                - min_doctor_length: 医生回答最小长度
                - min_total_turns: 最少对话轮数
                - strict_mode: 严格模式（所有检查都通过才pass）
        """
        self.config = config or {}
        self.min_patient_length = self.config.get("min_patient_length", self.MIN_PATIENT_LENGTH)
        self.min_doctor_length = self.config.get("min_doctor_length", self.MIN_DOCTOR_LENGTH)
        self.min_total_turns = self.config.get("min_total_turns", self.MIN_TOTAL_TURNS)
        self.strict_mode = self.config.get("strict_mode", False)

        self.logger = logging.getLogger(__name__)

    def validate_dialogue(
        self,
        dialogue_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        验证单条对话数据

        Args:
            dialogue_data: 对话数据字典
                {
                    "department": "内科",
                    "dialogue_id": "D001",
                    "turns": [
                        {"role": "patient", "content": "..."},
                        {"role": "doctor", "content": "..."}
                    ]
                }

        Returns:
            ValidationResult: 验证结果
        """
        dialogue_id = dialogue_data.get("dialogue_id", "unknown")
        department = dialogue_data.get("department", "unknown")
        turns = dialogue_data.get("turns", [])

        issues = []
        warnings = []
        metrics = {}

        # 检查1: 必需字段
        if not dialogue_id or dialogue_id == "unknown":
            issues.append("缺少dialogue_id")

        if not department or department == "unknown":
            issues.append("缺少department信息")

        # 检查2: 对话轮数
        total_turns = len(turns)
        metrics["total_turns"] = total_turns

        if total_turns < self.min_total_turns:
            issues.append(f"对话轮数不足：{total_turns} < {self.min_total_turns}")

        # 检查3: 患者主诉
        patient_turns = [t for t in turns if t.get("role") == "patient"]
        metrics["patient_turns"] = len(patient_turns)

        if not patient_turns:
            issues.append("缺少患者主诉")
        else:
            patient_content = " ".join([t.get("content", "") for t in patient_turns])
            patient_length = len(patient_content.strip())
            metrics["patient_content_length"] = patient_length

            if patient_length < self.min_patient_length:
                warnings.append(f"患者主诉过短：{patient_length} < {self.min_patient_length}")

        # 检查4: 医生回答
        doctor_turns = [t for t in turns if t.get("role") == "doctor"]
        metrics["doctor_turns"] = len(doctor_turns)

        if not doctor_turns:
            warnings.append("缺少医生回答")
        else:
            doctor_content = " ".join([t.get("content", "") for t in doctor_turns])
            doctor_length = len(doctor_content.strip())
            metrics["doctor_content_length"] = doctor_length

            if doctor_length < self.min_doctor_length:
                warnings.append(f"医生回答过短：{doctor_length} < {self.min_doctor_length}")

        # 检查5: 医学相关性
        all_content = " ".join([t.get("content", "") for t in turns])
        medical_keyword_count = sum(1 for kw in self.MEDICAL_KEYWORDS_ZH if kw in all_content)
        metrics["medical_keywords_count"] = medical_keyword_count

        if medical_keyword_count == 0:
            issues.append("未检测到医学关键词，可能不是医学咨询")
        elif medical_keyword_count < 2:
            warnings.append(f"医学关键词较少：{medical_keyword_count} < 2")

        # 检查6: 对话内容是否为空
        empty_turns = sum(1 for t in turns if not t.get("content", "").strip())
        if empty_turns > 0:
            issues.append(f"有{empty_turns}轮对话内容为空")

        # 判断是否通过
        # 严格模式：所有检查都通过
        # 宽松模式：只有issues才阻断，warnings不阻断
        if self.strict_mode:
            passed = len(issues) == 0 and len(warnings) == 0
        else:
            passed = len(issues) == 0

        return ValidationResult(
            passed=passed,
            dialogue_id=dialogue_id,
            department=department,
            issues=issues,
            warnings=warnings,
            metrics=metrics
        )

    def validate_csv_file(
        self,
        csv_path: str,
        encoding: str = "utf-8"
    ) -> ValidationReport:
        """
        验证CSV格式的对话数据

        Args:
            csv_path: CSV文件路径
            encoding: 文件编码

        Returns:
            ValidationReport: 验证报告
        """
        self.logger.info(f"开始验证CSV文件: {csv_path}")

        report = ValidationReport()
        dialogues = self._load_csv(csv_path, encoding)

        report.total_dialogues = len(dialogues)

        # 验证每条对话
        for dialogue_data in dialogues:
            result = self.validate_dialogue(dialogue_data)
            report.details.append(result)

            # 更新统计
            if result.passed:
                report.passed_dialogues += 1
            else:
                report.failed_dialogues += 1
                report.failure_reasons.update(result.issues)

            report.warning_distribution.update(result.warnings)

            # 科室分布
            dept = result.department
            report.department_distribution[dept] = report.department_distribution.get(dept, 0) + 1

        # 计算通过率
        if report.total_dialogues > 0:
            report.pass_rate = report.passed_dialogues / report.total_dialogues

        self.logger.info(f"验证完成: {report.passed_dialogues}/{report.total_dialogues} 通过 ({report.pass_rate:.1%})")

        return report

    def validate_json_file(
        self,
        json_path: str,
        encoding: str = "utf-8"
    ) -> ValidationReport:
        """
        验证JSON格式的对话数据

        Args:
            json_path: JSON文件路径
            encoding: 文件编码

        Returns:
            ValidationReport: 验证报告
        """
        self.logger.info(f"开始验证JSON文件: {json_path}")

        report = ValidationReport()

        with open(json_path, "r", encoding=encoding) as f:
            dialogues = json.load(f)

        if isinstance(dialogues, dict):
            dialogues = dialogues.get("dialogues", dialogues.get("data", [dialogues]))

        report.total_dialogues = len(dialogues)

        # 验证每条对话
        for dialogue_data in dialogues:
            result = self.validate_dialogue(dialogue_data)
            report.details.append(result)

            # 更新统计
            if result.passed:
                report.passed_dialogues += 1
            else:
                report.failed_dialogues += 1
                report.failure_reasons.update(result.issues)

            report.warning_distribution.update(result.warnings)

            # 科室分布
            dept = result.department
            report.department_distribution[dept] = report.department_distribution.get(dept, 0) + 1

        # 计算通过率
        if report.total_dialogues > 0:
            report.pass_rate = report.passed_dialogues / report.total_dialogues

        self.logger.info(f"验证完成: {report.passed_dialogues}/{report.total_dialogues} 通过 ({report.pass_rate:.1%})")

        return report

    def _load_csv(self, csv_path: str, encoding: str) -> List[Dict[str, Any]]:
        """
        加载CSV文件并转换为对话格式

        Args:
            csv_path: CSV文件路径
            encoding: 文件编码

        Returns:
            对话数据列表
        """
        dialogues = defaultdict(lambda: {"department": "", "dialogue_id": "", "turns": []})

        with open(csv_path, "r", encoding=encoding, errors="ignore") as f:
            reader = csv.DictReader(f)

            for row in reader:
                department = row.get("department", "")
                dialogue_id = row.get("dialogue_id", "")
                role = row.get("role", "")
                content = row.get("content", "")

                if not dialogue_id:
                    continue

                dialogues[dialogue_id]["department"] = department
                dialogues[dialogue_id]["dialogue_id"] = dialogue_id
                dialogues[dialogue_id]["turns"].append({
                    "role": role,
                    "content": content
                })

        return list(dialogues.values())

    def generate_summary(self, report: ValidationReport) -> str:
        """
        生成验证摘要

        Args:
            report: 验证报告

        Returns:
            摘要字符串
        """
        summary = []
        summary.append("=" * 60)
        summary.append("原始数据验证报告")
        summary.append("=" * 60)
        summary.append(f"总对话数: {report.total_dialogues}")
        summary.append(f"通过: {report.passed_dialogues} ({report.pass_rate:.1%})")
        summary.append(f"失败: {report.failed_dialogues}")

        if report.department_distribution:
            summary.append("")
            summary.append("科室分布:")
            for dept, count in sorted(report.department_distribution.items(), key=lambda x: -x[1]):
                summary.append(f"  - {dept}: {count}")

        if report.failure_reasons:
            summary.append("")
            summary.append("主要失败原因:")
            for reason, count in report.failure_reasons.most_common(5):
                summary.append(f"  - {reason}: {count}")

        if report.warning_distribution:
            summary.append("")
            summary.append("主要警告:")
            for warning, count in report.warning_distribution.most_common(5):
                summary.append(f"  - {warning}: {count}")

        summary.append("")
        summary.append("=" * 60)

        return "\n".join(summary)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="原始数据验证器 - 验证医患对话数据是否适合转换"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="输入文件路径（CSV或JSON格式）"
    )
    parser.add_argument(
        "--output",
        help="输出报告文件路径（JSON格式）"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="输入文件格式（默认自动检测）"
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="文件编码（默认: utf-8）"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式（warnings也会导致验证失败）"
    )
    parser.add_argument(
        "--min-patient-length",
        type=int,
        default=5,
        help="患者主诉最小长度（默认: 5）"
    )
    parser.add_argument(
        "--min-doctor-length",
        type=int,
        default=10,
        help="医生回答最小长度（默认: 10）"
    )
    parser.add_argument(
        "--min-turns",
        type=int,
        default=2,
        help="最少对话轮数（默认: 2）"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 检测文件格式
    file_path = Path(args.input)
    if args.format == "auto":
        file_format = file_path.suffix.lstrip(".")
    else:
        file_format = args.format

    # 创建验证器配置
    config = {
        "min_patient_length": args.min_patient_length,
        "min_doctor_length": args.min_doctor_length,
        "min_total_turns": args.min_turns,
        "strict_mode": args.strict
    }

    # 创建验证器
    validator = RawDataValidator(config)

    # 验证文件
    if file_format == "csv":
        report = validator.validate_csv_file(args.input, args.encoding)
    elif file_format == "json":
        report = validator.validate_json_file(args.input, args.encoding)
    else:
        print(f"❌ 不支持的文件格式: {file_format}")
        return 1

    # 打印摘要
    print(validator.generate_summary(report))

    # 保存详细报告
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"✅ 详细报告已保存到: {args.output}")

    # 返回状态码
    return 0 if report.failed_dialogues == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
