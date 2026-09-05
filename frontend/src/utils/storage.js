/**
 * localStorage 轻量封装
 * 统一加 ruc: 前缀、JSON 序列化，避免与其他站点键冲突
 */
const PREFIX = 'ruc:'

function serialize(value) {
  return JSON.stringify(value)
}

function deserialize(raw) {
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

export function getStorage(key, defaultValue = null) {
  const raw = localStorage.getItem(PREFIX + key)
  if (raw === null) return defaultValue
  return deserialize(raw)
}

export function setStorage(key, value) {
  localStorage.setItem(PREFIX + key, serialize(value))
}

export function removeStorage(key) {
  localStorage.removeItem(PREFIX + key)
}

/** 清空本项目全部本地缓存 */
export function clearStorage() {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith(PREFIX))
  keys.forEach((k) => localStorage.removeItem(k))
}
