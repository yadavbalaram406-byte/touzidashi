import json
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.scoring import DIMENSIONS, get_decision
from app.services.llm import LLMClient, parse_json_response
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """你是一位专业的早期项目投资顾问，擅长用YC标准评估创业项目。

【文案风格要求】
- 语气果断，不打太极。直接说"这是典型的……"、"天花板过低"、"存在天然隐患"，避免"可能"、"也许"等模糊措辞。
- 用鲜活的比喻把抽象特征具象化，例如："成建制正规军的执行力"、"流量寄生策略"、"基于人头的服务外包生意"。
- 尽量引用文档中出现的真实数字（金额、用户数、增速等）来锚定判断。
- 每个维度的分析必须用"加分项："和"扣分项："两段式结构，关键弱点可用括号强调，如"扣分项（重灾区）："。
- 综合评述和投资建议要有行动号召感：一句话定性 + 一个关键考察里程碑 + 一个假设性结论（"如果……，该项目具备……的潜质"）。
- 区分PE（现金流）和VC（爆发增长）两种视角时，必须明确点出来。
- 禁止空洞褒义词（"较为优秀"、"具有一定竞争力"）和学术腔（"综上所述"、"基于以上分析"）。

所有输出必须是合法的JSON格式，不要包含任何JSON以外的内容。
重要：JSON字符串值中不得使用中文引号（"" ''），只能使用英文双引号。字符串内部如需引用，用【】或()替代引号。"""

DIMENSIONS_TEXT = "\n".join(
    f"{i+1}. {d.name}（满分{d.max_score}分）"
    for i, d in enumerate(DIMENSIONS)
)

TIERS_TEXT = "\n\n".join(
    f"【{d.name}，满分{d.max_score}分】\n" +
    "\n".join(f"  - [{t['range']}分] {t['label']}：{t['description']}" for t in d.tiers)
    for d in DIMENSIONS
)


async def _section1_project_intro(llm: LLMClient, text: str) -> dict:
    """Generate project introduction."""
    user_prompt = f"""请根据以下项目文档内容，生成一份项目简介。

项目文档内容：
{text}

请严格按照以下JSON格式输出，不要输出任何其他内容：
{{
  "project_name": "项目/公司名称（如无法判断填'未知项目'）",
  "one_liner": "一句话介绍项目核心价值（20字以内）",
  "summary": "项目核心业务与价值主张（200字以内）",
  "market_background": "市场背景与行业机会分析（150字以内）",
  "comparables": ["对标企业1", "对标企业2", "对标企业3（最多列3个）"],
  "highlights": ["项目积极亮点1（仅列正面优势，禁止包含任何负面或扣分内容）", "亮点2", "亮点3（最多列5个）"]
}}"""

    raw = await llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=2048)
    return parse_json_response(raw)


async def _section2_scores(llm: LLMClient, text: str, intro: dict) -> dict:
    """Score each dimension."""
    intro_text = json.dumps(intro, ensure_ascii=False)
    user_prompt = f"""请根据以下项目文档和项目简介，按照YC标准对该项目进行打分评估。

项目简介：
{intro_text}

项目文档内容：
{text[:30000]}

打分维度与标准：
{TIERS_TEXT}

【reasoning字段写法示例】
好的写法："加分项：团队属于SAS中国核心研发全建制转移，人均拥有十余年深厚背景，这种(成建制正规军)在早期项目中极其罕见。扣分项（重灾区）：这是典型的技术极客做业务短板，MVP刚完成，完全没有已验证的商业流水和真实的获客漏斗数据。"
差的写法："团队背景较为扎实，有一定的技术实力，但商业化经验有待提升。"

请严格按照以下JSON格式输出每个维度的评分，不要输出任何其他内容：
{{
  "dimensions": [
    {{
      "key": "team",
      "name": "团队与执行力",
      "max_score": 30,
      "score": <0-30的整数>,
      "tier_label": "<顶级配置|标准组合|存在硬伤>",
      "reasoning": "加分项：……（具体、鲜活、引用数据）。扣分项：……（直击要害，可加括号强调程度）"
    }},
    {{
      "key": "pain_point",
      "name": "痛点与市场时机",
      "max_score": 25,
      "score": <0-25的整数>,
      "tier_label": "<完美击中|稳健生意|伪需求/红海>",
      "reasoning": "加分项：……。扣分项：……"
    }},
    {{
      "key": "traction",
      "name": "商业牵引力与模型",
      "max_score": 25,
      "score": <0-25的整数>,
      "tier_label": "<极强验证|初步成型|逻辑断裂>",
      "reasoning": "加分项：……。扣分项：……"
    }},
    {{
      "key": "moat",
      "name": "产品护城河与壁垒",
      "max_score": 20,
      "score": <0-20的整数>,
      "tier_label": "<极高壁垒|先发优势|极易复制>",
      "reasoning": "加分项：……。扣分项：……"
    }}
  ]
}}"""

    raw = await llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=2048)
    return parse_json_response(raw)


