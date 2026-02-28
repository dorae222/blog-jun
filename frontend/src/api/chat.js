import client from './client'

export const sendMessage = (message, sessionId) =>
  client.post('/chat/', { message, session_id: sessionId })

export const getChatSessions = () => client.get('/chat/sessions/')
