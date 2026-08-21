/**
 * Vercel Serverless Function — 飞书反馈提交接口
 *
 * 作用：H5 前端调用 /api/submit，此函数加上飞书 API 凭证后写入多维表格工单池。
 * 部署到 Vercel 后自动生效，密钥通过 Vercel 环境变量注入，不暴露到前端。
 *
 * 需要在 Vercel Dashboard 中配置的环境变量：
 *   FEISHU_APP_ID      — 飞书自建应用 App ID
 *   FEISHU_APP_SECRET  — 飞书自建应用 App Secret（绝不出现在前端）
 *   BITABLE_APP_TOKEN  — 多维表格 app_token
 *   BITABLE_TABLE_ID   — 工单表 table_id
 */

// 从 types.ts 导入枚举映射表和类型（唯一 SSOT：AGENTS.md）
import {
  CHANNEL_MAP,
  CATEGORY_PRIORITY_DEFAULT,
  PRIORITY_RESPONSE_TIME,
  type FeedbackCategory,
  type FeedbackSubmitData,
  type UserTier,
} from '../src/types';

const TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal';

// 请求超时时间（毫秒）
const FETCH_TIMEOUT = 10_000;
// 请求体最大大小（字节）
const MAX_BODY_SIZE = 10_000;

// ---------------------------------------------------------------------------
// 生成符合 Schema 的 feedback_id：FB-YYYYMMDD-序号
// 来源标识后缀：H=车身扫码（与 S=舆情/M=Mock 不重复）
// ---------------------------------------------------------------------------
function generateFeedbackId(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  const seq4 = String(Math.floor(Math.random() * 9000 + 1000)); // 4 位随机，够用
  return `FB-${y}${m}${d}-H${seq4}`; // H 前缀 = 扫码 H5 提交
}

// ---------------------------------------------------------------------------
// 带超时的 fetch 封装
// ---------------------------------------------------------------------------
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout = FETCH_TIMEOUT,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const resp = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return resp;
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// 获取飞书 tenant_access_token（有效期约 2 小时，每次请求都重新获取即可）
// ---------------------------------------------------------------------------
async function getTenantToken(): Promise<string> {
  const appId = process.env.FEISHU_APP_ID;
  const appSecret = process.env.FEISHU_APP_SECRET;

  if (!appId || !appSecret) {
    throw new Error('飞书应用凭证未配置（FEISHU_APP_ID / FEISHU_APP_SECRET）');
  }

  const resp = await fetchWithTimeout(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_id: appId, app_secret: appSecret }),
  });

  if (!resp.ok) {
    throw new Error(`飞书鉴权接口 HTTP ${resp.status}`);
  }

  const data = (await resp.json()) as { code: number; msg: string; tenant_access_token: string };
  if (data.code !== 0) {
    throw new Error(`飞书鉴权失败: [${data.code}] ${data.msg}`);
  }

  return data.tenant_access_token;
}

