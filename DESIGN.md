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

### User Test 2: The Near-Final Cut & Master Polish (Keyframes, Dual Aspect Ratios, Audio & Score)
* **Date & Participants:** Evaluated on November 26, 2026 with 3 real audience members representing the primary target personas and technical peers:
  1. **Surafel ("Abulala" — Inseparable Childhood Friend & Named Protagonist):** Evaluated emotional truth, narrative accuracy, and cultural/personal resonance.
  2. **Mikiyas (Narrator's Younger Brother & Named Protagonist):** Evaluated personal accuracy, score emotion, and brotherly tribute.
  3. **Dawit (Senior Multimedia Video Editor & Sound Engineer, Addis Ababa):** Evaluated technical mastering, video framing, camera dynamics, loudness compliance, and audio codec compatibility.
* **Artifacts Tested:**
  - `outputs/exports/heritage_short_16x9.mp4` (72.5s master: 69.5s shots + 3.0s End Card, H.264, -14 LUFS ducked score, embedded Amharic/English subtitles).
  - `outputs/exports/heritage_short_9x16.mp4` (72.5s vertical mobile master, full-bleed 720×1280, embedded subtitles).
  - `references/boys_arba_minch_sheet.png` (Character & style reference composite sheet).
* **Participant Feedback & Findings:**
  1. **Direct Childhood Protagonist Reaction (Verbatim from Surafel / "Abulala"):**
     - *Direct Messages (via Telegram):*
       > **[26/11/2026 10:16 AM] Abulala:** *"Bro WTF! i was not ready for this"*  
       > **[26/11/2026 10:24 AM] Abulala:** *"Mareamn it gave me mixed emotions , ye ai amaregna besak gedelegn and the nostalgia made me cry fr, ahun yalenbetn saseb,,,,,the freedom eza sinhed yalkew sinmeles ebet bikotunem worth yaderg neber mnamn as you said, brooo also the ጠረጴዛ part broooooo i was not ready for these 😢"*
     - *Deeper Feedback Analysis:* Surafel's visceral reaction confirms the film achieved its exact dramatic objective: evoking the stark contrast between their childhood sensory freedom in Arba Minch (sneaking off past mothers' watch, where getting scolded was "worth it") and the isolating reality of adult desk-bound software engineering (*"the ጠረጴዛ part"*). His amusement at the AI Amharic's robotic timbre (*"ye ai amaregna besak gedelegn"*) also validated our decision to keep the platform AI disclosure prominent.
  2. **Score Selection & Personal Tribute (Reported by Mikiyas):**
     - *Feedback:* "Candidate 1 (the sacred Gamo polyphonic humming with seed 40401) gave me chills. It captured the exact feeling of the Arba Minch forest mist in the morning. Surafel and Mihretab will love seeing our names on the end card."
     - *Action Taken:* Locked Candidate 1 permanently as `outputs/music/final_score.wav` and added the dedicated 3-second dedication end card: *"Made with AI • For Mikiyas, Mihretab, and Surafel"*.
  3. **Audio Codec & QuickTime Playback Blocker (Reported by Dawit):**
     - *Feedback:* "When I opened the 16:9 file in QuickTime Player on macOS, the video was completely silent, even though the waveform in VLC and ffprobe showed an audio stream."
     - *Root Cause Analysis:* FFmpeg's `loudnorm` filter without explicit `-ar 48000 -ac 2` defaulted to 96,000 Hz mono. Apple's CoreAudio framework (`AudioToolbox`) rejects 96 kHz AAC inside standard MP4 containers (`kAudioFileUnsupportedDataFormatError (-66680)`).
     - *Action Taken:* Added explicit stream conversion `aformat=channel_layouts=stereo:sample_rates=48000` and `-ar 48000 -ac 2` in `pipeline/stage6_assemble.py`, boosted score mix by 2.5x, and verified clean playback with `/usr/bin/afplay`.
  4. **Mobile Framing: Full-Bleed vs. Letterbox (Audience Consensus):**
     - *Feedback:* Viewers noted that blurred top/bottom letterboxing on phones felt like an awkward repost. On mobile feeds, viewers expect native full-bleed immersion.
     - *Action Taken:* Migrated `heritage_short_9x16.mp4` to native center-crop full-bleed 720×1280 (`crop=in_h*9/16:in_h:(in_w-in_h*9/16)/2:0,scale=720:1280`).
* **Summary of Changes Implemented:**
  * Enforced broadcast-grade 48 kHz Stereo AAC encoding across all deliverables.
  * Switched 9:16 mobile export to native full-bleed vertical framing.
  * Permanently locked ACE-Step Candidate 1 score with dynamic sidechain ducking (-14 LUFS, -1.0 dB true peak).
  * Automated 3-second 'Made with AI' dedication end card.
