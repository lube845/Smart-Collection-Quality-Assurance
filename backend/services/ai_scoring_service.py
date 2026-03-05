"""
AI评分服务
"""
import json
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime

from ..core.config import settings
from ..models.rule import ScoringRule, RuleItem, RuleStatus


class AIScoringService:
    """AI评分服务"""

    def __init__(self):
        self.api_url = settings.LLM_API_URL
        self.api_key = settings.LLM_API_KEY
        self.timeout = 120  # 2分钟超时

    async def score(
        self,
        transcript: str,
        segments: List[Dict],
        rule: ScoringRule,
    ) -> Dict:
        """
        使用LLM进行智能评分

        Args:
            transcript: 转写文本
            segments: 转写片段（带时间戳）
            rule: 评分规则

        Returns:
            评分结果
        """
        # 构建评分提示词
        prompt = self._build_scoring_prompt(transcript, segments, rule)

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": "claude-sonnet",
            "messages": [
                {"role": "system", "content": "你是一个专业的金融催收录音质检专家，负责对催收对话进行评分。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return self._parse_scoring_result(content, rule, segments)
        except httpx.TimeoutException:
            raise Exception("AI评分超时")
        except httpx.HTTPStatusError as e:
            raise Exception(f"AI评分失败: {e.response.text}")
        except Exception as e:
            raise Exception(f"AI评分异常: {str(e)}")

    def _build_scoring_prompt(
        self,
        transcript: str,
        segments: List[Dict],
        rule: ScoringRule,
    ) -> str:
        """构建评分提示词"""
        # 准备考核项信息
        items_info = []
        for item in rule.items:
            if item.is_active:
                items_info.append({
                    "name": item.name,
                    "code": item.code,
                    "type": item.item_type.value,
                    "max_score": item.max_score,
                    "is_veto": item.is_veto,
                    "match_prompt": item.match_prompt or "",
                })

        prompt = f"""## 录音转写文本
{transcript}

## 对话片段详情（带时间戳）
{json.dumps(segments, ensure_ascii=False, indent=2)}

## 评分规则
{json.dumps(items_info, ensure_ascii=False, indent=2)}

## 评分要求
请根据上述转写文本和对话片段，对每个考核项进行评分。

输出格式要求（JSON）：
{{
    "items": [
        {{
            "code": "考核项代码",
            "status": "done/not_done/wrong",  // done=已做到, not_done=未做到, wrong=做错了
            "score": 得分,
            "matched_text": "匹配到的文本（如果没有则为空）",
            "matched_segment_ids": [匹配的片段ID列表],
            "reason": "评分理由"
        }}
    ],
    "total_score": 总分,
    "is_rejected": false,  // 是否一票否决
    "warnings": ["风险预警列表"]
}}

请严格按照上述JSON格式输出，不要包含其他内容。"""

        return prompt

    def _parse_scoring_result(
        self,
        content: str,
        rule: ScoringRule,
        segments: List[Dict],
    ) -> Dict:
        """解析LLM返回的评分结果"""
        try:
            # 尝试解析JSON
            # 提取JSON部分
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(content)

            # 验证结果
            items_result = result.get("items", [])
            total_score = result.get("total_score", 0)
            is_rejected = result.get("is_rejected", False)
            warnings = result.get("warnings", [])

            # 构建详细结果
            details = []
            for item in rule.items:
                if not item.is_active:
                    continue

                # 查找对应评分
                item_result = next(
                    (i for i in items_result if i.get("code") == item.code),
                    None
                )

                if item_result:
                    status = item_result.get("status", "not_done")
                    matched_text = item_result.get("matched_text", "")
                    matched_segment_ids = item_result.get("matched_segment_ids", [])

                    # 计算得分
                    if status == "done":
                        score = item.max_score
                    elif status == "not_done":
                        score = 0
                    elif status == "wrong":
                        if item.is_deduction:
                            if item.deduction_type == "fixed":
                                score = item.max_score - (item.deduction_value or 0)
                            else:
                                score = item.max_score * (1 - (item.deduction_value or 0) / 100)
                        else:
                            score = item.default_score
                    else:
                        score = 0

                    # 确保分数在0到满分之间
                    score = max(0, min(score, item.max_score))
                else:
                    status = "not_done"
                    score = 0
                    matched_text = ""
                    matched_segment_ids = []

                details.append({
                    "rule_item_id": item.id,
                    "item_name": item.name,
                    "item_type": item.item_type.value,
                    "status": status,
                    "score": score,
                    "max_score": item.max_score,
                    "matched_text": matched_text,
                    "matched_segment_ids": matched_segment_ids,
                })

            # 重新计算总分
            total_score = sum(d["score"] for d in details)
            total_max_score = sum(d["max_score"] for d in details)

            # 检查一票否决
            for d in details:
                item = next((i for i in rule.items if i.id == d["rule_item_id"]), None)
                if item and item.is_veto and d["status"] == "wrong":
                    is_rejected = True
                    break

            return {
                "total_score": total_score,
                "total_max_score": total_max_score,
                "passed": total_score >= rule.pass_score and not is_rejected,
                "is_rejected": is_rejected,
                "details": details,
                "warnings": warnings,
            }

        except json.JSONDecodeError as e:
            raise Exception(f"解析AI评分结果失败: {str(e)}")


class MockAIScoringService(AIScoringService):
    """模拟AI评分服务（用于开发和测试）"""

    async def score(
        self,
        transcript: str,
        segments: List[Dict],
        rule: ScoringRule,
    ) -> Dict:
        """模拟评分结果"""
        details = []
        total_score = 0

        for item in rule.items:
            if not item.is_active:
                continue

            # 简单的关键词匹配模拟
            status = "not_done"
            matched_text = ""
            score = 0

            # 模拟一些基本的匹配逻辑
            if "逾期" in transcript:
                if item.code == "overdue_info":
                    status = "done"
                    score = item.max_score
                    matched_text = "提到了逾期情况"
                elif item.code == "payment_request":
                    status = "done"
                    score = item.max_score
                    matched_text = "请求客户还款"

            if item.is_veto and status == "wrong":
                is_rejected = True

            details.append({
                "rule_item_id": item.id,
                "item_name": item.name,
                "item_type": item.item_type.value,
                "status": status,
                "score": score,
                "max_score": item.max_score,
                "matched_text": matched_text,
                "matched_segment_ids": [],
            })

            total_score += score

        total_max_score = sum(d["max_score"] for d in details)
        passed = total_score >= rule.pass_score
        is_rejected = False

        return {
            "total_score": total_score,
            "total_max_score": total_max_score,
            "passed": passed,
            "is_rejected": is_rejected,
            "details": details,
            "warnings": [],
        }


# 根据配置选择使用真实服务还是模拟服务
if settings.LLM_API_URL:
    ai_scoring_service = AIScoringService()
else:
    ai_scoring_service = MockAIScoringService()
