/**
 * 关键词高亮：将文本按关键词（大小写不敏感）切分为片段，
 * 命中片段标记 match: true，供模板用 .highlight 类渲染，避免 v-html 注入风险。
 */
export function highlightSegments(text, keyword) {
  const source = text ?? ''
  const kw = String(keyword ?? '').trim()

  if (!kw || !source) {
    return source ? [{ text: source, match: false }] : []
  }

  const segments = []
  const lowerSource = source.toLowerCase()
  const lowerKw = kw.toLowerCase()
  let lastIndex = 0
  let index = lowerSource.indexOf(lowerKw)

  while (index !== -1) {
    if (index > lastIndex) {
      segments.push({ text: source.slice(lastIndex, index), match: false })
    }
    segments.push({ text: source.slice(index, index + kw.length), match: true })
    lastIndex = index + kw.length
    index = lowerSource.indexOf(lowerKw, lastIndex)
  }

  if (lastIndex < source.length) {
    segments.push({ text: source.slice(lastIndex), match: false })
  }

  return segments
}
