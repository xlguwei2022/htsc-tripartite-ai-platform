from __future__ import annotations
from sqlalchemy import delete, select
from .models import UniversityRule, RuleVersion, TripartiteTask, TaskEvent, Anomaly, RuntimeLog, ConnectorExecution, InboxEvent, OutboxEvent, AuditLog
from .workflow import WORKFLOW_VERSIONS

BASE_DATE = "2026-08-10"

RULES = [
("uestc","电子科技大学","10614","national","全国网签","全国高校毕业生网上签约平台","企业",False,True,"API/RPA",5,"企业需在全国平台注册认证后才能发起邀约","电子科技大学就业信息网","2026-07-15","需在全国网签平台完成企业注册与资质审核","营业执照、法人代表证、Offer letter、企业联系人信息","v2.1","Published","v2.1","已核验"),
("fudan","复旦大学","10246","national","全国网签","全国高校毕业生网上签约平台","企业",False,True,"API/RPA",5,"部分院系要求额外提交纸质留存件","复旦大学学生就业指导服务中心","2026-07-08","需在全国网签平台完成企业注册与资质审核","营业执照、法人代表证、Offer letter、企业联系人信息","v2.0","Published","v2.0","已核验"),
("nju","南京大学","10284","campus","校级网签","南京大学就业系统","企业",True,True,"RPA",7,"企业需在南京大学就业系统注册","南京大学就业中心","2026-07-12","需在南京大学就业系统注册企业账号并完成审核","营业执照、Offer letter、企业联系人信息、校级系统注册材料","v1.3","Published","v1.3","已核验"),
("zju","浙江大学","10335","hybrid","混合","浙江大学就业系统 + 纸质留存","学生",True,True,"半自动",8,"线上签约后仍需提交纸质留存件至学院","浙江大学就业指导中心","2026-07-05","需在浙江大学就业系统注册，线上签约后线下提交留存件","营业执照复印件（盖章）、Offer letter、企业联系人信息","v1.2","Published","v1.2","已核验"),
("sjtu","上海交通大学","10248","paper","纸质三方","线下纸质协议","学生",True,True,"OCR+提醒",10,"学生需先到学院领取协议书，再找企业盖章","上海交通大学计算机学院","2026-07-10","无需线上注册，线下完成企业盖章","营业执照复印件（盖章）、Offer letter、企业公章","v1.0","Published","v1.0","已核验"),
("dlut","大连理工大学","10141","hybrid","混合","大连理工就业网","学生",True,True,"OCR+提醒",10,"盘锦校区流程与主校区略有差异","盘锦校区就业信息网","2026-07-03","需在大连理工就业网注册，盘锦校区流程略有差异","营业执照复印件（盖章）、Offer letter、企业联系人信息","v1.1","Published","v1.1","已核验"),
("pku","北京大学","10001","national","全国网签","全国高校毕业生网上签约平台","企业",False,True,"API/RPA",5,"部分院系要求线下确认后方可网签","待核验 · Demo模拟规则","2026-08-10","需在全国网签平台完成企业注册与资质审核","营业执照、法人代表证、Offer letter、企业联系人信息","v0.9","Draft","v0.8","待核验"),
("tsinghua","清华大学","10003","campus","校级网签","清华大学学生职业发展指导中心系统","企业",True,True,"RPA",6,"企业需在清华就业系统注册，部分院系要求额外材料","待核验 · Demo模拟规则","2026-08-10","需在清华大学就业系统注册企业账号","营业执照、Offer letter、企业联系人信息、校级系统注册材料","v0.9","Draft",None,"待核验"),
("sufe","上海财经大学","10272","campus","校级网签","上海财经大学就业系统","企业",True,True,"RPA",6,"金融类企业优先审核通道","待核验 · Demo模拟规则","2026-08-10","需在上海财经大学就业系统注册企业账号","营业执照、金融许可证（金融类企业）、Offer letter、企业联系人信息","v0.9","Draft","v0.8","待核验"),
("cufe","中央财经大学","10034","hybrid","混合","中央财经大学就业系统 + 纸质留存","学生",True,True,"半自动",8,"线上签约后需提交纸质留存件至学院","待核验 · Demo模拟规则","2026-08-10","需在中央财经大学就业系统注册，线上签约后线下提交留存件","营业执照复印件（盖章）、金融许可证（金融类企业）、Offer letter","v0.9","Draft","v0.8","待核验"),
("tongji","同济大学","10247","national","全国网签","全国高校毕业生网上签约平台","企业",False,True,"API/RPA",5,"部分专业要求额外确认","待核验 · Demo模拟规则","2026-08-10","需在全国网签平台完成企业注册与资质审核","营业执照、法人代表证、Offer letter、企业联系人信息","v0.9","Draft","v0.8","待核验"),
("whu","武汉大学","10486","paper","纸质三方","线下纸质协议","学生",True,True,"OCR+提醒",10,"学生需先到学院领取协议书，再找企业盖章","待核验 · Demo模拟规则","2026-08-10","无需线上注册，线下完成企业盖章","营业执照复印件（盖章）、Offer letter、企业公章","v0.9","Draft","v0.8","待核验"),
]

