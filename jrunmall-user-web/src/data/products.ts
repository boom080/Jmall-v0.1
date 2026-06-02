import type { CatalogProduct } from '@/types/product'

const placeholder = '/placeholders/products/default-product.svg'

export const fallbackProducts: CatalogProduct[] = [
  {
    id: 101,
    title: 'Jrun Air 14 轻薄本',
    category: '电脑办公',
    subtitle: '移动办公优先的轻薄笔记本',
    sellingPoints: ['13代酷睿', '16GB 内存', '2.8K 高亮屏'],
    price: 5699,
    coverUrl: placeholder,
    imageUrls: [placeholder],
    summary: '移动办公优先的轻薄笔记本',
    detail: '适合日常办公、远程会议和差旅使用。',
    detailAttributes: ['屏幕：2.8K', '内存：16GB'],
  },
  {
    id: 102,
    title: 'Jrun Fit 智能手表',
    category: '智能穿戴',
    subtitle: '轻量续航与运动记录兼顾',
    sellingPoints: ['7 天续航', '全天心率', '50 米防水'],
    price: 899,
    coverUrl: placeholder,
    imageUrls: [placeholder],
    summary: '轻量续航与运动记录兼顾',
    detail: '适合通勤、健身和睡眠追踪的入门智能手表。',
    detailAttributes: ['续航：7天', '防水：50米'],
  },
  {
    id: 103,
    title: 'Jrun Sound 蓝牙耳机',
    category: '数码配件',
    subtitle: '更适合长时间佩戴的降噪耳机',
    sellingPoints: ['主动降噪', '双设备切换', '28 小时总续航'],
    price: 699,
    coverUrl: placeholder,
    imageUrls: [placeholder],
    summary: '更适合长时间佩戴的降噪耳机',
    detail: '满足办公室与通勤场景的日常听音需求。',
    detailAttributes: ['续航：28小时', '连接：双设备切换'],
  },
  {
    id: 104,
    title: 'Jrun Home 空气炸锅',
    category: '家用电器',
    subtitle: '适合小家庭的轻量厨房设备',
    sellingPoints: ['5L 容量', '触控菜单', '免翻面循环热风'],
    price: 399,
    coverUrl: placeholder,
    imageUrls: [placeholder],
    summary: '适合小家庭的轻量厨房设备',
    detail: '面向一到三人家庭的轻量厨房烹饪设备。',
    detailAttributes: ['容量：5L', '模式：触控菜单'],
  },
]


