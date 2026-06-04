"""Curated, cited Vedic-astrology knowledge base (Phase C, first cut).

This is the interpretive corpus the Jyotishi agent retrieves from. It distils
WELL-ESTABLISHED classical significations into structured, cited entries so the
agent reasons from grounded material rather than only parametric memory.

Honesty rules baked in (CONTRACT #4 + #5):
  - Citations name the TEXT and TOPIC (e.g. "BPHS — graha karakatva"), not
    fabricated chapter/verse numbers we cannot verify.
  - Where schools genuinely differ, the entry says so.
  - This is interpretation reference, NOT chart computation. The engine remains
    the only source of placements (CONTRACT #1).

`knowledge_for_chart()` selects the slice relevant to one chart for RAG.
"""

from __future__ import annotations

from engine import constants as C
from engine.chart import ChartFact

# --- Grahas: karakatva (what each planet signifies) -------------------------
GRAHAS = {
    "Sun":     dict(nature="mild malefic; royal/sattvic", karaka="soul (atma), ego, vitality, father, authority, government, status, health, leadership", ref="BPHS — graha karakatva; Phaladeepika ch. 2"),
    "Moon":    dict(nature="benefic when waxing; sattvic", karaka="mind (manas), emotions, mother, nourishment, the public, fluids, comfort, memory", ref="BPHS — graha karakatva; Saravali on Chandra"),
    "Mars":    dict(nature="malefic; tamasic", karaka="energy, courage, drive, siblings (younger), land/property, engineering, conflict, discipline, surgery", ref="BPHS — graha karakatva; Phaladeepika ch. 2"),
    "Mercury": dict(nature="benefic by association; rajasic", karaka="intellect, speech, commerce, calculation, communication, writing, trade, skill, analysis", ref="BPHS — graha karakatva; Saravali on Budha"),
    "Jupiter": dict(nature="great benefic; sattvic", karaka="wisdom, dharma, wealth, children, teachers/guru, counsel, expansion, fortune, law, finance", ref="BPHS — graha karakatva; Phaladeepika ch. 2"),
    "Venus":   dict(nature="benefic; rajasic", karaka="relationships, spouse, luxury, art, beauty, comfort, vehicles, refinement, pleasures, design", ref="BPHS — graha karakatva; Saravali on Shukra"),
    "Saturn":  dict(nature="malefic; tamasic", karaka="discipline, labour, longevity, delay, structure, service, masses, detachment, perseverance, old age", ref="BPHS — graha karakatva; Phaladeepika ch. 2"),
    "Rahu":    dict(nature="shadow malefic; tamasic/amplifying", karaka="ambition, obsession, foreign/unconventional, technology, disruption, sudden gains, illusion, speculation", ref="BPHS — on the nodes; Jaimini tradition"),
    "Ketu":    dict(nature="shadow malefic; moksha-karaka", karaka="detachment, research, spirituality, past-life skill, sudden loss/insight, niche mastery, liberation", ref="BPHS — on the nodes; Jaimini tradition"),
}

# --- Bhavas: what each house governs ----------------------------------------
BHAVAS = {
    1:  dict(name="Tanu (self)", signifies="body, self, vitality, temperament, overall life direction", ref="BPHS — bhava-vichara"),
    2:  dict(name="Dhana (wealth)", signifies="accumulated wealth, family, speech, food, savings, values", ref="BPHS — bhava-vichara (a wealth/dhana house)"),
    3:  dict(name="Sahaja (effort)", signifies="courage, initiative, younger siblings, skills, communication, short travel", ref="BPHS — bhava-vichara"),
    4:  dict(name="Sukha (home)", signifies="mother, home, property, vehicles, inner peace, education base", ref="BPHS — bhava-vichara"),
    5:  dict(name="Putra (creativity)", signifies="intelligence, children, creativity, speculation, purva-punya (merit), romance", ref="BPHS — bhava-vichara (a trikona/lakshmi house)"),
    6:  dict(name="Ari (challenges)", signifies="enemies, debts, disease, service, daily work, obstacles overcome", ref="BPHS — bhava-vichara (a dusthana)"),
    7:  dict(name="Yuvati (partnership)", signifies="spouse, partnerships, business dealings, the public, contracts", ref="BPHS — bhava-vichara (a kendra/maraka)"),
    8:  dict(name="Randhra (transformation)", signifies="longevity, sudden events, inheritance, hidden things, research, crises", ref="BPHS — bhava-vichara (a dusthana)"),
    9:  dict(name="Dharma (fortune)", signifies="fortune, dharma, father/guru, higher learning, long travel, grace", ref="BPHS — bhava-vichara (a trikona/lakshmi house)"),
    10: dict(name="Karma (career)", signifies="career, public standing, action in the world, authority, reputation", ref="BPHS — bhava-vichara (a kendra)"),
    11: dict(name="Labha (gains)", signifies="gains, income, fulfilment of desires, networks, elder siblings", ref="BPHS — bhava-vichara (an upachaya/dhana house)"),
    12: dict(name="Vyaya (loss/liberation)", signifies="expenditure, loss, foreign lands, isolation, sleep, moksha", ref="BPHS — bhava-vichara (a dusthana/moksha)"),
}

