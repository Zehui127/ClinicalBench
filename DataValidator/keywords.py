#!/usr/bin/env python3
"""
Medical Keywords for Consultation Dialogue Validation

Contains extensive bilingual (English/Chinese) medical terminology
for content validation and recognition.
"""


class MedicalKeywords:
    """Medical domain keywords (English + Chinese)."""

    # ============================================================
    # ENGLISH KEYWORDS
    # ============================================================

    # Common symptoms
    SYMPTOMS_EN = [
        "pain", "fever", "headache", "nausea", "vomiting", "cough",
        "dizziness", "fatigue", "insomnia", "diarrhea", "constipation",
        "chest pain", "shortness of breath", "palpitation", "swelling", "numbness",
        "itching", "rash", "weakness", "sore throat", "runny nose",
        "sneezing", "chills", "sweating", "appetite", "thirst",
    ]

    # Medical professionals and terms
    MEDICAL_TERMS_EN = [
        "doctor", "physician", "patient", "symptom", "diagnosis",
        "treatment", "medication", "prescription", "therapy", "surgery",
        "blood pressure", "heart rate", "temperature", "examination", "test",
        "medical", "clinical", "health", "disease", "condition", "illness",
    ]

    # Body systems
    BODY_SYSTEMS_EN = [
        "cardiovascular", "respiratory", "digestive", "nervous", "endocrine",
        "immune", "skeletal", "muscular", "urinary", "reproductive",
    ]

    # Common conditions
    CONDITIONS_EN = [
        "hypertension", "diabetes", "cold", "flu", "infection", "inflammation",
        "allergy", "tumor", "cancer", "virus", "bacteria", "chronic", "acute",
    ]

    # Medical settings
    SETTINGS_EN = [
        "hospital", "clinic", "emergency", "icu", "ward", "pharmacy",
        "laboratory", "radiology", "outpatient", "inpatient", "admission",
    ]

    # Medications and treatments
    MEDICATIONS_EN = [
        "antibiotic", "painkiller", "analgesic", "anti-inflammatory", "antihistamine",
        "vaccine", "injection", "infusion", "dosage", "side effect",
    ]

    # Diagnostic tests
    TESTS_EN = [
        "x-ray", "ct scan", "mri", "ultrasound", "ecg", "eeg",
        "blood test", "urine test", "biopsy", "endoscopy",
    ]

    # ============================================================
    # CHINESE KEYWORDS
    # ============================================================

    # ---------- Symptoms (症状) ----------
    GENERAL_SYMPTOMS_ZH = [
        "疼痛", "疼", "痛", "难受", "不舒服",
        "发烧", "发热", "体温高", "热度",
        "头痛", "头疼", "头晕", "头昏", "眩晕",
        "恶心", "呕吐", "反胃", "想吐",
        "咳嗽", "咳", "咳痰", "干咳",
        "乏力", "疲劳", "累", "没劲", "虚弱",
        "失眠", "睡不着", "睡眠差", "多梦",
        "腹泻", "拉肚子", "肚泻", "稀便",
        "便秘", "大便干", "排便困难", "解不出大便",
    ]

    RESPIRATORY_SYMPTOMS_ZH = [
        "胸闷", "胸痛", "心痛", "心口痛",
        "气短", "气促", "呼吸困难", "喘气",
        "心悸", "心慌", "心跳快", "心跳不齐",
        "喘息", "哮喘", "气喘",
        "咳血", "吐血", "痰中带血",
    ]

    SKIN_SYMPTOMS_ZH = [
        "水肿", "肿胀", "浮肿",
        "麻木", "发麻", "木",
        "瘙痒", "痒", "抓痒",
        "皮疹", "疹子", "红斑", "红点",
        "起泡", "水泡", "疱疹",
    ]

    DIGESTIVE_SYMPTOMS_ZH = [
        "胃痛", "肚子痛", "腹痛", "腹胀", "胃胀",
        "反酸", "烧心", "胃酸", "胃灼热",
        "食欲不振", "没胃口", "不想吃", "厌食",
        "口干", "口苦", "口臭",
        "吞咽困难", "咽不下去", "噎住",
        "便血", "黑便", "大便带血",
        "黄疸", "皮肤黄", "眼黄",
    ]

    URINARY_SYMPTOMS_ZH = [
        "尿频", "尿急", "尿痛", "排尿困难",
        "血尿", "尿中有血", "尿色红",
        "尿失禁", "憋不住尿", "漏尿",
        "少尿", "尿少", "无尿",
        "多尿", "尿多", "夜尿多",
    ]

    NEUROLOGICAL_SYMPTOMS_ZH = [
        "抽搐", "痉挛", "抽筋",
        "震颤", "颤抖", "手抖",
        "瘫痪", "半身不遂", "偏瘫",
        "意识不清", "昏迷", "晕厥", "晕倒",
        "失忆", "健忘", "记忆力下降",
        "麻木感", "针刺感", "烧灼感",
    ]

    OTHER_SYMPTOMS_ZH = [
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
    ]

    # ---------- Medical Terms (医学名词) ----------
    MEDICAL_ROLES_ZH = [
        "医生", "大夫", "医师", "专家", "主任",
        "护士", "护师", "护理员",
        "患者", "病人", "病号", "病患",
        "主治", "主治医师", "主治医生",
    ]

    MEDICAL_CONCEPTS_ZH = [
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
    ]

    MEDICATION_TERMS_ZH = [
        "药", "药品", "药物", "药剂", "药材",
        "西药", "中药", "成药", "处方药", "非处方药",
        "抗生素", "消炎药", "止痛药", "退烧药",
        "降血压药", "降糖药", "胰岛素",
        "剂量", "用量", "用法", "服用方法",
        "副作用", "不良反应", "过敏反应",
        "耐药性", "抗药性", "依赖性",
        "注射", "打针", "输液", "吊瓶", "静脉滴注",
        "口服", "外用", "外敷", "含服",
    ]

    EXAMINATION_TERMS_ZH = [
        "CT", "核磁共振", "MRI", "B超", "彩超", "X光", "X线",
        "心电图", "脑电图", "肺功能", "胃镜", "肠镜", "支气管镜",
        "血常规", "尿常规", "便常规", "肝功能", "肾功能",
        "血糖", "血脂", "胆固醇", "甘油三酯",
        "肿瘤标志物", "癌症筛查", "病理检查", "活检",
        "CT扫描", "磁共振", "超声检查", "影像学",
        "拍片", "透视", "造影", "增强CT",
    ]

    # ---------- Departments (科室) ----------
    DEPARTMENTS_ZH = [
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
        "口腔科", "牙科",
        "皮肤科", "性病科", "性传播疾病科",
        "精神科", "心理科", "精神卫生科",
        "传染科", "感染科", "感染性疾病科",
        "急诊科", "急救中心", "ICU", "重症监护室",
        "麻醉科", "疼痛科", "康复科", "理疗科",
        "中医科", "针灸科", "推拿科", "按摩科",
        "体检中心", "预防保健科", "保健科",
    ]

    # ---------- Common Diseases (常见疾病) ----------
    CARDIOVASCULAR_DISEASES_ZH = [
        "高血压", "高血压病", "原发性高血压", "继发性高血压",
        "冠心病", "心肌梗死", "心梗", "心绞痛", "心力衰竭", "心衰",
        "心律失常", "心动过速", "心动过缓", "早搏",
        "心肌炎", "心肌病", "心包炎",
        "动脉硬化", "动脉粥样硬化", "血管硬化",
    ]

    ENDOCRINE_DISEASES_ZH = [
        "糖尿病", "1型糖尿病", "2型糖尿病", "妊娠糖尿病",
        "甲亢", "甲状腺功能亢进", "甲减", "甲状腺功能减退",
        "甲状腺结节", "甲状腺肿",
        "肥胖症", "代谢综合征",
        "高血脂", "高胆固醇", "高甘油三酯",
    ]

    RESPIRATORY_DISEASES_ZH = [
        "感冒", "上呼吸道感染", "上感",
        "流感", "流行性感冒",
        "支气管炎", "急性支气管炎", "慢性支气管炎",
        "肺炎", "大叶性肺炎", "支气管肺炎",
        "哮喘", "支气管哮喘",
        "慢阻肺", "慢性阻塞性肺疾病", "COPD",
        "肺结核", "结核病", "肺痨",
        "肺气肿", "肺心病", "肺源性心脏病",
    ]

    DIGESTIVE_DISEASES_ZH = [
        "胃炎", "急性胃炎", "慢性胃炎", "浅表性胃炎",
        "胃溃疡", "十二指肠溃疡", "消化性溃疡",
        "胃食管反流", "反流性食管炎", "GERD",
        "肝炎", "乙肝", "丙肝", "甲肝", "肝硬化",
        "脂肪肝", "酒精性肝病",
        "胆囊炎", "胆结石", "胆管结石",
        "胰腺炎", "急性胰腺炎", "慢性胰腺炎",
        "结肠炎", "肠炎", "急性肠炎", "慢性肠炎",
        "痢疾", "腹泻病",
    ]

    NEUROLOGICAL_DISEASES_ZH = [
        "中风", "脑卒中", "脑梗死", "脑出血", "脑溢血",
        "癫痫", "羊癫疯", "癫痫病",
        "帕金森", "帕金森病", "震颤麻痹",
        "老年痴呆", "阿尔茨海默病", "痴呆症",
        "偏头痛", "紧张性头痛", "丛集性头痛",
        "面瘫", "面神经麻痹", "贝尔麻痹",
        "三叉神经痛", "坐骨神经痛",
    ]

    URINARY_DISEASES_ZH = [
        "肾炎", "肾小球肾炎", "肾病综合征",
        "肾衰竭", "肾衰", "尿毒症", "肾功能障碍",
        "肾结石", "输尿管结石", "膀胱结石", "尿路结石",
        "前列腺炎", "前列腺增生", "前列腺肥大",
        "尿路感染", "膀胱炎", "尿道炎", "肾盂肾炎",
        "性病", "性传播疾病", "艾滋病", "梅毒", "淋病",
    ]

    GYNECOLOGICAL_DISEASES_ZH = [
        "月经不调", "痛经", "闭经", "月经量多", "月经量少",
        "子宫肌瘤", "子宫肌腺症",
        "卵巢囊肿", "多囊卵巢综合征", "PCOS",
        "宫颈炎", "宫颈糜烂", "宫颈息肉",
        "阴道炎", "霉菌性阴道炎", "细菌性阴道炎",
        "盆腔炎", "附件炎", "盆腔积液",
        "乳腺增生", "乳腺结节", "乳腺癌",
    ]

    PEDIATRIC_DISEASES_ZH = [
        "手足口病", "水痘", "麻疹", "风疹", "幼儿急疹",
        "百日咳", "猩红热", "流脑", "乙脑",
        "佝偻病", "缺钙", "营养不良",
        "小儿肺炎", "小儿腹泻", "小儿惊厥",
    ]

    ORTHOPEDIC_DISEASES_ZH = [
        "骨折", "骨裂", "粉碎性骨折",
        "关节炎", "风湿性关节炎", "类风湿性关节炎", "骨关节炎",
        "颈椎病", "腰椎间盘突出", "腰突",
        "骨质疏松", "骨质增生", "骨刺",
        "韧带损伤", "肌肉拉伤", "软组织损伤",
        "腱鞘炎", "滑膜炎", "半月板损伤",
    ]

    DERMATOLOGICAL_DISEASES_ZH = [
        "湿疹", "皮炎", "神经性皮炎", "接触性皮炎",
        "荨麻疹", "风疹块", "过敏性皮肤病",
        "银屑病", "牛皮癣",
        "痤疮", "青春痘", "粉刺",
        "带状疱疹", "蛇盘疮", "缠腰龙",
        "脚气", "足癣", "手癣", "体癣", "股癣",
        "白癜风", "白癜风病",
        "黄褐斑", "雀斑", "老年斑",
    ]

    ONCOLOGICAL_DISEASES_ZH = [
        "肿瘤", "良性肿瘤", "恶性肿瘤",
        "癌症", "癌", "肉瘤",
        "肺癌", "胃癌", "肝癌", "肠癌", "结肠癌", "直肠癌",
        "乳腺癌", "宫颈癌", "卵巢癌", "子宫内膜癌",
        "前列腺癌", "膀胱癌", "肾癌",
        "食管癌", "胰腺癌", "胆囊癌",
        "鼻咽癌", "喉癌", "甲状腺癌",
        "白血病", "血癌", "淋巴瘤", "骨髓瘤",
        "脑瘤", "胶质瘤", "脑膜瘤",
    ]

    # ---------- Traditional Chinese Medicine (中医术语) ----------
    TCM_TERMS_ZH = [
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
    ]

    # ---------- Medical Settings (医疗场景) ----------
    MEDICAL_SETTINGS_ZH = [
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
    ]

    # ---------- Body Parts (身体部位) ----------
    BODY_PARTS_ZH = [
        # Head
        "头", "头部", "额头", "太阳穴",
        "眼睛", "眼", "耳朵", "耳", "鼻子", "鼻",
        "嘴巴", "口", "嘴唇", "牙", "牙齿", "舌头", "咽喉", "嗓子",
        "脖子", "颈", "颈部",

        # Trunk
        "肩", "肩膀", "背", "背部", "腰", "腰部", "腰子",
        "胸", "胸部", "乳房", "肚子", "腹部", "腹",
        "肚脐", "臀部", "屁股", "肛门",

        # Limbs
        "手臂", "胳膊", "肘", "手", "手腕", "手指",
        "腿", "大腿", "膝盖", "小腿",
        "脚", "脚腕", "脚踝", "脚掌", "脚趾",
        "关节", "骨骼", "骨头", "肌肉", "筋",
        "皮肤", "毛发", "指甲", "趾甲",

        # Internal organs
        "心", "心脏", "肺", "肝脏", "肝", "胆囊", "胆",
        "脾", "脾脏", "胃", "肠道", "肠",
        "肾", "肾脏", "膀胱", "尿道",
        "子宫", "卵巢", "输卵管", "阴道",
        "前列腺", "睾丸", "附睾",
        "脑", "大脑", "小脑", "脑干", "脊髓",
        "神经", "血管", "动脉", "静脉", "毛细血管",
        "淋巴", "淋巴结", "甲状腺", "胰腺",
    ]

    @classmethod
    def get_all_keywords(cls) -> List[str]:
        """Get all medical keywords as a flat list."""
        keywords = []

        # English keywords
        keywords.extend(cls.SYMPTOMS_EN)
        keywords.extend(cls.MEDICAL_TERMS_EN)
        keywords.extend(cls.BODY_SYSTEMS_EN)
        keywords.extend(cls.CONDITIONS_EN)
        keywords.extend(cls.SETTINGS_EN)
        keywords.extend(cls.MEDICATIONS_EN)
        keywords.extend(cls.TESTS_EN)

        # Chinese keywords
        keywords.extend(cls.GENERAL_SYMPTOMS_ZH)
        keywords.extend(cls.RESPIRATORY_SYMPTOMS_ZH)
        keywords.extend(cls.SKIN_SYMPTOMS_ZH)
        keywords.extend(cls.DIGESTIVE_SYMPTOMS_ZH)
        keywords.extend(cls.URINARY_SYMPTOMS_ZH)
        keywords.extend(cls.NEUROLOGICAL_SYMPTOMS_ZH)
        keywords.extend(cls.OTHER_SYMPTOMS_ZH)
        keywords.extend(cls.MEDICAL_ROLES_ZH)
        keywords.extend(cls.MEDICAL_CONCEPTS_ZH)
        keywords.extend(cls.MEDICATION_TERMS_ZH)
        keywords.extend(cls.EXAMINATION_TERMS_ZH)
        keywords.extend(cls.DEPARTMENTS_ZH)
        keywords.extend(cls.CARDIOVASCULAR_DISEASES_ZH)
        keywords.extend(cls.ENDOCRINE_DISEASES_ZH)
        keywords.extend(cls.RESPIRATORY_DISEASES_ZH)
        keywords.extend(cls.DIGESTIVE_DISEASES_ZH)
        keywords.extend(cls.NEUROLOGICAL_DISEASES_ZH)
        keywords.extend(cls.URINARY_DISEASES_ZH)
        keywords.extend(cls.GYNECOLOGICAL_DISEASES_ZH)
        keywords.extend(cls.PEDIATRIC_DISEASES_ZH)
        keywords.extend(cls.ORTHOPEDIC_DISEASES_ZH)
        keywords.extend(cls.DERMATOLOGICAL_DISEASES_ZH)
        keywords.extend(cls.ONCOLOGICAL_DISEASES_ZH)
        keywords.extend(cls.TCM_TERMS_ZH)
        keywords.extend(cls.MEDICAL_SETTINGS_ZH)
        keywords.extend(cls.BODY_PARTS_ZH)

        return keywords

    @classmethod
    def get_keyword_count(cls) -> int:
        """Get total number of keywords."""
        return len(cls.get_all_keywords())
