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