# --- Dignity: what a planet's state means for results -----------------------
DIGNITY_MEANING = {
    "exalted":      "gives its significations in their highest, most refined form; very strong to deliver good results",
    "moolatrikona": "near-maximal strength; expresses its nature powerfully and favourably",
    "own":          "comfortable and stable; reliably delivers its significations",
    "neutral":      "ordinary strength; results depend on house, aspects, and dasha",
    "debilitated":  "weakened and strained in its significations; needs cancellation (neecha-bhanga) or support to give results",
    "n/a":          "a shadow graha (node) — judged by house, sign, dispositor, and conjunctions rather than classical dignity",
}

# --- Signs: brief temperament (element/quality/lord live in constants) -------
SIGN_TRAITS = {
    0:  "Aries — assertive, pioneering, impulsive (Mars-ruled, fiery cardinal)",
    1:  "Taurus — steady, sensual, resource-building (Venus-ruled, earthy fixed)",
    2:  "Gemini — curious, communicative, versatile (Mercury-ruled, airy dual)",
    3:  "Cancer — nurturing, emotional, protective (Moon-ruled, watery cardinal)",
    4:  "Leo — proud, generous, authoritative (Sun-ruled, fiery fixed)",
    5:  "Virgo — analytical, precise, service-minded (Mercury-ruled, earthy dual)",
    6:  "Libra — relational, balanced, refined (Venus-ruled, airy cardinal)",
    7:  "Scorpio — intense, secretive, transformative (Mars-ruled, watery fixed)",
    8:  "Sagittarius — philosophical, optimistic, dharmic (Jupiter-ruled, fiery dual)",
    9:  "Capricorn — disciplined, ambitious, pragmatic (Saturn-ruled, earthy cardinal)",
    10: "Aquarius — humanitarian, unconventional, systemic (Saturn-ruled, airy fixed)",
    11: "Pisces — compassionate, imaginative, spiritual (Jupiter-ruled, watery dual)",
}
SIGN_TRAITS_REF = "Brihat Jataka / Phaladeepika — rasi-svabhava"

