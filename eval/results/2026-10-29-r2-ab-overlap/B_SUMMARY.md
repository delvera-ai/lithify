Phase-0 parallel B summary: stopped; owner review.

[
  {
    "label": "r1-B-rep2",
    "tasks": 3,
    "passes": 2,
    "timeouts": 0,
    "cost_usd": 0.5358,
    "mean_cost_usd": 0.17859999999999998,
    "median_wall_s": 181.4,
    "median_active_s": 224.118,
    "median_api_s": 117.984,
    "median_idle_s": -47.718
  },
  {
    "label": "r1-B-rep3",
    "tasks": 0,
    "passes": 0,
    "timeouts": 0,
    "cost_usd": 0,
    "mean_cost_usd": null,
    "median_wall_s": null,
    "median_active_s": null,
    "median_api_s": null,
    "median_idle_s": null
  }
]

Two runs maximum; pipeline concurrency 4 each. Budgets $7/run and $30/phase unchanged. Median-wall tripwire remains 620s.
Mean-cost tripwire applies only to A per owner decision.
