# CivicPulse — Live Demonstration Script & Viva Defense Walkthrough

A structured, examiner-ready 6-step walkthrough for defending CivicPulse during viva evaluations and capstone presentations.

---

## Prerequisites Before Starting the Demo
1. Ensure the FastAPI backend is running:
   ```bash
   python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
   ```
2. Ensure the Vite React frontend is running:
   ```bash
   cd client
   npm run dev
   ```
3. Open `http://localhost:3000` in your browser.

---

## 🌟 Opening Hook: The Flagship End-to-End Scenario
> **Examiner Hook:** *"Most civic apps broadcast 10-page municipal PDFs that citizens never read until their taps run dry. Watch what happens when an official Hyderabad water board notice is ingested into CivicPulse."*

### The Scenario:
- **Event:** A scheduled 12-hour drinking water shutdown in **Madhapur** for pipeline realignment.
- **Citizen:** Suresh, an apartment resident who relies on tankers and prefers Telugu.

### Live Action:
1. **Live Ingestion (Admin & Ingest Tab):**
   Paste this real-world announcement into the ingestion textarea:
   ```text
   HMWSSB Official Release: Due to 1200mm dia Krishna Phase-3 pipeline junction repair, drinking water supply will be completely suspended from 9 AM to 9 PM tomorrow across Madhapur, Ayyappa Society, and Kavuri Hills. Citizens are advised to store sufficient water in advance.
   ```
   Click **"Ingest & Process Text"**.

2. **Immediate Pipeline Execution (< 1s):**
   - **Spam Filtering:** Classified as 0.0% spam (legitimate municipal notice).
   - **Category & Severity Classification:** Predicted `water_supply` (Confidence: 0.94) and `warning`.
   - **Hyperlocal Gazetteer Resolution:** Automatically resolves `Madhapur`, `Ayyappa Society`, and `Kavuri Hills` to canonical coordinates (`17.4483, 78.3915`).
   - **Temporal Extraction:** Extracts `start_time` (tomorrow 9:00 AM), `expected_end_time` (tomorrow 9:00 PM), and `duration_hours: 12.0`.
   - **Proactive Reminders:** Schedules automated reminders at 12 hours and 2 hours before the 9:00 AM shutdown.

3. **Multilingual Telugu Delivery & TTS:**
   - In the top navbar, switch language to **"🇮🇳 తెలుగు"**.
   - Show the alert card rendered in fluent Telugu:
     - Title: **మంచినీటి సరఫరా అంతరాయం హెచ్చరిక: HMWSSB Official Release...**
     - Action Checklist: *"ముందస్తుగా సరిపడా తాగునీటిని నిల్వ చేసుకోండి."*
   - Click the **"Listen"** button: browser Web Speech API reads the Telugu alert aloud.

4. **Telegram Bot Dispatch:**
   - Demonstrate the Telegram bot command (`/alerts` or `/reminders`):
     Delivers formatted notification directly to the resident's phone with bold time windows and action steps.

---

## Step 2: Trust Layer — Source Credibility, Rumors & Stale Event Linking (CO3)
- **Goal:** Show how CivicPulse prevents misinformation and solves alert overload.
- **Actions:**
  1. Show the **Source Tier Badges** on alert cards:
     - **Official Authority** (green shield: GHMC, HMWSSB, TGSPDCL, Traffic Police)
     - **Verified News** (blue badge: The Hindu, Deccan Chronicle, Times of India)
     - **Unverified Public Report** (prominent amber warning banner urging discretion).
  2. Demonstrate **Cancellation / Event Linking**:
     - Ingest a follow-up: *"HMWSSB update: Madhapur pipeline repair completed early; water supply restored."*
     - Show that the system detects the keyword *"restored"*, automatically links to the original Madhapur alert (`parent_alert_id`), and marks the stale alert as **resolved**.
- **Viva Talking Point:** *"Civic panic happens when citizens act on rumors or when outdated emergency notices stay active for days. Our dual-layer trust pipeline provides instant credibility badges and automatically resolves stale events when restoration updates arrive."*

---

