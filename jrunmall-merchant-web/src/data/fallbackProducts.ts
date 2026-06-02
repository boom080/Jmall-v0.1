import type { MerchantOption, MerchantProduct } from '@/types/merchant'

const placeholder = '/placeholders/products/default-product.svg'

export const fallbackMerchantProducts: MerchantProduct[] = [
  {
    id: 201,
    title: 'Jrun Air 14 轻薄本',
    category: '电脑办公',
    price: 6299,
    sellingPoints: ['13代酷睿', '16GB 内存', '2.8K 高亮屏'],
    coverUrl: placeholder,
    status: 'ready',
  },
  {
    id: 202,
    title: 'Jrun Fit 智能手表',
    category: '智能穿戴',
    price: 899,
    sellingPoints: ['7 天续航', '全天心率', '50 米防水'],
    coverUrl: placeholder,
    status: 'ready',
  },
]

export const fallbackModels: MerchantOption[] = [
  {
    id: 'langchain4j-openai:deepseek-chat',
    label: 'DeepSeek / deepseek-chat',
    provider: 'langchain4j-openai',
    description: 'Java LangChain4j 直连 DeepSeek OpenAI-compatible 模型，请配置 JRUNMALL_AI_DEEPSEEK_API_KEY',
  },
  {
    id: 'langchain4j-openai:qwen3-max',
    label: 'Qwen / qwen3-max',
    provider: 'langchain4j-openai',
    description: 'Java LangChain4j 直连阿里云百炼 OpenAI-compatible 模型，请配置 JRUNMALL_AI_QWEN_API_KEY',
  },
  {
    id: 'langchain4j-openai:qwen3.6-plus',
    label: 'Qwen / qwen3.6-plus',
    provider: 'langchain4j-openai',
    description: 'Java LangChain4j 直连阿里云百炼 OpenAI-compatible 模型，请配置 JRUNMALL_AI_QWEN_API_KEY',
  },
  {
    id: 'mock:mock-product-copy-v1',
    label: 'Mock / mock-product-copy-v1',
    provider: 'mock',
    description: '本地联调默认模型',
  },
]

export const fallbackKnowledgeBases: MerchantOption[] = [
]


