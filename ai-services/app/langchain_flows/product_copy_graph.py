from typing import Any, Dict, List, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from app.core.config import Settings
from app.models.requests import ProductCopyRequest
from app.models.responses import ProductCopyResponse, RagUsedChunkResponse
from app.providers.factory import ProviderFactory
from app.repositories.request_log_repository import RequestLogRepository
from app.retrieval.service import RetrievalService


HIGH_RISK_FACTS = {
    "减少油烟": "请商家确认是否有“减少油烟”的检测依据或商品资料。",
    "永不粘锅": "请商家确认不粘性能依据；避免使用“永不粘锅”等绝对化表述。",
    "3-5人适用": "请商家确认适用人数是否为 3-5 人。",
    "3到5人适用": "请商家确认适用人数是否为 3-5 人。",
    "3至5人适用": "请商家确认适用人数是否为 3-5 人。",
    "导热均匀": "请商家确认是否有“导热均匀”的材质、结构或测试依据。",
    "耐用抗腐蚀": "请商家确认是否有“耐用抗腐蚀”的材质或测试依据。",
}

CONSERVATIVE_REPLACEMENTS = {
    "减少油烟": "请商家确认油烟表现",
    "永不粘锅": "请商家确认不粘性能",
    "3-5人适用": "请商家确认适用人数",
    "3到5人适用": "请商家确认适用人数",
    "3至5人适用": "请商家确认适用人数",
    "导热均匀": "请商家确认导热表现",
    "耐用抗腐蚀": "请商家确认耐用和抗腐蚀表现",
}


class ProductCopyGraphState(TypedDict, total=False):
    request: ProductCopyRequest
    provider_name: str
    model_name: str
    retrieved_chunks: List[Dict[str, Any]]
    prompt_context: str
    response_source: str
    result: ProductCopyResponse


