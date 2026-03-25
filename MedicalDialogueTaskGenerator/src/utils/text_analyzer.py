"""
文本分析工具
Medical Dialogue Task Generator - Text Analyzer

This module provides text analysis utilities for processing medical dialogues.
"""

import re
from typing import List, Dict, Tuple, Optional


class TextAnalyzer:
    """文本分析器"""

    # 医学术语关键词
    MEDICAL_KEYWORDS = {
        "symptoms": ["痛", "晕", "咳", "喘", "发热", "腹泻", "便秘", "失眠", "乏力"],
        "body_parts": ["头", "胸", "腹", "背", "腰", "腿", "手", "脚", "心", "肺", "胃"],
        "medications": ["药", "丸", "片", "胶囊", "注射液", "阿司匹林", "胰岛素"],
        "diseases": ["高血压", "糖尿病", "心脏病", "感冒", "发烧", "炎症"],
        "time_expressions": ["今天", "明天", "昨天", "最近", "一直", "经常", "偶尔"]
    }

    # 情绪关键词
    EMOTION_KEYWORDS = {
        "anxious": ["担心", "焦虑", "不安", "紧张", "害怕"],
        "fearful": ["恐惧", "可怕", "害怕", "恐慌"],
        "angry": ["生气", "愤怒", "恼火", "不满"],
        "sad": ["难过", "伤心", "痛苦", "悲伤"],
        "hopeful": ["希望", "期待", "相信"],
        "calm": ["平静", "安心", "放心"]
    }

    # 严重程度关键词
    SEVERITY_KEYWORDS = {
        "mild": ["轻微", "有点", "一点", "稍微"],
        "moderate": ["比较", "相当", "蛮"],
        "severe": ["严重", "剧烈", "非常", "特别", "极其"]
    }

    def __init__(self):
        """初始化文本分析器"""
        # 编译正则表达式模式
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 医学术语模式
        self.medical_patterns = {}
        for category, keywords in self.MEDICAL_KEYWORDS.items():
            pattern = '|'.join(keywords)
            self.medical_patterns[category] = re.compile(pattern)

        # 情绪模式
        self.emotion_patterns = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            pattern = '|'.join(keywords)
            self.emotion_patterns[emotion] = re.compile(pattern)

    def analyze_text(self, text: str) -> Dict:
        """分析文本

        Args:
            text: 要分析的文本

        Returns:
            分析结果字典
        """
        return {
            "length": len(text),
            "medical_terms": self.extract_medical_terms(text),
            "emotions": self.detect_emotions(text),
            "severity": self.detect_severity(text),
            "questions": self.count_questions(text)
        }

    def extract_medical_terms(self, text: str) -> Dict[str, List[str]]:
        """提取医学术语

        Args:
            text: 要分析的文本

        Returns:
            医学术语字典，按类别分组
        """
        results = {}

        for category, pattern in self.medical_patterns.items():
            matches = pattern.findall(text)
            if matches:
                results[category] = list(set(matches))  # 去重

        return results

    def detect_emotions(self, text: str) -> Dict[str, int]:
        """检测情绪

        Args:
            text: 要分析的文本

        Returns:
            情绪计数字典
        """
        results = {}

        for emotion, pattern in self.emotion_patterns.items():
            matches = pattern.findall(text)
            if matches:
                results[emotion] = len(matches)

        return results

    def detect_severity(self, text: str) -> Optional[str]:
        """检测严重程度

        Args:
            text: 要分析的文本

        Returns:
            严重程度 (mild/moderate/severe) 或 None
        """
        severity_counts = {}

        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    severity_counts[severity] = severity_counts.get(severity, 0) + text.count(keyword)

        if not severity_counts:
            return None

        # 返回出现次数最多的严重程度
        return max(severity_counts.items(), key=lambda x: x[1])[0]

    def count_questions(self, text: str) -> int:
        """统计问题数量

        Args:
            text: 要分析的文本

        Returns:
            问题数量
        """
        # 统计中英文问号
        count = text.count('？') + text.count('?')
        return count

    def extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """提取关键短语

        Args:
            text: 要分析的文本
            top_n: 返回前N个关键短语

        Returns:
            关键短语列表
        """
        # 简单实现：提取医学术语和疾病名称
        phrases = []

        # 添加疾病名称
        diseases = self.MEDICAL_KEYWORDS.get("diseases", [])
        for disease in diseases:
            if disease in text:
                phrases.append(disease)

        # 添加症状
        symptoms = self.MEDICAL_KEYWORDS.get("symptoms", [])
        for symptom in symptoms:
            if symptom in text:
                phrases.append(symptom)

        # 添加药物
        medications = self.MEDICAL_KEYWORDS.get("medications", [])
        for medication in medications:
            if medication in text:
                phrases.append(medication)

        return phrases[:top_n]

    def split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子

        Args:
            text: 要分割的文本

        Returns:
            句子列表
        """
        # 简单实现：按句号、问号、感叹号分割
        sentences = re.split(r'[。？！?!]', text)
        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def calculate_complexity_score(self, text: str) -> float:
        """计算文本复杂度分数

        Args:
            text: 要分析的文本

        Returns:
            复杂度分数 (0-1)
        """
        score = 0.0

        # 长度因子 (0-0.3)
        length = len(text)
        if length > 0:
            length_score = min(length / 200, 1.0) * 0.3
            score += length_score

        # 问题数量因子 (0-0.2)
        question_count = self.count_questions(text)
        question_score = min(question_count / 5, 1.0) * 0.2
        score += question_score

        # 医学术语因子 (0-0.3)
        medical_terms = self.extract_medical_terms(text)
        term_count = sum(len(terms) for terms in medical_terms.values())
        term_score = min(term_count / 10, 1.0) * 0.3
        score += term_score

        # 情绪因子 (0-0.2)
        emotions = self.detect_emotions(text)
        emotion_score = min(len(emotions) / 3, 1.0) * 0.2
        score += emotion_score

        return min(score, 1.0)

    def find_contradictions(self, statements: List[str]) -> List[Tuple[int, int, str]]:
        """查找矛盾陈述

        Args:
            statements: 陈述列表

        Returns:
            矛盾列表 [(index1, index2, contradiction_type), ...]
        """
        contradictions = []
        n = len(statements)

        # 简单实现：检查相互矛盾的陈述
        for i in range(n):
            for j in range(i + 1, n):
                stmt1 = statements[i]
                stmt2 = statements[j]

                # 检查"是"和"不是"的矛盾
                if ("是" in stmt1 or "有" in stmt1) and ("不是" in stmt2 or "没有" in stmt2):
                    # 进一步检查是否涉及同一主体
                    if self._has_same_subject(stmt1, stmt2):
                        contradictions.append((i, j, "statement_contradiction"))

                # 检查时间矛盾
                time_exprs1 = self._extract_time_expressions(stmt1)
                time_exprs2 = self._extract_time_expressions(stmt2)
                if time_exprs1 and time_exprs2:
                    if self._are_contradictory_times(time_exprs1, time_exprs2):
                        contradictions.append((i, j, "timeline_inconsistency"))

        return contradictions

    def _has_same_subject(self, stmt1: str, stmt2: str) -> bool:
        """检查两个陈述是否有相同主体"""
        # 简化实现：检查是否有共同的名词
        # 实际应用中可以使用更复杂的NLP方法
        nouns1 = set(re.findall(r'[\u4e00-\u9fff]+', stmt1))
        nouns2 = set(re.findall(r'[\u4e00-\u9fff]+', stmt2))
        return len(nouns1 & nouns2) > 0

    def _extract_time_expressions(self, stmt: str) -> List[str]:
        """提取时间表达式"""
        time_exprs = []
        time_keywords = ["今天", "昨天", "明天", "最近", "一直", "经常", "偶尔", "每天", "从来"]
        for keyword in time_keywords:
            if keyword in stmt:
                time_exprs.append(keyword)
        return time_exprs

    def _are_contradictory_times(self, times1: List[str], times2: List[str]) -> bool:
        """判断两个时间列表是否矛盾"""
        # 简化实现：检查"一直"和"偶尔"等矛盾
        contradictory_pairs = [("一直", "偶尔"), ("每天", "偶尔"), ("从来", "偶尔")]
        for t1 in times1:
            for t2 in times2:
                if (t1, t2) in contradictory_pairs or (t2, t1) in contradictory_pairs:
                    return True
        return False
