const config = {
  snowflakeCount: 100,
  minSize: 3,
  maxSize: 8,
  minSpeedY: 0.5,
  maxSpeedY: 2,
  minSpeedX: -0.5,
  maxSpeedX: 0.5,
  minOpacity: 0.7,
  maxOpacity: 1.0,
  wind: 0.005,
  swingRange: 0.2,
  swingSpeed: 0.005,
  rotationSpeedMin: -0.5,
  rotationSpeedMax: 0.5,
  surpriseDropInterval: 1500,
  maxSurprisesOnScreen: 3,
  surpriseFallSpeedMin: 1,
  surpriseFallSpeedMax: 4,
  surpriseTypes: [
    { type: 'gift', weight: 3 },
    { type: 'hat', weight: 2 },
    { type: 'tree', weight: 1 },
  ],
  svgViewportWidth: 100,
  svgViewportHeight: 100,
  sizeRelativeToViewportWidth: 0.04,
}

const SURPRISE_ASSETS_SVG = {
  gift: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${config.svgViewportWidth} ${config.svgViewportHeight}">
          <defs>
            <linearGradient id="boxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#FF8C00;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="ribbonGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#DC143C;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#8B0000;stop-opacity:1" />
            </linearGradient>
          </defs>
          <rect x="15" y="30" width="70" height="50" rx="5" ry="5" fill="url(#boxGrad)" stroke="#8B4513" stroke-width="2"/>
          <rect x="10" y="25" width="80" height="15" rx="3" ry="3" fill="url(#boxGrad)" stroke="#8B4513" stroke-width="2"/>
          <rect x="45" y="25" width="10" height="55" fill="url(#ribbonGrad)" stroke="#8B0000" stroke-width="1"/>
          <rect x="10" y="35" width="80" height="10" fill="url(#ribbonGrad)" stroke="#8B0000" stroke-width="1"/>
          <circle cx="50" cy="30" r="5" fill="#FFD700" stroke="#8B4513" stroke-width="1"/>
          <path d="M40,25 Q35,20 30,25 Q35,30 40,25 Z" fill="url(#ribbonGrad)" stroke="#8B0000" stroke-width="1"/>
          <path d="M60,25 Q65,20 70,25 Q65,30 60,25 Z" fill="url(#ribbonGrad)" stroke="#8B0000" stroke-width="1"/>
        </svg>`,
  hat: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${config.svgViewportWidth} ${config.svgViewportHeight}">
          <defs>
              <radialGradient id="hatGrad" cx="50%" cy="30%" r="70%" fx="50%" fy="30%">
                  <stop offset="0%" stop-color="#FF3333"/>
                  <stop offset="100%" stop-color="#990000"/>
              </radialGradient>
               <linearGradient id="trimGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#FFFFFF"/>
                  <stop offset="50%" stop-color="#FFFF99"/>
                  <stop offset="100%" stop-color="#FFFFFF"/>
              </linearGradient>
          </defs>
          <path d="M50,10 L85,70 Q50,85 15,70 Z" fill="url(#hatGrad)" stroke="#660000" stroke-width="2"/>
          <path d="M15,70 Q10,75 15,80 Q20,75 25,80 Q30,75 35,80 Q40,75 45,80 Q50,75 55,80 Q60,75 65,80 Q70,75 75,80 Q80,75 85,80 L85,70 Q80,72 75,70 Q70,72 65,70 Q60,72 55,70 Q50,72 45,70 Q40,72 35,70 Q30,72 25,70 Q20,72 15,70 Z" fill="url(#trimGrad)" stroke="#CCCCCC" stroke-width="1"/>
          <circle cx="50" cy="10" r="6" fill="#FFFFFF" stroke="#CCCCCC" stroke-width="1"/>
        </svg>`,
  tree: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${config.svgViewportWidth} ${config.svgViewportHeight}">
          <defs>
              <linearGradient id="treeGreen" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="#32CD32"/>
                  <stop offset="100%" stop-color="#006400"/>
              </linearGradient>
              <linearGradient id="trunkBrown" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="#8B4513"/>
                  <stop offset="100%" stop-color="#5D2906"/>
              </linearGradient>
              <radialGradient id="starGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#FFFF00" stop-opacity="1"/>
                  <stop offset="100%" stop-color="#FFFF00" stop-opacity="0"/>
              </radialGradient>
          </defs>
          <rect x="45" y="70" width="10" height="20" fill="url(#trunkBrown)" />
          <polygon points="50,20 20,70 80,70" fill="url(#treeGreen)" />
          <polygon points="50,10 30,60 70,60" fill="url(#treeGreen)" />
          <polygon points="50,0 40,50 60,50" fill="url(#treeGreen)" />
          <polygon points="50,2 53,8 59,9 55,13 56,19 50,16 44,19 45,13 41,9 47,8" fill="#FFD700" stroke="#DAA520" stroke-width="0.5"/>
          <circle cx="50" cy="10" r="8" fill="url(#starGlow)" />
          <circle cx="35" cy="45" r="3" fill="#FF0000" />
          <circle cx="65" cy="45" r="3" fill="#0000FF" />
          <circle cx="50" cy="60" r="3" fill="#FFFF00" />
          <path d="M40,30 Q45,35 50,30 T60,30" fill="none" stroke="#FF00FF" stroke-width="2" stroke-linecap="round"/>
          <path d="M30,50 Q50,60 70,50" fill="none" stroke="#00FFFF" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
}

