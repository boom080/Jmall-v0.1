-- Local cleanup for fake/demo RAG data only.
-- Run manually after applying resource/db/5.6-rag-ingestion.sql.

delete from jrunmall_merchant_ai.knowledge_chunks
where knowledge_base_id in (
    'kb-product-baseline',
    'kb-appliance-style',
    'kb-f9bbace5a922',
    'kb-5386c067f305'
)
or knowledge_base_id in (
    select id
    from jrunmall_merchant_ai.knowledge_bases
    where source in ('fallback', 'file-fallback')
       or id in ('kb-product-baseline', 'kb-appliance-style', 'kb-f9bbace5a922', 'kb-5386c067f305')
       or coalesce(name, label, '') in (
            '商品基础知识库',
            '家电文案知识库',
            'Runbook KB 20260507131952',
            'Runbook KB 20260507132201'
       )
);

delete from jrunmall_merchant_ai.knowledge_documents
where knowledge_base_id in (
    select id
    from jrunmall_merchant_ai.knowledge_bases
    where source in ('fallback', 'file-fallback')
       or id in ('kb-product-baseline', 'kb-appliance-style', 'kb-f9bbace5a922', 'kb-5386c067f305')
       or coalesce(name, label, '') in (
            '商品基础知识库',
            '家电文案知识库',
            'Runbook KB 20260507131952',
            'Runbook KB 20260507132201'
       )
);

delete from jrunmall_merchant_ai.knowledge_bases
where source in ('fallback', 'file-fallback')
   or id in ('kb-product-baseline', 'kb-appliance-style', 'kb-f9bbace5a922', 'kb-5386c067f305')
   or coalesce(name, label, '') in (
        '商品基础知识库',
        '家电文案知识库',
        'Runbook KB 20260507131952',
        'Runbook KB 20260507132201'
   );
