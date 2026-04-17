import { motion } from 'framer-motion'

type Props = {
  score: number
}

export function BiasGauge({ score }: Props) {
  const clamped = Math.max(0, Math.min(100, score))
  return (
    <div className="relative h-44 w-44">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r="52" stroke="#E7D7CA" strokeWidth="10" fill="none" />
        <motion.circle
          cx="60"
          cy="60"
          r="52"
          stroke="url(#meterGradient)"
          strokeWidth="10"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={327}
          initial={{ strokeDashoffset: 327 }}
          animate={{ strokeDashoffset: 327 - (327 * clamped) / 100 }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
        <defs>
          <linearGradient id="meterGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#E24B4A" />
            <stop offset="55%" stopColor="#C48A52" />
            <stop offset="100%" stopColor="#1D9E75" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted">Fairness</p>
        <p className="text-4xl font-display text-espresso">{clamped}</p>
      </div>
    </div>
  )
}
