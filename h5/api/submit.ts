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

const TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal';

// 请求超时时间（毫秒）
const FETCH_TIMEOUT = 10_000;
// 请求体最大大小（字节）
const MAX_BODY_SIZE = 10_000;

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
// ---------------------------------------------------------------------------
function buildFields(body: {
  vehicle_id: string;
  content_raw: string;
  category?: string;
  contact_name?: string;
  contact_phone?: string;
  contact_allowed?: boolean;
  location_detail?: string;
}): Record<string, unknown> {
  const fields: Record<string, unknown> = {
    channel: '车身扫码',
    vehicle_id: body.vehicle_id,
    content_raw: body.content_raw,
    status: '待处理',
  };

  if (body.category) fields.category = body.category;
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
    log('info', '提交成功', { record_id: recordId, elapsed_ms: elapsed });

    return json({
      ticket_id: recordId,
      category: body.category || '待AI识别',
      priority: '待AI判定',
      summary:
        body.content_raw.length > 30
          ? body.content_raw.slice(0, 28) + '...'
          : body.content_raw,
      estimated_response_time: '待系统分配',
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