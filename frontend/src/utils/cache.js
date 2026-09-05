import { getStorage, setStorage, removeStorage } from './storage'

const CACHE_PREFIX = 'cache:'
const DEFAULT_TTL = 5 * 60 * 1000 // 默认 5 分钟

/**
 * 带 TTL 的统一缓存工具（对应设计文档 6.2）
 * 写入记录时间戳，读取时校验是否过期，过期自动清除并返回 null
 */

/**
 * @param {string} key 缓存键
 * @param {*} data 缓存数据
 * @param {number} [ttl=DEFAULT_TTL] 有效期（毫秒）
 */
export function setCache(key, data, ttl = DEFAULT_TTL) {
  const record = {
    data,
    expireAt: Date.now() + ttl
  }
  setStorage(CACHE_PREFIX + key, record)
}

/**
 * @param {string} key 缓存键
 * @returns {*|null} 命中且未过期返回数据，否则返回 null
 */
export function getCache(key) {
  const record = getStorage(CACHE_PREFIX + key)
  if (!record || typeof record.expireAt !== 'number') return null
  if (Date.now() > record.expireAt) {
    removeStorage(CACHE_PREFIX + key)
    return null
  }
  return record.data
}

export function removeCache(key) {
  removeStorage(CACHE_PREFIX + key)
}

/** 清空所有带 TTL 的缓存（不影响 token / 用户信息） */
export function clearCache() {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith('ruc:' + CACHE_PREFIX))
  keys.forEach((k) => localStorage.removeItem(k))
}
