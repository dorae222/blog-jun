import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import App from './App'
import './index.css'

// 어떤 빌드가 떠 있는지 브라우저에서 바로 확인하려고 남긴다.
// 2026-08-17 장애 때 배포한 번들이 실제로 실행되고 있는지를 알 방법이 없어
// 원인을 서버에서만 찾다가 시간을 버렸다. 콘솔에서 window.__BUILD__를 보면 된다.
window.__BUILD__ = '2026-08-17-nocache404'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HelmetProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </HelmetProvider>
  </React.StrictMode>,
)
