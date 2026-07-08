# Business Logic

---

## 1. Domain Whitelisting
**Rule:** URLs matching the whitelist bypass ML evaluation and are marked SAFE.
**Why:** Prevents false positives on trusted platforms. Reduces backend load.
**Where:** `content.js:isWhitelisted()` — checks 20 trusted domains (google.com, github.com, etc.) including subdomain matching.

---

## 2. Threat Classification Thresholds
**Rule:** Probability → tier mapping:
| Tier | Probability Range | Action |
| :--- | :--- | :--- |
| SAFE | `[0, 0.35)` | Green badge |
| LOW_RISK | `[0.35, 0.50)` | Yellow badge |
| SUSPICIOUS | `[0.50, 0.75)` | Orange badge |
| DANGEROUS | `[0.75, 1.0]` | Red badge + click blocked |

**Why:** Threshold of `0.35` (not `0.50`) prioritizes recall over precision — it's better to flag a legitimate URL than to miss a phishing one.
**Where:** `app.py:get_threat_level()` (backend) and `content.js:checkUrl()` (frontend, re-evaluated after hybrid boost).

---

## 3. NLP Keyword Analysis
**Rule:** Email body scanned for keywords across 5 weighted categories:
| Category | Weight | Examples |
| :--- | :--- | :--- |
| urgency | 3 | "urgent", "immediately", "within 24 hours" |
| account | 4 | "verify your account", "suspended", "unusual activity" |
| financial | 3 | "bank account", "wire transfer", "payment required" |
| action | 2 | "click here", "download now", "verify now" |
| threat | 5 | "will be terminated", "legal action" |

Score ≥ 10 = HIGH, ≥ 5 = MEDIUM, ≥ 1 = LOW, 0 = NONE.
**Why:** Phishing relies on psychological manipulation that URL-only analysis cannot detect.
**Where:** `content.js:analyzeEmailText()`

---

## 4. Hybrid Scoring
**Rule:** Final probability = ML prob + NLP boost:
- NLP score ≥ 10 → `+0.15`
- NLP score ≥ 5 → `+0.08`
- Capped at `1.0`

**Why:** Adjusts ambiguous URLs upward when found in high-risk email contexts.
**Where:** `content.js:checkUrl()`

---

## 5. Sender Validation
**Rule:** Flag sender if: (a) domain ends with suspicious TLD (`.xyz`, `.top`, etc.), or (b) name contains brand keywords but sent from freemail provider.
**Why:** Brand impersonation from free email accounts is a common phishing vector.
**Where:** `content.js:isSuspiciousSender()`

---

## 6. Graceful Degradation
**Rule:** If backend is unreachable: if NLP score ≥ 10, mark URL as SUSPICIOUS (prob 0.6). Otherwise, silent fail.
**Why:** Extension must never break Gmail UI regardless of backend status.
**Where:** `content.js:checkUrl()` catch block.

---

## 7. Reputation Scoring
**Rule:** Aggregated score (0–100): PhishTank verified (+40), VirusTotal malicious (+40), VT ≥ 1 engine (+10), domain age < 180 days (+20). Score ≥ 40 = dangerous.
**Why:** External intelligence provides ground-truth signals independent of ML model.
**Where:** `reputation.py:get_reputation()`
