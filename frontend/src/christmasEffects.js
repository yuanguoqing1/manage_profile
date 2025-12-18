const snowState = {
  canvas: null,
  context: null,
  rafId: null,
  flakes: [],
  resizeHandler: null,
}

function initSnowFlakes() {
  if (!snowState.canvas || !snowState.context) return
  const { innerWidth, innerHeight } = window
  snowState.canvas.width = innerWidth
  snowState.canvas.height = innerHeight
  snowState.flakes = Array.from({ length: Math.min(160, Math.max(80, Math.floor(innerWidth / 10))) }, () => ({
    x: Math.random() * innerWidth,
    y: Math.random() * innerHeight,
    r: Math.random() * 3 + 1,
    d: Math.random() * 1 + 0.5,
  }))
}

function drawSnow() {
  if (!snowState.context || !snowState.canvas) return
  const ctx = snowState.context
  const w = snowState.canvas.width
  const h = snowState.canvas.height
  ctx.clearRect(0, 0, w, h)
  ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
  ctx.beginPath()
  snowState.flakes.forEach((flake) => {
    ctx.moveTo(flake.x, flake.y)
    ctx.arc(flake.x, flake.y, flake.r, 0, Math.PI * 2, true)
  })
  ctx.fill()

  snowState.flakes = snowState.flakes.map((flake) => {
    let { x, y, r, d } = flake
    y += d
    x += Math.sin(d * 2) * 0.5
    if (y > h) {
      y = -10
      x = Math.random() * w
    }
    return { x, y, r, d }
  })

  snowState.rafId = requestAnimationFrame(drawSnow)
}

export function startChristmasEffects() {
  if (snowState.canvas) return
  const canvas = document.createElement('canvas')
  canvas.id = 'christmas-snow'
  canvas.style.position = 'fixed'
  canvas.style.pointerEvents = 'none'
  canvas.style.top = '0'
  canvas.style.left = '0'
  canvas.style.width = '100vw'
  canvas.style.height = '100vh'
  canvas.style.zIndex = '999'
  document.body.appendChild(canvas)
  snowState.canvas = canvas
  snowState.context = canvas.getContext('2d')
  snowState.resizeHandler = () => initSnowFlakes()
  window.addEventListener('resize', snowState.resizeHandler)
  initSnowFlakes()
  drawSnow()
}

export function stopChristmasEffects() {
  if (!snowState.canvas) return
  if (snowState.rafId) cancelAnimationFrame(snowState.rafId)
  if (snowState.resizeHandler) window.removeEventListener('resize', snowState.resizeHandler)
  snowState.canvas.remove()
  snowState.canvas = null
  snowState.context = null
  snowState.flakes = []
  snowState.rafId = null
}
