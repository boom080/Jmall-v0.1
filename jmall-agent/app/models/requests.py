from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


SUPPORTED_TONES = {"professional", "marketing", "warm", "concise"}


class ProductCopyRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120, description="商品标题")
    category: str = Field("未分类", max_length=60, description="商品分类")
    sellingPoints: List[str] = Field(default_factory=list, description="商品卖点")
    tone: str = Field("professional", description="文案风格")
    modelProvider: Optional[str] = Field(default=None, max_length=32, description="模型提供方")
    modelName: Optional[str] = Field(default=None, max_length=120, description="模型名")
    knowledgeBaseId: Optional[str] = Field(default=None, max_length=64, description="知识库 ID")

    @field_validator("title", "category", "tone", "modelProvider", "modelName", "knowledgeBaseId", mode="before")
    @classmethod
    def normalize_text_fields(cls, value):
        if value is None:
            return value
        normalized = str(value).strip()
        return normalized

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if value is None:
            raise ValueError("title 不能为空")
        normalized = value.strip()
        if not normalized:
            raise ValueError("title 不能为空")
        return normalized

    @field_validator("category")
    @classmethod
    def validate_category(cls, value):
        if value is None:
            return "未分类"
        normalized = value.strip()
        return normalized or "未分类"

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, value):
        normalized = (value or "professional").lower()
        if normalized not in SUPPORTED_TONES:
            raise ValueError("tone 仅支持 professional、marketing、warm、concise")
        return normalized

    @field_validator("modelProvider")
    @classmethod
    def validate_model_provider(cls, value):
        return value or None

    @field_validator("modelName")
    @classmethod
    def validate_model_name(cls, value):
        return value or None

    @field_validator("knowledgeBaseId")
    @classmethod
    def validate_knowledge_base_id(cls, value):
        return value or None

    @field_validator("sellingPoints", mode="before")
    @classmethod
    def normalize_selling_points(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("sellingPoints 必须是数组")

        normalized = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if not text:
                continue
            if len(text) > 30:
                raise ValueError("sellingPoints 单条最多 30 个字符")
            normalized.append(text)

        if len(normalized) > 6:
            raise ValueError("sellingPoints 最多允许 6 条")

        return normalized


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="知识库名称")
    description: Optional[str] = Field(default="", max_length=240, description="知识库说明")

    @field_validator("name", "description", mode="before")
    @classmethod
    def normalize_knowledge_base_fields(cls, value):
        if value is None:
            return value
        return str(value).strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value or not value.strip():
            raise ValueError("name 不能为空")
        return value.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        return (value or "").strip()


class KnowledgeDocumentTextImportRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120, description="文档标题")
    content: str = Field(..., min_length=1, max_length=8000, description="文本文档内容")

    @field_validator("title", "content", mode="before")
    @classmethod
    def normalize_document_fields(cls, value):
        if value is None:
            return value
        return str(value).strip()

    @field_validator("title")
    @classmethod
    def validate_document_title(cls, value):
        if not value or not value.strip():
            raise ValueError("title 不能为空")
        return value.strip()

    @field_validator("content")
    @classmethod
    def validate_document_content(cls, value):
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("content 不能为空")
        return normalized
