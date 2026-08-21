#!/usr/bin/env python3
"""Idempotently seed a source-traceable professional Jmall knowledge base."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


KNOWLEDGE_BASE_NAME = "Jmall 专业经营知识库"
KNOWLEDGE_BASE_DESCRIPTION = "来自市场监管法规、国家标准与电商实务的可追溯专业资料；用于商品详情生成和合规核对。"

DOCUMENTS = [
    {
        "title": "电商商品信息披露与消费者知情权",
        "source": "https://www.samr.gov.cn/wljys/gzzd/art/2023/art_09c394cce74f424a8d82dbc4811a11ec.html",
        "body": """
专业用途：指导商品详情页的信息完整性与事实边界。

核心原则：
1. 商品或服务信息应全面、真实、准确、及时，避免遗漏影响消费者选择的重要内容。
2. 商品详情应围绕品名、价格、规格、用途、性能、生产者或经营主体、售后服务等可核验信息组织。
3. 直播、社交内容与普通商品页一样，需要清楚展示实际经营主体和售后信息或有效链接。
4. 商品事实、市场趋势、平台热词必须分开。市场热度不能自动转化为当前商品的销量、材质、功效或认证。

Jmall 回填模板：
【商品概览】说明商品是什么、解决什么需求。
【核心亮点】只提炼商家已填写或有证据支持的特点。
【规格参数】按型号、尺寸、材质、容量、数量、适用范围等字段列出。
【适用场景】描述真实用途，不能虚构体验。
【购买前核对】提示颜色、尺寸、包装、售后等需要确认的事项。

审核清单：商品标题与实物一致；描述中每个数字都有来源；认证、授权、销量、排名能够举证；缺失字段明确标记待商家确认。
""",
    },
    {
        "title": "互联网广告与营销文案合规手册",
        "source": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_d93a579afd45413e8576e4623fab348f.html",
        "body": """
专业用途：审核商品标题、促销文案、种草内容和广告素材。

内容边界：
1. 直接或间接推销商品的文字、图片、音视频都可能属于互联网广告活动，应保留广告主、素材和审核记录。
2. 不生成无法证明的绝对化表达，如最好、第一、唯一、百分之百、永久有效。
3. 销量、市场占有率、用户评价、检测结论、认证和奖项属于需要证据的事实信息；没有依据就不写。
4. 种草风可以改变语气和结构，但不得伪造亲身购买、试用、朋友推荐或用户口碑。
5. 医疗、保健食品、特殊医学用途食品、医疗器械等品类需要更严格的资质和广告审查，不应使用通用模板直接发布。

安全改写方法：把“全网第一”改为具体可核验参数；把“人人都适合”改为商家已确认的适用范围；把“限时最低价”改为实际活动名称、期限、到手价条件；无法核实时使用“请商家确认”并阻止自动发布。
""",
    },
    {
        "title": "互联网平台价格与促销展示规范",
        "source": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/jjjzs/art/2025/art_eef66659c9624c5091bd3acd050b1710.html",
        "body": """
专业用途：生成价格展示、优惠说明和促销活动文案时使用。

价格信息结构：
1. 明确当前销售价格、计价单位、规格数量和适用条件。
2. 划线价、参考价、活动价、会员价、优惠券后价格应说明含义及使用条件，不能制造虚假比较价格。
3. 优惠活动需写明有效期、适用商品、门槛、数量限制、叠加规则和退款口径。
4. 不得通过虚假提高数量、等级、时长等方式变相调整价格；不要先提价后打折或虚构原价。
5. AI 只能把已确认的价格事实组织成清晰文案，不能根据市场区间自行承诺成交价或优惠。

推荐详情字段：销售价；计价单位；规格/数量；优惠条件；活动期限；库存限制；运费；退款后优惠处理。任何未提供字段应显示“待商家确认”，而不是自动补数字。
""",
    },
    {
        "title": "服装与纺织品商品详情字段指南",
        "source": "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=E143935EB536F1260D189F833BA98302&refer=outter",
        "body": """
专业用途：依据现行推荐性国家标准 GB/T 5296.4-2012 的使用说明方向，完善服饰鞋包类商品资料。

建议采集字段：产品名称；号型或规格；纤维成分及含量；维护/洗涤方法；执行标准；安全类别；制造者或经销者信息；产地；颜色；款式；适用季节；包装数量。

详情页写法：
【版型与设计】只描述可从商家资料确认的剪裁、领型、袖型、口袋、开合方式。
【面料信息】成分和含量必须来自标签或检测资料，不得由图片推断“纯棉”“羊毛”等材质。
【尺码信息】用尺码表呈现胸围、衣长、肩宽等实测数据，并说明测量方法和合理误差。
【洗护提示】按吊牌或商家确认信息填写，不自动生成可机洗、可烘干等结论。
【色差提示】可以提示显示设备与光线差异，但不能借此掩盖商品不一致。

风险词：不起球、不褪色、绝对保暖、人人适合、官方联名、限量版。出现时需要相应检测、授权或发行依据。
""",
    },
    {
        "title": "家用电器商品说明与参数模板",
        "source": "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=B4DFF317C010BF87A23D5EA109D2CE5D",
        "body": """
