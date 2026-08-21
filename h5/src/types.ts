export type FeedbackCategory = '安全' | '故障' | '体验' | '投诉' | '建议';
export type FeedbackPriority = 'P0' | 'P1' | 'P2' | 'P3';
export type FeedbackChannel = '车身扫码' | '客服电话' | '微信群' | '社媒舆情' | '滴滴评价' | '车端告警' | '人工录入';

export interface FeedbackSubmitData {
  vehicle_id: string;
  content_raw: string;
  category?: FeedbackCategory;
  contact_name?: string;
  contact_phone?: string;
  contact_allowed?: boolean;
  location_detail?: string;
  city?: string;             // 从二维码 payload 透传的城市（问题4同修）
  user_tier_hint?: string;   // 前端能识别时传（如扫码是收件人），不传兜底路人社区
}

export interface FeedbackResult {
  ticket_id: string;
  category: FeedbackCategory;
  priority: FeedbackPriority;
  summary: string;
  estimated_response_time: string;
  status: string;
}

export type AppPage = 'home' | 'form' | 'submitting' | 'result' | 'error';

export interface QRCodeData {
  vehicle_id: string;
  vehicle_model?: string;
  city?: string;
  location?: string;
}

// ======================================================
// 工单枚举映射表（唯一 SSOT：AGENTS.md 工单 Schema）
// 所有前后端写入飞书的枚举值必须经此表转换，保证中/英文一致
// ======================================================

/** 渠道枚举映射：前端中文展示 → AGENTS.md Schema 英文值（写入多维表格） */
export const CHANNEL_MAP: Record<FeedbackChannel, string> = {
  '车身扫码': 'scan_qr',
  '客服电话': 'hotline',
  '微信群':  'wechat_group',
  '社媒舆情': 'social_media',
  '滴滴评价': 'didi_review',
  '车端告警': 'telemetry',
  '人工录入': 'manual',
};

/** 优先级 → 预计响应时间（严格对应 AGENTS.md 定义） */
export const PRIORITY_RESPONSE_TIME: Record<FeedbackPriority, string> = {
  'P0': '5分钟内',
  'P1': '30分钟内',
  'P2': '1小时内',
  'P3': '24小时内',
};

/** 分类 → 优先级 默认映射（扫码场景兜底用，按 Schema 安全→P0 等比例） */
export const CATEGORY_PRIORITY_DEFAULT: Record<FeedbackCategory, FeedbackPriority> = {
  '安全': 'P0',
  '故障': 'P1',
  '投诉': 'P1',
  '体验': 'P2',
  '建议': 'P3',
};

/** user_tier 枚举（AGENTS.md 规定 6 类） */
export type UserTier = '网点经理' | '快递员' | 'RaaS商户' | '收件人' | '路人社区' | '监管方';
