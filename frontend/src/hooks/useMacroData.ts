/**
 * useMacroData — fetches all four macro API endpoints once on mount.
 * Data is slow-moving (macro series update hourly at most) so no polling is needed.
 * The at-a-glance WebSocket subscription is handled separately in AtAGlanceStrip.
 */
import { useState, useEffect } from 'react'

export interface CurvesData {
  us_curve: { tenor: string; yield: number }[]
  uk_curve: { tenor: string; yield: number }[]
  us_curve_1m_ago: { tenor: string; yield: number }[]
  us_curve_1y_ago: { tenor: string; yield: number }[]
  uk_curve_1m_ago: { tenor: string; yield: number }[]
  uk_curve_1y_ago: { tenor: string; yield: number }[]
  spreads_2s10s: { date: string; value: number }[]
  spreads_5s30s: { date: string; value: number }[]
  curve_shape: string
  curve_shape_context: string
  real_yield: { date: string; value: number }[]
  stale: boolean
}

export interface IndicatorPanel {
  current_us: number | null
  current_uk?: number | null
  current_eu?: number | null
  history_us: number[]
  history_uk?: number[]
  history_eu?: number[]
  mom: number | null
  yoy: number | null
}

export interface PolicyRatesPanel {
  fed: number | null
  boe: number | null
  ecb: number | null
  history_fed: number[]
  history_boe: number[]
  history_ecb: number[]
}

export interface IndicatorsData {
  cpi: IndicatorPanel
  core_cpi: IndicatorPanel
  pce: IndicatorPanel
  gdp: IndicatorPanel
  unemployment: IndicatorPanel
  policy_rates: PolicyRatesPanel
}

export interface RiskData {
  vix_term_structure: { date: string; spot: number; vix3m: number | null; vix6m: number | null }[]
  history_depth_ok: boolean
  contango: boolean
  regime: string
  percentile_1y: number | null
  percentile_5y: number | null
  put_call_ratio: { date: string; value: number }[]
  stale: boolean
}

export interface FearGreedComponent {
  name: string
  score: number
  source: string
}

export interface SentimentData {
  fear_greed: {
    score: number
    band: string
    components: FearGreedComponent[]
  }
  seasonality: {
    ticker: string
    monthly_avg: { month: string; avg_return: number }[]
  }
  stale: boolean
}

export interface MacroData {
  curves: CurvesData | null
  indicators: IndicatorsData | null
  risk: RiskData | null
  sentiment: SentimentData | null
  loading: boolean
  error: string | null
}

export function useMacroData(): MacroData {
  const [curves, setCurves] = useState<CurvesData | null>(null)
  const [indicators, setIndicators] = useState<IndicatorsData | null>(null)
  const [risk, setRisk] = useState<RiskData | null>(null)
  const [sentiment, setSentiment] = useState<SentimentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchAll() {
      try {
        const [curvesRes, indicatorsRes, riskRes, sentimentRes] = await Promise.all([
          fetch('/api/macro/curves'),
          fetch('/api/macro/indicators'),
          fetch('/api/macro/risk'),
          fetch('/api/macro/sentiment'),
        ])

        if (cancelled) return

        if (!curvesRes.ok || !indicatorsRes.ok || !riskRes.ok || !sentimentRes.ok) {
          setError('FETCH ERROR — CHECK BACKEND')
          setLoading(false)
          return
        }

        const [curvesData, indicatorsData, riskData, sentimentData] = await Promise.all([
          curvesRes.json(),
          indicatorsRes.json(),
          riskRes.json(),
          sentimentRes.json(),
        ])

        if (cancelled) return

        setCurves(curvesData)
        setIndicators(indicatorsData)
        setRisk(riskData)
        setSentiment(sentimentData)
        setError(null)
      } catch (err) {
        if (!cancelled) setError('FETCH ERROR — CHECK BACKEND')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchAll()
    return () => { cancelled = true }
  }, [])

  return { curves, indicators, risk, sentiment, loading, error }
}
