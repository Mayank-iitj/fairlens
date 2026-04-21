"""Production-ready AI service using Groq.

Provides intelligent explanations, recommendations, and bias remediation
suggestions through a Groq-hosted open model.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI service errors."""


class GroqAIService:
    """Production-ready AI service using Groq-hosted LLMs."""

    def __init__(self) -> None:
        self.client = None
        self.model = settings.groq_model

        api_key = settings.groq_api_key.strip()
        if not api_key:
            raise AIServiceError("GROQ_API_KEY is required for audit generation")

        try:
            from groq import Groq

            self.client = Groq(api_key=api_key)
        except ImportError:
            raise AIServiceError("Groq SDK is not installed") from None
        except Exception as exc:
            raise AIServiceError(f"Failed to initialize Groq client: {exc}") from exc

    def explain_metric(
        self,
        metric_name: str,
        metric_value: float,
        threshold: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Provide a human-readable explanation of a fairness metric."""
        try:
            prompt = self._build_metric_prompt(metric_name, metric_value, threshold, context)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fairness and compliance expert who explains audit results clearly for non-technical stakeholders.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=220,
            )
            text = self._extract_text(response)
            if not text:
                raise AIServiceError("Groq returned an empty metric explanation")
            return text
        except Exception as exc:
            logger.error(f"AI explanation failed: {exc}")
            raise AIServiceError(f"AI explanation failed: {exc}") from exc

    def suggest_fix(
        self,
        metric_name: str,
        metric_value: float,
        violation_severity: str = "medium",
        model_type: str = "classification",
        accuracy_priority: str = "balanced",
    ) -> Dict[str, Any]:
        """Get specific remediation suggestions for a fairness violation."""
        try:
            prompt = (
                "You are a machine learning fairness expert. Return only JSON. "
                "Suggest the top 3 bias mitigation techniques for this case.\n"
                f"Metric: {metric_name}\n"
                f"Value: {metric_value:.4f}\n"
                f"Severity: {violation_severity}\n"
                f"Model: {model_type}\n"
                f"Priority: {accuracy_priority}\n\n"
                "Return JSON in this exact shape:\n"
                '{"techniques":[{"name":"...","description":"...","complexity":"low|medium|high","fairness_gain":"low|medium|high"}]}'
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Return strict JSON only, with no markdown fences or extra commentary.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=700,
            )
            response_text = self._extract_text(response)
            parsed = self._parse_json_response(response_text)
            if isinstance(parsed, dict) and parsed.get("techniques"):
                return parsed
            raise AIServiceError("Groq returned an invalid remediation payload")
        except json.JSONDecodeError:
            raise AIServiceError("Groq returned invalid JSON for remediation suggestions")
        except Exception as exc:
            logger.error(f"AI suggestion failed: {exc}")
            raise AIServiceError(f"AI suggestion failed: {exc}") from exc

    def summarize_audit(
        self,
        score: float,
        flagged_metrics: List[str],
        dataset_info: Optional[Dict[str, Any]] = None,
        compliance_framework: str = "EEOC",
    ) -> str:
        """Generate an executive summary of audit results."""
        try:
            flagged_list = ", ".join(flagged_metrics) if flagged_metrics else "none"
            dataset_summary = json.dumps(dataset_info or {}, default=str)
            prompt = (
                "Generate a brief executive summary of this fairness audit for business stakeholders. "
                "Be clear, direct, and actionable.\n"
                f"Score: {score}/100\n"
                f"Violations: {len(flagged_metrics)}\n"
                f"Framework: {compliance_framework}\n"
                f"Flagged Metrics: {flagged_list}\n"
                f"Dataset Info: {dataset_summary}\n"
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Write concise executive summaries for compliance and risk reviews.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=220,
            )
            text = self._extract_text(response)
            if not text:
                raise AIServiceError("Groq returned an empty audit summary")
            return text
        except Exception as exc:
            logger.error(f"AI summary failed: {exc}")
            raise AIServiceError(f"AI summary failed: {exc}") from exc

    async def stream_remediation_suggestions(
        self,
        metric_name: str,
        metric_value: float,
        violation_severity: str = "medium",
    ) -> AsyncGenerator[str, None]:
        """Stream remediation suggestions as text chunks."""
        suggestion = self.suggest_fix(metric_name, metric_value, violation_severity)
        yield json.dumps(suggestion)

    def _build_metric_prompt(
        self,
        metric_name: str,
        metric_value: float,
        threshold: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        context_text = json.dumps(context or {}, default=str)
        status = "VIOLATION" if self._is_violation(metric_name, metric_value, threshold) else "PASS"
        return (
            f"Metric: {metric_name.replace('_', ' ')}\n"
            f"Current Value: {metric_value:.4f}\n"
            f"Threshold: {threshold:.4f}\n"
            f"Status: {status}\n"
            f"Context: {context_text}\n\n"
            "Explain what this means in 2-3 sentences, using plain language and a practical next step."
        )

    def _extract_text(self, response: Any) -> str:
        try:
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                parts = []
                for item in content:
                    text = getattr(item, "text", None)
                    if text:
                        parts.append(text)
                return "".join(parts).strip()
            if hasattr(message, "content") and message.content:
                return str(message.content).strip()
        except Exception:
            return ""
        return ""

    def _parse_json_response(self, response_text: str) -> Any:
        if not response_text:
            raise json.JSONDecodeError("Empty AI response", response_text, 0)

        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text
            if text.endswith("```"):
                text = text[:-3].strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        return json.loads(text)

    def _is_violation(self, metric_name: str, value: float, threshold: float) -> bool:
        if metric_name == "disparate_impact":
            return value < threshold
        return value > threshold

_ai_service = GroqAIService()


def explain_metric(metric_name: str, metric_value: float, threshold: float, context: Optional[Dict[str, Any]] = None) -> str:
    """Explain a fairness metric."""
    return _ai_service.explain_metric(metric_name, metric_value, threshold, context)


def suggest_fix(context: dict) -> str:
    """Get remediation suggestions (backward compat)."""
    return json.dumps(
        _ai_service.suggest_fix(
            context.get("metric_name", "unknown"),
            float(context.get("metric_value", 0.0)),
            context.get("violation_severity", "medium"),
            context.get("model_type", "classification"),
            context.get("accuracy_priority", "balanced"),
        )
    )


def summarize_audit(score: float, flagged_metrics: list[str]) -> str:
    """Summarize audit results (backward compat)."""
    return _ai_service.summarize_audit(score, flagged_metrics, {}, "EEOC")


def get_ai_service() -> GroqAIService:
    """Get the AI service singleton."""
    return _ai_service