TASKS = [
("T20260801-001","张明远","uestc","投行部-分析师","2026-08-01","2026-08-15",6,"2026-08-10",None,"normal","v2.1"),
("T20260803-002","李思雨","fudan","研究所-行业研究员","2026-08-03","2026-08-12",5,"2026-08-04",None,"warning","v2.0"),
("T20260805-003","王子轩","sjtu","资产管理部-量化研究员","2026-08-05","2026-08-11",4,"2026-08-09",None,"critical","v1.0"),
("T20260807-004","陈晓彤","zju","财富管理部-理财顾问","2026-08-07","2026-08-20",9,"2026-08-10","2026-08-10","done","v1.2"),
("T20260808-005","赵宇辰","nju","FinTech-开发工程师","2026-08-08","2026-08-20",4,"2026-08-08",None,"warning","v1.3"),
("T20260809-006","刘佳琪","dlut","投行部-助理","2026-08-09","2026-08-18",2,"2026-08-10",None,"warning","v1.1"),
("T20260809-007","孙浩然","pku","投行部-分析师","2026-08-09","2026-08-22",1,"2026-08-10",None,"normal","v0.8"),
("T20260809-008","周雨桐","tongji","研究所-量化分析师","2026-08-09","2026-08-22",4,"2026-08-09",None,"normal","v0.8"),
("T20260809-009","林思源","sufe","财富管理部-投资顾问","2026-08-09","2026-08-23",5,"2026-08-10",None,"normal","v0.8"),
("T20260809-010","吴俊杰","cufe","FinTech-数据工程师","2026-08-09","2026-08-23",6,"2026-08-10",None,"normal","v0.8"),
("T20260809-011","黄诗涵","whu","资产管理部-风控专员","2026-08-09","2026-08-24",3,"2026-08-09",None,"normal","v0.8"),
("T20260809-012","郑明昊","fudan","投行部-业务助理","2026-08-08","2026-08-18",8,"2026-08-10","2026-08-10","done","v2.0"),
]

ANOMS = [
("AN001","T20260805-003","王子轩","上海交通大学","签署逾期","距截止日仅剩 1 天，企业尚未完成纸质协议盖章",4,"高","纸质协议流程中企业盖章环节滞后。学生已取得协议但 HR 尚未操作。风险等级：高。","暂不催促学生；立即通知 HR 负责人完成盖章；若今日内无法完成，启动延期流程。",3,"待处理","已推送HR负责人（企业微信+短信），待处理"),
("AN002","T20260803-002","李思雨","复旦大学","学校审核超时","全国网签平台显示学校审核已超过 3 天",3,"中","全国网签流程中学校审核环节滞后。复旦大学通常审核周期 1-2 个工作日，当前已超出。候选人无操作需要。","暂不重复催促学生；系统继续巡检高校状态。若超过 48 小时仍未更新，转 HR 人工联系高校就业中心。",0,"自动处理中","系统持续巡检中（每30分钟查询一次高校审核状态）"),
("AN003","T20260801-001","张明远","电子科技大学","学生反馈异常","学生反馈\"已确认但学校没审核\"",0,"中","学生消息分析：已在全国平台确认邀约，但学校端仍显示\"院系审核中\"。异常类型：学校审核滞后。责任节点：高校侧。候选人无需操作。","暂不重复催促学生；系统继续巡检高校状态。若超过 48 小时仍未更新，转 HR 人工联系高校就业中心。",0,"已解决","AI已完成异常分类；对账发现学校已审核通过，任务已自动推进至协议生成"),
("AN004","T20260809-006","刘佳琪","大连理工大学","协议信息错误","AI 字段校验发现岗位名称与 Offer 不一致",0,"中","OCR 识别结果显示协议上岗位为\"投行部-助理\"，系统记录为\"投行部-业务助理\"。可能为学生填写时简化了岗位名称。","请 HR 确认岗位全称，若一致则标记为可接受差异；若不一致则联系学生修改。",2,"待处理","已生成修改建议，待HR确认岗位全称"),
("AN005","T20260808-005","赵宇辰","南京大学","RPA执行失败","南京大学就业系统页面元素变化，RPA 连续重试 3 次失败，Connector 已降级",0,"中","自动化执行失败属于 Connector 运行异常，不应绕过 Workflow 强行推进。系统已保留失败证据并暂停该校批量自动任务。","由 HR/运维人工接管当前任务；待 Connector 修复后，通过状态对账确认外部状态，再由业务事件恢复流程。",2,"人工处理中","截图留证完成；南京大学 Connector 已降级，任务已转人工接管"),
]