## Step 3: Hyperlocal Circles & Household Personalization (CO2 & CO3)
- **Goal:** Prove that two citizens in the same neighborhood receive tailored guidance based on their household infrastructure.
- **Actions:**
  1. Click the **Locality pill** in the navbar to open the **Hyperlocal & Profile Modal**:
     - **Tab 1 (Primary Locality):** Show fuzzy gazetteer matching — typing *"Gachibowli X Roads"* resolves instantly to canonical Gachibowli with coordinates.
     - **Tab 2 (Saved Circles):** Show multiple monitored zones (Home in Gachibowli, Office in Hitec City, Parents in Begumpet) with adjustable Haversine distance radii (1 to 15 km).
     - **Tab 3 (Household Profile):**
       - Toggle Water Source: **Municipal Tap** vs. **Tanker Dependent** vs. **Borewell**.
       - Toggle Housing: **Apartment Society** vs. **Independent Bungalow**.
       - Toggle Vulnerable Care: **Peritoneal Dialysis / Medical Oxygen** or **Elderly Alone**.
  2. Return to the alert feed:
     - Point out the **"Tailored for your profile"** badge.
     - For **Apartment + Tanker**: checklist advises *"Notify RWA to ration common overhead water"* and *"Book tankers 6-8 hours in advance"*.
     - For **Power Outage with Dialysis**: effective severity is elevated to **CRITICAL**, injecting life-support UPS battery verification steps.
- **Viva Talking Point:** *"One size does not fit all in civic management. An independent house with a borewell reacts differently to a water shutdown than a 200-flat apartment reliant on municipal tankers. CivicPulse adapts the actionable checklist to the citizen's exact domestic infrastructure."*

---

## Step 4: Explainable AI (XAI) — Auditing Model Decisions (CO4)
- **Goal:** Demystify black-box machine learning for municipal officers.
- **Actions:**
  1. On any alert, click **"Why this alert?"** to expand the **LIME Attribution Panel**:
     - Green highlighted tokens (e.g. *pipeline, rupture, repair, shutdown*) show positive attribution towards `water_supply`.
     - Red tokens indicate features pulling towards other categories.
     - Display model confidence and feature weights.
  2. Click **"Full View →"** to inspect the side-by-side comparison between the raw announcement and the AI-extracted structured fields.
- **Viva Talking Point:** *"In municipal governance, automated models cannot be a black box. LIME provides token-level feature attribution so officers can audit why a report was flagged as Critical before broadcasting it to 50,000 residents."*

---

## Step 5: Positioning vs. Google Maps — Complementary, Not Competing
- **Goal:** Answer the quintessential examiner question: *"Why wouldn't citizens just use Google Maps?"*
- **Key Examiner Distinction:**
  1. **Reactive Navigation vs. Proactive Planning:**
     *"Google Maps tells you traffic is red while you are already in the car. CivicPulse tells you 12 hours before you leave that a flyover will be closed, so you work from home or reschedule."*
  2. **Causal Understanding:**
     *"Google Maps shows a red line without explanation. CivicPulse tells you WHY: an 8-inch water main burst near the junction, backed by official HMWSSB bulletins."*
  3. **Non-Transit Civic Infrastructure:**
     *"Google Maps has zero awareness of drinking water shutdowns, scheduled power cuts, or ward-level civic orders. CivicPulse covers the entire civic lifeline of your home and workplace."*

---

## Step 6: Model Hub & Academic Syllabus Coverage (CO1 – CO4)
- **Goal:** Satisfy every theoretical syllabus requirement.
- **Actions:**
  1. Click the **"Model Hub"** tab in the navigation bar.
  2. Walk through the interactive performance dashboards:
     - **CO1:** Comparison table across 10 classical models (Stacking Ensemble top performer at 90.8% accuracy).
     - **CO2:** Preprocessing ablation study (showing accuracy drops when lemmatization or normalization is omitted) + t-SNE / PCA / UMAP 2D embedding projections.
     - **CO3:** Confusion matrices, ROC-AUC curves (macro AUC = 0.98), and Silhouette clustering scores.
     - **CO4:** Fine-tuned DistilBERT comparison, low-resource learning curves ($N \in \{50, 100, 200, 500\}$), and IndicBERT/MuRIL code-mixed evaluation on Romanized Telugu.
- **Closing Statement:** *"CivicPulse bridges advanced NLP theory with real-world municipal impact: turning noisy, unstructured official notifications into personalized, proactive, life-saving alerts for every Hyderabad citizen."*
