export type FeedbackCategory = '安全' | '故障' | '体验' | '投诉' | '建议';
export type FeedbackPriority = 'P0' | 'P1' | 'P2' | 'P3';

/**
 * 工单渠道枚举（唯一 SSOT = AGENTS.md Schema 英文值）
 * 此类型贯穿前后端，写入飞书多维表格时直接用，无需再做中文→英文转换
 */
export type FeedbackChannel =
  | 'scan_qr'        // 车身扫码
  | 'hotline'        // 客服电话
  | 'wechat_group'   // 微信群
  | 'didi_review'    // 滴滴评价
  | 'social_media'   // 社媒舆情
  | 'telemetry'      // 车端告警
  | 'manual';        // 人工录入

/**
 * contact_allowed 的合法值（Schema 单选枚举，必须是字符串，严禁 boolean）
 * - '' 空串 = 用户未表态（checkbox 未勾选时写入）
 * - '是' = 允许工作人员联系
 * - '否' = 不希望被打扰
 */
export type ContactAllowed = '是' | '否' | '';

export interface FeedbackSubmitData {
  vehicle_id: string;
  content_raw: string;
  category?: FeedbackCategory;
  contact_name?: string;
  contact_phone?: string;
  /** 联系意愿，必须是字符串三态，传 boolean 会在编译期报错 */
  contact_allowed?: ContactAllowed;
  location_detail?: string;
  city?: string;             // 从二维码 payload 透传的城市
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
// ======================================================

/** 渠道英文枚举 → 前端中文展示标签 */
export const CHANNEL_LABEL: Record<FeedbackChannel, string> = {
  scan_qr: '车身扫码',
  hotline: '客服电话',
  wechat_group: '微信群',
  didi_review: '滴滴评价',
  social_media: '社媒舆情',
  telemetry: '车端告警',
  manual: '人工录入',
};

/** （兼容旧代码保留）中文展示名 → Schema 英文值，新代码请直接用 FeedbackChannel 英文枚举 */
export const CHANNEL_MAP: Record<string, FeedbackChannel> = {
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
