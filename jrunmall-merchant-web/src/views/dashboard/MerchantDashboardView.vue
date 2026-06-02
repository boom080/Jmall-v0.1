<template>
  <section class="merchant-page-grid">
    <el-card shadow="never">
      <template #header>商家端可用流程</template>
      <p>建议按“商品管理 -> 新增或编辑商品 -> 选择模型/知识库 -> 生成文案 -> 回填商品”的顺序使用；普通订单和秒杀订单当前保持只读查看。</p>
    </el-card>
    <el-card shadow="never">
      <template #header>AI 链路</template>
      <p>商家端只通过 Java 正式接口调用后端 AI Adapter；LangChain4j 模型密钥只读取后端环境变量，前端不保存任何模型 API Key。</p>
    </el-card>
    <el-card shadow="never">
      <template #header>RAG 状态</template>
      <p>当前支持知识库新增、文本导入、PDF 导入、切块、embedding 与检索参与生成；从知识库页可直接带入新增商品表单。</p>
    </el-card>
  </section>
</template>


