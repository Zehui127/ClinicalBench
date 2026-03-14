#!/usr/bin/env python3
"""
Medical Consultation Dialogue Dataset Validator

This module validates whether a dataset conforms to medical consultation
multi-turn dialogue standards for tau2-bench format.

Author: Claude Sonnet 4.5
Date: 2025-03-14
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "ERROR"      # Critical issues that prevent dataset usage
    WARNING = "WARNING"  # Issues that should be addressed but don't block usage
    INFO = "INFO"        # Informational messages


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the dataset."""
    level: ValidationLevel
    category: str  # e.g., "structure", "content", "medical", "multi_turn"
    message: str
    task_id: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format the issue for display."""
        prefix = f"[{self.level.value}]"
        task_info = f" (Task: {self.task_id})" if self.task_id else ""
        suggestion = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"{prefix} {self.category}: {self.message}{task_info}{suggestion}"


@dataclass
class ValidationResult:
    """Results of dataset validation."""
    is_valid: bool
    total_tasks: int
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.INFO]

    def print_report(self, verbose: bool = True) -> None:
        """Print a formatted validation report."""
        print("\n" + "=" * 80)
        print("  MEDICAL CONSULTATION DIALOGUE DATASET VALIDATION REPORT")
        print("=" * 80)

        # Overall status
        status = "[VALID]" if self.is_valid else "[INVALID]"
        print(f"\nOverall Status: {status}")
        print(f"Total Tasks: {self.total_tasks}")
        print(f"Issues Found: {len(self.issues)}")
        print(f"  - Errors: {len(self.errors)}")
        print(f"  - Warnings: {len(self.warnings)}")
        print(f"  - Info: {len(self.infos)}")

        # Statistics
        if self.stats:
            print("\n" + "-" * 80)
            print("  DATASET STATISTICS")
            print("-" * 80)
            for key, value in self.stats.items():
                print(f"  {key}: {value}")

        # Issues by level
        if self.issues and verbose:
            for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
                level_issues = [i for i in self.issues if i.level == level]
                if level_issues:
                    print(f"\n{level.value}s ({len(level_issues)}):")
                    for issue in level_issues[:20]:  # Limit to 20 per level
                        print(f"  {issue}")
                    if len(level_issues) > 20:
                        print(f"  ... and {len(level_issues) - 20} more {level.value.lower()}s")

        print("\n" + "=" * 80 + "\n")


class MedicalDialogueValidator:
    """Validates medical consultation dialogue datasets."""

    # Medical domain keywords (English + Chinese)
    MEDICAL_KEYWORDS = [
        # ============================================================
        # ENGLISH KEYWORDS
        # ============================================================
        # Common symptoms
        "pain", "fever", "headache", "nausea", "vomiting", "cough",
        "dizziness", "fatigue", "insomnia", "diarrhea", "constipation",
        "chest pain", "shortness of breath", "palpitation", "swelling", "numbness",
        "itching", "rash", "weakness", "sore throat", "runny nose",
        "sneezing", "chills", "sweating", "appetite", "thirst",

        # Medical professionals and terms
        "doctor", "physician", "patient", "symptom", "diagnosis",
        "treatment", "medication", "prescription", "therapy", "surgery",
        "blood pressure", "heart rate", "temperature", "examination", "test",
        "medical", "clinical", "health", "disease", "condition", "illness",

        # Body systems
        "cardiovascular", "respiratory", "digestive", "nervous", "endocrine",
        "immune", "skeletal", "muscular", "urinary", "reproductive",

        # Common conditions
        "hypertension", "diabetes", "cold", "flu", "infection", "inflammation",
        "allergy", "tumor", "cancer", "virus", "bacteria", "chronic", "acute",

        # Medical settings
        "hospital", "clinic", "emergency", "icu", "ward", "pharmacy",
        "laboratory", "radiology", "outpatient", "inpatient", "admission",

        # Medications and treatments
        "antibiotic", "painkiller", "analgesic", "anti-inflammatory", "antihistamine",
        "vaccine", "injection", "infusion", "dosage", "side effect",

        # Diagnostic tests
        "x-ray", "ct scan", "mri", "ultrasound", "ecg", "eeg",
        "blood test", "urine test", "biopsy", "endoscopy",

        # ============================================================
        # CHINESE KEYWORDS - 中文关键词
        # ============================================================

        # ---------- 症状 Symptoms ----------
        # General symptoms - 一般症状
        "疼痛", "疼", "痛", "难受", "不舒服",
        "发烧", "发热", "体温高", "热度",
        "头痛", "头疼", "头晕", "头昏", "眩晕",
        "恶心", "呕吐", "反胃", "想吐",
        "咳嗽", "咳", "咳痰", "干咳",
        "乏力", "疲劳", "累", "没劲", "虚弱",
        "失眠", "睡不着", "睡眠差", "多梦",
        "腹泻", "拉肚子", "肚泻", "稀便",
        "便秘", "大便干", "排便困难", "解不出大便",

        # Respiratory symptoms - 呼吸系统症状
        "胸闷", "胸痛", "心痛", "心口痛",
        "气短", "气促", "呼吸困难", "喘气",
        "心悸", "心慌", "心跳快", "心跳不齐",
        "喘息", "哮喘", "气喘",
        "咳血", "吐血", "痰中带血",

        # Skin symptoms - 皮肤症状
        "水肿", "肿胀", "浮肿",
        "麻木", "发麻", "木",
        "瘙痒", "痒", "抓痒",
        "皮疹", "疹子", "红斑", "红点",
        "起泡", "水泡", "疱疹",

        # Digestive symptoms - 消化系统症状
        "胃痛", "肚子痛", "腹痛", "腹胀", "胃胀",
        "反酸", "烧心", "胃酸", "胃灼热",
        "食欲不振", "没胃口", "不想吃", "厌食",
        "口干", "口苦", "口臭",
        "吞咽困难", "咽不下去", "噎住",
        "便血", "黑便", "大便带血",
        "黄疸", "皮肤黄", "眼黄",

        # Urinary symptoms - 泌尿系统症状
        "尿频", "尿急", "尿痛", "排尿困难",
        "血尿", "尿中有血", "尿色红",
        "尿失禁", "憋不住尿", "漏尿",
        "少尿", "尿少", "无尿",
        "多尿", "尿多", "夜尿多",

        # Neurological symptoms - 神经系统症状
        "抽搐", "痉挛", "抽筋",
        "震颤", "颤抖", "手抖",
        "瘫痪", "半身不遂", "偏瘫",
        "意识不清", "昏迷", "晕厥", "晕倒",
        "失忆", "健忘", "记忆力下降",
        "麻木感", "针刺感", "烧灼感",

        # Other symptoms - 其他症状
        "体重下降", "消瘦", "体重减轻",
        "体重增加", "肥胖", "发胖",
        "多汗", "出虚汗", "盗汗",
        "怕冷", "畏寒", "手脚冰凉",
        "潮热", "烘热", "阵发性潮热",
        "脱发", "掉头发", "秃顶",
        "耳鸣", "耳朵响", "耳聋",
        "视力模糊", "看不清", "视力下降",
        "红眼", "眼红", "眼睛红",
        "流鼻涕", "鼻塞", "鼻出血",
        "喉咙痛", "嗓子痛", "咽痛",
        "声音嘶哑", "嗓子哑", "失声",

        # ---------- 医学名词 Medical Terms ----------
        # Medical roles - 医学角色
        "医生", "大夫", "医师", "专家", "主任",
        "护士", "护师", "护理员",
        "患者", "病人", "病号", "病患",
        "主治", "主治医师", "主治医生",

        # Medical concepts - 医学概念
        "症状", "病症", "病状", "表现",
        "诊断", "确诊", "误诊", "鉴别诊断",
        "治疗", "疗法", "诊治", "救治",
        "药物", "药品", "医药", "药剂",
        "处方", "药方", "开药", "取药",
        "手术", "动手术", "开刀", "手术台",
        "血压", "高压", "低压", "收缩压", "舒张压",
        "心率", "脉搏", "心跳", "心律",
        "体温", "温度", "发烧度数",
        "检查", "检验", "体检", "复查", "检查结果",
        "化验", "化验单", "化验结果", "验血",
        "医学", "医务", "医学界",
        "临床", "临床上", "临床表现",
        "健康", "身体状况", "体质", "健康状况",
        "疾病", "病", "病症", "病情", "病程",
        "病因", "病因学", "发病原因",
        "病机", "发病机制", "病理",
        "预后", "预后情况", "转归",
        "并发症", "合并症", "后遗症",

        # Medication terms - 药物相关
        "药", "药品", "药物", "药剂", "药材",
        "西药", "中药", "成药", "处方药", "非处方药",
        "抗生素", "消炎药", "止痛药", "退烧药",
        "降血压药", "降糖药", "胰岛素",
        "剂量", "用量", "用法", "服用方法",
        "副作用", "不良反应", "过敏反应",
        "耐药性", "抗药性", "依赖性",
        "注射", "打针", "输液", "吊瓶", "静脉滴注",
        "口服", "外用", "外敷", "含服",

        # Examination and tests - 检查和化验
        "CT", "核磁共振", "MRI", "B超", "彩超", "X光", "X线",
        "心电图", "脑电图", "肺功能", "胃镜", "肠镜", "支气管镜",
        "血常规", "尿常规", "便常规", "肝功能", "肾功能",
        "血糖", "血脂", "胆固醇", "甘油三酯",
        "肿瘤标志物", "癌症筛查", "病理检查", "活检",
        "CT扫描", "磁共振", "超声检查", "影像学",
        "拍片", "透视", "造影", "增强CT",

        # ---------- 科室 Departments ----------
        "内科", "外科", "妇产科", "妇科", "产科",
        "儿科", "新生儿科", "小儿科",
        "肿瘤科", "癌症中心", "放疗科", "化疗科",
        "神经科", "神经内科", "神经外科",
        "心脏科", "心内科", "心外科", "心血管科",
        "消化科", "消化内科", "胃肠科",
        "内分泌科", "代谢科",
        "肾病科", "肾内科", "泌尿科", "泌尿外科",
        "男科", "泌尿男科",
        "骨科", "创伤骨科", "关节外科", "脊柱外科",
        "眼科", "耳鼻喉科", "耳鼻喉", "五官科",
        "口腔科", "牙科", "牙科",
        "皮肤科", "性病科", "性传播疾病科",
        "精神科", "心理科", "精神卫生科",
        "传染科", "感染科", "感染性疾病科",
        "急诊科", "急救中心", "ICU", "重症监护室",
        "麻醉科", "疼痛科", "康复科", "理疗科",
        "中医科", "针灸科", "推拿科", "按摩科",
        "体检中心", "预防保健科", "保健科",

        # ---------- 常见疾病 Common Diseases ----------
        # Cardiovascular - 心血管疾病
        "高血压", "高血压病", "原发性高血压", "继发性高血压",
        "冠心病", "心肌梗死", "心梗", "心绞痛", "心力衰竭", "心衰",
        "心律失常", "心动过速", "心动过缓", "早搏",
        "心肌炎", "心肌病", "心包炎",
        "动脉硬化", "动脉粥样硬化", "血管硬化",

        # Endocrine - 内分泌疾病
        "糖尿病", "1型糖尿病", "2型糖尿病", "妊娠糖尿病",
        "甲亢", "甲状腺功能亢进", "甲减", "甲状腺功能减退",
        "甲状腺结节", "甲状腺肿",
        "肥胖症", "代谢综合征",
        "高血脂", "高胆固醇", "高甘油三酯",

        # Respiratory - 呼吸系统疾病
        "感冒", "上呼吸道感染", "上感",
        "流感", "流行性感冒",
        "支气管炎", "急性支气管炎", "慢性支气管炎",
        "肺炎", "大叶性肺炎", "支气管肺炎",
        "哮喘", "支气管哮喘",
        "慢阻肺", "慢性阻塞性肺疾病", "COPD",
        "肺结核", "结核病", "肺痨",
        "肺气肿", "肺心病", "肺源性心脏病",

        # Digestive - 消化系统疾病
        "胃炎", "急性胃炎", "慢性胃炎", "浅表性胃炎",
        "胃溃疡", "十二指肠溃疡", "消化性溃疡",
        "胃食管反流", "反流性食管炎", "GERD",
        "肝炎", "乙肝", "丙肝", "甲肝", "肝硬化",
        "脂肪肝", "酒精性肝病",
        "胆囊炎", "胆结石", "胆管结石",
        "胰腺炎", "急性胰腺炎", "慢性胰腺炎",
        "结肠炎", "肠炎", "急性肠炎", "慢性肠炎",
        "痢疾", "腹泻病",

        # Neurological - 神经系统疾病
        "中风", "脑卒中", "脑梗死", "脑出血", "脑溢血",
        "癫痫", "羊癫疯", "癫痫病",
        "帕金森", "帕金森病", "震颤麻痹",
        "老年痴呆", "阿尔茨海默病", "痴呆症",
        "偏头痛", "紧张性头痛", "丛集性头痛",
        "面瘫", "面神经麻痹", "贝尔麻痹",
        "三叉神经痛", "坐骨神经痛",

        # Urinary - 泌尿系统疾病
        "肾炎", "肾小球肾炎", "肾病综合征",
        "肾衰竭", "肾衰", "尿毒症", "肾功能障碍",
        "肾结石", "输尿管结石", "膀胱结石", "尿路结石",
        "前列腺炎", "前列腺增生", "前列腺肥大",
        "尿路感染", "膀胱炎", "尿道炎", "肾盂肾炎",
        "性病", "性传播疾病", "艾滋病", "梅毒", "淋病",

        # Gynecological - 妇科疾病
        "月经不调", "痛经", "闭经", "月经量多", "月经量少",
        "子宫肌瘤", "子宫肌腺症",
        "卵巢囊肿", "多囊卵巢综合征", "PCOS",
        "宫颈炎", "宫颈糜烂", "宫颈息肉",
        "阴道炎", "霉菌性阴道炎", "细菌性阴道炎",
        "盆腔炎", "附件炎", "盆腔积液",
        "乳腺增生", "乳腺结节", "乳腺癌",

        # Pediatric - 儿科疾病
        "手足口病", "水痘", "麻疹", "风疹", "幼儿急疹",
        "百日咳", "猩红热", "流脑", "乙脑",
        "佝偻病", "缺钙", "营养不良",
        "小儿肺炎", "小儿腹泻", "小儿惊厥",

        # Orthopedic - 骨科疾病
        "骨折", "骨裂", "粉碎性骨折",
        "关节炎", "风湿性关节炎", "类风湿性关节炎", "骨关节炎",
        "颈椎病", "腰椎间盘突出", "腰突",
        "骨质疏松", "骨质增生", "骨刺",
        "韧带损伤", "肌肉拉伤", "软组织损伤",
        "腱鞘炎", "滑膜炎", "半月板损伤",

        # Dermatological - 皮肤科疾病
        "湿疹", "皮炎", "神经性皮炎", "接触性皮炎",
        "荨麻疹", "风疹块", "过敏性皮肤病",
        "银屑病", "牛皮癣",
        "痤疮", "青春痘", "粉刺",
        "带状疱疹", "蛇盘疮", "缠腰龙",
        "脚气", "足癣", "手癣", "体癣", "股癣",
        "白癜风", "白癜风病",
        "黄褐斑", "雀斑", "老年斑",

        # Ophthalmological - 眼科疾病
        "近视", "远视", "散光", "老花", "老花眼",
        "白内障", "青光眼",
        "结膜炎", "红眼病", "沙眼",
        "角膜炎", "角膜溃疡",
        "视网膜病变", "糖尿病视网膜病变",
        "干眼症", "眼干燥症",

        # Ear, Nose, Throat - 耳鼻喉疾病
        "中耳炎", "外耳道炎", "耳鸣", "耳聋", "听力下降",
        "鼻炎", "过敏性鼻炎", "鼻窦炎", "鼻息肉",
        "鼻中隔偏曲", "鼻出血", "流鼻血",
        "咽炎", "喉炎", "扁桃体炎", "扁桃体肥大",
        "腺样体肥大", "打呼噜", "睡眠呼吸暂停",
        "声带息肉", "声带小结", "失声",

        # Oncological - 肿瘤疾病
        "肿瘤", "良性肿瘤", "恶性肿瘤",
        "癌症", "癌", "肉瘤",
        "肺癌", "胃癌", "肝癌", "肠癌", "结肠癌", "直肠癌",
        "乳腺癌", "宫颈癌", "卵巢癌", "子宫内膜癌",
        "前列腺癌", "膀胱癌", "肾癌",
        "食管癌", "胰腺癌", "胆囊癌",
        "鼻咽癌", "喉癌", "甲状腺癌",
        "白血病", "血癌", "淋巴瘤", "骨髓瘤",
        "脑瘤", "胶质瘤", "脑膜瘤",

        # Others - 其他疾病
        "贫血", "缺铁性贫血", "再生障碍性贫血",
        "白血病", "血友病", "血小板减少",
        "过敏性疾病", "过敏性休克", "花粉症",
        "自身免疫病", "红斑狼疮", "类风湿",
        "抑郁症", "焦虑症", "强迫症", "神经官能症",
        "精神分裂症", "双相情感障碍", "躁郁症",

        # ---------- 中医术语 Traditional Chinese Medicine ----------
        "中医", "中药", "中药材", "中成药",
        "辨证论治", "辨证", "论治",
        "望闻问切", "望诊", "闻诊", "问诊", "切诊",
        "脉诊", "把脉", "号脉",
        "舌苔", "脉象", "脉弦", "脉细", "脉滑", "脉数",
        "气虚", "血虚", "阴虚", "阳虚",
        "气滞", "血瘀", "痰湿", "湿热",
        "风寒", "风热", "暑湿", "燥邪",
        "经络", "穴位", "针灸", "艾灸",
        "推拿", "按摩", "拔罐", "刮痧",
        "汤药", "煎药", "服中药",
        "补气", "补血", "滋阴", "壮阳",
        "清热解毒", "活血化瘀", "祛湿化痰",
        "理气", "止痛", "止血", "消炎",

        # ---------- Medical Settings 医疗场景 ----------
        "医院", "诊所", "卫生院", "社区卫生服务中心",
        "门诊", "急诊", "住院", "入院", "出院",
        "病房", "病床", "床位",
        "手术室", "手术台",
        "挂号", "预约", "排队", "候诊",
        "就诊", "看病", "问诊", "诊疗",
        "处方单", "病历", "病史", "既往史",
        "医嘱", "遵医嘱",
        "医保", "医保卡", "新农合",
        "体检", "体检中心", "健康体检",
        "疫苗", "打疫苗", "预防接种",
        "药房", "取药", "买药",

        # ---------- Body Parts 身体部位 ----------
        # Head - 头部
        "头", "头部", "额头", "太阳穴",
        "眼睛", "眼", "耳朵", "耳", "鼻子", "鼻",
        "嘴巴", "口", "嘴唇", "牙", "牙齿", "舌头", "咽喉", "嗓子",
        "脖子", "颈", "颈部",

        # Trunk - 躯干
        "肩", "肩膀", "背", "背部", "腰", "腰部", "腰子",
        "胸", "胸部", "乳房", "肚子", "腹部", "腹",
        "肚脐", "臀部", "屁股", "肛门",

        # Limbs - 四肢
        "手臂", "胳膊", "肘", "手", "手腕", "手指",
        "腿", "大腿", "膝盖", "小腿",
        "脚", "脚腕", "脚踝", "脚掌", "脚趾",
        "关节", "骨骼", "骨头", "肌肉", "筋",
        "皮肤", "毛发", "指甲", "趾甲",

        # Internal organs - 内脏器官
        "心", "心脏", "肺", "肝脏", "肝", "胆囊", "胆",
        "脾", "脾脏", "胃", "肠道", "肠",
        "肾", "肾脏", "膀胱", "尿道",
        "子宫", "卵巢", "输卵管", "阴道",
        "前列腺", "睾丸", "附睾",
        "脑", "大脑", "小脑", "脑干", "脊髓",
        "神经", "血管", "动脉", "静脉", "毛细血管",
        "淋巴", "淋巴结", "甲状腺", "胰腺"
    ]

    # Consultation patterns (English + Chinese)
    CONSULTATION_PATTERNS = [
        # English patterns
        r"(what|how|should|can|could|i|i'm|i have|my)",
        r"(help|advice|concern|worried)",
        r"(diagnosis|treatment|prescribe|recommend)",
        # Chinese patterns
        r"(怎么|如何|应该|可以|能否|我|我的)",
        r"(帮助|建议|担心|咨询|请问)",
        r"(诊断|治疗|开药|推荐)"
    ]

    # Multi-turn indicators (English + Chinese)
    MULTI_TURN_INDICATORS = [
        # English indicators
        "follow-up", "follow up", "additional", "more information",
        "clarification", "also", "another question", "further",
        # Chinese indicators
        "随访", "复查", "补充", "更多信息",
        "澄清", "还有", "另外", "进一步", "另外想问"
    ]

    # Dialogue markers (English + Chinese)
    DIALOGUE_MARKERS = [
        # English markers
        "patient:", "doctor:", "physician:", "assistant:", "user:", "clinician:",
        # Chinese markers
        "患者:", "医生:", "医师:", "助理:", "用户:", "临床医生:"
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.

        Args:
            strict_mode: If True, treats warnings as errors
        """
        self.strict_mode = strict_mode
        self.stats = defaultdict(int)

    def validate_dataset(self, data_path: Path) -> ValidationResult:
        """
        Validate a medical consultation dialogue dataset.

        Args:
            data_path: Path to the dataset JSON file

        Returns:
            ValidationResult with all issues and statistics
        """
        issues = []

        # Load dataset
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                total_tasks=0,
                issues=[ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="file",
                    message=f"File not found: {data_path}",
                    suggestion="Check the file path"
                )],
                stats={}
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                total_tasks=0,
                issues=[ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="format",
                    message=f"Invalid JSON format: {e}",
                    suggestion="Validate JSON syntax"
                )],
                stats={}
            )

        # Check if it's a list
        if not isinstance(tasks, list):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message=f"Root element must be a list, got {type(tasks).__name__}",
                suggestion="Wrap tasks in a JSON array"
            ))
            return ValidationResult(is_valid=False, total_tasks=0, issues=issues)

        # Validate each task
        for idx, task in enumerate(tasks):
            task_issues = self.validate_task(task, idx)
            issues.extend(task_issues)

        # Calculate statistics
        stats = self._calculate_statistics(tasks, issues)

        # Determine overall validity
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        is_valid = len(errors) == 0

        if self.strict_mode:
            warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
            is_valid = is_valid and len(warnings) == 0

        return ValidationResult(
            is_valid=is_valid,
            total_tasks=len(tasks),
            issues=issues,
            stats=stats
        )

    def validate_task(self, task: Dict[str, Any], idx: int) -> List[ValidationIssue]:
        """Validate a single task."""
        issues = []
        task_id = task.get("id", f"task_{idx}")

        # 1. Check required fields
        required_fields = ["id", "description", "user_scenario", "ticket", "evaluation_criteria"]
        for field in required_fields:
            if field not in task:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message=f"Missing required field: '{field}'",
                    task_id=task_id,
                    suggestion=f"Add '{field}' field to the task"
                ))

        # 2. Validate ticket content
        ticket = task.get("ticket", "")
        if ticket:
            self._validate_ticket_content(ticket, task_id, issues)

        # 3. Check for multi-turn structure
        self._validate_multi_turn_structure(task, task_id, issues)

        # 4. Validate medical content
        self._validate_medical_content(task, task_id, issues)

        # 5. Validate evaluation criteria
        self._validate_evaluation_criteria(task, task_id, issues)

        # 6. Check user_scenario
        user_scenario = task.get("user_scenario", {})
        if isinstance(user_scenario, dict):
            instructions = user_scenario.get("instructions", {})
            if not instructions.get("domain"):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="content",
                    message="Missing 'domain' in user_scenario.instructions",
                    task_id=task_id,
                    suggestion="Specify the medical domain (e.g., 'cardiology', 'neurology')"
                ))

        return issues

    def _validate_ticket_content(self, ticket: str, task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate that the ticket represents a medical consultation."""
        if not isinstance(ticket, str):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="content",
                message=f"'ticket' must be a string, got {type(ticket).__name__}",
                task_id=task_id,
                suggestion="Ensure ticket is a string"
            ))
            return

        # Check minimum length
        if len(ticket.strip()) < 10:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="content",
                message="Ticket content is too short (< 10 characters)",
                task_id=task_id,
                suggestion="Provide a more detailed patient inquiry"
            ))

        # Check for medical keywords
        has_medical_keywords = any(
            keyword.lower() in ticket.lower()
            for keyword in self.MEDICAL_KEYWORDS
        )

        if not has_medical_keywords:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="medical",
                message="Ticket may not be medical-related (no medical keywords found)",
                task_id=task_id,
                suggestion="Ensure content describes a health-related concern"
            ))

        # Check for consultation patterns
        has_consultation_pattern = any(
            re.search(pattern, ticket, re.IGNORECASE)
            for pattern in self.CONSULTATION_PATTERNS
        )

        if not has_consultation_pattern:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="content",
                message="Ticket lacks typical consultation question patterns",
                task_id=task_id,
                suggestion="Consider framing as a patient inquiry"
            ))

    def _validate_multi_turn_structure(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate multi-turn dialogue structure."""
        user_scenario = task.get("user_scenario", {})
        if not isinstance(user_scenario, dict):
            return

        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if not task_instructions:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="multi_turn",
                message="No task_instructions found - may be single-turn dialogue",
                task_id=task_id,
                suggestion="Add task_instructions to enable multi-turn evaluation"
            ))
            return

        # Check for dialogue pattern
        has_dialogue_structure = any(
            indicator.lower() in task_instructions.lower()
            for indicator in self.DIALOGUE_MARKERS
        )

        if has_dialogue_structure:
            # Count turns
            lines = task_instructions.split('\n')
            dialogue_lines = [
                line for line in lines
                if any(indicator in line.lower() for indicator in self.DIALOGUE_MARKERS)
            ]
            num_turns = len(dialogue_lines)

            if num_turns < 4:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="multi_turn",
                    message=f"Few dialogue turns detected ({num_turns} lines)",
                    task_id=task_id,
                    suggestion="Consider adding more turns for comprehensive multi-turn evaluation"
                ))
            else:
                self.stats["multi_turn_tasks"] += 1
        else:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="multi_turn",
                message="task_instructions doesn't contain clear dialogue structure",
                task_id=task_id,
                suggestion="Use 'Patient:', 'Doctor:', or similar markers (including Chinese: '患者:', '医生:') to structure dialogue"
            ))

    def _validate_medical_content(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate medical content quality."""
        ticket = task.get("ticket", "")
        description = task.get("description", {})

        # Check description purpose
        purpose = description.get("purpose", "") if isinstance(description, dict) else ""
        medical_terms_in_purpose = sum(
            1 for keyword in self.MEDICAL_KEYWORDS
            if keyword.lower() in purpose.lower()
        )

        if medical_terms_in_purpose < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="medical",
                message="Description purpose may lack specific medical context",
                task_id=task_id,
                suggestion="Include relevant medical terms in the description"
            ))

        # Check for safety-related content
        safety_keywords = ["emergency", "urgent", "severe", "chest pain", "difficulty breathing"]
        has_safety_concern = any(
            keyword in ticket.lower()
            for keyword in safety_keywords
        )

        if has_safety_concern:
            self.stats["safety_related_tasks"] += 1

    def _validate_evaluation_criteria(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate evaluation criteria."""
        eval_criteria = task.get("evaluation_criteria")

        if not eval_criteria:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="evaluation",
                message="Missing evaluation_criteria",
                task_id=task_id,
                suggestion="Add evaluation criteria to assess model performance"
            ))
            return

        if not isinstance(eval_criteria, dict):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message=f"evaluation_criteria must be a dict, got {type(eval_criteria).__name__}",
                task_id=task_id
            ))
            return

        # Check for actions or communication_checks
        has_actions = eval_criteria.get("actions")
        has_communication_checks = eval_criteria.get("communication_checks")

        if not has_actions and not has_communication_checks:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="evaluation",
                message="evaluation_criteria lacks 'actions' or 'communication_checks'",
                task_id=task_id,
                suggestion="Add specific actions to evaluate or communication checks"
            ))

        if has_actions and isinstance(has_actions, list):
            self.stats["total_evaluation_actions"] += len(has_actions)

    def _calculate_statistics(self, tasks: List[Dict], issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Calculate dataset statistics."""
        stats = dict(self.stats)

        # Count tasks by category
        stats["tasks_with_errors"] = len(set(i.task_id for i in issues if i.level == ValidationLevel.ERROR))
        stats["tasks_with_warnings"] = len(set(i.task_id for i in issues if i.level == ValidationLevel.WARNING))

        # Average ticket length
        ticket_lengths = [
            len(task.get("ticket", ""))
            for task in tasks
            if task.get("ticket")
        ]
        if ticket_lengths:
            stats["avg_ticket_length"] = sum(ticket_lengths) / len(ticket_lengths)
            stats["min_ticket_length"] = min(ticket_lengths)
            stats["max_ticket_length"] = max(ticket_lengths)

        # Medical domain distribution
        domains = {}
        for task in tasks:
            domain = task.get("user_scenario", {}).get("instructions", {}).get("domain", "unknown")
            domains[domain] = domains.get(domain, 0) + 1
        stats["domain_distribution"] = domains

        return stats


def main():
    """Command-line interface for the validator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate medical consultation dialogue datasets"
    )
    parser.add_argument(
        "dataset_path",
        type=str,
        help="Path to the dataset JSON file"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (warnings become errors)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors and warnings, not info"
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Save validation result to JSON file"
    )

    args = parser.parse_args()

    # Initialize validator
    validator = MedicalDialogueValidator(strict_mode=args.strict)

    # Validate dataset
    data_path = Path(args.dataset_path)
    result = validator.validate_dataset(data_path)

    # Print report
    result.print_report(verbose=not args.quiet)

    # Save JSON output if requested
    if args.json_output:
        output = {
            "is_valid": result.is_valid,
            "total_tasks": result.total_tasks,
            "errors": [
                {
                    "category": e.category,
                    "message": e.message,
                    "task_id": e.task_id,
                    "suggestion": e.suggestion
                }
                for e in result.errors
            ],
            "warnings": [
                {
                    "category": w.category,
                    "message": w.message,
                    "task_id": w.task_id,
                    "suggestion": w.suggestion
                }
                for w in result.warnings
            ],
            "stats": result.stats
        }
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Validation result saved to: {args.json_output}")

    # Exit code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
