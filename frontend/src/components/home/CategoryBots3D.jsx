import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import * as THREE from 'three'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { CATEGORY_TREE } from '../../data/categories'

// 카테고리 ↔ 봇(엠블럼/색/표정) 매핑
const BOTS = [
  { key: 'ai', emblem: 'sparkle', color: 0xff6f00, face: 'smile' },
  { key: 'tool', emblem: 'gear', color: 0x7c3aed, face: 'terminal' },
  { key: 'ml', emblem: 'chart', color: 0x10b981, face: 'smile' },
  { key: 'cloud', emblem: 'cloud', color: 0xff9900, face: 'smile' },
  { key: 'data', emblem: 'dbstack', color: 0x336791, face: 'smile' },
]
const HEAD = 0xf3f6fc, EYE = 0x35e0ff
const hex = (n) => '#' + n.toString(16).padStart(6, '0')

export default function CategoryBots3D({ counts = {} }) {
  const mountRef = useRef(null)
  const navigate = useNavigate()
  const navRef = useRef(navigate); navRef.current = navigate
  const countsRef = useRef(counts); countsRef.current = counts
  const [tip, setTip] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true })
    } catch {
      setFailed(true); return
    }
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let W = mount.clientWidth || 800, H = mount.clientHeight || 500

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, reduce ? 1 : 2))
    renderer.setSize(W, H)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.1
    mount.appendChild(renderer.domElement)
    renderer.domElement.style.display = 'block'

    const scene = new THREE.Scene(); scene.background = new THREE.Color(0xeef1f8)
    const pmrem = new THREE.PMREMGenerator(renderer)
    const envRT = pmrem.fromScene(new RoomEnvironment(), 0.04)
    scene.environment = envRT.texture
    const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 100)
    scene.add(new THREE.AmbientLight(0xffffff, 0.4))
    const kl = new THREE.DirectionalLight(0xffffff, 1.2); kl.position.set(4, 7, 6); scene.add(kl)
    const rl = new THREE.DirectionalLight(0xa78bfa, 0.6); rl.position.set(-5, -1, 3); scene.add(rl)

    const disposables = []
    const phys = (o) => { const m = new THREE.MeshPhysicalMaterial({ metalness: 0, roughness: 0.16, clearcoat: 1, clearcoatRoughness: 0.13, envMapIntensity: 1.1, ...o }); disposables.push(m); return m }
    const glow = (c) => { const m = new THREE.MeshStandardMaterial({ color: 0x0a0a0a, emissive: new THREE.Color(c), emissiveIntensity: 2.8 }); disposables.push(m); return m }
    const mk = (geo, mat, pos, rot) => { disposables.push(geo); const m = new THREE.Mesh(geo, mat); if (pos) m.position.set(pos[0], pos[1], pos[2]); if (rot) m.rotation.set(rot[0], rot[1], rot[2]); return m }

    function emblem(type, color) {
      const g = new THREE.Group(); g.position.y = 2.05
      if (type === 'sparkle') {
        const a = mk(new THREE.OctahedronGeometry(0.13, 0), glow(color)); a.scale.set(0.45, 1.7, 0.45)
        const b = mk(new THREE.OctahedronGeometry(0.13, 0), glow(color)); b.scale.set(1.7, 0.45, 0.45)
        g.add(a, b)
      } else if (type === 'gear') {
        g.add(mk(new THREE.CylinderGeometry(0.3, 0.3, 0.16, 24), phys({ color }), null, [Math.PI / 2, 0, 0]))
        for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; const th = mk(new THREE.BoxGeometry(0.13, 0.13, 0.16), phys({ color }), [Math.cos(a) * 0.34, Math.sin(a) * 0.34, 0]); th.rotation.z = a; g.add(th) }
        g.add(mk(new THREE.CylinderGeometry(0.11, 0.11, 0.2, 18), phys({ color: 0x111726 }), null, [Math.PI / 2, 0, 0]))
      } else if (type === 'chart') {
        [0.26, 0.44, 0.64].forEach((h, i) => g.add(mk(new THREE.BoxGeometry(0.15, h, 0.15), phys({ color }), [(i - 1) * 0.23, h / 2 - 0.24, 0])))
      } else if (type === 'cloud') {
        for (const o of [[-0.27, -0.02, 0.22], [0.04, 0.09, 0.29], [0.31, -0.03, 0.2]]) g.add(mk(new THREE.SphereGeometry(o[2], 20, 20), phys({ color }), [o[0], o[1], 0]))
      } else if (type === 'dbstack') {
        for (let i = 0; i < 3; i++) g.add(mk(new THREE.CylinderGeometry(0.3, 0.3, 0.15, 28), phys({ color }), [0, i * 0.2 - 0.22, 0]))
        g.add(mk(new THREE.CylinderGeometry(0.3, 0.3, 0.02, 28), phys({ color: HEAD, roughness: 0.1 }), [0, 0.3, 0]))
      }
      return g
    }

    const bots = []
    BOTS.forEach((cfg, index) => {
      const g = new THREE.Group(); g.scale.setScalar(0.82); g.userData.botIndex = index
      g.add(mk(new RoundedBoxGeometry(2.5, 2.05, 1.75, 8, 0.55), phys({ color: HEAD })))
      g.add(mk(new RoundedBoxGeometry(1.85, 1.4, 0.25, 6, 0.28), phys({ color: 0x111726, roughness: 0.08 }), [0, 0.05, 0.82]))
      const eyes = new THREE.Group(); g.add(eyes)
      const e = mk(new THREE.SphereGeometry(0.17, 28, 28), glow(EYE), [-0.42, 0.24, 0.98]); const e2 = e.clone(); e2.position.x = 0.42; eyes.add(e, e2)
      if (cfg.face === 'terminal') g.add(mk(new THREE.BoxGeometry(0.42, 0.12, 0.06), glow(EYE), [0, -0.28, 0.98]))
      else g.add(mk(new THREE.TorusGeometry(0.32, 0.05, 14, 28, Math.PI), glow(EYE), [0, -0.24, 0.98], [0, 0, Math.PI]))
      for (const s of [-1, 1]) g.add(mk(new THREE.CylinderGeometry(0.3, 0.3, 0.26, 28), phys({ color: cfg.color, roughness: 0.2 }), [s * 1.33, 0.05, 0], [0, 0, Math.PI / 2]))
      g.add(mk(new RoundedBoxGeometry(1.5, 0.85, 1.1, 6, 0.32), phys({ color: cfg.color }), [0, -1.5, 0]))
      const em = emblem(cfg.emblem, cfg.color); g.add(em)
      scene.add(g)
      bots.push({ group: g, eyes, em, cat: CATEGORY_TREE.find((c) => c.key === cfg.key), color: hex(cfg.color), ph: (index * 1.7) % 6, baseX: 0, baseY: 0 })
    })
    const botGroups = bots.map((b) => b.group)

    const composer = new EffectComposer(renderer)
    composer.addPass(new RenderPass(scene, camera))
    composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.5, 0.5, 0.95))
    composer.addPass(new OutputPass())

    // 반응형 그리드 배치 + 카메라 핏
    function layout() {
      const cols = W < 560 ? 2 : 5
      const rows = Math.ceil(bots.length / cols)
      const spx = W < 560 ? 3.4 : 3.15, spy = 4.2
      bots.forEach((b, i) => {
        const col = i % cols, row = Math.floor(i / cols)
        b.baseX = (col - (cols - 1) / 2) * spx
        b.baseY = -(row - (rows - 1) / 2) * spy
        b.group.position.set(b.baseX, b.baseY, 0)
      })
      const vFov = 42 * Math.PI / 180
      const gridW = (cols - 1) * spx + 3.6, gridH = (rows - 1) * spy + 6.4
      const fitH = (gridH / 2) / Math.tan(vFov / 2)
      const fitW = (gridW / 2) / (Math.tan(vFov / 2) * (W / H))
      camera.position.set(0, 0, Math.max(fitH, fitW, 8))
      camera.lookAt(0, 0, 0)
    }
    layout()

    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2(999, 999)
    let mx = 0, my = 0 // parallax 입력 (기본 0 — hover 센티넬과 분리)
    const hoveredRef = { current: -1 }
    const onMove = (ev) => { const r = renderer.domElement.getBoundingClientRect(); pointer.x = ((ev.clientX - r.left) / r.width) * 2 - 1; pointer.y = -((ev.clientY - r.top) / r.height) * 2 + 1; mx = pointer.x; my = pointer.y }
    const onLeave = () => { pointer.set(999, 999); mx = 0; my = 0 }
    const onClick = () => { const i = hoveredRef.current; if (i >= 0 && bots[i].cat) navRef.current(bots[i].cat.path) }
    renderer.domElement.addEventListener('pointermove', onMove)
    renderer.domElement.addEventListener('pointerleave', onLeave)
    renderer.domElement.addEventListener('click', onClick)

    function onHoverChange(idx) {
      renderer.domElement.style.cursor = idx >= 0 ? 'pointer' : 'default'
      if (idx < 0) { setTip(null); return }
      const b = bots[idx]
      const v = new THREE.Vector3(b.baseX, b.baseY + 2.9 * 0.82, 0).project(camera)
      const r = mount.getBoundingClientRect()
      const cnt = countsRef.current?.[b.cat.key]?.count
      setTip({ label: b.cat.label, count: typeof cnt === 'number' ? cnt : null, x: (v.x * 0.5 + 0.5) * r.width, y: (-v.y * 0.5 + 0.5) * r.height, color: b.color })
    }

    let t = 0, raf = 0, running = false
    function animate() {
      if (!running) return
      raf = requestAnimationFrame(animate)
      t += 0.016
      raycaster.setFromCamera(pointer, camera)
      const hit = raycaster.intersectObjects(botGroups, true)[0]
      let idx = -1
      if (hit) { let o = hit.object; while (o && o.userData.botIndex === undefined) o = o.parent; if (o) idx = o.userData.botIndex }
      if (idx !== hoveredRef.current) { hoveredRef.current = idx; onHoverChange(idx) }
      bots.forEach((b, i) => {
        const ts = i === idx ? 0.94 : 0.82
        const s = b.group.scale.x + (ts - b.group.scale.x) * 0.15
        b.group.scale.setScalar(s)
        if (!reduce) {
          b.group.position.y = b.baseY + Math.sin(t * 0.9 + b.ph) * 0.12
          b.group.rotation.y += (mx * 0.35 - b.group.rotation.y) * 0.05
          b.group.rotation.x += (-my * 0.2 - b.group.rotation.x) * 0.05
          b.eyes.scale.y += ((Math.sin(t * 1.1 + b.ph) > 0.985 ? 0.12 : 1) - b.eyes.scale.y) * 0.4
          b.em.rotation.y += 0.02
          b.em.position.y = 2.05 + Math.sin(t * 1.4 + b.ph) * 0.07
        }
      })
      composer.render()
    }
    const start = () => { if (!running) { running = true; animate() } }
    const stop = () => { running = false; cancelAnimationFrame(raf) }

    const io = new IntersectionObserver(([e]) => (e.isIntersecting ? start() : stop()), { threshold: 0.02 })
    io.observe(mount)
    const ro = new ResizeObserver(() => {
      W = mount.clientWidth || W; H = mount.clientHeight || H
      renderer.setSize(W, H); composer.setSize(W, H)
      camera.aspect = W / H; camera.updateProjectionMatrix(); layout()
    })
    ro.observe(mount)

    return () => {
      stop(); io.disconnect(); ro.disconnect()
      renderer.domElement.removeEventListener('pointermove', onMove)
      renderer.domElement.removeEventListener('pointerleave', onLeave)
      renderer.domElement.removeEventListener('click', onClick)
      disposables.forEach((d) => d.dispose && d.dispose())
      envRT.dispose(); pmrem.dispose(); composer.dispose?.(); renderer.dispose()
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div>
      <div className="mb-5 flex items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.28em]" style={{ color: 'var(--text-secondary)' }}>Explore</span>
          </div>
          <h2 className="text-2xl font-bold md:text-3xl" style={{ color: 'var(--text)' }}>카테고리</h2>
        </div>
        <span className="hidden text-sm sm:block" style={{ color: 'var(--text-secondary)' }}>봇을 클릭해 탐색하세요</span>
      </div>

      {failed ? (
        <div className="flex flex-wrap gap-2 rounded-3xl border p-6" style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
          {CATEGORY_TREE.map((c) => (
            <Link key={c.key} to={c.path} className="rounded-full border px-4 py-2 text-sm font-medium transition-colors hover:bg-gray-50"
              style={{ borderColor: `${c.color}55`, color: 'var(--text)' }}>{c.label}</Link>
          ))}
        </div>
      ) : (
        <div className="relative w-full" style={{ height: 'clamp(440px, 60vh, 560px)' }}>
          <div ref={mountRef} className="absolute inset-0 overflow-hidden rounded-3xl border" style={{ borderColor: 'var(--border)' }} />
          {tip && (
            <div className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-full border px-3 py-1 text-xs font-semibold shadow-sm"
              style={{ left: tip.x, top: tip.y - 8, background: 'var(--card-bg)', borderColor: 'var(--border)', color: 'var(--text)' }}>
              <span style={{ color: tip.color }}>●</span> {tip.label}{tip.count != null ? ` · ${tip.count}` : ''}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