// ---------------------------------------------------------------------------
// 写入一条工单记录到多维表格
// ---------------------------------------------------------------------------
async function createRecord(
  appToken: string,
  tableId: string,
  token: string,
  fields: Record<string, unknown>,
): Promise<{ recordId: string }> {
  const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records`;

  const resp = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ fields }),
  });

  if (!resp.ok) {
    throw new Error(`飞书写入接口 HTTP ${resp.status}`);
  }

  const data = (await resp.json()) as {
    code: number;
    msg: string;
    data?: { record?: { record_id?: string } };
  };

  if (data.code !== 0) {
    throw new Error(`飞书写入失败: [${data.code}] ${data.msg}`);
  }

  return { recordId: data.data?.record?.record_id || 'unknown' };
}

// ---------------------------------------------------------------------------
// 构建飞书多维表格的字段对象（字段名需与多维表格列名一致）
// 严格按 AGENTS.md 工单 18 字段 Schema 顺序写入，不漏不增
// ---------------------------------------------------------------------------
function buildFields(body: FeedbackSubmitData): Record<string, unknown> {
  // priority 兜底：用户选了分类就按映射，未选默认 P2（体验级，不会误触发 P0）
  const category: FeedbackCategory | undefined = body.category;
  const priority = category ? CATEGORY_PRIORITY_DEFAULT[category] : 'P2';
  // user_tier 兜底：前端传了 hint 就用，否则"路人社区"（扫码场景最常见）
  const validHints: UserTier[] = ['网点经理', '快递员', 'RaaS商户', '收件人', '路人社区', '监管方'];
  const user_tier: UserTier =
    body.user_tier_hint && validHints.includes(body.user_tier_hint as UserTier)
      ? (body.user_tier_hint as UserTier)
      : '路人社区';
  // 当前时间：ISO 精确到分钟，与 Schema 和仿真数据 CSV 格式一致
  const now = new Date();
  const pad2 = (n: number) => String(n).padStart(2, '0');
  const created_at = `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())} ${pad2(now.getHours())}:${pad2(now.getMinutes())}`;

  // 先填 18 字段（按 Schema 严格顺序），再覆盖非空联系人字段
  const fields: Record<string, unknown> = {
    // ===== 18 字段 Schema 按顺序 =====
    feedback_id: generateFeedbackId(),   // 1. 符合 Schema：FB-YYYYMMDD-Hxxxx
    channel: CHANNEL_MAP['车身扫码'],    // 2. 统一英文 scan_qr，与仿真/舆情一致
    user_tier,                            // 3. 兜底路人社区
    category: category || '',             // 4. 用户勾选或空字符串
    priority,                             // 5. 按分类兜底，不会空
    status: '待处理',                     // 6. 枚举：待处理/处理中/待回访/已闭环
    vehicle_id: body.vehicle_id,          // 7. 必填
    city: body.city || '',                // 8. 问题4：二维码透传，空就给空串
    content_raw: body.content_raw,        // 9. 必填
    content_summary: '',                  // 10. AI 摘要，留空等飞书 AI 字段自动填
    created_at,                           // 11. 后端当前时间戳（精确到分钟）
    closed_at: '',                        // 12. 新工单未关闭，空串
    assigned_to: '',                      // 13. 未分派，走飞书自动化
    csat_score: '',                       // 14. 未回访，空
    contact_name: '',                     // 15. 默认空，下面有值再覆盖
    contact_phone: '',                    // 16. 默认空
    contact_allowed: '',                  // 17. ⚠️ 只能是 "是"/"否"/"" 三值（单选枚举）
    location_detail: '',                  // 18. 默认空
  };

  // ===== 联系人字段（有值才覆盖，空就保持空串）=====
  if (body.contact_name) fields.contact_name = body.contact_name;
  if (body.contact_phone) fields.contact_phone = body.contact_phone;
  if (body.contact_allowed !== undefined) {
    fields.contact_allowed = body.contact_allowed ? '是' : '否';
  }
  if (body.location_detail) fields.location_detail = body.location_detail;

  return fields;
}

// ---------------------------------------------------------------------------
// 响应辅助函数
// ---------------------------------------------------------------------------
function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

// ---------------------------------------------------------------------------
// 日志辅助：生产环境用 console，避免泄露敏感信息
// ---------------------------------------------------------------------------
function log(level: 'info' | 'error', message: string, extra?: Record<string, unknown>) {
  const ts = new Date().toISOString();
  const prefix = `[submit][${ts}]`;
  if (level === 'error') {
    console.error(prefix, message, extra ?? '');
  } else {
    console.log(prefix, message, extra ?? '');
  }
}

// ---------------------------------------------------------------------------
// Serverless Function 入口
// ---------------------------------------------------------------------------
export default async function handler(request: Request): Promise<Response> {
  // CORS 预检请求
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400',
      },
    });
  }

  if (request.method !== 'POST') {
    log('error', `不支持的请求方法: ${request.method}`);
    return json({ error: '仅支持 POST 请求' }, 405);
  }

  // 请求体大小限制
  const contentLength = parseInt(request.headers.get('content-length') || '0', 10);
  if (contentLength > MAX_BODY_SIZE) {
    log('error', `请求体过大: ${contentLength} bytes`);
    return json({ error: '请求体过大，请缩短反馈内容' }, 413);
  }

  const appToken = process.env.BITABLE_APP_TOKEN;
  const tableId = process.env.BITABLE_TABLE_ID;

  if (!appToken || !tableId) {
    log('error', '多维表格配置缺失');
    return json({ error: '多维表格配置缺失（BITABLE_APP_TOKEN / BITABLE_TABLE_ID）' }, 500);
  }

  const startTime = Date.now();

  try {
    const body = await request.json().catch(() => null);
    if (!body || !body.vehicle_id || !body.content_raw) {
      log('error', '缺少必填字段', { has_body: !!body, has_vehicle_id: !!body?.vehicle_id, has_content_raw: !!body?.content_raw });
      return json({ error: '缺少必填字段：vehicle_id 或 content_raw' }, 400);
    }

    log('info', '开始处理提交', {
      vehicle_id: body.vehicle_id,
      content_length: String(body.content_raw?.length ?? 0),
      category: body.category || '(未指定)',
      has_contact: !!(body.contact_name || body.contact_phone),
    });

    const token = await getTenantToken();
    const fields = buildFields(body);
    const { recordId } = await createRecord(appToken, tableId, token, fields);

    const elapsed = Date.now() - startTime;
    log('info', '提交成功', {
      record_id: recordId,
      feedback_id: fields.feedback_id,
      elapsed_ms: elapsed,
    });

    // category/priority/resp_time 与 buildFields 内用同一份逻辑，保证前后一致
    const category: FeedbackCategory = body.category || '体验';
    const priority = CATEGORY_PRIORITY_DEFAULT[category];
    const resp_time = PRIORITY_RESPONSE_TIME[priority];

    return json({
      ticket_id: String(fields.feedback_id),  // 用 Schema 格式的 FB-xxx-ID，与其他渠道统一
      category,                                // ✅ 严格是 FeedbackCategory 枚举值
      priority,                                // ✅ 严格是 P0-P3（问题3修）
      summary:
        body.content_raw.length > 30
          ? body.content_raw.slice(0, 28) + '...'
          : body.content_raw,
      estimated_response_time: resp_time,     // ✅ '5分钟内/30分钟内/1小时内/24小时内'
      status: '已受理',
    });
  } catch (err) {
    const elapsed = Date.now() - startTime;
    const message = err instanceof Error ? err.message : String(err);
    const isTimeout = err instanceof DOMException && err.name === 'AbortError';

    log('error', isTimeout ? '请求超时' : '服务器错误', {
      error: message,
      elapsed_ms: elapsed,
      is_timeout: isTimeout,
    });

    if (isTimeout) {
      return json({ error: '飞书API响应超时，请稍后重试' }, 504);
    }

    return json({ error: `服务器错误: ${message}` }, 500);
  }
}