const surpriseStyles = `
  #snow-surprise-container {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      pointer-events: none;
      z-index: 9998;
      overflow: hidden;
  }
  .falling-surprise-svg {
      position: absolute;
      user-select: none;
      pointer-events: none;
      animation-name: fallSurpriseSvg;
      animation-timing-function: linear;
      animation-iteration-count: 1;
      animation-fill-mode: forwards;
      width: auto;
      height: auto;
      max-width: 100px;
      max-height: 100px;
  }
  @keyframes fallSurpriseSvg {
      to {
          transform: translateY(100vh) rotate(360deg);
      }
  }
`

const state = {
  canvas: null,
  ctx: null,
  snowflakes: [],
  resizeHandler: null,
  animationId: null,
  surpriseContainer: null,
  surpriseManager: null,
}

class Snowflake {
  constructor(width, height) {
    this.canvasWidth = width
    this.canvasHeight = height
    this.reset()
  }

  reset() {
    this.x = Math.random() * this.canvasWidth
    this.y = Math.random() * -this.canvasHeight
    this.size = Math.random() * (config.maxSize - config.minSize) + config.minSize
    this.speedY = Math.random() * (config.maxSpeedY - config.minSpeedY) + config.minSpeedY
    this.speedX = Math.random() * (config.maxSpeedX - config.minSpeedX) + config.minSpeedX
    this.opacity = Math.random() * (config.maxOpacity - config.minOpacity) + config.minOpacity
    this.swingOffset = Math.random() * Math.PI * 2
    this.rotation = Math.random() * 360
    this.rotationSpeed = Math.random() * (config.rotationSpeedMax - config.rotationSpeedMin) + config.rotationSpeedMin
    this.timeAlive = 0
  }

  update(time) {
    this.timeAlive++
    this.y += this.speedY
    this.x += this.speedX + config.wind + Math.sin(this.swingOffset + time * config.swingSpeed) * config.swingRange
    this.rotation += this.rotationSpeed
    if (this.rotation >= 360) this.rotation -= 360
    if (this.rotation < 0) this.rotation += 360

    if (this.y > this.canvasHeight || this.x < -this.size * 2 || this.x > this.canvasWidth + this.size * 2) {
      this.reset()
      this.y = -this.size * 2
    }
  }

  draw(ctx) {
    ctx.save()
    ctx.translate(this.x, this.y)
    ctx.rotate((this.rotation * Math.PI) / 180)
    ctx.strokeStyle = `rgba(255, 255, 255, ${this.opacity})`
    ctx.lineWidth = 1
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    const s = this.size
    ctx.beginPath()
    for (let i = 0; i < 6; i++) {
      ctx.rotate(Math.PI / 3)
      ctx.moveTo(0, 0)
      ctx.lineTo(0, -s)
      ctx.moveTo(0, -s * 0.5)
      ctx.lineTo(-s * 0.3, -s * 0.7)
      ctx.moveTo(0, -s * 0.5)
      ctx.lineTo(s * 0.3, -s * 0.7)
    }
    ctx.stroke()
    ctx.restore()
  }
}

class SvgSurpriseManager {
  constructor(containerElement) {
    this.container = containerElement
    this.currentSurprises = []
    this.dropTimer = null
  }

  startDropping() {
    const getRandomSurpriseType = () => {
      const totalWeight = config.surpriseTypes.reduce((sum, item) => sum + item.weight, 0)
      let randomValue = Math.random() * totalWeight
      for (const item of config.surpriseTypes) {
        randomValue -= item.weight
        if (randomValue <= 0) return item.type
      }
      return config.surpriseTypes[0].type
    }

    const dropSurprise = () => {
      if (this.currentSurprises.length < config.maxSurprisesOnScreen) {
        const type = getRandomSurpriseType()
        this.createSurprise(type)
      }
      const variance = config.surpriseDropInterval * 0.5
      const nextDropTime = config.surpriseDropInterval + Math.random() * variance * 2 - variance
      this.dropTimer = window.setTimeout(dropSurprise, Math.max(nextDropTime, 500))
    }

    this.dropTimer = window.setTimeout(dropSurprise, config.surpriseDropInterval)
  }

