FLOWS = {
    "national": [
        {"id":"S0","name":"Offer Accepted","actor":"系统","auto":True},
        {"id":"S1","name":"创建三方任务","actor":"系统","auto":True},
        {"id":"S2","name":"规则引擎匹配高校规则","actor":"系统","auto":True},
        {"id":"S3","name":"企业发起网签","actor":"RPA","auto":True},
        {"id":"S4","name":"待学生确认","actor":"学生","auto":False},
        {"id":"S5","name":"学校审核","actor":"学校","auto":False},
        {"id":"S6","name":"协议生成","actor":"系统","auto":True},
        {"id":"S7","name":"协议归档","actor":"RPA","auto":True},
        {"id":"S8","name":"完成","actor":"系统","auto":True},
    ],
    "campus": [
        {"id":"S0","name":"Offer Accepted","actor":"系统","auto":True},
        {"id":"S1","name":"创建三方任务","actor":"系统","auto":True},
        {"id":"S2","name":"规则引擎匹配高校规则","actor":"系统","auto":True},
        {"id":"S3","name":"企业发起网签","actor":"RPA","auto":True},
        {"id":"S4","name":"待学生确认","actor":"学生","auto":False},
        {"id":"S5","name":"企业盖章","actor":"HR","auto":False,"conditional":True},
        {"id":"S6","name":"学校审核","actor":"学校","auto":False},
        {"id":"S7","name":"协议下载","actor":"RPA","auto":True},
        {"id":"S8","name":"协议归档","actor":"RPA","auto":True},
        {"id":"S9","name":"完成","actor":"系统","auto":True},
    ],
    "paper": [
        {"id":"S0","name":"Offer Accepted","actor":"系统","auto":True},
        {"id":"S1","name":"创建三方任务","actor":"系统","auto":True},
        {"id":"S2","name":"规则引擎匹配高校规则","actor":"系统","auto":True},
        {"id":"S3","name":"待学生取得协议","actor":"学生","auto":False},
        {"id":"S4","name":"企业填写/盖章","actor":"HR","auto":False},
        {"id":"S5","name":"学校鉴证盖章","actor":"学校","auto":False},
        {"id":"S6","name":"协议扫描/OCR","actor":"AI","auto":True},
        {"id":"S7","name":"协议归档","actor":"RPA","auto":True},
        {"id":"S8","name":"完成","actor":"系统","auto":True},
    ],
    "hybrid": [
        {"id":"S0","name":"Offer Accepted","actor":"系统","auto":True},
        {"id":"S1","name":"创建三方任务","actor":"系统","auto":True},
        {"id":"S2","name":"规则引擎匹配高校规则","actor":"系统","auto":True},
        {"id":"S3","name":"学生线上发起/提交","actor":"学生","auto":False},
        {"id":"S4","name":"企业确认/盖章","actor":"HR","auto":False},
        {"id":"S5","name":"学校审核","actor":"学校","auto":False},
        {"id":"S6","name":"纸质留存/材料回收","actor":"学生","auto":False,"conditional":True},
        {"id":"S7","name":"OCR字段校验","actor":"AI","auto":True},
        {"id":"S8","name":"协议归档","actor":"RPA","auto":True},
        {"id":"S9","name":"完成","actor":"系统","auto":True},
    ],
}

WORKFLOW_VERSIONS = {
    "national":"wf-national-v1.3",
    "campus":"wf-campus-v1.2",
    "paper":"wf-paper-v1.1",
    "hybrid":"wf-hybrid-v1.2",
}

EVENT_BY_ACTOR = {
    "学生":"STUDENT_COMPLETED",
    "学校":"SCHOOL_COMPLETED",
    "HR":"HR_COMPLETED",
}
