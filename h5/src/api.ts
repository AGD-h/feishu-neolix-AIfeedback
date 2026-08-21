import type { FeedbackSubmitData, FeedbackResult } from './types';
// 与 submit.ts 共用同一份枚举映射常量（唯一 SSOT：AGENTS.md Schema）
import { CATEGORY_PRIORITY_DEFAULT, PRIORITY_RESPONSE_TIME } from './types';
import { logger } from './utils/logger';

const FEISHU_API_BASE = import.meta.env.VITE_FEISHU_API_BASE || '';
const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true';
const REQUEST_TIMEOUT = 15_000; // 15秒超时

export type MockMode = 'success' | 'network_error' | 'server_error' | 'timeout';

let _mockMode: MockMode = (() => {
  const params = new URLSearchParams(window.location.search);
  const m = params.get('mock');
  if (m === 'fail' || m === 'network' || m === 'network_error') return 'network_error';
  if (m === 'server' || m === 'server_error' || m === '500') return 'server_error';
  if (m === 'timeout') return 'timeout';
  return 'success';
})();

export function setMockMode(mode: MockMode) {
  _mockMode = mode;
  logger.warn('Mock', `🔧 模拟模式已切换为: ${mode}`, { mode });
}

export function getMockMode(): MockMode {
  return _mockMode;
}

if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).__setMockMode = setMockMode;
  (window as unknown as Record<string, unknown>).__getMockMode = getMockMode;
}

export async function submitFeedback(data: FeedbackSubmitData): Promise<FeedbackResult> {
  logger.info('API', '准备提交反馈数据', {
    vehicle_id: data.vehicle_id,
    content_length: data.content_raw.length,
    category: data.category || '(AI自动识别)',
    has_contact: !!data.contact_phone,
  });

  if (!USE_REAL_API) {
    logger.warn('API', '⚠️ USE_REAL_API 未开启，使用本地模拟AI分析模式（不会发送到真实后端）');

    if (_mockMode === 'network_error') {
      logger.info('API', `🧪 [模拟模式] 模拟网络错误...`);
      const t0 = performance.now();
      await new Promise(resolve => setTimeout(resolve, 1200));
      const elapsed = Math.round(performance.now() - t0);
      logger.error('API', `❌ [模拟] 网络连接失败（${elapsed}ms）`, 'NetworkError: Failed to fetch');
      throw new Error('网络连接失败，请检查网络设置后重试');
    }

    if (_mockMode === 'server_error') {
      logger.info('API', `🧪 [模拟模式] 模拟服务器500错误...`);
      const t0 = performance.now();
      await new Promise(resolve => setTimeout(resolve, 1500));
      const elapsed = Math.round(performance.now() - t0);
      logger.error('API', `❌ [模拟] 服务器内部错误 HTTP 500（${elapsed}ms）`);
      throw new Error('服务器异常（HTTP 500），请稍后重试或联系管理员');
    }

    if (_mockMode === 'timeout') {
      logger.info('API', `🧪 [模拟模式] 模拟请求超时...`);
      const t0 = performance.now();
      await new Promise(resolve => setTimeout(resolve, 8000));
      const elapsed = Math.round(performance.now() - t0);
      logger.error('API', `❌ [模拟] 请求超时（${elapsed}ms）`, 'AbortError: The operation timed out');
      throw new Error('请求超时，请检查网络信号后重试');
    }

    logger.info('API', `模拟网络延迟 2500ms...`);
    const t0 = performance.now();
    await new Promise(resolve => setTimeout(resolve, 2500));
    const elapsed = Math.round(performance.now() - t0);
    logger.info('API', `模拟延迟结束（${elapsed}ms），开始本地AI分类...`);
    const result = simulateAIAnalysis(data);
    logger.success('API', '✅ 本地模拟提交成功', result);
    return result;
  }

  const apiUrl = `${FEISHU_API_BASE}/api/submit`;
  logger.info('API', `📡 发送请求到 ${apiUrl}`);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  const t0 = performance.now();
  try {
    const resp = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const elapsed = Math.round(performance.now() - t0);
    logger.info('API', `响应状态: HTTP ${resp.status}（耗时 ${elapsed}ms）`);

    if (!resp.ok) {
      const errorText = await resp.text().catch(() => '无法读取错误详情');
      logger.error('API', `❌ 请求失败: HTTP ${resp.status}`, errorText.slice(0, 200));
      if (resp.status === 504) {
        throw new Error('服务器响应超时，请稍后重试');
      }
      if (resp.status >= 500) {
        throw new Error('服务器异常，请稍后重试或联系管理员');
      }
      throw new Error(`提交失败: HTTP ${resp.status}`);
    }

    const result = await resp.json();
    logger.success('API', '✅ 后端返回成功', result);
    return result;
  } catch (err) {
    clearTimeout(timeoutId);
    const elapsed = Math.round(performance.now() - t0);

    if (err instanceof DOMException && err.name === 'AbortError') {
      logger.error('API', `⏱️ 请求超时（${elapsed}ms，超过 ${REQUEST_TIMEOUT / 1000}s）`);
      throw new Error('请求超时，请检查网络信号后重试');
    }

    // 如果是我们主动抛出的错误，直接传递
    if (err instanceof Error && err.message.startsWith('服务器')) {
      logger.error('API', `❌ ${err.message}（${elapsed}ms）`);
      throw err;
    }
    if (err instanceof Error && err.message.startsWith('提交失败')) {
      throw err;
    }

    logger.error('API', `❌ 网络异常（${elapsed}ms）`, err instanceof Error ? err.message : String(err));
    throw new Error('网络连接失败，请检查网络设置后重试');
  }
}

