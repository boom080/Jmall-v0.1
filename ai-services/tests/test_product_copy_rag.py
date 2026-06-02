from app.core.config import Settings
from app.langchain_flows.product_copy_graph import ProductCopyLangGraphFlow
from app.models.requests import ProductCopyRequest
from app.providers.factory import ProviderFactory
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.request_log_repository import RequestLogRepository
from app.retrieval.service import RetrievalService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService


class RiskyProductCopyProvider:
    provider_name = "risky"
    mock = False

    def generate_product_copy(
        self,
        title,
        category,
        selling_points,
        tone,
        prompt_context,
        model_name,
        metadata,
    ):
        return {
            "generatedTitle": f"爆款推荐 | {title} | 3-5人适用",
            "highlights": ["减少油烟", "永不粘锅", "导热均匀", "耐用抗腐蚀"],
            "summary": "详情页：3-5人适用，导热均匀，耐用抗腐蚀。合规风险提醒：注意绝对化表达。",
            "pendingMerchantConfirmations": [],
            "provider": model_name,
            "mock": False,
            "success": True,
            "message": "ok",
        }


class RiskyProviderFactory(ProviderFactory):
    def get_product_copy_provider(self, provider_name):
        if provider_name == "risky":
            return RiskyProductCopyProvider()
        return super().get_product_copy_provider(provider_name)


def build_stack(tmp_path, ai_provider="mock"):
    settings = Settings(
        ai_provider=ai_provider,
        merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"),
        rag_chunk_size=100,
        rag_top_k=3,
        _env_file=None,
    )
    repository = KnowledgeBaseRepository(settings)
    embedding_service = EmbeddingService(settings)
    knowledge_base_service = KnowledgeBaseService(repository, embedding_service, ChunkingService(settings))
    provider_factory = RiskyProviderFactory(settings) if ai_provider == "risky" else ProviderFactory(settings)
    flow = ProductCopyLangGraphFlow(
        settings=settings,
        provider_factory=provider_factory,
        retrieval_service=RetrievalService(settings, repository, embedding_service),
        request_log_repository=RequestLogRepository(),
    )
    return knowledge_base_service, flow


def test_product_copy_uses_rag_chunks_and_returns_citations(tmp_path):
    knowledge_base_service, flow = build_stack(tmp_path)
    created = knowledge_base_service.create_knowledge_base("手机知识库", "用于测试文本导入")
    knowledge_base_service.import_text_document(
        created.id,
        "新品手机卖点",
        "Jrun X1 主打 5000mAh 长续航、电池耐用与轻办公通勤场景。",
        source_type="txt",
        source_filename="phone.txt",
    )

    response = flow.invoke(
        ProductCopyRequest(
            title="Jrun X1",
            category="手机数码",
            sellingPoints=["轻办公", "长续航"],
            tone="professional",
            knowledgeBaseId=created.id,
        )
    )

    assert response.success is True
    assert response.response_source == "rag"
    assert response.usedChunks
    assert response.usedChunks[0].knowledgeBaseId == created.id
    assert "【电商知识库参考资料】" in response.summary


def test_product_copy_no_chunks_uses_no_rag_fallback(tmp_path):
    _, flow = build_stack(tmp_path)

    response = flow.invoke(
        ProductCopyRequest(
            title="静音破壁机",
            category="厨房电器",
            sellingPoints=["低噪音", "一键清洗"],
            tone="warm",
            knowledgeBaseId="kb-missing",
        )
    )

    assert response.response_source == "no_rag_fallback"
    assert response.usedChunks == []


def test_product_copy_provider_error_keeps_rag_metadata(tmp_path):
    knowledge_base_service, flow = build_stack(tmp_path)
    created = knowledge_base_service.create_knowledge_base("家电知识库", "")
    knowledge_base_service.import_text_document(
        created.id,
        "家电资料",
        "破壁机主打低噪音与一键清洗。",
        source_type="txt",
        source_filename="appliance.txt",
    )

    response = flow.invoke(
        ProductCopyRequest(
            title="静音破壁机",
            category="厨房电器",
            sellingPoints=["低噪音"],
            tone="warm",
            modelProvider="deepseek",
            modelName="deepseek-chat",
            knowledgeBaseId=created.id,
        )
    )

    assert response.success is False
    assert response.response_source == "rag"
    assert response.usedChunks


def test_sparse_product_input_does_not_invent_unprovided_facts(tmp_path):
    _, flow = build_stack(tmp_path)

    response = flow.invoke(
        ProductCopyRequest(
            title="不锈钢汤锅",
            category="厨房锅具",
            sellingPoints=["不锈钢锅体", "电磁炉适用", "易清洁"],
            tone="professional",
            knowledgeBaseId="kb-missing",
        )
    )

    text = " ".join([response.generatedTitle, response.summary, *response.highlights])
    assert "3-5人适用" not in text
    assert "永不粘锅" not in text
    assert "减少油烟" not in text
    assert "导热均匀" not in text
    assert "耐用抗腐蚀" not in text
    assert "合规风险提醒" in response.summary
    assert response.pendingMerchantConfirmations
    assert any("请商家确认" in item for item in response.pendingMerchantConfirmations)


def test_rag_structure_examples_are_not_current_product_facts(tmp_path):
    knowledge_base_service, flow = build_stack(tmp_path)
    created = knowledge_base_service.create_knowledge_base("锅具写法知识库", "只提供写法结构")
    knowledge_base_service.import_text_document(
        created.id,
        "锅具示例文案",
        "示例写法：标题可突出锅具场景，卖点示例包含 3-5人适用、导热均匀、耐用抗腐蚀、减少油烟。",
        source_type="txt",
        source_filename="pot-example.txt",
    )

    response = flow.invoke(
        ProductCopyRequest(
            title="不锈钢汤锅",
            category="厨房锅具",
            sellingPoints=["不锈钢锅体", "电磁炉适用", "易清洁"],
            tone="professional",
            knowledgeBaseId=created.id,
        )
    )

    text = " ".join([response.generatedTitle, response.summary, *response.highlights])
    assert response.response_source == "rag"
    assert response.usedChunks
    assert "不将知识库示例参数直接作为当前商品事实" in response.summary
    assert "3-5人适用" not in text
    assert "减少油烟" not in text
    assert "导热均匀" not in text
    assert "耐用抗腐蚀" not in text


def test_high_risk_generated_claims_are_converted_to_pending_confirmation(tmp_path):
    _, flow = build_stack(tmp_path, ai_provider="risky")

    response = flow.invoke(
        ProductCopyRequest(
            title="不锈钢汤锅",
            category="厨房锅具",
            sellingPoints=["不锈钢锅体", "电磁炉适用", "易清洁"],
            tone="professional",
        )
    )

    text = " ".join([response.generatedTitle, response.summary, *response.highlights])
    assert "3-5人适用" not in text
    assert "永不粘锅" not in text
    assert "减少油烟" not in text
    assert "导热均匀" not in text
    assert "耐用抗腐蚀" not in text
    assert "请商家确认适用人数" in text
    assert len(response.pendingMerchantConfirmations) >= 5
    assert any("减少油烟" in item for item in response.pendingMerchantConfirmations)