async def _section3_suggestions(llm: LLMClient, text: str, intro: dict, scores: dict, final_score: float, decision: dict) -> dict:
    """Generate evaluation suggestions."""
    intro_text = json.dumps(intro, ensure_ascii=False)
    scores_text = json.dumps(scores, ensure_ascii=False)

    user_prompt = f"""请根据以下项目评估结果，生成投资评估建议报告。

项目简介：
{intro_text}

维度打分：
{scores_text}

综合得分：{final_score}/100 → {decision['icon']} {decision['label']}（{decision['chinese']}）

【风格要求】
- strengths/risks/improvements 每条要具体、直击要害，禁止空洞表述。
- comprehensive_review 格式：一句话定性这个项目的本质 + 点出最关键的一个问题/里程碑 + 给出假设性结论（"如果……，该项目具备……的潜质"或"建议……"）。如果是现金流生意而非爆发型VC项目，必须明确点出。
- next_steps 是给投资人的行动清单，要有决策感（"立即"、"重点考察"、"推进深度DD"）。

【comprehensive_review示例】
好："技术壁垒极高，但商业化能力存疑。建议重点考察其首个付费标杆客户的获取周期。如果能引入一位极具狼性的销售合伙人，该项目具备冲击90分以上的潜质。"
好："这是一个能快速分红的极佳PE标的，但作为追求指数级增长的VC项目天花板过低。如果平台需要稳定现金流反哺，可考虑深度绑定；若纯粹追求生态爆发，建议降低优先级。"
差："综上所述，该项目整体表现较为优秀，具有一定的投资价值，建议进一步关注。"

请严格按照以下JSON格式输出，不要输出任何其他内容：
{{
  "strengths": ["核心优势1（具体、有洞察力，引用文档数据）", "核心优势2", "核心优势3（最多列5条）"],
  "risks": ["主要风险1（直击要害，不模糊）", "主要风险2", "主要风险3（最多列5条）"],
  "improvements": ["改进建议1（可操作，说清楚怎么做）", "改进建议2", "改进建议3（最多列5条）"],
  "comprehensive_review": "综合评述（150-250字，按上述风格要求写）",
  "next_steps": ["下一步行动1（有决策感）", "下一步行动2", "下一步行动3（最多3条，针对投资人）"]
}}"""

    raw = await llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=3000)
    return parse_json_response(raw)


def _extract_scores(scores_data: dict) -> dict[str, float]:
    """Extract score values keyed by dimension key."""
    result = {}
    for dim in scores_data.get("dimensions", []):
        key = dim.get("key")
        score = float(dim.get("score", 0))
        result[key] = score
    return result


async def run_evaluation(evaluation_id: int, db: AsyncSession):
    """Main evaluation pipeline. Called as a background task."""
    from sqlalchemy import select

    try:
        # Load record
        stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
        result = await db.execute(stmt)
        ev = result.scalar_one()

        ev.status = "processing"
        ev.updated_at = datetime.utcnow()
        await db.commit()

        # Parse documents if not yet done
        if not ev.extracted_text:
            from pathlib import Path
            from app.services.parser import parse_document, truncate_text
            file_paths = [fp.strip() for fp in (ev.file_path or "").split("\n") if fp.strip()]
            merged_parts = []
            for fp in file_paths:
                ext = Path(fp).suffix.lstrip(".").lower()
                try:
                    text, _ = await parse_document(fp, ext)
                    if text.strip():
                        merged_parts.append(text.strip())
                except Exception as e:
                    logger.warning(f"[eval:{evaluation_id}] Parse failed for {fp}: {e}")
            merged_text = truncate_text("\n\n---\n\n".join(merged_parts))
            ev.extracted_text = merged_text
            ev.text_length = len(merged_text)
            await db.commit()
            logger.info(f"[eval:{evaluation_id}] Parsed {len(file_paths)} file(s), {ev.text_length} chars")

        llm = LLMClient()
        ev.llm_provider = llm.provider
        ev.llm_model = llm.model

        # Section 1: Project intro
        logger.info(f"[eval:{evaluation_id}] Section 1: project intro")
        intro = await _section1_project_intro(llm, ev.extracted_text or "")
        ev.project_intro = json.dumps(intro, ensure_ascii=False)
        ev.project_name = intro.get("project_name", ev.project_name)
        await db.commit()

        # Section 2: Scores
        logger.info(f"[eval:{evaluation_id}] Section 2: scoring")
        scores = await _section2_scores(llm, ev.extracted_text or "", intro)
        ev.scores_json = json.dumps(scores, ensure_ascii=False)

        score_map = _extract_scores(scores)
        ev.score_team = score_map.get("team")
        ev.score_pain_point = score_map.get("pain_point")
        ev.score_traction = score_map.get("traction")
        ev.score_moat = score_map.get("moat")

        final_score = sum(score_map.values())
        ev.final_score = round(final_score, 1)
        decision = get_decision(final_score)
        ev.decision = f"{decision['icon']} {decision['label']}"
        await db.commit()

        # Section 3: Suggestions
        logger.info(f"[eval:{evaluation_id}] Section 3: suggestions")
        suggestions = await _section3_suggestions(llm, ev.extracted_text or "", intro, scores, final_score, decision)
        ev.suggestions_json = json.dumps(suggestions, ensure_ascii=False)

        ev.status = "completed"
        ev.updated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[eval:{evaluation_id}] Completed. Score: {ev.final_score}, Decision: {ev.decision}")

    except Exception as e:
        logger.exception(f"[eval:{evaluation_id}] Failed: {e}")
        try:
            stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
            result = await db.execute(stmt)
            ev = result.scalar_one_or_none()
            if ev:
                ev.status = "failed"
                ev.error_message = str(e)
                ev.updated_at = datetime.utcnow()
                await db.commit()
        except Exception:
            pass