# --- Nakshatras: deity, symbol, gana, theme ---------------------------------
# Standard nakshatra lore (Vedic tradition). Index aligns with C.NAKSHATRAS.
NAKSHATRA_INFO = {
    "Ashwini": dict(deity="Ashwini Kumaras", symbol="horse's head", gana="Deva", theme="swift initiative, healing, new beginnings"),
    "Bharani": dict(deity="Yama", symbol="yoni", gana="Manushya", theme="restraint, bearing burdens, transformation"),
    "Krittika": dict(deity="Agni", symbol="razor/flame", gana="Rakshasa", theme="sharpness, purification, cutting through"),
    "Rohini": dict(deity="Brahma/Prajapati", symbol="ox-cart", gana="Manushya", theme="growth, fertility, material beauty"),
    "Mrigashira": dict(deity="Soma", symbol="deer's head", gana="Deva", theme="searching, curiosity, gentleness"),
    "Ardra": dict(deity="Rudra", symbol="teardrop", gana="Manushya", theme="storm, breakthrough, intensity"),
    "Punarvasu": dict(deity="Aditi", symbol="quiver of arrows", gana="Deva", theme="renewal, return, expansion"),
    "Pushya": dict(deity="Brihaspati", symbol="cow's udder", gana="Deva", theme="nourishment, support, the most auspicious nakshatra"),
    "Ashlesha": dict(deity="Nagas", symbol="coiled serpent", gana="Rakshasa", theme="penetration, cunning, kundalini, entwining"),
    "Magha": dict(deity="Pitris", symbol="throne", gana="Rakshasa", theme="ancestry, authority, legacy"),
    "Purva Phalguni": dict(deity="Bhaga", symbol="front of a bed", gana="Manushya", theme="pleasure, creativity, rest, romance"),
    "Uttara Phalguni": dict(deity="Aryaman", symbol="back of a bed", gana="Manushya", theme="patronage, contracts, generosity"),
    "Hasta": dict(deity="Savitar", symbol="hand", gana="Deva", theme="skill, craftsmanship, dexterity"),
    "Chitra": dict(deity="Tvashtar/Vishwakarma", symbol="bright jewel", gana="Rakshasa", theme="design, brilliance, craftsmanship of form"),
    "Swati": dict(deity="Vayu", symbol="young shoot in wind", gana="Deva", theme="independence, adaptability, trade, movement"),
    "Vishakha": dict(deity="Indra-Agni", symbol="triumphal arch", gana="Rakshasa", theme="goal-focus, ambition, determination"),
    "Anuradha": dict(deity="Mitra", symbol="lotus", gana="Deva", theme="friendship, devotion, cooperation"),
    "Jyeshtha": dict(deity="Indra", symbol="umbrella/earring", gana="Rakshasa", theme="seniority, responsibility, protective power"),
    "Mula": dict(deity="Nirriti", symbol="bundle of roots", gana="Rakshasa", theme="getting to the root, dissolution, investigation"),
    "Purva Ashadha": dict(deity="Apas (waters)", symbol="fan/tusk", gana="Manushya", theme="invincibility, persuasion, early victory"),
    "Uttara Ashadha": dict(deity="Vishvedevas", symbol="elephant tusk", gana="Manushya", theme="lasting victory, integrity, leadership"),
    "Shravana": dict(deity="Vishnu", symbol="ear / three footprints", gana="Deva", theme="listening, learning, connection, reputation"),
    "Dhanishta": dict(deity="Vasus", symbol="drum", gana="Rakshasa", theme="rhythm, wealth, music, abundance"),
    "Shatabhisha": dict(deity="Varuna", symbol="empty circle / 100 healers", gana="Rakshasa", theme="healing, secrecy, systems, the unconventional"),
    "Purva Bhadrapada": dict(deity="Aja Ekapada", symbol="front of funeral cot", gana="Manushya", theme="intensity, idealism, transformation through fire"),
    "Uttara Bhadrapada": dict(deity="Ahir Budhnya", symbol="back of funeral cot", gana="Manushya", theme="depth, wisdom, the cosmic serpent, stillness"),
    "Revati": dict(deity="Pushan", symbol="fish", gana="Deva", theme="nourishing safe passage, completion, compassion"),
}
NAKSHATRA_REF = "Taittiriya Brahmana / classical nakshatra lore"

# --- Yogas: what the texts promise ------------------------------------------
YOGA_INFO = {
    "gajakesari_yoga": dict(promise="intelligence, virtue, lasting reputation, prosperity, and the favour of authority; strengthens the mind (Moon) with wisdom (Jupiter)", ref="BPHS / classical — Gaja-Kesari Yoga", school="measured from Moon (some texts: from Lagna)"),
    "dhana_yoga": dict(promise="capacity for wealth accumulation and gains, especially through the significations of the 2nd/11th lords involved", ref="BPHS — Dhana Yogas (combinations of 2/5/9/11 lords)", school="Parashara"),
    "raja_yoga": dict(promise="rise in status, success, authority and recognition through the union of kendra (power) and trikona (fortune) lords", ref="BPHS — Raja Yogas", school="Parashara"),
    "budhaditya_yoga": dict(promise="sharp intellect, communication skill, and analytical ability (Sun + Mercury); note possible combustion of Mercury to weigh", ref="classical — Budha-Aditya Yoga", school="Parashara"),
}

