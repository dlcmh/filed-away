# Latecomer industrialization: certification, catch-up, and the portfolio state

Notes on how a latecomer industrial power actually closes the gap — certification
as the true bottleneck, the three-act catch-up pattern, and the portfolio-state
model of industrial investment.

## Certification, not technology, is the bottleneck

Mature-industry entrants import certification, not just technology. The C919 is
the pure case: the airframe is COMAC's own design, but the load-bearing
certifiable subsystems — LEAP engines (CFM), avionics and fly-by-wire
(GE/Honeywell/Rockwell Collins), landing gear (Liebherr) — are imported from
suppliers whose certification pedigrees the FAA/EASA system demands. This made
the aircraft certifiable by CAAC years earlier than a clean-sheet supply chain
would have, at the price of strategic exposure: the supplying countries can
squeeze those dependencies at will. The C919 is, in effect, a delivery vehicle
for certified Western subsystems wrapped in a Chinese airframe.

HarmonyOS rhymes with this structure. The "already-certified subsystems" are
the C/C++ toolchains, vendor driver SDKs, and Android/AOSP heritage; the
certification regime is telecom carrier acceptance, silicon-vendor enablement,
and an engineering organization's review culture — all of which already spoke
C++. Huawei chose C++ over Rust in 2019 not on technical merit but because a
ground-up OS is a decade-scale, ten-thousand-engineer undertaking, and betting
it on a language without the talent pool, embedded supply chain, or
safety-critical track record was the larger risk. Rust-for-Linux, the proof
that postdated the decision, arrived too late to change it. The compromise the
industry converged on: memory-unsafe core, memory-safe periphery, migrating
outward-in.

The C919 had no choice — there was no certifiable alternative to importing the
subsystems. Software's "certification" was self-inflicted path dependence;
HarmonyOS could have chosen differently at a schedule and talent price. The
plane is the purer case of renting the giants' shoulders; the OS is the hybrid
that spends the next decade converting imported trust into indigenous
capability.

## The three-act catch-up pattern

Tunnel boring machines are the cleanest exhibit: import the machines, absorb
the operating knowledge, hit the ceiling (premium prices, long lead times,
refusal to tailor designs to Chinese geology), then build domestic — now
dominant, at a fraction of the cost, with exports following. High-speed rail
compressed the same curve: technology-transfer deals with Kawasaki, Siemens,
Alstom in the 2000s; a native platform (CR400) setting the global benchmark by
the 2010s; international contracts against the former suppliers by the 2020s.

The catch-up phase gets the headlines, but the pattern's real signature is the
third act: **commoditizing what was once a moat.** The moats of incumbents are
accumulated hand-written, hand-audited artifacts — code, certification
pedigrees, manufacturing tacit knowledge. If latecomer technology makes the
accumulation restartable (generate-and-verify against a specification in years
instead of decades), the moat inverts, and lack of legacy becomes an advantage
— no sunk-cost ABI to honor. ML-driven optimization of compiler schedules and
NPU kernels (TVM/Ansor, MLGO, TileLang-style DSLs) is the leading edge of
this; the harder frontier is verified synthesis, where the scarce human input
becomes the specification rather than the implementation.

## The portfolio state

The national IC fund ("Big Fund") functions as a venture portfolio, not a
project. Phase 1 (2014, ~138B RMB) seeded the whole stack — SMIC, YMTC,
design houses, equipment makers; some bets succeeded, some were forgettable,
one became a corruption scandal. Judged on IRR, mediocre. Judged on "did China
have fabs, designers, and equipment makers when export controls arrived,"
it was the state's best spending — the fund bought the *option*, and the
option paid off precisely because the adverse scenario materialized.

Write-off tolerance is the strategic asset. Local-government missteps —
duplicated chip parks, fab frauds like HSMC, bond-financed stadiums — are
individually indefensible, but failure is survivable at every level: the LGFV
absorbs the loss, the official rotates, the industry keeps the trained workers
and the shell. It is wasteful the way evolution is wasteful — a high gross
mutation rate against a brutal selection environment. The Western alternative
makes fewer mistakes per dollar but also fewer bets, because the minister who
funds a failed champion commits career suicide — one consolidated national
champion per technology, and if it is wrong, the whole position is wrong.

The portfolio is rebalanced across decades by the same general partner: Big
Fund Phase 3 (2024, ~344B RMB) rotates into the positions sanctions proved
weak — equipment, materials, HBM.

## The horizon defense of "overinvestment"

The overinvestment critique (Pettis et al.) priced Chinese infrastructure with
Western discount rates and Western tenure horizons — a category error twice
over. A US administration with a four-year clock cannot hold a 30-year
positive-NPV project even when it can see one; China's system can eat the early
negative years. The high-speed rail network was condemned at buildout and now
moves billions of passengers at fares it was mocked for nobody affording — the
ridership compounded into infrastructure built ahead of demand.

Two honest limits. First, horizon length rescues *slow* projects, not
*terminal-value-zero* projects: prefecture airports and half-empty districts
in shrinking tier-3/4 cities are negative at any discount rate, and roughly
some fraction of post-2010 buildout is in that category. "Built 30% too much"
can be true simultaneously with "the 70% was worth building and only this
actor could have built it." Second, the NPV of the project is not the NPV of
the economy: projects funded through LGFVs borrowing against land values
inflated by the borrowing left a balance sheet that had to reconcile — the
property-sector deflation is that reconciliation. A long-horizon state can
hold assets, but the debt on them is often held by short-horizon entities.

Synthesis: the frontier airports-to-nowhere are the venture losses inside a
portfolio whose index fund was the rail network, the grid, the ports, and the
cold chain. The West's quarterly lens saw the losses and missed that the
portfolio, not the individual bet, was the investment. The open question —
the first one a long horizon does not automatically win — is whether the
demographic turn and the debt load let the horizon keep extending.