RUNTIME_LOGS = [
("09:10:00","error","RPA","[南京大学] 登录失败：页面元素「确认签约」未找到（疑似高校系统改版）"),
("09:10:03","warn","RPA","[南京大学] 自动重试第 1 次… 失败（元素定位超时）"),
("09:10:15","warn","RPA","[南京大学] 自动重试第 2 次… 失败（元素定位超时）"),
("09:10:28","warn","RPA","[南京大学] 自动重试第 3 次… 失败（已达最大重试次数）"),
("09:10:30","error","RPA","[南京大学] 已截图留证 → exception_screenshot_NJU_0910.png"),
("09:10:32","warn","Workflow","[南京大学] Connector 状态降级 → 暂停该校批量任务"),
("09:10:38","done","Workflow","[南京大学] 受影响任务（赵宇辰）已转入异常队列，等待人工接管"),
("09:11:08","done","Workflow","[对账] 已自动修正张明远任务状态 → 推进至「协议生成」节点"),
]


def reset_seed(session):
    for model in [AuditLog, OutboxEvent, InboxEvent, ConnectorExecution, TaskEvent, Anomaly, TripartiteTask, RuleVersion, UniversityRule, RuntimeLog]:
        session.execute(delete(model))
    session.flush()
    for i, r in enumerate(RULES, 1):
        rid,name,code,mode,ml,platform,initiator,seal,review,automation,sla,issues,source,updated,ereg,mats,latest,status,lastpub,verified = r
        rule = UniversityRule(id=rid,name=name,code=code,mode=mode,mode_label=ml,platform=platform,initiator=initiator,needs_seal=seal,needs_review=review,automation=automation,sla_days=sla,issues=issues,source=source,updated=updated,enterprise_reg=ereg,company_materials=mats,latest_version=latest,publish_status=status,last_published_version=lastpub,effective_from=updated if status == 'Published' else '—',verified_by='校招运营 + HR数字化双人复核' if status == 'Published' else '待复核',verified_at=f'{updated} 17:30' if status == 'Published' else '—',evidence_id=f'EV-{code}-{i:02d}',verified=verified)
        session.add(rule)
        session.add(RuleVersion(university_id=rid,version=latest,status=status,date=updated,change_note='当前最新规则版本'))
        if lastpub and lastpub != latest:
            session.add(RuleVersion(university_id=rid,version=lastpub,status='Published',date='2026-06-25',change_note='上一版已完成核验并作为当前可执行基线'))
        session.add(RuleVersion(university_id=rid,version='baseline',status='Archived',date='2026-06-20',change_note='建立高校规则基础档案与签约模式分类'))
    session.flush()
    for t in TASKS:
        tid,name,uid,pos,offer,deadline,step,node,completed,risk,pin = t
        rule = session.get(UniversityRule, uid)
        session.add(TripartiteTask(id=tid,candidate_name=name,university_id=uid,position=pos,offer_date=offer,deadline=deadline,current_step=step,node_entered_at=node,completed_at=completed,risk=risk,rule_version_pinned=pin,rule_source_pinned=rule.source,workflow_version=WORKFLOW_VERSIONS[rule.mode],trace_id=f'TRC-{tid.replace("-","")}',version=1))
    session.flush()
    for task in session.scalars(select(TripartiteTask)).all():
        session.add(TaskEvent(task_id=task.id,event_id=f'SEED-{task.id}',occurred_at=f'{task.node_entered_at} 09:00',source='Workflow',result='等待中' if task.risk != 'done' else '完成',message='PoC 初始状态已载入',event_type='SEED'))
    for a in ANOMS:
        session.add(Anomaly(id=a[0],task_id=a[1],candidate_name=a[2],university_name=a[3],type=a[4],description=a[5],days=a[6],risk=a[7],analysis=a[8],suggestion=a[9],level=a[10],state=a[11],status=a[12]))
    for log in RUNTIME_LOGS:
        session.add(RuntimeLog(time=log[0],level=log[1],source=log[2],message=log[3]))
    session.commit()
