// 组合式 API：统一对外暴露请求能力

import { request } from '../utils/request'

export function useApi() {
  return {
    request,
  }
}