# --- Dasha: themes of each mahadasha lord's period ---------------------------
DASHA_EFFECTS = {
    "Sun":     "themes of authority, recognition, father, health, government dealings, self-assertion",
    "Moon":    "themes of mind, emotions, mother, public life, travel, comfort and change",
    "Mars":    "themes of energy, drive, property, siblings, competition, courage and conflict",
    "Mercury": "themes of intellect, commerce, communication, study, trade and skilful work",
    "Jupiter": "themes of wisdom, growth, wealth, children, teaching, dharma and fortune",
    "Venus":   "themes of relationships, comfort, art, luxury, vehicles and refinement",
    "Saturn":  "themes of discipline, labour, responsibility, delay-then-reward, structure and detachment",
    "Rahu":    "themes of ambition, the unconventional/foreign, technology, sudden rise, intensity and illusion",
    "Ketu":    "themes of detachment, research, spirituality, endings, niche mastery and inward turning",
}
DASHA_REF = "BPHS — Vimshottari dasha phala"


# --- Divisional chart significations (fuller than the labels) ---------------
VARGA_MEANING = {
    "D1": "Rasi — the physical body, overall life and personality; the foundation every other varga refines.",
    "D2": "Hora — wealth and sustenance; the Sun's hora (Leo) vs the Moon's hora (Cancer) colours one's earning temperament.",
    "D3": "Drekkana — siblings, courage, initiative, and the fruit of self-effort.",
    "D4": "Chaturthamsha — fixed assets, land, home, vehicles, and inner contentment.",
    "D7": "Saptamsha — children, progeny, and creative/biological legacy.",
    "D9": "Navamsha — dharma, marriage, and the inner strength (or weakness) of every planet; the most important varga after the rasi.",
    "D10": "Dashamsha — career, profession, status, authority and action in the world.",
    "D12": "Dwadashamsha — parents and inherited ancestral patterns.",
}
VARGA_MEANING_REF = "BPHS — shodasa-varga; Phaladeepika"

