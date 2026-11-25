# DESIGN.md — Audience, Intent & Design Thinking

## 1. Intent & Creative Vision
* **Core Question:** How can generative AI capture the delicate sensory memory and intergenerational love of the Ethiopian coffee ritual without reducing it to a generic ethnographic trope?
* **Emotional Target:** Nostalgic warmth, ancestral gratitude, grounded cultural pride.
* **Format & Platform:** 60–90s short film designed primarily for mobile feeds (9:16 vertical TikTok/Instagram Reels/YouTube Shorts) and widescreen viewing (16:9).

## 2. Target Audience & Persona
* **Primary Persona:** *Hermela*, 24, second-generation Ethiopian diaspora in Washington D.C., nostalgic for family memories, consumes short-form vertical cultural stories on phones.
* **Secondary Persona:** *Ato Tadesse*, 58, Addis Ababa resident, appreciative of authentic cultural details, cautious about AI misrepresenting traditional heritage.
* **Viewing Context:** Watched on smartphones with sound on, captions active.

---

## 3. Shot-by-Shot Filmmaking Rationale
*Every shot must carry a clear dramatic reason justifying its place in the 68-second cut:*

| Shot ID | Shot Type | Duration | Dramatic & Narrative Purpose |
| :--- | :--- | :--- | :--- |
| **shot_01** | Establishing | 7.0s | Establishes the tranquil mountain dawn of Addis Ababa before domestic life stirs; grounds the viewer in the altitude and morning atmosphere. |
| **shot_02** | Close-Up | 6.5s | Tactile opening: shows weathered grandmotherly hands sorting green coffee beans on a straw tray, honoring the physical labor of the ritual. |
| **shot_03** | Medium Portrait | 7.0s | Introduces the central character (Elder Emaye); locks visual continuity and conveys her serene resilience against past hardships. |
| **shot_04** | Close-Up | 6.5s | Sensory transformation: beans crackling and darkening over charcoal; fragrant smoke rising into sunlight. |
| **shot_05** | Medium Close-Up | 7.0s | Cultural climax: the traditional wafting of the roasting pan smoke toward guests with maternal blessings (*Merekata*). |
| **shot_06** | Insert | 6.0s | Focuses on the iconic black clay *Jebena* simmering; symbolizes patience, time, and ancestral craftsmanship. |
| **shot_07** | Medium | 7.0s | Transmission beat: pouring the first round (*Abol*) into handleless *cini* cups while the younger generation gathers. |
| **shot_08** | Medium Close-Up | 6.5s | Modern diaspora bridge: the granddaughter holding a cup by an apartment window, connecting memory across oceans. |
| **shot_09** | Wide | 7.0s | Poetic resolution: embers and empty cups on the woven mat (*ketema*), leaving the viewer with quiet continuity and warmth. |

---

## 4. User Testing & Iteration Notes

### User Test 1: The Radio Cut Prototype (Audio & Black Screen)
* **Date & Medium:** Conducted with 3 test viewers (1 diaspora family member, 2 peers on Slack).
* **Artifact Tested:** `outputs/exports/radio_cut.mp4` (Narration + Temp Score).
* **Participant Feedback:**
  1. *Viewer A (Diaspora):* "The Amharic cadence in shot 3 felt a bit too brisk. In real life, grandmother takes a deep breath before giving advice."
  2. *Viewer B (Peer):* "The acoustic music drowned out the word 'መከራ' (hardship) around second 16."
  3. *Viewer C (Elder):* "The transition between the roasting and the pouring was too quick; we usually linger on the scent."
* **Changes Made to Storyboard:**
  * Extended `shot_03` duration from 5.5s to 7.0s and added a prosody pause instruction.
  * Adjusted audio ducking threshold to 0.02 and deepened score attenuation under voice.
  * Inserted `shot_05` specifically dedicated to the smoke-wafting blessing.

---

### User Test 2: The Near-Final Cut (Video + Subtitles + Ducked Score)
* **Date & Medium:** Conducted with 3 test viewers using the 9:16 mobile export.
* **Participant Feedback:**
  1. *Viewer A:* "Subtitles were partially blocked by TikTok's UI buttons at the very bottom."
  2. *Viewer B:* "The face of the grandmother in shot 5 looked slightly different from shot 3."
  3. *Viewer C:* "The end card timing felt natural, giving a moment to reflect before loop restarted."
* **Changes Made to Assembly:**
  * Raised subtitle positioning (`MarginV=90`) to sit safely inside vertical phone UI safe zones.
  * Re-conditioned shot 5 prompt with explicit character facial traits from the golden reference sheet to eliminate identity drift.