function simulateAIAnalysis(data: FeedbackSubmitData): FeedbackResult {
  const content = data.content_raw;
  let category = data.category || '体验';

  if (!data.category) {
    logger.info('AI', '未手动选择分类，开始关键词匹配...');
    const rules: { pattern: RegExp; cat: FeedbackSubmitData['category'] extends infer R ? R : never; name: string }[] = [
      { pattern: /碰撞|事故|危险|撞到|撞了|安全|压到|刮擦|翻车/, cat: '安全' as const, name: '安全类关键词命中' },
      { pattern: /故障|坏了|打不开|趴窝|不动|失灵|没电|锁|卡住/, cat: '故障' as const, name: '故障类关键词命中' },
      { pattern: /投诉|不满|太差|垃圾|骗人|赔偿|说法/, cat: '投诉' as const, name: '投诉类关键词命中' },
      { pattern: /建议|希望|能不能|可以加|建议增加|优化|改进/, cat: '建议' as const, name: '建议类关键词命中' },
    ];
    for (const rule of rules) {
      if (rule.pattern.test(content)) {
        category = rule.cat!;
        logger.info('AI', `分类规则命中: ${rule.name} → ${category}`);
        break;
      }
    }
    if (category === '体验') {
      logger.info('AI', '无特殊关键词命中，默认分类为「体验」');
    }
  } else {
    logger.info('AI', `使用用户手动选择的分类: ${category}`);
  }

  // 直接复用 types.ts 的共享常量，与 submit.ts 保证 100% 一致
  const priority = CATEGORY_PRIORITY_DEFAULT[category];
  const resp_time = PRIORITY_RESPONSE_TIME[priority];
  logger.info('AI', `优先级判定: ${category} → ${priority}（预计响应: ${resp_time}）`);

  const now = new Date();
  const pad2 = (n: number) => String(n).padStart(2, '0');
  const dateStr = `${now.getFullYear()}${pad2(now.getMonth() + 1)}${pad2(now.getDate())}`;
  const seq4 = Math.floor(Math.random() * 9000 + 1000); // 4位随机

  const result: FeedbackResult = {
    ticket_id: `FB-${dateStr}-M${seq4}`,  // M 前缀 = Mock（本地模拟模式），与 H=H5扫码 / S=舆情 / 仿真无后缀 天然不冲突
    category,
    priority,
    summary: content.length > 30 ? content.slice(0, 28) + '...' : content,
    estimated_response_time: resp_time,  // PRIORITY_RESPONSE_TIME 已修正 P2=1小时内（按 Schema）
    status: '已受理',
  };

  logger.info('AI', `生成工单号: ${result.ticket_id}`);
  return result;
}
