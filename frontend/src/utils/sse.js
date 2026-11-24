/**
 * SSE(text/event-stream) 파서.
 *
 * fetch + ReadableStream으로 받은 바이트 조각은 이벤트 경계와 무관하게 잘려서 온다.
 * 그래서 남은 꼬리(buffer)를 들고 있다가 빈 줄이 나올 때마다 이벤트 하나로 자른다.
 * blog-agent는 `data: {json}` 한 줄짜리 이벤트만 보내지만, 여러 줄 data와
 * CRLF 줄바꿈도 표준대로 처리해 둔다.
 */
export function createSSEParser(onEvent) {
  let buffer = ''

  function flushBlock(block) {
    const dataLines = []
    for (const line of block.split('\n')) {
      if (!line || line.startsWith(':')) continue
      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).replace(/^ /, ''))
      }
    }
    if (!dataLines.length) return
    const data = dataLines.join('\n')
    let parsed
    try {
      parsed = JSON.parse(data)
    } catch {
      parsed = { type: 'token', content: data }
    }
    onEvent(parsed)
  }

  return {
    push(chunk) {
      buffer += chunk
      // CR과 LF가 청크 경계에서 갈리면 빈 줄로 잘못 볼 수 있어, 끝의 CR은 다음 청크까지 미룬다.
      let tail = ''
      if (buffer.endsWith('\r')) {
        tail = '\r'
        buffer = buffer.slice(0, -1)
      }
      buffer = buffer.replace(/\r\n?/g, '\n')
      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        flushBlock(block)
      }
      buffer += tail
    },
    end() {
      buffer = buffer.replace(/\r\n?/g, '\n')
      if (buffer.trim()) flushBlock(buffer)
      buffer = ''
    },
  }
}