# --- Yoga library (reference definitions; the engine detects only a few) -----
# The agent may name a yoga as PRESENT only if it is in the chart's active_yogas
# OR it can verify the stated condition from the given placements; otherwise it
# is general classical knowledge. This avoids false yoga claims (CONTRACT #1).
YOGA_LIBRARY = {
    # Pancha Mahapurusha (a planet in own/exalted sign placed in a kendra)
    "Ruchaka": dict(condition="Mars in own/exalted sign in a kendra", result="courage, leadership, a commanding physique and martial success", ref="BPHS / Saravali — Pancha Mahapurusha"),
    "Bhadra": dict(condition="Mercury in own/exalted sign in a kendra", result="sharp intellect, eloquence, scholarship and business acumen", ref="BPHS / Saravali — Pancha Mahapurusha"),
    "Hamsa": dict(condition="Jupiter in own/exalted sign in a kendra", result="wisdom, virtue, respect, a dharmic and fortunate nature", ref="BPHS / Saravali — Pancha Mahapurusha"),
    "Malavya": dict(condition="Venus in own/exalted sign in a kendra", result="luxury, beauty, refinement, vehicles and artistic gifts", ref="BPHS / Saravali — Pancha Mahapurusha"),
    "Sasa": dict(condition="Saturn in own/exalted sign in a kendra", result="authority over others, discipline, leadership of the masses, longevity", ref="BPHS / Saravali — Pancha Mahapurusha"),
    # Lunar yogas (planets relative to the Moon)
    "Sunapha": dict(condition="a planet (not Sun) in the 2nd from the Moon", result="self-earned wealth, intelligence, good reputation", ref="BPHS — Chandra yogas"),
    "Anapha": dict(condition="a planet (not Sun) in the 12th from the Moon", result="health, well-being, a pleasant nature and renown", ref="BPHS — Chandra yogas"),
    "Durudhara": dict(condition="planets in BOTH the 2nd and 12th from the Moon", result="wealth, generosity, comforts and a balanced life", ref="BPHS — Chandra yogas"),
    "Adhi": dict(condition="benefics in the 6th, 7th and 8th from the Moon", result="leadership, prosperity, trustworthiness and high office", ref="BPHS — Adhi yoga"),
    "Chandra-Mangala": dict(condition="Moon conjunct or with Mars", result="drive to earn, business sharpness, but emotional intensity", ref="classical — Chandra-Mangala yoga"),
    "Gajakesari": dict(condition="Jupiter in a kendra from the Moon", result="intelligence, virtue, lasting reputation and prosperity", ref="classical — Gaja-Kesari yoga"),
    # Solar yogas
    "Vesi": dict(condition="a planet (not Moon) in the 2nd from the Sun", result="balanced speech, steadiness, eventual gains", ref="BPHS — Surya yogas"),
    "Vasi": dict(condition="a planet (not Moon) in the 12th from the Sun", result="skilfulness, charity, recognition", ref="BPHS — Surya yogas"),
    "Budha-Aditya": dict(condition="Sun conjunct Mercury", result="intelligence, communication and analytical skill (weigh Mercury's combustion)", ref="classical — Budha-Aditya yoga"),
    # Raja & Dhana yogas
    "Raja (kendra-trikona)": dict(condition="a kendra lord associates with a trikona lord", result="rise in status, authority, success and recognition", ref="BPHS — Raja yogas"),
    "Dharma-Karmadhipati": dict(condition="the 9th and 10th lords associate", result="a powerful rise through righteous work; a premier Raja yoga", ref="BPHS — Raja yogas"),
    "Neecha-Bhanga Raja": dict(condition="a debilitated planet's debility is cancelled (e.g. its dispositor or exaltation-lord is strong/in a kendra)", result="a fall reversed into great rise; success after early struggle", ref="BPHS — Neecha Bhanga"),
    "Vipreet Raja (Harsha)": dict(condition="the 6th lord placed in the 6th/8th/12th", result="victory over enemies, health, sudden rise from adversity", ref="classical — Vipreet Raja yoga"),
    "Vipreet Raja (Sarala)": dict(condition="the 8th lord placed in the 6th/8th/12th", result="longevity, fearlessness, rise through crisis", ref="classical — Vipreet Raja yoga"),
    "Vipreet Raja (Vimala)": dict(condition="the 12th lord placed in the 6th/8th/12th", result="thrift, independence, gains from expenditure", ref="classical — Vipreet Raja yoga"),
    "Dhana (2/11)": dict(condition="association of the 2nd and 11th lords", result="capacity to accumulate wealth and gains", ref="BPHS — Dhana yogas"),
    "Lakshmi": dict(condition="the 9th lord strong and Venus well-placed/dignified", result="wealth, fortune, beauty and prosperity", ref="classical — Lakshmi yoga"),
    "Saraswati": dict(condition="Mercury, Jupiter and Venus strong in kendra/trikona/2nd", result="brilliance in learning, arts and expression", ref="classical — Saraswati yoga"),
    "Amala": dict(condition="a benefic in the 10th from Lagna or Moon", result="a spotless reputation and lasting good name", ref="BPHS — Amala yoga"),
    "Parivartana (Maha)": dict(condition="mutual exchange between lords of auspicious houses", result="powerful mutual support of those houses' significations", ref="BPHS — Parivartana yogas"),
    # Arishta / cautionary
    "Kemadruma": dict(condition="no planet (excl. Sun/nodes) in the 2nd or 12th from the Moon and no kendra support", result="isolation, struggle, instability — often cancelled by aspects/kendra planets", ref="BPHS — Kemadruma (with bhanga)"),
    "Shakata": dict(condition="the Moon in the 6th, 8th or 12th from Jupiter", result="fluctuating fortunes (cancelled if Moon is in a kendra from Lagna)", ref="classical — Shakata yoga"),
    "Daridra": dict(condition="the 11th lord placed in a dusthana (6/8/12)", result="drain on gains, financial struggle — read with other strengths", ref="classical — Daridra yoga"),
    "Grahan (eclipse)": dict(condition="Sun or Moon conjunct Rahu or Ketu", result="intensity, eclipse of the luminary's significations; needs careful judgement", ref="classical — Grahan dosha"),
}

# --- Remedies (upaya) — traditional custom, NOT guarantees -------------------
REMEDY_CAVEAT = ("Remedies below are TRADITIONAL classical custom, not guarantees "
                 "and not medical/financial advice. Gemstones especially should be "
                 "chosen with a qualified astrologer, never self-prescribed.")
