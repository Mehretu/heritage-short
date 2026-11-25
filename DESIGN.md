# DESIGN.md — Audience, Intent & Design Thinking

## 1. Intent & Creative Vision
* **Working Title:** *The Forty Springs of Arba Minch (የአርባ ምንጭ ምንጮች)*
* **Core Question:** How does the sensory memory of childhood brotherhood and raw natural wonder in Arba Minch anchor an adult navigating the modern, high-pressure professional grind?
* **Emotional Target:** Deep nostalgic warmth, innocent joy, connection to nature, enduring brotherhood.
* **Format & Platform:** 60–90s short film designed for dual presentation: mobile vertical feeds (9:16 for TikTok/Reels/Shorts) and horizontal cinematic presentation (16:9).

---

## 2. Target Audience & Persona
* **Primary Persona:** *Mikiyas, Mihretab & Surafel* (the brother and childhood friends), now adults working across cities, reminiscing about the freedom of youth.
* **Secondary Persona:** Young Ethiopian diaspora and urban professionals who spend long hours behind computer screens in concrete offices, feeling disconnected from the natural landscapes and carefree adventures of their upbringing.
* **Viewing Context:** Watched on mobile devices with headphones or phone speakers, captions burned in for dual Amharic and English comprehension.

---

## 3. Narrative Arc (The Flashback Structure)
1. **The Anchor (Present):** A tired developer sitting at a cluttered work desk in the evening, fingers resting on the keyboard. A photo, water glass, or screen reflection triggers a memory.
2. **The Reveal (Past - Arba Minch):** Breathtaking panoramic view from the hill overlooking the emerald canopy of the groundwater forest between Lake Abaya and Lake Chamo.
3. **The Mischief (Childhood):** Whispering behind the mud-brick wall, ducking away from mothers' calls on Sunday morning.
4. **The Descent:** Bare feet racing along forest dirt tracks shaded by giant fig trees.
5. **The Secret Sanctuary:** The crystal-clear natural pool bubbling from the forty underground springs.
6. **The Joy:** Splashing, swimming, laughing under shafts of golden sunlight piercing the canopy.
7. **The Return (Present):** The narrator looks up from the keyboard with a gentle smile, knowing that heaven on earth still flows inside him.

---

## 4. Shot-by-Shot Filmmaking Rationale
*Every shot has a stated dramatic reason justifying its place in the 70-second cut:*

| Shot ID | Shot Type | Duration | Dramatic & Narrative Purpose |
| :--- | :--- | :--- | :--- |
| **shot_01** | Medium Close-Up | 6.5s | **The Catalyst:** Establishes the narrator at a modern work desk late at night, tired eyes lit by monitor glow; creates visual contrast with the lush nature to come. |
| **shot_02** | Extreme Wide | 7.5s | **The Awakening (Arba Minch):** Grand establishing shot from the hill above Arba Minch, revealing the endless sea of green forest canopy stretching between the two lakes. |
| **shot_03** | Medium | 6.5s | **The Conspiracy:** Childhood friends (Mihretab, Surafel, Mikiyas, narrator) whispering conspiratorially near a gate, glancing back to make sure moms aren't looking. |
| **shot_04** | Wide Tracking | 7.0s | **The Escape:** The four boys running barefoot down a forest trail, laughing freely as branches part and sunlight glints. |
| **shot_05** | Close-Up | 6.0s | **The Sacred Water:** Underground spring water bubbling up through black volcanic stones and sand; tactile purity of the "Forty Springs". |
| **shot_06** | Wide Action | 7.5s | **The Plunge:** Boys jumping into the natural emerald swimming pool, water droplets catching the sunlight like diamonds. |
| **shot_07** | Medium Close-Up | 7.0s | **The Bond:** Surafel and Mikiyas laughing on sun-warmed rocks by the water's edge, soaking wet and utterly carefree. |
| **shot_08** | Wide Sunset | 7.0s | **The Golden Walk Home:** Golden hour dusk filtering through tall acacia trees as the tired, smiling boys walk back before nightfall. |
| **shot_09** | Close-Up | 6.5s | **The Resolution:** Back at the desk in the present; narrator looking away from the monitor with a serene, grounded smile. The spring is still alive in memory. |

---

## 5. User Testing & Feedback Protocol

### User Test 1: The Radio Cut Prototype (Audio & Narration Audit)
* **Date & Participants:** Evaluated with native Ethiopian listener and family audience.
* **Artifact Tested:** `outputs/exports/radio_cut.wav` (75.5s combined Amharic narration + ducked ambient score).
* **Participant Feedback & Findings:**
  1. **Voice Gender Mismatch:** The default AI voice was female, which breaks immersion for a first-person male memory about his brother and friends.
  2. **Severe Phonetic Breakdown on Amharic Gemination (ጥብቅና ላልት):** The model mispronounced 19 crucial words:
     - `ጠረጴዛዬ`, `ይሮጣል።`, `ወደ`, `የምድር`, `ጥቅጥቅ`, `ወንድሜ`, `ተደብቀን`, `ቅዳሜ`, `ሳንደናገጥ`, `ወደ ደኑ ስንሮጥ`, `የሚፈልቁት`, `ንጹሕ`, `ገንዳ`, `ጭንቀት`, `ቀልጦ ይጠፋል`, `በድንጋይ`, `ይበልጥ`, `ስትጠልቅ`, `ብትቆጣንም`, `ይፈሳሉ።`
     - The AI read them with flat English-like phonetic pacing, ignoring unwritten Ge'ez consonant doubling.
  3. **Pacing & Timing:** The 75.5-second total duration landed squarely in the desired 60–90 second window, and the ambient stream background was praised for naturalness.
* **Concrete Changes Made to Storyboard & Pipeline:**
  * Updated `voice_profile` in `storyboard.json` to explicitly configure a male voice (`voiceName: "Puck"`) and updated the prompt to enforce native Addis Ababa gemination rules.
  * Added human voice-over bypass in `pipeline/stage2_narration.py` so authentic voice recordings can be compared against AI synthesis for the final report.

---

### Planned User Test 2: The Near-Final Cut (Dual Aspect Ratios & Keyframes)
* **Focus Questions:** Subtitle readability on mobile 9:16 safe areas, visual consistency of the 4 boys across shots, and loudness balance.
