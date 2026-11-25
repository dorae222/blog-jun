// 챗봇 답변 피드백(👍/👎) 요청 본문. 화면·API·테스트가 같은 규칙을 쓴다.
export const FEEDBACK_COMMENT_MAX = 300

/** 피드백 요청 본문. 의견은 앞뒤 공백을 떼고 300자로 자르며, 비면 넣지 않는다. */
export function feedbackPayload({ messageId, feedbackToken, value, comment }) {
  const text = typeof comment === 'string' ? comment.trim().slice(0, FEEDBACK_COMMENT_MAX) : ''
  return {
    message_id: messageId,
    feedback_token: feedbackToken,
    value,
    ...(text ? { comment: text } : {}),
  }
}
