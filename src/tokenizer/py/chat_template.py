import copy
import json
import os
import threading
from typing import Any, Optional

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
from transformers import AutoTokenizer  # lazy import，避免非必要依赖

class ChatTemplate:
    """
    通用 Chat Template 渲染器（对应单个 model_id）。

    支持：
    - 纯文本 token 计数
    - OpenAI 格式 messages（含 tool_calls）token 计数
    - 已渲染 prompt 字符串 token 计数

    Args:
        model_id (str): HuggingFace 模型 ID，如 "Qwen/Qwen3.5-397B-A17B"。
        hf_endpoint (str, optional): HuggingFace 镜像地址，默认读取环境变量
            HF_ENDPOINT，若未设置则使用 https://hf-mirror.com。
    """

    def __init__(self, model_id: str, hf_endpoint: Optional[str] = None):
        if hf_endpoint:
            os.environ["HF_ENDPOINT"] = hf_endpoint


        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

    def render_messages(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        add_generation_prompt: bool = False,
    ) -> str:
        """
        将 messages 渲染为模型专属的 prompt 字符串（不进行 tokenize）。

        Args:
            messages (list[dict]): OpenAI 格式的对话消息列表。
            tools (list[dict], optional): 工具定义列表。
            add_generation_prompt (bool): 是否在末尾添加 assistant 生成提示标记。

        Returns:
            str: 渲染后的 prompt 字符串。
        """
        messages = self._normalize_messages(messages)

        kwargs: dict[str, Any] = {
            "tokenize": False,
            "add_generation_prompt": add_generation_prompt,
        }
        if tools:
            kwargs["tools"] = tools

        return self.tokenizer.apply_chat_template(messages, **kwargs)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_messages(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        对 messages 做预处理：将 tool_calls.function.arguments 从 JSON
        字符串自动解析为字典（部分模型 chat template 要求 arguments 为 dict）。
        深拷贝，不修改原始数据。
        """
        normalized = copy.deepcopy(messages)
        for msg in normalized:
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                continue
            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                arguments = func.get("arguments")
                if isinstance(arguments, str):
                    try:
                        func["arguments"] = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass  # 保留原始字符串
        return normalized


    def __repr__(self) -> str:
        return f"ChatTemplate(model_id={self.model_id!r})"


# ----------------------------------------------------------------------
# 注册表：按 model_id 管理多个 ChatTemplate，同一模型只加载一次 tokenizer
# ----------------------------------------------------------------------

class ChatTemplateRegistry:
    """
    ChatTemplate 注册表，按 model_id 缓存 ChatTemplate 实例。

    同一 model_id 只会加载一次 tokenizer，线程安全。

    Args:
        hf_endpoint (str, optional): 全局 HuggingFace 镜像地址，创建新
            ChatTemplate 时使用。若单个 get() 调用也传入了 hf_endpoint，
            则以 get() 传入的为准。

    示例::

        registry = ChatTemplateRegistry()

        # 首次调用会下载/加载 tokenizer
        template_a = registry.get("Qwen/Qwen3.5-397B-A17B")
        template_b = registry.get("Qwen/Qwen3-8B")

        # 相同 model_id 直接命中缓存，不重复加载
        template_a2 = registry.get("Qwen/Qwen3.5-397B-A17B")
        assert template_a is template_a2

        print(registry.list_models())
        # ['Qwen/Qwen3.5-397B-A17B', 'Qwen/Qwen3-8B']
    """

    def __init__(self, hf_endpoint: Optional[str] = None):
        self._hf_endpoint = hf_endpoint
        self._templates: dict[str, ChatTemplate] = {}
        self._lock = threading.Lock()

    def get(
        self,
        model_id: str,
        hf_endpoint: Optional[str] = None,
    ) -> ChatTemplate:
        """
        获取指定 model_id 的 ChatTemplate，若不存在则自动创建并缓存。

        Args:
            model_id (str): HuggingFace 模型 ID。
            hf_endpoint (str, optional): 覆盖注册表级别的 hf_endpoint。

        Returns:
            ChatTemplate: 对应模型的 ChatTemplate 实例。
        """
        if model_id not in self._templates:
            with self._lock:
                if model_id not in self._templates:
                    endpoint = hf_endpoint or self._hf_endpoint
                    self._templates[model_id] = ChatTemplate(
                        model_id, hf_endpoint=endpoint
                    )
        return self._templates[model_id]

    def register(self, template: ChatTemplate) -> None:
        """
        手动注册一个已创建的 ChatTemplate 实例。

        Args:
            template (ChatTemplate): 要注册的 ChatTemplate 实例。
        """
        with self._lock:
            self._templates[template.model_id] = template

    def unregister(self, model_id: str) -> None:
        """
        从注册表中移除指定 model_id 的 ChatTemplate（释放 tokenizer 内存）。

        Args:
            model_id (str): 要移除的模型 ID。
        """
        with self._lock:
            self._templates.pop(model_id, None)

    def list_models(self) -> list[str]:
        """
        返回当前注册表中所有已缓存的 model_id 列表。

        Returns:
            list[str]: model_id 列表。
        """
        return list(self._templates.keys())

    def __contains__(self, model_id: str) -> bool:
        return model_id in self._templates

    def __repr__(self) -> str:
        models = ", ".join(self._templates.keys()) or "<empty>"
        return f"ChatTemplateRegistry(models=[{models}])"


# 全局单例注册表，可在整个进程中共享
global_registry = ChatTemplateRegistry()