class ProductCopyLangGraphFlow:
    def __init__(
        self,
        settings: Settings,
        provider_factory: ProviderFactory,
        retrieval_service: RetrievalService,
        request_log_repository: RequestLogRepository,
    ) -> None:
        self.settings = settings
        self.provider_factory = provider_factory
        self.retrieval_service = retrieval_service
        self.request_log_repository = request_log_repository
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(ProductCopyGraphState)
        graph.add_node("select_model", self._select_model)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("compose_prompt", self._compose_prompt)
        graph.add_node("generate_copy", self._generate_copy)
        graph.set_entry_point("select_model")
        graph.add_edge("select_model", "retrieve_context")
        graph.add_edge("retrieve_context", "compose_prompt")
        graph.add_edge("compose_prompt", "generate_copy")
        graph.add_edge("generate_copy", END)
        return graph.compile()

    def invoke(self, request: ProductCopyRequest) -> ProductCopyResponse:
        state = self.graph.invoke({"request": request})
        return state["result"]

    def _select_model(self, state: ProductCopyGraphState) -> ProductCopyGraphState:
        request = state["request"]
        provider_name = (request.modelProvider or self.settings.ai_provider or "mock").strip().lower()
        model_name = self.provider_factory.resolve_model_name(provider_name, request.modelName or "")
        return {"provider_name": provider_name, "model_name": model_name}

    def _retrieve_context(self, state: ProductCopyGraphState) -> ProductCopyGraphState:
        request = state["request"]
        query = self._build_retrieval_query(request)
        chunks = self.retrieval_service.retrieve(
            request.knowledgeBaseId,
            query,
            top_k=self.settings.rag_top_k or self.settings.ai_rag_top_k,
        )
        return {
            "retrieved_chunks": chunks,
            "response_source": "rag" if chunks else "no_rag_fallback",
        }

    def _compose_prompt(self, state: ProductCopyGraphState) -> ProductCopyGraphState:
        request = state["request"]
        chunks = state.get("retrieved_chunks", [])
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是 Jrunmall 商家端商品文案助手，需要基于证据资料输出结构稳定、可直接使用的中文电商文案。"),
                (
                    "human",
                    "{rag_context}\n\n【生成任务】\n"
                    "结合商品信息、目标人群、平台风格和以上知识库资料，生成：\n"
                    "1. 商品标题\n"
                    "2. 3-5 条短卖点\n"
                    "3. 详情页文案\n"
                    "4. 短视频口播文案\n"
                    "5. 合规风险提醒\n"
                    "6. 待商家确认信息\n\n"
                    "【事实约束】\n"
                    "- 商品输入中没有提供的信息，不要编造。\n"
                    "- 不要主动生成未提供的认证、销量、排名、保修、适用人数、材质等级。\n"
                    "- 如果信息不足，用“请商家确认……”表达。\n"
                    "- 可以根据类目做一般性文案组织，但不能把一般经验写成确定事实。\n"
                    "- RAG 资料只作为文案结构和写法参考，不代表当前商品一定具备其中所有特性。\n"
                    "- 如果出现减少油烟、永不粘锅、3-5人适用、导热均匀、耐用抗腐蚀等高风险表达，且商品输入没有证据，必须改成保守表达或放入待商家确认信息。\n\n"
                    "商品标题：{title}\n"
                    "商品分类：{category}\n"
                    "用户填写卖点：{selling_points}\n"
                    "平台/风格：{tone}",
                ),
            ]
        )
        prompt_value = prompt.format(
            rag_context=self._format_rag_context(chunks),
            title=request.title,
            category=request.category,
            selling_points="；".join(request.sellingPoints) or "无额外卖点",
            tone=request.tone,
        )
        return {"prompt_context": prompt_value}

    def _generate_copy(self, state: ProductCopyGraphState) -> ProductCopyGraphState:
        request = state["request"]
        provider_name = state["provider_name"]
        model_name = state["model_name"]
        prompt_context = state.get("prompt_context", "")
        response_source = state.get("response_source", "no_rag_fallback")
        retrieved_chunks = state.get("retrieved_chunks", [])
        provider = self.provider_factory.get_product_copy_provider(provider_name)

        self.request_log_repository.save(
            {
                "title": request.title,
                "provider": provider_name,
                "modelName": model_name,
                "knowledgeBaseId": request.knowledgeBaseId or "",
            }
        )

        try:
            payload = provider.generate_product_copy(
                title=request.title,
                category=request.category,
                selling_points=request.sellingPoints,
                tone=request.tone,
                prompt_context=prompt_context,
                model_name=model_name,
                metadata={
                    "knowledgeBaseId": request.knowledgeBaseId or "",
                    "response_source": response_source,
                },
            )
            return {"result": self._build_response(payload, request, response_source, retrieved_chunks)}
        except Exception as exc:
            fallback = self.provider_factory.get_product_copy_provider(self.settings.ai_fallback_provider)
            fallback_payload = fallback.generate_product_copy(
                title=request.title,
                category=request.category,
                selling_points=request.sellingPoints,
                tone=request.tone,
                prompt_context=prompt_context,
                model_name=self.provider_factory.resolve_model_name("mock", ""),
                metadata={"fallbackReason": str(exc), "response_source": response_source},
            )
            fallback_payload["success"] = False
            fallback_payload["message"] = f"AI provider 调用失败，已回退到 {self.settings.ai_fallback_provider}: {exc}"
            return {"result": self._build_response(fallback_payload, request, response_source, retrieved_chunks)}

    def _build_response(
        self,
        payload: Dict[str, Any],
        request: ProductCopyRequest,
        response_source: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> ProductCopyResponse:
        used_chunks = [RagUsedChunkResponse(**self._normalize_chunk(chunk)) for chunk in retrieved_chunks]
        self._apply_fact_guard(payload, request)
        payload["response_source"] = response_source
        payload["usedChunks"] = used_chunks
        payload["citations"] = used_chunks
        payload["embeddingProvider"] = self._embedding_provider(retrieved_chunks)
        return ProductCopyResponse(**payload)

    def _format_rag_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "【电商知识库参考资料】\n未命中指定知识库的 chunks。"
        lines = ["【电商知识库参考资料】"]
        for index, chunk in enumerate(chunks, start=1):
            lines.append(
                f"{index}. 来源：{chunk.get('sourceFilename') or '未命名来源'}\n"
                f"相关度：{float(chunk.get('score') or 0):.4f}\n"
                f"内容：{chunk.get('content', '')}"
            )
        return "\n\n".join(lines)

    def _build_retrieval_query(self, request: ProductCopyRequest) -> str:
        return " ".join(
            item
            for item in [request.title, request.category, request.tone, *list(request.sellingPoints)]
            if item and item.strip()
        )

    def _normalize_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "chunkId": str(chunk.get("chunkId", "")),
            "documentId": str(chunk.get("documentId", "")),
            "knowledgeBaseId": str(chunk.get("knowledgeBaseId", "")),
            "content": str(chunk.get("content", "")),
            "score": float(chunk.get("score") or 0.0),
            "sourceFilename": str(chunk.get("sourceFilename", "")),
            "chunkIndex": int(chunk.get("chunkIndex") or 0),
            "metadata": chunk.get("metadata") or {},
        }

    def _embedding_provider(self, chunks: List[Dict[str, Any]]) -> str:
        for chunk in chunks:
            provider = str(chunk.get("embeddingProvider") or "")
            if provider:
                return provider
        return ""

    def _apply_fact_guard(self, payload: Dict[str, Any], request: ProductCopyRequest) -> None:
        evidence = " ".join([request.title, request.category, *request.sellingPoints]).lower()
        pending = payload.get("pendingMerchantConfirmations") or []
        if not isinstance(pending, list):
            pending = [str(pending)]
        normalized_pending = [str(item).strip() for item in pending if str(item).strip()]

        for phrase, confirmation in HIGH_RISK_FACTS.items():
            if not self._payload_contains(payload, phrase):
                continue
            if phrase.lower() in evidence:
                continue
            self._replace_payload_phrase(payload, phrase, CONSERVATIVE_REPLACEMENTS[phrase])
            if confirmation not in normalized_pending:
                normalized_pending.append(confirmation)

        if len(request.sellingPoints) <= 3 and not normalized_pending:
            normalized_pending.append("请商家确认是否有认证、保修、适用人数、材质等级、价格活动等补充信息。")
        payload["pendingMerchantConfirmations"] = normalized_pending

    def _payload_contains(self, payload: Dict[str, Any], phrase: str) -> bool:
        values = [str(payload.get("generatedTitle") or ""), str(payload.get("summary") or "")]
        values.extend(str(item) for item in payload.get("highlights") or [])
        return any(phrase in value for value in values)

    def _replace_payload_phrase(self, payload: Dict[str, Any], phrase: str, replacement: str) -> None:
        payload["generatedTitle"] = str(payload.get("generatedTitle") or "").replace(phrase, replacement)
        payload["summary"] = str(payload.get("summary") or "").replace(phrase, replacement)
        highlights = payload.get("highlights") or []
        if isinstance(highlights, list):
            payload["highlights"] = [str(item).replace(phrase, replacement) for item in highlights]
