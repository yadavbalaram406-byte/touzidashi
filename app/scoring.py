from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreDimension:
    key: str
    name: str
    max_score: int
    tiers: list[dict]


DIMENSIONS: list[ScoreDimension] = [
    ScoreDimension(
        key="team",
        name="团队与执行力",
        max_score=30,
        tiers=[
            {
                "range": "25-30",
                "label": "顶级配置",
                "description": '创始人对赛道有十年以上极深认知，极客动手能力+极强销售能力。迭代速度按"天"计算。',
            },
            {
                "range": "15-24",
                "label": "标准组合",
                "description": "团队配置完整（技术+商业），有大厂或相关行业背景，执行力在线，1-2月内能跑出MVP。",
            },
            {
                "range": "0-14",
                "label": "存在硬伤",
                "description": '核心技术外包，或全技术无商业操盘人，或陷入半年以上"憋大招"研发期。',
            },
        ],
    ),
    ScoreDimension(
        key="pain_point",
        name="痛点与市场时机",
        max_score=25,
        tiers=[
            {
                "range": "20-25",
                "label": "完美击中",
                "description": '切中"头发着火"级别的绝对刚需，契合当下大模型技术突破或生态结构性真空，百亿美金巨头潜力。',
            },
            {
                "range": "10-19",
                "label": "稳健生意",
                "description": '痛点真实但属"改良型"，市场规模有明显天花板，更像千万级现金流好生意而非爆发式平台。',
            },
            {
                "range": "0-9",
                "label": "伪需求/红海",
                "description": "拿着技术找场景的自嗨产品，或进入已被巨头免费策略锁死的红海市场。",
            },
        ],
    ),
    ScoreDimension(
        key="traction",
        name="商业牵引力与模型",
        max_score=25,
        tiers=[
            {
                "range": "20-25",
                "label": "极强验证",
                "description": "产品未写完代码前就已通过手工/外部工具跑通真实付费订单。优秀流量转化漏斗和高复购/留存率。",
            },
            {
                "range": "10-19",
                "label": "初步成型",
                "description": "有早期内测用户，虽然还在烧钱或靠免费吸引流量，但单体经济模型（LTV/CAC）在逻辑上通顺。",
            },
            {
                "range": "0-9",
                "label": "逻辑断裂",
                "description": '只有免费用户群，商业模式完全寄希望于未来"流量变现"，对获客成本和付费转化率一无所知。',
            },
        ],
    ),
    ScoreDimension(
        key="moat",
        name="产品护城河与壁垒",
        max_score=20,
        tiers=[
            {
                "range": "16-20",
                "label": "极高壁垒",
                "description": "颠覆性专有技术架构，或切入极难替换的企业级工作流，或率先建立坚不可摧的双边交易网络。",
            },
            {
                "range": "8-15",
                "label": "先发优势",
                "description": "逻辑跑得顺，用户体验极佳，但底层依赖开源工具或外部模型。护城河主要靠执行力、认知差和时间窗口。",
            },
            {
                "range": "0-7",
                "label": "极易复制",
                "description": "纯粹UI创新或简单Prompt工程套壳，巨头或有资源竞对一个周末就能克隆。",
            },
        ],
    ),
]

DECISIONS = [
    {"min": 85, "max": 100, "icon": "🏆", "label": "Strong Yes", "chinese": "绝对力推", "description": "极具爆发力的风投级项目，立刻启动TS谈判"},
    {"min": 70, "max": 84, "icon": "📈", "label": "Cautious Yes", "chinese": "谨慎看好/重点孵化", "description": "优质标的，需通过深度DD施压补齐短板"},
    {"min": 50, "max": 69, "icon": "👀", "label": "Keep in Touch", "chinese": "保持观察/暂缓", "description": "为时尚早，留尖锐优化指标做长期观察"},
    {"min": 0, "max": 49, "icon": "🛑", "label": "Pass", "chinese": "直接否决", "description": "存在不可修复的基因缺陷"},
]


def get_decision(final_score: float) -> dict:
    for d in DECISIONS:
        if d["min"] <= final_score <= d["max"]:
            return d
    return DECISIONS[-1]


def get_dimension_by_key(key: str) -> Optional[ScoreDimension]:
    return next((d for d in DIMENSIONS if d.key == key), None)
