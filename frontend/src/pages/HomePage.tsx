import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

import { BiasGauge } from '../components/BiasGauge'

const useCases = ['Hiring', 'Lending', 'Healthcare', 'Content Moderation']

export function HomePage() {
  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-3xl border border-caramel20 bg-white p-8 shadow-card">
        <div className="pointer-events-none absolute -right-24 -top-20 h-72 w-72 rounded-full bg-caramel10 blur-3xl" />
        <div className="grid gap-8 md:grid-cols-2 md:items-center">
          <div className="space-y-5">
            <p className="inline-flex rounded-full bg-caramel10 px-3 py-1 text-xs font-bold uppercase tracking-widest text-caramel">
              AI Fairness Assurance
            </p>
            <h1 className="text-4xl font-display leading-tight text-espresso md:text-5xl">
              Detect hidden bias before your model goes live.
            </h1>
            <p className="max-w-xl text-base text-muted">
              FairLens helps data science and compliance teams upload datasets, compute fairness metrics, test remediations, and publish compliance-ready reports.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/login" className="rounded-full bg-caramel px-5 py-3 font-semibold text-white transition hover:bg-walnut">
                Start Audit
              </Link>
              <Link to="/audit/new" className="rounded-full border border-caramel20 bg-white px-5 py-3 font-semibold text-espresso transition hover:bg-caramel10">
                Configure Audit
              </Link>
            </div>
          </div>
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }} className="grid place-items-center">
            <BiasGauge score={86} />
          </motion.div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {['Upload', 'Detect', 'Fix'].map((step, idx) => (
          <motion.article key={step} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 * idx }} className="rounded-2xl border border-caramel20 bg-white p-5 shadow-card">
            <p className="text-xs font-semibold uppercase tracking-widest text-caramel">Step {idx + 1}</p>
            <h3 className="mt-2 text-xl font-display text-espresso">{step}</h3>
            <p className="mt-2 text-sm text-muted">{step === 'Upload' && 'Bring CSV, JSON, XLSX, DB sources, or API endpoints.'}{step === 'Detect' && 'Compute DI, DPD, EO, PP, intersectionality, and drift.'}{step === 'Fix' && 'Preview re-weighting, threshold optimization, and in-processing.'}</p>
          </motion.article>
        ))}
      </section>

      <section className="rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
        <h2 className="text-2xl font-display text-espresso">Where teams use FairLens</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {useCases.map((item) => (
            <div key={item} className="rounded-xl bg-caramel10 p-4 text-center font-semibold text-espresso">
              {item}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
