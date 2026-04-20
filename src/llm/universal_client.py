"""
Universal LLM Client for Career-Ops
Supports: OpenAI, Anthropic, Ollama, Local LLMs, Custom APIs
"""

import os
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request"""
        pass
    
    @abstractmethod
    def stream(self, messages: List[Dict], **kwargs):
        """Stream chat completion"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI and OpenAI-compatible APIs (LM Studio, vLLM, etc.)"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
        # If no model specified, try to get from API
        if model is None:
            model = self._get_default_model()
        
        self.model = model
    
    def _get_default_model(self) -> str:
        """Get default model from API /models endpoint"""
        try:
            models = self.client.models.list()
            if models.data and len(models.data) > 0:
                # Return the first available model
                model_name = models.data[0].id
                print(f"🔍 Auto-detected model: {model_name}")
                return model_name
            else:
                print("⚠️  No models found, using default: gpt-3.5-turbo")
                return "gpt-3.5-turbo"
        except Exception as e:
            print(f"⚠️  Could not fetch models ({e}), using default: gpt-3.5-turbo")
            return "gpt-3.5-turbo"
    
    def list_available_models(self) -> list:
        """List all available models from the API"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            print(f"⚠️  Could not fetch models: {e}")
            return []
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    def stream(self, messages: List[Dict], **kwargs):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        # Convert OpenAI format to Anthropic format
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]
        
        response = self.client.messages.create(
            model=self.model,
            system=system_msg,
            messages=user_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            **{k: v for k, v in kwargs.items() if k != "max_tokens"}
        )
        return response.content[0].text
    
    def stream(self, messages: List[Dict], **kwargs):
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]
        
        with self.client.messages.stream(
            model=self.model,
            system=system_msg,
            messages=user_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
        ) as stream:
            for text in stream.text_stream:
                yield text


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        import requests
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
        )
        return response.json()["message"]["content"]
    
    def stream(self, messages: List[Dict], **kwargs):
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                **kwargs
            },
            stream=True
        )
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]


class UniversalLLMClient:
    """Universal client that works with any LLM provider"""
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Initialize with provider name and config
        
        Args:
            provider_name: "openai", "anthropic", "ollama", "custom"
            config: Provider-specific configuration
        """
        self.provider_name = provider_name
        self.config = config
        self.provider = self._init_provider()
    
    def _init_provider(self) -> LLMProvider:
        """Initialize the appropriate provider"""
        if self.provider_name == "openai":
            return OpenAIProvider(
                api_key=self.config.get("api_key", os.getenv("OPENAI_API_KEY", "dummy")),
                base_url=self.config.get("base_url", "https://api.openai.com/v1"),
                model=self.config.get("model")  # None = auto-detect
            )
        elif self.provider_name == "anthropic":
            return AnthropicProvider(
                api_key=self.config.get("api_key", os.getenv("ANTHROPIC_API_KEY")),
                model=self.config.get("model", "claude-3-5-sonnet-20241022")
            )
        elif self.provider_name == "ollama":
            return OllamaProvider(
                base_url=self.config.get("base_url", "http://localhost:11434"),
                model=self.config.get("model", "llama3.1")
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider_name}")
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request"""
        return self.provider.chat(messages, **kwargs)
    
    def stream(self, messages: List[Dict], **kwargs):
        """Stream chat completion"""
        return self.provider.stream(messages, **kwargs)
    
    def get_model_name(self) -> str:
        """Get the current model name"""
        return getattr(self.provider, 'model', 'unknown')
    
    def list_available_models(self) -> list:
        """List all available models (if supported by provider)"""
        if hasattr(self.provider, 'list_available_models'):
            return self.provider.list_available_models()
        return []


def create_llm_client(provider: str = None, **config) -> UniversalLLMClient:
    """
    Create LLM client from config
    
    Examples:
        # OpenAI
        client = create_llm_client("openai", api_key="sk-...", model="gpt-4o")
        
        # Ollama (local)
        client = create_llm_client("ollama", model="llama3.1:70b")
        
        # Anthropic
        client = create_llm_client("anthropic", api_key="sk-ant-...")
        
        # Custom OpenAI-compatible (like your Qwen setup)
        client = create_llm_client("openai", 
            base_url="http://127.0.0.1:1337/v1",
            api_key="dummy",
            model="Qwen3.6-35B-A3B-UD-Q4_K_S.gguf"
        )
    """
    if provider is None:
        # Auto-detect from environment
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            provider = "ollama"  # Default to local
    
    return UniversalLLMClient(provider, config)


def create_from_config_file(config_path: str = "config.yaml") -> UniversalLLMClient:
    """Create LLM client from config.yaml file"""
    import yaml
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    api_config = config.get("api", {})
    
    # Determine provider based on base_url
    base_url = api_config.get("base_url", "")
    if "anthropic" in base_url:
        provider = "anthropic"
    elif "localhost" in base_url or "127.0.0.1" in base_url:
        provider = "openai"  # Local OpenAI-compatible
    elif "openai" in base_url:
        provider = "openai"
    else:
        provider = "openai"  # Default
    
    return create_llm_client(
        provider=provider,
        api_key=api_config.get("api_key", "dummy"),
        base_url=api_config.get("base_url"),
        model=api_config.get("model")
    )
