/**
 * Cloud 서브카테고리 커스텀 SVG 아이콘 컴포넌트
 */

export function AwsIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M6.5 17.5C3.5 17.5 2 15.5 2 13c0-2.3 1.7-4.2 4-4.5C6.5 5.8 8.9 4 12 4c3.7 0 6.5 2.5 7 5.5 1.7.3 3 1.8 3 3.5 0 2-1.5 3.5-3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M8 20l4-3 4 3" stroke="#FF9900" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 17v-4" stroke="#FF9900" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}

export function DockerIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="2" y="11" width="4" height="3" rx="0.5" stroke="currentColor" strokeWidth="1.3"/>
      <rect x="7" y="11" width="4" height="3" rx="0.5" stroke="currentColor" strokeWidth="1.3"/>
      <rect x="12" y="11" width="4" height="3" rx="0.5" stroke="currentColor" strokeWidth="1.3"/>
      <rect x="7" y="7" width="4" height="3" rx="0.5" stroke="currentColor" strokeWidth="1.3"/>
      <rect x="12" y="7" width="4" height="3" rx="0.5" stroke="currentColor" strokeWidth="1.3"/>
      <rect x="12" y="3" width="4" height="3" rx="0.5" stroke="currentColor" strokeWidth="1.3"/>
      <path d="M17 12c3 0 5-1 5.5-3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <path d="M1 15c1 3 4 5 10 5 7 0 10-3 11-6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  )
}

export function LxdIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.5"/>
      <rect x="6" y="7" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <rect x="13" y="7" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <rect x="6" y="13" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <rect x="13" y="13" width="5" height="4" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <circle cx="8" cy="9" r="0.7" fill="currentColor"/>
      <circle cx="15" cy="9" r="0.7" fill="currentColor"/>
      <circle cx="8" cy="15" r="0.7" fill="currentColor"/>
      <circle cx="15" cy="15" r="0.7" fill="currentColor"/>
    </svg>
  )
}

export function DevOpsIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c1.5 0 3-.3 4.3-.9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="3 3"/>
      <path d="M8 12l2 2 4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="19" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.3"/>
      <path d="M19 4v2M18 5h2" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    </svg>
  )
}