专业用途：参考现行推荐性国家标准 GB/T 5296.2-2008 的产品使用说明方向，组织家用和类似用途电器详情。

建议采集字段：产品名称与型号；额定电压、频率和功率；容量或关键尺寸；功能模式；控制方式；随机附件；安装条件；使用步骤；清洁维护；安全警示；执行标准；生产者信息；保修及售后政策。

专业详情结构：先说明产品用途，再列关键参数，然后写安装与使用场景，最后给出安全、清洁和售后提示。功率、能效、噪声、容量、温度、续航、保修期等数字必须来自铭牌、说明书、检测资料或商家确认信息。

禁止自动推断：节能百分比、静音分贝、食品级材质、国家认证、终身保修、全屋适用、医疗或保健功效。市场调研只能用于发现消费者关注的参数，不能替代当前 SKU 的参数证据。
""",
    },
    {
        "title": "预包装食品标签与商品页字段指南",
        "source": "https://www.nhc.gov.cn/sps/c100088/202503/e8a432507f7d4f08a877e76a9b0578ce.shtml",
        "body": """
专业用途：根据国家卫生健康委发布的 GB 7718-2025 等食品安全国家标准信息，完善预包装食品商品资料。标准具体实施日期和适用版本应以官方文本及商品生产日期为准。

建议采集字段：食品真实属性名称；配料表；净含量和规格；生产者名称、地址及联系方式；生产日期和保质期；贮存条件；食品生产许可证编号；产品标准代号；营养标签；食用或冲调方法；过敏原提示；进口食品原产国或地区等。

电商页面原则：页面信息应与实物标签一致，不能根据同类商品知识自动补配料、营养数据、无添加、低糖、高蛋白等结论。图片中的原料示意不能造成对配料或成分的误解。组合装需清楚说明单件规格、数量和总净含量。

审核重点：食品名称是否反映真实属性；净含量与销售规格是否一致；保质期和贮存方式是否同时展示；营养、功效、特殊人群适用性是否有标签或法规依据；新旧标准衔接期是否选用了与当前产品相匹配的版本。
""",
    },
    {
        "title": "Jmall AI 商品详情生成与 RAG 使用规范",
        "source": "https://www.samr.gov.cn/zfjcj/tzgg/art/2023/art_615af9ed6bcd4974bf853dd2e02bc663.html",
        "body": """
专业用途：统一 Agent 将市场调研、知识库资料和商家事实写入表单的边界。

信息分层：
A 级为商家已输入或上传证明的商品事实，可直接改写进入标题、卖点、规格和详情。
B 级为知识库中的法规、标准和模板，只能指导结构、必填字段与风险检查。
C 级为实时市场调研，只能进入右侧市场面板，用于关键词和运营建议；不能当作当前商品属性。

生成步骤：
1. 锁定商品名称、品类、价格、原始描述和商家确认参数。
2. 检索知识库，找出该品类详情应包含的字段和合规提醒。
3. 生成不同平台语气的标题与卖点，但所有事实必须可追溯到 A 级信息。
4. 生成结构化长详情：商品概览、核心亮点、规格参数、适用人群与场景、购买前核对。
5. 对市场词、数字、认证、功效、销量、优惠和第一人称体验做二次隔离审查。
6. 信息不足时写入待确认项，不用知识库样例值填补当前商品。

质量标准：详情不能只是原描述复述；各区块内容不得完全重复；副标题需要概括一个主要价值；浏览卡片展示副标题和摘要；用户进入详情页后能看到完整分段信息。
""",
    },
]


def request_json(url: str, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:18080/api")
    args = parser.parse_args()
    root = args.base_url.rstrip("/")

    kb = request_json(
        f"{root}/merchant/knowledge-bases",
        method="POST",
        payload={"name": KNOWLEDGE_BASE_NAME, "description": KNOWLEDGE_BASE_DESCRIPTION},
    )
    knowledge_base_id = kb["id"]
    imported = []
    for document in DOCUMENTS:
        content = (
            f"资料标题：{document['title']}\n"
            f"来源：{document['source']}\n"
            f"来源类型：官方法规或国家标准\n\n"
            f"{document['body'].strip()}"
        )
        response = request_json(
            f"{root}/merchant/knowledge-bases/{knowledge_base_id}/documents/text",
            method="POST",
            payload={"title": document["title"], "content": content},
        )
        imported.append({
            "title": document["title"],
            "documentId": response.get("id"),
            "chunkCount": response.get("chunkCount", 0),
        })

    summary = request_json(f"{root}/merchant/knowledge-bases")
    current = next((item for item in summary if item.get("id") == knowledge_base_id), {})
    print(json.dumps({
        "knowledgeBaseId": knowledge_base_id,
        "label": current.get("label", KNOWLEDGE_BASE_NAME),
        "documentCount": current.get("documentCount"),
        "chunkCount": current.get("chunkCount"),
        "documents": imported,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        raise SystemExit(f"Knowledge service unavailable: {exc}") from exc