REMEDIES = {
    "Sun":     dict(beej_mantra="Om Hraam Hreem Hraum Sah Suryaya Namah", gemstone="ruby", deity="Surya / Shiva", daana="wheat, jaggery (Sunday)", day="Sunday"),
    "Moon":    dict(beej_mantra="Om Shraam Shreem Shraum Sah Chandraya Namah", gemstone="pearl", deity="Parvati / Shiva", daana="rice, milk, silver (Monday)", day="Monday"),
    "Mars":    dict(beej_mantra="Om Kraam Kreem Kraum Sah Bhaumaya Namah", gemstone="red coral", deity="Hanuman / Kartikeya", daana="red lentils, jaggery (Tuesday)", day="Tuesday"),
    "Mercury": dict(beej_mantra="Om Braam Breem Braum Sah Budhaya Namah", gemstone="emerald", deity="Vishnu / Ganesha", daana="green gram, green cloth (Wednesday)", day="Wednesday"),
    "Jupiter": dict(beej_mantra="Om Graam Greem Graum Sah Gurave Namah", gemstone="yellow sapphire", deity="Brihaspati / Vishnu", daana="turmeric, gold, yellow items (Thursday)", day="Thursday"),
    "Venus":   dict(beej_mantra="Om Draam Dreem Draum Sah Shukraya Namah", gemstone="diamond / white sapphire", deity="Lakshmi", daana="white cloth, sugar, ghee (Friday)", day="Friday"),
    "Saturn":  dict(beej_mantra="Om Praam Preem Praum Sah Shanaischaraya Namah", gemstone="blue sapphire", deity="Shani / Hanuman", daana="sesame, iron, black cloth (Saturday)", day="Saturday"),
    "Rahu":    dict(beej_mantra="Om Bhraam Bhreem Bhraum Sah Rahave Namah", gemstone="hessonite (gomed)", deity="Durga", daana="mustard, blanket", day="Saturday"),
    "Ketu":    dict(beej_mantra="Om Sraam Sreem Sraum Sah Ketave Namah", gemstone="cat's eye (lehsunia)", deity="Ganesha", daana="multicoloured blanket, sesame", day="Tuesday"),
}
REMEDIES_REF = "classical remedial Jyotish (mantra/ratna/daana tradition)"

# --- Doshas (definitions + traditional remedies; detection is in signals.py) -
DOSHA_INFO = {
    "manglik": dict(meaning="Mars in 1/2/4/7/8/12 stresses marriage/partnership matters; intensity varies and many cancellations exist (e.g. both partners Manglik, Mars in own/exalt).", remedy="Hanuman worship, Mangal mantra, marrying after careful matching; do not treat as a verdict.", ref="Kuja/Mangal dosha"),
    "kala_sarpa": dict(meaning="all grahas hemmed between Rahu and Ketu; can bring intensity, delays then breakthroughs. Often overstated — judge the whole chart.", remedy="Rahu-Ketu propitiation, Nag worship, Mahamrityunjaya mantra.", ref="Kala Sarpa yoga/dosha"),
    "kemadruma": dict(meaning="an isolated Moon (no support in 2nd/12th, no kendra planets) can bring emotional/financial instability; frequently cancelled.", remedy="strengthen the Moon (Monday observances, Shiva worship), build supportive routines.", ref="Kemadruma yoga"),
    "sade_sati": dict(meaning="Saturn's ~7.5-year transit over the 12th, 1st and 2nd from the natal Moon — a maturing, demanding period. NOTE: the engine does not yet compute transits, so this is described in principle only.", remedy="Shani/Hanuman worship, discipline, service, patience.", ref="Shani sade-sati (gochara)"),
}

# --- Honest limits on the predictive layer (CONTRACT #1, #4) -----------------
PREDICTIVE_NOTES = {
    "transits": "Gochara (current transits) are NOT computed by the engine yet (Phase E/roadmap). Do not state any transit position or sade-sati status as fact; speak only in principle if asked.",
    "ashtakavarga": "Ashtakavarga bindus (SAV/BAV) are NOT computed yet (Phase E). Do not cite any SAV/BAV numbers.",
    "antardasha": "Only the Vimshottari mahadasha sequence is provided; sub-periods (antardasha/bhukti) are not yet computed, so discuss the mahadasha as the timing window.",
}


