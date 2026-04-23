from groq import Groq
import json
import logging
import time
from backend.app.models.schemas import CodeChunk, AnalysisIssue
from backend.app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyzerService:
    def __init__(self):
        api_key = settings.GROQ_API_KEY or settings.GEMINI_API_KEY
        if api_key:
            self.client = Groq(api_key=api_key)
            self.enabled = True
        else:
            logger.warning("GROQ_API_KEY not found. Analyzer will run in mock mode.")
            self.enabled = False

    def analyze_code(self, chunk: CodeChunk) -> AnalysisIssue:
        """
        Analyzes a code chunk using a Groq-hosted LLM.
        """
        if not self.enabled:
            return self._mock_analysis(chunk)

        prompt = self._build_prompt(chunk, include_improved_code=True)

        for attempt in range(settings.MAX_RETRIES):
            try:
                result_json = self._request_analysis(prompt)
                return AnalysisIssue(**result_json)

            except Exception as e:
                # Some models fail strict JSON when improved_code contains triple quotes.
                if self._is_json_validate_error(e):
                    try:
                        fallback_prompt = self._build_prompt(chunk, include_improved_code=False)
                        fallback_json = self._request_analysis(fallback_prompt)
                        fallback_json["improved_code"] = None
                        return AnalysisIssue(**fallback_json)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback JSON attempt failed (Attempt {attempt + 1}/{settings.MAX_RETRIES}): {fallback_error}"
                        )

                logger.error(f"Error during LLM analysis (Attempt {attempt + 1}/{settings.MAX_RETRIES}): {e}")
                if attempt < settings.MAX_RETRIES - 1:
                    time.sleep(settings.RETRY_DELAY * (attempt + 1))
                else:
                    return self._fallback_error_analysis(chunk, str(e))

    def _build_prompt(self, chunk: CodeChunk, include_improved_code: bool = True) -> str:
        improved_code_block = '"improved_code": "..."' if include_improved_code else '"improved_code": null'
        improved_code_rule = (
            "- improved_code must be a single JSON string with escaped newlines (\\\\n). Do not use triple quotes.\n"
            if include_improved_code
            else "- Set improved_code to null.\n"
        )

        return f"""
        Task: Review the following {chunk.type} from the file '{chunk.file}'.

        Input Code:
        ```
        {chunk.code}
        ```

        Instructions:
        1. Identify bugs, logical errors, or edge cases.
        2. Find warnings (style issues, non-idiomatic code).
        3. Spot performance bottlenecks.
        4. Detect security vulnerabilities (e.g., injection, hardcoded secrets).
        5. Provide specific suggestions for improvement.
        6. Provide an improved version of the code snippet.

        Output MUST be a valid JSON object with the following structure:
        {{
            "bugs": ["bug 1", "bug 2"],
            "warnings": ["warning 1"],
            "performance_issues": ["issue 1"],
            "security_issues": ["vulnerability 1"],
            "suggestions": ["suggestion 1"],
            {improved_code_block}
        }}

        Rules:
        - Return empty arrays if no issues are found.
        - Be precise and technical.
        - Do not provide any text outside the JSON object.
        {improved_code_rule}
        """

    def _request_analysis(self, prompt: str) -> dict:
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior software engineer and security reviewer. Respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content or "{}"
        return self._safe_json_parse(content)

    def _is_json_validate_error(self, error: Exception) -> bool:
        return "json_validate_failed" in str(error)

    def _safe_json_parse(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Defensive fallback if the model wraps JSON in markdown fences.
            stripped = text.strip()
            if stripped.startswith("```"):
                stripped = stripped.strip("`")
                if stripped.lower().startswith("json"):
                    stripped = stripped[4:].strip()
                return json.loads(stripped)
            raise

    def _mock_analysis(self, chunk: CodeChunk) -> AnalysisIssue:
        # Keep a basic mock for when API key is missing
        return AnalysisIssue(
            bugs=["MOCK: API Key missing"],
            suggestions=["Add GROQ_API_KEY to your environment variables."]
        )

    def _fallback_error_analysis(self, chunk: CodeChunk, error: str) -> AnalysisIssue:
        return AnalysisIssue(
            bugs=[f"Analysis failed: {error}"],
            suggestions=["Please check your internet connection, API key, model name, or limits."]
        )
