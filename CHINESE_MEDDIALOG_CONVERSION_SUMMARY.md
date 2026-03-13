# Chinese MedDialog 转换总结

## 📊 数据集信息

### 原始数据集
- **名称**: Chinese MedDialog Dataset (中文医疗对话数据集)
- **来源**: [GitHub - Toyhom/Chinese-medical-dialogue-data](https://github.com/Toyhom/Chinese-medical-dialogue-data)
- **总数据量**: 792,099 个问答对
- **时间跨度**: 2010-2020 年
- **数据来源**: 好大夫在线 (haodf.com)

### 科室分布
| 科室 | 数据量 |
|---|---|
| 内科 | 220,606 |
| 外科 | 115,991 |
| 妇产科 | 183,751 |
| 儿科 | 101,602 |
| 肿瘤科 | 75,553 |
| 男科 | 94,596 |

---

## 🔄 转换结果

### 已转换任务
- **总任务数**: 3,000 (测试集，每个科室 500 个)
- **患者数**: 2,996
- **数据格式**: tau2-bench 兼容

### 输出文件
```
data/processed/medical_dialogues/chinese_meddialog/
├── tasks.json              # 所有 3,000 个任务
├── tasks_内科.json         # 内科 500 个任务
├── tasks_外科.json         # 外科 500 个任务
├── tasks_妇产科.json       # 妇产科 500 个任务
├── tasks_儿科.json         # 儿科 500 个任务
├── tasks_肿瘤科.json       # 肿瘤科 500 个任务
├── tasks_男科.json         # 男科 500 个任务
├── db.json                 # 患者数据库
└── split_tasks.json        # 训练/验证/测试划分
```

---

## 🛠️ 转换脚本

### 脚本位置
`convert_chinese_meddialog.py`

### 功能特性
- ✅ 多编码支持 (gbk, gb18030, utf-8, utf-8-sig, latin1)
- ✅ 自动科室识别和映射
- ✅ 实体提取（年龄、性别、症状等）
- ✅ tau2-bench 格式转换
- ✅ 患者数据库生成
- ✅ 数据集划分 (train/val/test)

### 配置选项
```python
config = {
    "max_samples": 500,          # 每个科室最大样本数
    "min_dialogue_length": 10,   # 最小对话长度
    "departments": None,         # None = 处理所有科室
}
```

### 使用方法
```bash
# 转换所有数据（每个科室 500 个样本）
python convert_chinese_meddialog.py

# 修改配置以转换更多样本
# 编辑 convert_chinese_meddialog.py 中的 config 字典
```

---

## 📋 任务格式示例

```json
{
  "id": "clinical_andrology_0",
  "description": {
    "purpose": "Medical consultation - 男科有关钙片什么原因导致男...",
    "notes": "Real Chinese medical dialogue from 男科. Source: Chinese MedDialog Dataset."
  },
  "user_scenario": {
    "persona": "45-year-old male patient with ...",
    "instructions": {
      "domain": "andrology",
      "reason_for_call": "...",
      "task_instructions": "You are a patient seeking medical advice..."
    }
  },
  "ticket": "患者问题描述...",
  "initial_state": {
    "initialization_actions": [
      {
        "env_type": "user",
        "func_name": "set_user_info",
        "arguments": {
          "name": "患者姓名",
          "mrn": "MRN编号",
          "age": 45,
          "gender": "male"
        }
      }
    ]
  },
  "evaluation_criteria": {
    "actions": [...],
    "communication_checks": [...]
  }
}
```

---

## 🆚 对比：真实对话 vs 模拟对话

| 特性 | Chinese MedDialog | MedXpertQA (现有) |
|---|---|---|
| 数据类型 | ✅ 真实医患对话 | ❌ 从考试题模拟生成 |
| 数据量 | 792,099 对话 | 2,450 任务 |
| 来源 | 好大夫在线 (2010-2020) | 医疗多选题考试 |
| 对话自然度 | ⭐⭐⭐⭐⭐ 真实交互 | ⭐⭐⭐ 模拟对话 |
| 场景真实性 | ⭐⭐⭐⭐⭐ 实际问诊 | ⭐⭐⭐ 考试场景 |

---

## 📈 下一步

### 短期目标
1. ✅ 下载 Chinese MedDialog 数据集
2. ✅ 创建转换脚本
3. ✅ 转换测试集 (3,000 任务)
4. ⏳ 验证任务格式
5. ⏳ 运行评估测试

### 中期目标
1. 转换完整数据集（所有 792,099 个对话）
2. 添加更多数据集（MedDG, English MedDialog, ChatDoctor）
3. 优化实体提取和患者画像生成
4. 改进评估标准

### 长期目标
1. 建立大规模中文医学问诊基准
2. 发表相关论文
3. 开源完整的转换工具链
4. 社区贡献和反馈

---

## 🔗 相关链接

- **GitHub 仓库**: [circadiancity/agentmy](https://github.com/circadiancity/agentmy)
- **数据分支**: [feature/medical-dialogue-datasets](https://github.com/circadiancity/agentmy/tree/feature/medical-dialogue-datasets)
- **原始数据**: [Toyhom/Chinese-medical-dialogue-data](https://github.com/Toyhom/Chinese-medical-dialogue-data)
- **阿里云天池**: [MedDialog-CN 数据集](https://tianchi.aliyun.com/dataset/92110)

---

## 📝 引用

如果使用此数据集，请引用：

```bibtex
@article{chen2020meddiag,
  title={MedDialog: a large-scale medical dialogue dataset},
  author={Chen, Shu and Ju, Zeqian and Dong, Xiangyu and others},
  journal={arXiv preprint arXiv:2004.03329},
  year={2020}
}
```

---

**创建日期**: 2025-03-13
**作者**: Claude Sonnet 4.5
**分支**: feature/medical-dialogue-datasets