def functional_lords(asc_sign: int) -> dict:
    """Functional benefic/malefic/yogakaraka lords for an ascendant (Parashari).
    Kendra(1/4/7/10)+trikona(1/5/9) lords are functional benefics; a planet lording
    both a kendra and a trikona is a yogakaraka. Lords of 3/6/11 (and 8/12) tend to
    functional malefic. classical_ref: BPHS — functional nature of grahas by Lagna."""
    lord_of = {h: C.SIGN_LORD[(asc_sign + h - 1) % 12] for h in range(1, 13)}
    kendra_lords = {lord_of[h] for h in (1, 4, 7, 10)}
    trikona_lords = {lord_of[h] for h in (1, 5, 9)}
    yogakaraka = sorted((kendra_lords & trikona_lords) - {lord_of[1]})
    benefics = sorted(kendra_lords | trikona_lords)
    malefics = sorted({lord_of[h] for h in (3, 6, 11)})
    return {"lord_of_house": lord_of, "yogakaraka": yogakaraka,
            "functional_benefics": benefics, "functional_malefics": malefics,
            "ref": "BPHS — functional nature of grahas by Lagna"}


# --- RAG selector ------------------------------------------------------------

def knowledge_for_chart(chart: ChartFact, signals: dict) -> dict:
    """Select the cited knowledge slice relevant to ONE chart, for the agent.

    Pure: reads the computed ChartFact + fired signals and assembles the
    classical reference material the agent should ground its reading in.
    """
    asc_idx = chart.ascendant.sign
    lagna_lord = C.SIGN_LORD[asc_idx]

    grahas = {}
    for name, p in chart.planets.items():
        g = GRAHAS.get(name, {})
        grahas[name] = {
            "placement": f"{p.sign_name} ({SIGN_TRAITS[p.sign]}), house {p.house} "
                         f"[{BHAVAS[p.house]['name']}], dignity {p.dignity}"
                         + (" (R)" if p.retrograde else ""),
            "karaka": g.get("karaka"),
            "nature": g.get("nature"),
            "dignity_meaning": DIGNITY_MEANING.get(p.dignity),
            "ref": g.get("ref"),
        }

    moon_nak = chart.dasha.moon_nakshatra
    asc_nak = chart.ascendant.nakshatra
    nak = {n: {**NAKSHATRA_INFO.get(n, {}), "lord": C.nakshatra_lord(C.NAKSHATRAS.index(n)),
               "ref": NAKSHATRA_REF}
           for n in {moon_nak, asc_nak} if n in NAKSHATRA_INFO}

    active = [k for k in YOGA_INFO if signals.get(k, {}).get("value", 0) >= 1.0]
    yogas = {k: YOGA_INFO[k] for k in active}

    dasha_lords = [md.lord for md in chart.dasha.mahadashas[:3]]
    dasha = {lord: {"theme": DASHA_EFFECTS.get(lord), "ref": DASHA_REF}
             for lord in dict.fromkeys(dasha_lords)}

    # Deterministic pattern detectors (live in signals.py; no import cycle).
    from signals import detect_doshas, planet_aspects, combustion
    doshas = detect_doshas(chart)
    aspects = planet_aspects(chart)
    combust = {g: True for g, c in combustion(chart).items() if c}

    func = functional_lords(asc_idx)

    # Remedies surfaced for the planets that most need support: the lagna lord,
    # any debilitated/combust graha, and the current dasha lord.
    needy = {lagna_lord, dasha_lords[0] if dasha_lords else lagna_lord}
    needy |= {n for n, p in chart.planets.items() if p.dignity == "debilitated"}
    needy |= set(combust)
    remedies = {p: REMEDIES[p] for p in needy if p in REMEDIES}

    return {
        "lagna": {"sign": chart.ascendant.sign_name, "traits": SIGN_TRAITS[asc_idx],
                  "lord": lagna_lord, "house_meaning": BHAVAS[1], "ref": SIGN_TRAITS_REF},
        "functional_lords": func,
        "grahas": grahas,
        "graha_aspects": aspects,
        "combust_planets": sorted(combust),
        "bhavas": BHAVAS,
        "nakshatras": nak,
        "active_yogas": yogas,
        "yoga_library": YOGA_LIBRARY,
        "doshas": doshas,
        "dasha_themes": dasha,
        "divisional_meanings": {"meanings": VARGA_MEANING, "ref": VARGA_MEANING_REF},
        "remedies": {"caveat": REMEDY_CAVEAT, "per_planet": remedies, "ref": REMEDIES_REF},
        "dosha_reference": DOSHA_INFO,
        "predictive_notes": PREDICTIVE_NOTES,
        "note": "Cited classical reference for INTERPRETATION only. Placements come "
                "from the deterministic engine, not from this knowledge base. Name a "
                "yoga as present only if it is in active_yogas or its condition is "
                "verifiable from the placements.",
    }