  stopDropping() {
    if (this.dropTimer) {
      clearTimeout(this.dropTimer)
      this.dropTimer = null
    }
    this.currentSurprises.forEach((item) => item.remove())
    this.currentSurprises = []
  }

  createSurprise(type) {
    const svgString = SURPRISE_ASSETS_SVG[type]
    if (!svgString) return

    const surpriseWrapper = document.createElement('div')
    surpriseWrapper.className = 'falling-surprise-svg'
    surpriseWrapper.setAttribute('data-surprise-type', type)

    const parser = new DOMParser()
    const svgDoc = parser.parseFromString(svgString, 'image/svg+xml')
    const svgElement = svgDoc.documentElement
    if (svgElement?.tagName === 'svg') {
      surpriseWrapper.appendChild(svgElement)
    } else {
      return
    }

    const startX = Math.random() * 100
    surpriseWrapper.style.left = `${startX}vw`

    const baseSizeRatio = config.sizeRelativeToViewportWidth
    const finalWidth = window.innerWidth * baseSizeRatio
    const randomSizeFactor = 0.9 + Math.random() * 0.2
    const finalSize = finalWidth * randomSizeFactor
    surpriseWrapper.style.width = `${finalSize}px`
    surpriseWrapper.style.height = 'auto'

    const speed = Math.random() * (config.surpriseFallSpeedMax - config.surpriseFallSpeedMin) + config.surpriseFallSpeedMin
    const distance = window.innerHeight
    const durationSeconds = distance / (speed * 60)
    surpriseWrapper.style.animationDuration = `${durationSeconds.toFixed(2)}s`

    this.container.appendChild(surpriseWrapper)
    this.currentSurprises.push(surpriseWrapper)

    surpriseWrapper.addEventListener('animationend', () => {
      surpriseWrapper.remove()
      const index = this.currentSurprises.indexOf(surpriseWrapper)
      if (index > -1) this.currentSurprises.splice(index, 1)
    })
  }
}

function ensureStyleInjected() {
  if (document.getElementById('snow-surprise-style')) return
  const styleElement = document.createElement('style')
  styleElement.id = 'snow-surprise-style'
  styleElement.textContent = surpriseStyles
  document.head.appendChild(styleElement)
}

function setupCanvas() {
  const canvas = document.createElement('canvas')
  canvas.id = 'realistic-snow-canvas'
  canvas.style.position = 'fixed'
  canvas.style.top = '0'
  canvas.style.left = '0'
  canvas.style.pointerEvents = 'none'
  canvas.style.zIndex = '9999'
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  document.body.appendChild(canvas)
  return canvas
}

function createSnowflakes() {
  const { innerWidth, innerHeight } = window
  state.snowflakes = []
  for (let i = 0; i < config.snowflakeCount; i++) {
    state.snowflakes.push(new Snowflake(innerWidth, innerHeight))
  }
}

function renderLoop(startTime) {
  const loop = (currentTime) => {
    const elapsedTime = currentTime - startTime
    const ctx = state.ctx
    if (!ctx || !state.canvas) return
    ctx.clearRect(0, 0, state.canvas.width, state.canvas.height)
    state.snowflakes.forEach((flake) => {
      flake.update(elapsedTime)
      flake.draw(ctx)
    })
    state.animationId = requestAnimationFrame(loop)
  }
  state.animationId = requestAnimationFrame(loop)
}

export function startChristmasEffects() {
  if (state.canvas || typeof document === 'undefined') return
  ensureStyleInjected()

  state.canvas = setupCanvas()
  state.ctx = state.canvas.getContext('2d')
  createSnowflakes()

  state.resizeHandler = () => {
    if (!state.canvas) return
    state.canvas.width = window.innerWidth
    state.canvas.height = window.innerHeight
    createSnowflakes()
  }
  window.addEventListener('resize', state.resizeHandler)

  state.surpriseContainer = document.createElement('div')
  state.surpriseContainer.id = 'snow-surprise-container'
  document.body.appendChild(state.surpriseContainer)
  state.surpriseManager = new SvgSurpriseManager(state.surpriseContainer)
  state.surpriseManager.startDropping()

  renderLoop(performance.now())
}

export function stopChristmasEffects() {
  if (!state.canvas) return
  if (state.animationId) cancelAnimationFrame(state.animationId)
  if (state.resizeHandler) window.removeEventListener('resize', state.resizeHandler)
  state.animationId = null
  state.resizeHandler = null

  state.snowflakes = []
  state.ctx = null
  state.canvas.remove()
  state.canvas = null

  if (state.surpriseManager) {
    state.surpriseManager.stopDropping()
    state.surpriseManager = null
  }
  if (state.surpriseContainer) {
    state.surpriseContainer.remove()
    state.surpriseContainer = null
  }
}
