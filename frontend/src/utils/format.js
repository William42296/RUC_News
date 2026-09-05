import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * 相对时间，如「3分钟前」「昨天」
 * @param {string|number|Date} time
 */
export function fromNow(time) {
  if (!time) return ''
  return dayjs(time).fromNow()
}

/**
 * 绝对时间格式化
 * @param {string|number|Date} time
 * @param {string} [template='YYYY-MM-DD HH:mm']
 */
export function formatTime(time, template = 'YYYY-MM-DD HH:mm') {
  if (!time) return ''
  return dayjs(time).format(template)
}
