import os
from typing import Optional
import requests

try:
    from llama_cpp import Llama  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    Llama = None  # type: ignore


class LocalLLM:
    def __init__(self) -> None:
        # Optional: allow selecting multiple models via comma-separated list
        self.model_candidates = [m.strip() for m in os.getenv("HF_MODELS", "").split(",") if m.strip()]
        # Optional cloud providers
        self.textgen_base_url = os.getenv("TEXTGEN_BASE_URL")  # OpenAI-compatible base URL
        self.textgen_api_key = os.getenv("TEXTGEN_API_KEY")
        self.textgen_model = os.getenv("TEXTGEN_MODEL", "gpt-3.5-turbo")

        self.hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        self.hf_model = os.getenv("HUGGINGFACE_MODEL")
        self.hf_timeout = int(os.getenv("HF_TIMEOUT_SECONDS", "30"))

        # Optional truncation for very long prompts
        self.prompt_truncate_chars = int(os.getenv("PROMPT_TRUNCATE_CHARS", "8000"))

        self.model_path = os.getenv("LLM_MODEL_PATH")
        self.ctx_size = int(os.getenv("LLM_CTX_SIZE", "4096"))
        self.n_threads = int(os.getenv("LLM_N_THREADS", "4"))
        self.max_tokens_default = int(os.getenv("LLM_MAX_TOKENS", "768"))
        self.temperature_default = float(os.getenv("LLM_TEMPERATURE", "0.7"))

        self._llm = None
        if self.model_path and os.path.exists(self.model_path) and Llama is not None:
            try:
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.ctx_size,
                    n_threads=self.n_threads,
                    verbose=False,
                )
            except Exception:
                self._llm = None

    def is_available(self) -> bool:
        return bool(self.textgen_base_url or (self.hf_token and self.hf_model) or self._llm is not None)

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        # Truncate overly long prompts to avoid slow calls
        if len(prompt) > self.prompt_truncate_chars:
            prompt = prompt[: self.prompt_truncate_chars]

        # Prefer OpenAI-compatible endpoint if configured
        if self.textgen_base_url and self.textgen_api_key:
            headers = {
                "Authorization": f"Bearer {self.textgen_api_key}",
                "Content-Type": "application/json",
            }
            # Try legacy completions
            try:
                url = self.textgen_base_url.rstrip("/") + "/v1/completions"
                payload = {
                    "model": self.textgen_model,
                    "prompt": prompt,
                    "max_tokens": max_tokens or self.max_tokens_default,
                    "temperature": self.temperature_default if temperature is None else temperature,
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=self.hf_timeout)
                if resp.status_code < 400:
                    data = resp.json()
                    text = data.get("choices", [{}])[0].get("text", "").strip()
                    if text:
                        return text
            except Exception:
                pass
            # Try chat completions
            try:
                url = self.textgen_base_url.rstrip("/") + "/v1/chat/completions"
                payload = {
                    "model": self.textgen_model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful writing assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_tokens or self.max_tokens_default,
                    "temperature": self.temperature_default if temperature is None else temperature,
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=self.hf_timeout)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if text:
                    return text
            except Exception:
                pass

        # Next, try Hugging Face Inference API if configured
        # Try multiple HF models if provided
        if self.hf_token and (self.hf_model or self.model_candidates):
            models = [self.hf_model] if self.hf_model else []
            models += [m for m in self.model_candidates if m not in models]
            last_err = None
            for model in models:
                url = f"https://api-inference.huggingface.co/models/{model}"
                headers = {
                    "Authorization": f"Bearer {self.hf_token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max_tokens or self.max_tokens_default,
                        "temperature": self.temperature_default if temperature is None else temperature,
                        "return_full_text": False,
                    },
                }
                try:
                    resp = requests.post(url, json=payload, headers=headers, timeout=self.hf_timeout)
                    resp.raise_for_status()
                    data = resp.json()
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        gen = data[0].get("generated_text") or data[0].get("summary_text")
                        if isinstance(gen, str) and gen.strip():
                            return gen.strip()
                    if isinstance(data, dict):
                        gen = data.get("generated_text") or data.get("summary_text")
                        if isinstance(gen, str) and gen.strip():
                            return gen.strip()
                except Exception as e:
                    last_err = e
                    continue
            # Fall back if none succeeded

        # Local llama.cpp backend
        if self._llm is None:
            return self._fallback_generate(prompt)

        response = self._llm.create_completion(
            prompt=prompt,
            max_tokens=max_tokens or self.max_tokens_default,
            temperature=self.temperature_default if temperature is None else temperature,
            stop=["</s>"]
        )
        try:
            return response["choices"][0]["text"].strip()
        except Exception:
            return self._fallback_generate(prompt)

    def _fallback_generate(self, prompt: str) -> str:
        # Very simple deterministic fallback text, ensures project runs without a model
        if "BLOG_POST" in prompt:
            return (
                "# Sample Blog Post\n\n"
                "This is a locally generated placeholder blog post. Replace with a local LLM for richer content.\n\n"
                "## Introduction\n\n"
                "We explore the topic, highlight benefits, and provide actionable insights.\n\n"
                "## Key Points\n\n"
                "- Insight 1\n- Insight 2\n- Insight 3\n\n"
                "## Conclusion\n\n"
                "A concise wrap-up with a call-to-action."
            )
        if "SOCIAL_SNIPPETS" in prompt:
            return (
                "TWEETS:\n- Tweet 1\n- Tweet 2\n- Tweet 3\n\n"
                "LINKEDIN:\n- LinkedIn Post 1\n- LinkedIn Post 2\n\n"
                "INSTAGRAM:\n- Caption 1\n- Caption 2\n- Caption 3\n"
            )
        return "Generic response. Provide a local LLM for better results."


