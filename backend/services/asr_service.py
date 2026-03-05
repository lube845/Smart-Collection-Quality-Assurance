"""
ASR转写服务
"""
import json
import httpx
from typing import Optional, List, Dict
from datetime import datetime

from ..core.config import settings
from ..models.recording import TranscriptSegment


class ASRService:
    """ASR转写服务"""

    def __init__(self):
        self.api_url = settings.ASR_API_URL
        self.api_key = settings.ASR_API_KEY
        self.timeout = 300  # 5分钟超时

    async def transcribe(
        self,
        oss_url: str,
        vocabulary: Optional[List[str]] = None,
    ) -> Dict:
        """
        调用ASR接口进行转写

        Args:
            oss_url: 音频文件的OSS URL
            vocabulary: 金融术语词库（可选）

        Returns:
            转写结果，包含全文和分片段
        """
        # 构建请求
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "audio_url": oss_url,
            "format": "json",
            "vocabulary": vocabulary or self._get_default_vocabulary(),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/transcribe",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                return self._parse_transcript_result(result)
        except httpx.TimeoutException:
            raise Exception("ASR转写超时")
        except httpx.HTTPStatusError as e:
            raise Exception(f"ASR转写失败: {e.response.text}")
        except Exception as e:
            raise Exception(f"ASR转写异常: {str(e)}")

    async def transcribe_with_role(
        self,
        oss_url: str,
    ) -> Dict:
        """
        调用ASR接口进行转写，并区分说话人角色

        Returns:
            转写结果，包含全文、分片段、角色分离信息
        """
        # 使用带角色分离的转写
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "audio_url": oss_url,
            "format": "json",
            "speaker_diarization": True,  # 启用说话人分离
            "vocabulary": self._get_default_vocabulary(),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/transcribe_with_speaker",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                return self._parse_transcript_result(result)
        except httpx.TimeoutException:
            raise Exception("ASR转写超时")
        except httpx.HTTPStatusError as e:
            raise Exception(f"ASR转写失败: {e.response.text}")
        except Exception as e:
            raise Exception(f"ASR转写异常: {str(e)}")

    def _parse_transcript_result(self, result: Dict) -> Dict:
        """解析ASR返回的结果"""
        # 提取文本
        text = result.get("text", "")

        # 提取片段
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "speaker": seg.get("speaker", "unknown"),
                "speaker_name": seg.get("speaker_name"),
                "start_time": seg.get("start_time", 0),
                "end_time": seg.get("end_time", 0),
                "text": seg.get("text", ""),
                "confidence": seg.get("confidence", 1.0),
            })

        return {
            "full_text": text,
            "segments": segments,
        }

    def _get_default_vocabulary(self) -> List[str]:
        """获取默认金融术语词库"""
        return [
            # 催收相关
            "逾期", "还款", "分期", "本金", "利息", "滞纳金",
            "催收", "还款日", "还款额", "最低还款", "全额还款",
            "M1", "M2", "M3", "M3+", "不良资产",
            # 金融术语
            "征信", "征信报告", "信用记录", "黑名单",
            "划扣", "自动划扣", "银行转账",
            "诉讼", "仲裁", "起诉", "法院",
            "减免", "息费减免", "罚息减免",
            # 身份核实
            "身份证", "姓名", "手机号", "银行卡",
            "核实身份", "本人", "委托",
        ]


class MockASRService(ASRService):
    """模拟ASR服务（用于开发和测试）"""

    async def transcribe(
        self,
        oss_url: str,
        vocabulary: Optional[List[str]] = None,
    ) -> Dict:
        """模拟转写结果"""
        # 返回模拟数据
        return {
            "full_text": "您好，请问是张先生吗？您好，我是XX银行的催收专员，您在我们银行的贷款已经逾期三个月了，总金额是五万元。请问您现在方便还款吗？",
            "segments": [
                {
                    "speaker": "agent",
                    "speaker_name": "坐席",
                    "start_time": 0.0,
                    "end_time": 3.5,
                    "text": "您好，请问是张先生吗？",
                    "confidence": 0.98,
                },
                {
                    "speaker": "customer",
                    "speaker_name": "客户",
                    "start_time": 3.5,
                    "end_time": 8.0,
                    "text": "您好，我是。",
                    "confidence": 0.95,
                },
                {
                    "speaker": "agent",
                    "speaker_name": "坐席",
                    "start_time": 8.0,
                    "end_time": 15.0,
                    "text": "您好，我是XX银行的催收专员，您在我们银行的贷款已经逾期三个月了，总金额是五万元。请问您现在方便还款吗？",
                    "confidence": 0.96,
                },
            ],
        }


# 根据配置选择使用真实ASR还是模拟ASR
if settings.ASR_API_URL:
    asr_service = ASRService()
else:
    asr_service = MockASRService()
