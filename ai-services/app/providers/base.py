from abc import ABC, abstractmethod
from typing import Dict, List


class ProductCopyProvider(ABC):
    provider_name: str
    mock: bool = False

    @abstractmethod
    def generate_product_copy(
        self,
        title: str,
        category: str,
        selling_points: List[str],
        tone: str,
        prompt_context: str,
        model_name: str,
        metadata: Dict[str, str],
    ) -> Dict[str, object]:
        raise NotImplementedError
