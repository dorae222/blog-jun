import { useEffect, useState } from 'react'
import { getCachedTree, loadCategoryTree } from '../data/categoryTree'

/**
 * 카테고리 트리를 DB에서 받아 쓴다.
 * 첫 렌더는 캐시(로컬스토리지 또는 기본값)로 즉시 그리고, 응답이 오면 갈아 끼운다.
 * 덕분에 카테고리를 추가·삭제해도 프런트를 고칠 일이 없다.
 */
export default function useCategories() {
  const [tree, setTree] = useState(getCachedTree)

  useEffect(() => {
    let alive = true
    loadCategoryTree().then((t) => { if (alive && t?.length) setTree(t) })
    return () => { alive = false }
  }, [])

  return tree
}

/** CategoryTabs 등에서 쓰는 파생 목록 */
export function mainTabsOf(tree) {
  return [{ key: null, label: '전체', path: '/posts' },
    ...tree.map((c) => ({ key: c.key, label: c.label, path: c.path }))]
}

export function subTabsOf(tree) {
  return Object.fromEntries(
    tree.map((c) => [c.key, [{ key: null, label: '전체' }, ...(c.subs || [])]]),
  )
}
