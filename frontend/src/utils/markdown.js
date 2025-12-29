/**
 * 安全的 Markdown 渲染工具
 * 使用 marked 解析 Markdown，使用 DOMPurify 清理 HTML 防止 XSS
 */

import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 配置 marked
marked.setOptions({
  breaks: true, // 支持 GFM 换行
  gfm: true, // 启用 GitHub Flavored Markdown
})

/**
 * 安全地渲染 Markdown 为 HTML
 * @param {string} content - Markdown 内容
 * @returns {string} 清理后的 HTML
 */
export function renderMarkdown(content) {
  if (!content) return ''
  
  try {
    // 1. 使用 marked 解析 Markdown
    const rawHtml = marked.parse(content)
    
    // 2. 使用 DOMPurify 清理 HTML，防止 XSS
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: [
        'p', 'br', 'strong', 'em', 'u', 'code', 'pre',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'a', 'img'
      ],
      ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class'],
      ALLOW_DATA_ATTR: false,
    })
    
    return cleanHtml
  } catch (error) {
    console.error('Markdown 渲染失败：', error)
    // 降级：返回纯文本
    return DOMPurify.sanitize(content, { ALLOWED_TAGS: [] })
  }
}

/**
 * 转义 HTML 特殊字符（备用方案）
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的文本
 */
export function escapeHtml(text) {
  if (!text) return ''
  
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }
  
  return text.replace(/[&<>"']/g, (char) => map[char])
}
