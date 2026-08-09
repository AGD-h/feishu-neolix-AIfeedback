/**
 * submit.ts 单元测试（使用 Node.js 原生 test runner）
 *
 * 测试覆盖：
 * 1. 正常提交流程（鉴权 + 写入）
 * 2. 环境变量缺失
 * 3. 必填字段校验
 * 4. 飞书 API 返回错误码
 * 5. 飞书 API HTTP 错误
 * 6. 鉴权接口超时
 * 7. 写入接口超时
 * 8. CORS 预检请求
 * 9. 非 POST 请求拦截
 * 10. 请求体过大
 * 11. buildFields 字段映射
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';

// ---------------------------------------------------------------------------
// Mock fetch 全局函数
// ---------------------------------------------------------------------------
const originalFetch = globalThis.fetch;
let mockFetchCalls: Array<{ url: string; options: RequestInit }> = [];
let mockFetchResponses: Array<Response | Error> = [];

function setupMockFetch() {
  mockFetchCalls = [];
  mockFetchResponses = [];
  globalThis.fetch = (async (url: string, options: RequestInit) => {
    mockFetchCalls.push({ url, options });
    const response = mockFetchResponses.shift();
    if (response instanceof Error) throw response;
    return response as Response;
  }) as unknown as typeof fetch;
}

function restoreFetch() {
  globalThis.fetch = originalFetch;
}

// 辅助：创建模拟的 fetch 成功响应
function mockFetchOk(data: unknown) {
  mockFetchResponses.push({
    ok: true,
    status: 200,
    json: async () => data,
    headers: new Headers(),
  } as Response);
}

// 辅助：创建模拟的 fetch 错误响应
function mockFetchError(status: number, data: unknown) {
  mockFetchResponses.push({
    ok: false,
    status,
    json: async () => data,
    headers: new Headers(),
  } as Response);
}

// 辅助：创建模拟的 fetch 网络错误
function mockFetchNetworkError() {
  mockFetchResponses.push(new Error('fetch failed'));
}

// 辅助：创建模拟的 fetch 超时
function mockFetchTimeout() {
  mockFetchResponses.push(new DOMException('The operation was aborted', 'AbortError'));
}

// 辅助：创建标准请求
function createRequest(body: unknown, overrides: Partial<RequestInit> = {}): Request {
  return new Request('https://example.com/api/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    ...overrides,
  });
}

// ---------------------------------------------------------------------------
// 动态导入被测模块
// ---------------------------------------------------------------------------
async function loadHandler() {
  // 清除模块缓存
  const mod = await import('./submit.ts?' + Date.now());
  return mod.default;
}

// ---------------------------------------------------------------------------
// 测试套件
// ---------------------------------------------------------------------------
describe('submit.ts Serverless Function', () => {
  beforeEach(() => {
    setupMockFetch();
    process.env.FEISHU_APP_ID = 'test-app-id';
    process.env.FEISHU_APP_SECRET = 'test-app-secret';
    process.env.BITABLE_APP_TOKEN = 'test-app-token';
    process.env.BITABLE_TABLE_ID = 'test-table-id';
  });

  afterEach(() => {
    restoreFetch();
    delete process.env.FEISHU_APP_ID;
    delete process.env.FEISHU_APP_SECRET;
    delete process.env.BITABLE_APP_TOKEN;
    delete process.env.BITABLE_TABLE_ID;
  });

  // =========================================================================
  // 正常流程
  // =========================================================================
  describe('正常提交流程', () => {
    it('应该成功获取 token 并写入记录', async () => {
      mockFetchOk({ code: 0, msg: 'ok', tenant_access_token: 'mock-token-abc123' });
      mockFetchOk({
        code: 0,
        msg: 'ok',
        data: { record: { record_id: 'rec-test-001' } },
      });

      const handler = await loadHandler();
      const req = createRequest({
        vehicle_id: 'NX-001',
        content_raw: '柜门打不开，已经等了5分钟',
        category: '故障',
        contact_name: '张三',
        contact_phone: '13800000000',
        contact_allowed: true,
        location_detail: '3号门',
      });

      const resp = await handler(req);
      assert.strictEqual(resp.status, 200);
      const body = await resp.json();
      assert.strictEqual(body.ticket_id, 'rec-test-001');
      assert.strictEqual(body.status, '已受理');
      assert.strictEqual(body.category, '故障');

      // 验证调用次数
      assert.strictEqual(mockFetchCalls.length, 2);

      // 验证鉴权调用
      const authCall = mockFetchCalls[0];
      assert.ok(authCall.url.includes('/auth/v3/tenant_access_token/internal'));
      const authBody = JSON.parse(authCall.options.body as string);
      assert.strictEqual(authBody.app_id, 'test-app-id');

      // 验证写入调用
      const writeCall = mockFetchCalls[1];
      assert.ok(writeCall.url.includes('/bitable/v1/apps/test-app-token/tables/test-table-id/records'));
      const writeBody = JSON.parse(writeCall.options.body as string);
      assert.strictEqual(writeBody.fields.vehicle_id, 'NX-001');
      assert.strictEqual(writeBody.fields.channel, '车身扫码');
      assert.strictEqual(writeBody.fields.status, '待处理');
      assert.strictEqual(writeBody.fields.contact_allowed, '是');
    });

    it('只传必填字段时也能成功', async () => {
      mockFetchOk({ code: 0, msg: 'ok', tenant_access_token: 'mock-token' });
      mockFetchOk({ code: 0, msg: 'ok', data: { record: { record_id: 'rec-minimal' } } });

      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-002', content_raw: '测试' });

      const resp = await handler(req);
      assert.strictEqual(resp.status, 200);

      const writeBody = JSON.parse(mockFetchCalls[1].options.body as string);
      assert.strictEqual(writeBody.fields.category, undefined);
      assert.strictEqual(writeBody.fields.contact_name, undefined);
    });

    it('contact_allowed=false 时字段值为"否"', async () => {
      mockFetchOk({ code: 0, msg: 'ok', tenant_access_token: 'mock-token' });
      mockFetchOk({ code: 0, msg: 'ok', data: { record: { record_id: 'rec-003' } } });

      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-003', content_raw: '测试', contact_allowed: false });

      await handler(req);
      const writeBody = JSON.parse(mockFetchCalls[1].options.body as string);
      assert.strictEqual(writeBody.fields.contact_allowed, '否');
    });
  });

  // =========================================================================
  // 环境变量缺失
  // =========================================================================
  describe('环境变量校验', () => {
    it('缺少 BITABLE_APP_TOKEN 时应返回 500', async () => {
      delete process.env.BITABLE_APP_TOKEN;
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 500);
      const body = await resp.json();
      assert.ok(body.error.includes('多维表格配置缺失'));
    });
  });

  // =========================================================================
  // 必填字段校验
  // =========================================================================
  describe('必填字段校验', () => {
    it('缺少 vehicle_id 时应返回 400', async () => {
      const handler = await loadHandler();
      const req = createRequest({ content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 400);
      const body = await resp.json();
      assert.ok(body.error.includes('vehicle_id'));
    });

    it('缺少 content_raw 时应返回 400', async () => {
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 400);
      const body = await resp.json();
      assert.ok(body.error.includes('content_raw'));
    });

    it('请求体为空时应返回 400', async () => {
      const handler = await loadHandler();
      const req = new Request('https://example.com/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'null',
      });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 400);
    });
  });

  // =========================================================================
  // 飞书 API 错误
  // =========================================================================
  describe('飞书 API 错误处理', () => {
    it('鉴权接口返回非 0 错误码时应返回 500', async () => {
      mockFetchOk({ code: 10001, msg: 'app_id 不存在', tenant_access_token: '' });
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 500);
      const body = await resp.json();
      assert.ok(body.error.includes('飞书鉴权失败'));
      assert.ok(body.error.includes('10001'));
    });

    it('鉴权接口 HTTP 500 错误时应返回 500', async () => {
      mockFetchError(500, { error: 'internal error' });
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 500);
      const body = await resp.json();
      assert.ok(body.error.includes('HTTP 500'));
    });

    it('写入接口返回非 0 错误码时应返回 500', async () => {
      mockFetchOk({ code: 0, msg: 'ok', tenant_access_token: 'mock-token' });
      mockFetchOk({ code: 91402, msg: '应用未被添加为多维表格协作者' });
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 500);
      const body = await resp.json();
      assert.ok(body.error.includes('飞书写入失败'));
      assert.ok(body.error.includes('91402'));
    });
  });

  // =========================================================================
  // 超时处理
  // =========================================================================
  describe('超时处理', () => {
    it('鉴权接口超时应返回 504', async () => {
      mockFetchTimeout();
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 504);
      const body = await resp.json();
      assert.ok(body.error.includes('超时'));
    });

    it('写入接口超时应返回 504', async () => {
      mockFetchOk({ code: 0, msg: 'ok', tenant_access_token: 'mock-token' });
      mockFetchTimeout();
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 504);
      const body = await resp.json();
      assert.ok(body.error.includes('超时'));
    });
  });

  // =========================================================================
  // HTTP 方法校验
  // =========================================================================
  describe('HTTP 方法校验', () => {
    it('OPTIONS 预检请求应返回 204', async () => {
      const handler = await loadHandler();
      const req = new Request('https://example.com/api/submit', { method: 'OPTIONS' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 204);
      assert.strictEqual(resp.headers.get('Access-Control-Allow-Origin'), '*');
    });

    it('GET 请求应返回 405', async () => {
      const handler = await loadHandler();
      const req = new Request('https://example.com/api/submit', { method: 'GET' });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 405);
      const body = await resp.json();
      assert.ok(body.error.includes('仅支持 POST'));
    });
  });

  // =========================================================================
  // 请求体大小限制
  // =========================================================================
  describe('请求体大小限制', () => {
    it('请求体超过 10KB 应返回 413', async () => {
      const handler = await loadHandler();
      const req = new Request('https://example.com/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': '10001' },
        body: JSON.stringify({ vehicle_id: 'NX-001', content_raw: 'x'.repeat(10001) }),
      });
      const resp = await handler(req);
      assert.strictEqual(resp.status, 413);
      const body = await resp.json();
      assert.ok(body.error.includes('过大'));
    });
  });

  // =========================================================================
  // 响应格式
  // =========================================================================
  describe('响应格式', () => {
    it('成功响应应包含所有必要字段', async () => {
      mockFetchOk({ code: 0, msg: 'ok', tenant_access_token: 'mock-token' });
      mockFetchOk({ code: 0, msg: 'ok', data: { record: { record_id: 'rec-format-test' } } });

      const handler = await loadHandler();
      const req = createRequest({
        vehicle_id: 'NX-001',
        content_raw: '这是一段很长的反馈内容，超过30个字符以测试摘要截断功能是否正常工作',
      });

      const resp = await handler(req);
      const body = await resp.json();

      assert.strictEqual(body.ticket_id, 'rec-format-test');
      assert.strictEqual(body.status, '已受理');
      assert.ok(body.hasOwnProperty('category'));
      assert.ok(body.hasOwnProperty('priority'));
      assert.ok(body.hasOwnProperty('summary'));
      assert.ok(body.hasOwnProperty('estimated_response_time'));
      assert.ok(body.summary.length <= 31);
      assert.ok(body.summary.includes('...'));
    });

    it('错误响应应包含 error 字段', async () => {
      mockFetchNetworkError();
      const handler = await loadHandler();
      const req = createRequest({ vehicle_id: 'NX-001', content_raw: 'test' });
      const resp = await handler(req);
      const body = await resp.json();
      assert.ok(body.hasOwnProperty('error'));
    });
  });
});