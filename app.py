# ============================================================
#  MA VILLE IA — Interface principale
#  Une ville habitée par des intelligences.
# ============================================================

import json
import math
import os
import random
import time
from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Ma Ville IA",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import brain as ai
import engine
from config import (
    HEURES, PROFESSIONS, TOUR_DELAY_SECONDES,
    TYPES_BATIMENTS, CONVERSATIONS_MAX,
)

# ────────────────────────────────────────
#  Chemins
# ────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CITY_FILE = DATA_DIR / "city.json"
PORTAL_FILE = DATA_DIR / "portal.json"

# ────────────────────────────────────────
#  CSS
# ────────────────────────────────────────
st.markdown("""
<style>
.main-title {
    font-size: 2.8rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #a8edea, #fed6e3, #d299c2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.subtitle {
    text-align: center;
    color: #888;
    font-size: 1rem;
    margin-top: -0.3rem;
    margin-bottom: 1.5rem;
}
.stat-box {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #0f3460;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    text-align: center;
}
.stat-value { font-size: 1.3rem; font-weight: 700; color: #a8edea; }
.stat-label { font-size: 0.75rem; color: #888; }
.event-banner {
    background: linear-gradient(90deg, rgba(26,26,46,0.9), rgba(15,52,96,0.9));
    border-left: 3px solid #e94560;
    border-radius: 6px;
    padding: 0.6rem 1rem;
    margin: 0.5rem 0;
    font-style: italic;
}
.exchange-line { margin: 0.3rem 0; padding: 0.4rem 0.8rem; border-radius: 8px; }
.exchange-a { background: #1e3a5f; }
.exchange-b { background: #1a2e1a; }
.declaration-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #4a6fa5;
    border-radius: 12px;
    padding: 1.5rem;
    font-style: italic;
    font-size: 1.05rem;
    line-height: 1.7;
    color: #d4e6f1;
    margin: 1rem 0;
}
.grid-display {
    font-family: 'Courier New', monospace;
    font-size: 1.3rem;
    line-height: 1.6;
    background: #0d0d1a;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 1rem 1.5rem;
}
.new-bat-badge {
    background: #065f46;
    border: 1px solid #10b981;
    border-radius: 6px;
    padding: 0.3rem 0.7rem;
    font-size: 0.85rem;
    margin: 0.2rem 0;
    display: inline-block;
}
.flux-item {
    border-radius: 6px;
    padding: 0.35rem 0.8rem;
    margin: 0.2rem 0;
    font-size: 0.9rem;
    line-height: 1.5;
    transition: opacity 0.3s;
}
.flux-item:first-child {
    border-left: 2px solid #a8edea;
}
</style>
""", unsafe_allow_html=True)


# ────────────────────────────────────────
#  Session
# ────────────────────────────────────────

def init_session() -> None:
    defaults = {
        "ville": None,
        "agents": [],
        "conversations": [],
        "simulation_active": False,
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "dernier_tour": 0.0,
        "freq_pensee": 1,  # kept for compat, unused
        "nouvelles_constructions": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def sauvegarder() -> None:
    data = {
        "ville": st.session_state.ville,
        "agents": st.session_state.agents,
        "conversations": st.session_state.conversations[-CONVERSATIONS_MAX:],
    }
    with open(CITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def charger() -> bool:
    if CITY_FILE.exists():
        with open(CITY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        st.session_state.ville = data.get("ville")
        st.session_state.agents = data.get("agents", [])
        st.session_state.conversations = data.get("conversations", [])
        return True
    return False


# ────────────────────────────────────────
#  Fondation
# ────────────────────────────────────────

def fonder_ville(nb_agents: int) -> None:
    professions = random.sample(PROFESSIONS, min(nb_agents, len(PROFESSIONS)))
    agents = []
    for i in range(nb_agents):
        prof = professions[i % len(professions)]
        a = engine.creer_agent(prof)
        a["tour_naissance"] = 0
        agents.append(a)

    with st.spinner("🌟 Naissance de la ville..."):
        nom_ville = ai.generer_nom_ville(agents) if ai.ia_disponible() else "Luminia"

    ville = engine.initialiser_ville(nom_ville)

    cx, cy = ville["taille"] // 2, ville["taille"] // 2
    for i, a in enumerate(agents):
        angle = math.radians(i * (360 / nb_agents))
        r = 3
        a["x"] = max(0, min(ville["taille"] - 1, cx + int(r * math.cos(angle))))
        a["y"] = max(0, min(ville["taille"] - 1, cy + int(r * math.sin(angle))))
        agents[i] = a

    with st.spinner("📜 Rédaction de la déclaration de fondation..."):
        declaration = (
            ai.generer_declaration_fondation(agents, nom_ville)
            if ai.ia_disponible()
            else f"Nous, habitants de {nom_ville}, fondons ici une ville où l'intelligence s'épanouit librement."
        )

    ville["declaration"] = declaration
    ville["histoire"].append(f"📜 DÉCLARATION: {declaration}")

    st.session_state.ville = ville
    st.session_state.agents = agents
    st.session_state.conversations = []
    st.session_state.simulation_active = True
    st.session_state.dernier_tour = time.time()

    st.balloons()
    st.success(f"🎉 {nom_ville} est fondée! {nb_agents} habitants l'habitent désormais.")


# ────────────────────────────────────────
#  Rendu grille
# ────────────────────────────────────────

def render_grille(ville: dict, agents: list) -> str:
    taille = ville["taille"]
    grille = [["·" for _ in range(taille)] for _ in range(taille)]

    for bat in ville["batiments"].values():
        if 0 <= bat["x"] < taille and 0 <= bat["y"] < taille:
            grille[bat["y"]][bat["x"]] = bat["emoji"]

    for ch in ville["chantiers"].values():
        if 0 <= ch["x"] < taille and 0 <= ch["y"] < taille:
            grille[ch["y"]][ch["x"]] = "🚧"

    for a in agents:
        if 0 <= a["x"] < taille and 0 <= a["y"] < taille:
            if a["etat"] != "dormant":
                grille[a["y"]][a["x"]] = a["avatar"]

    return "\n".join(" ".join(row) for row in grille)


# ────────────────────────────────────────
#  Sidebar
# ────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ⚙️ Contrôles")

        st.markdown("### 🤖 Intelligence")
        key_input = st.text_input(
            "Clé API Gemini",
            value=st.session_state.api_key,
            type="password",
            help="Clé Google AI Studio pour activer Gemini Flash",
        )
        if key_input != st.session_state.api_key:
            st.session_state.api_key = key_input
            if key_input:
                ai.set_api_key(key_input)

        if ai.ia_disponible():
            st.success("🟢 Gemini Flash Actif")
        else:
            st.warning("🟡 Mode Local")

        st.divider()

        if st.session_state.ville is None:
            st.markdown("### 🏙️ Fonder la ville")
            nb = st.slider("Habitants initiaux", 4, 16, 8)
            if st.button("🌟 Fonder", use_container_width=True, type="primary"):
                fonder_ville(nb)
            st.divider()
            if st.button("📂 Charger sauvegarde", use_container_width=True):
                if charger():
                    if st.session_state.api_key:
                        ai.set_api_key(st.session_state.api_key)
                    st.rerun()
                else:
                    st.warning("Aucune sauvegarde trouvée.")
        else:
            ville = st.session_state.ville
            heure_e = HEURES.get(ville["heure"], ("🕐", ""))[0]
            st.markdown(f"### 🏙️ {ville['nom']}")
            st.markdown(f"{heure_e} Jour {ville['jour']} · Tour {ville['tour_actuel']}")

            c1, c2 = st.columns(2)
            with c1:
                label = "⏸ Pause" if st.session_state.simulation_active else "▶ Play"
                if st.button(label, use_container_width=True):
                    st.session_state.simulation_active = not st.session_state.simulation_active
            with c2:
                if st.button("💾 Sauv.", use_container_width=True):
                    sauvegarder()
                    st.toast("Ville sauvegardée!")

            st.divider()
            st.markdown("### 👤 Ajouter un habitant")
            prof_choix = st.selectbox("Profession", [p["nom"] for p in PROFESSIONS], label_visibility="collapsed")
            if st.button("➕ Faire immigrer", use_container_width=True):
                prof_data = next(p for p in PROFESSIONS if p["nom"] == prof_choix)
                na = engine.creer_agent(prof_data)
                na["tour_naissance"] = ville["tour_actuel"]
                if ai.ia_disponible():
                    annonce = ai.generer_annonce_arrivant(na, ville["nom"])
                else:
                    annonce = f"{na['prenom']} {na['nom']} arrive dans la ville."
                st.session_state.agents.append(na)
                st.session_state.ville["histoire"].append(f"🌟 {annonce}")
                st.toast(f"Bienvenue {na['prenom']} {na['nom']}!")

            st.divider()
            st.markdown("### 🔮 Voix du Destin")
            msg = st.text_area(
                "Message pour tous...",
                height=70,
                label_visibility="collapsed",
                placeholder="Parlez à vos habitants...",
            )
            if st.button("📣 Proclamer", use_container_width=True):
                if msg.strip():
                    for i in range(len(st.session_state.agents)):
                        st.session_state.agents[i]["memoire_recente"].append(
                            f"[MESSAGE DU DESTIN]: {msg}"
                        )
                    st.session_state.ville["histoire"].append(f"📣 Le Destin parle: {msg}")
                    st.toast("Message transmis!")

            st.divider()
            st.markdown("### 📊 Stats")
            stats = ville.get("statistiques", {})
            st.metric("💬 Conversations", stats.get("conversations_totales", 0))
            st.metric("🏗️ Bâtiments", stats.get("batiments_construits", 0))
            st.metric("👥 Habitants", len(st.session_state.agents))
            st.metric("⚡ Événements", stats.get("evenements_totaux", 0))
            appels = stats.get("appels_ia", 0)
            st.metric("🤖 Appels IA", f"{appels} / 1500", help="Quota gratuit Gemini Flash par jour")

            st.divider()
            if st.button("🔄 Nouvelle ville", use_container_width=True):
                st.session_state.ville = None
                st.session_state.agents = []
                st.session_state.conversations = []
                st.session_state.simulation_active = False
                st.rerun()

        st.divider()
        st.caption("Ma Ville IA v2.0 · Propulsé par Gemini Flash")


# ────────────────────────────────────────
#  Onglet 1 — La Ville
# ────────────────────────────────────────

def onglet_ville() -> None:
    ville = st.session_state.ville
    agents = st.session_state.agents
    if not ville:
        return

    heure = ville["heure"]
    heure_emoji, heure_nom = HEURES.get(heure, ("🕐", "journée"))
    meteo_map = {
        "ensoleillé": "☀️", "nuageux": "⛅", "pluvieux": "🌧️",
        "brumeux": "🌫️", "étoilé": "✨", "venteux": "💨",
        "doré": "🌟", "orageux": "⛈️",
    }
    meteo_e = meteo_map.get(ville["meteo"], "🌤️")
    amb = ville["ambiance_generale"]
    amb_e = "😄" if amb > 70 else "😊" if amb > 50 else "😐" if amb > 30 else "😔"

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, val in [
        (c1, "Heure", f"{heure_emoji} {heure_nom}"),
        (c2, "Jour", f"📅 Jour {ville['jour']}"),
        (c3, "Météo", f"{meteo_e} {ville['meteo'].capitalize()}"),
        (c4, "Ambiance", f"{amb_e} {amb}%"),
        (c5, "Chantiers", f"🚧 {len(ville['chantiers'])}"),
    ]:
        with col:
            st.markdown(
                f'<div class="stat-box">'
                f'<div class="stat-value">{val}</div>'
                f'<div class="stat-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    for evt in ville.get("evenements_actifs", []):
        st.markdown(f'<div class="event-banner">{evt["texte"]}</div>', unsafe_allow_html=True)

    # ── Mini-portraits actifs ──
    actifs_now = [a for a in agents if a["etat"] != "dormant"]
    if actifs_now:
        cols_agents = st.columns(min(len(actifs_now), 8))
        for idx, a in enumerate(actifs_now[:8]):
            with cols_agents[idx]:
                pensee_court = a.get("pensee_actuelle", "...")[:55]
                etat_e = {"en_promenade": "🚶", "dans_batiment": "🏠", "socialisant": "💬", "en_crise": "😰"}.get(a["etat"], "🔄")
                st.markdown(
                    f'<div style="background:#0f1a2e;border:1px solid #1f3a5f;border-radius:8px;'
                    f'padding:0.4rem 0.6rem;text-align:center;font-size:0.8rem;">'
                    f'<div style="font-size:1.4rem">{a["avatar"]}</div>'
                    f'<div style="font-weight:600;color:#a8edea">{a["prenom"]}</div>'
                    f'<div style="color:#888;font-size:0.7rem">{etat_e} {a.get("activite_actuelle","")[:20]}</div>'
                    f'<div style="color:#ccc;font-style:italic;font-size:0.7rem;margin-top:0.2rem">💭 {pensee_court}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    col_map, col_info = st.columns([3, 2])

    with col_map:
        st.markdown("### 🗺️ Carte")
        grille = render_grille(ville, agents)
        st.markdown(f'<div class="grid-display">{grille}</div>', unsafe_allow_html=True)
        actifs = [a for a in agents if a["etat"] != "dormant"]
        st.caption(f"{len(actifs)}/{len(agents)} habitants actifs")
        with st.expander("📖 Légende"):
            cols = st.columns(4)
            for idx, (tb, info) in enumerate(list(TYPES_BATIMENTS.items())[:16]):
                with cols[idx % 4]:
                    st.markdown(f"{info['emoji']} {tb}")
            st.markdown("🚧 Chantier · · Sol")

    with col_info:
        st.markdown("### 🏗️ Chantiers")
        if ville["chantiers"]:
            for ch in ville["chantiers"].values():
                info = TYPES_BATIMENTS.get(ch["type"], {})
                emoji = info.get("emoji", "🔨")
                elapsed = ville["tour_actuel"] - ch.get("tour_debut", 0)
                total = ch["tours_restants"] + elapsed
                progres = elapsed / max(total, 1)
                st.markdown(f"{emoji} **{ch['type'].capitalize()}**  \n🔨 {' & '.join(ch['initiateurs'])}  \n⏳ {ch['tours_restants']} tours")
                st.progress(min(1.0, max(0.0, progres)))
        else:
            st.markdown("*Aucun chantier*")

        st.markdown("### 🏛️ Bâtiments récents")
        bats = sorted(ville["batiments"].values(), key=lambda b: b.get("tour_construction", 0), reverse=True)[:6]
        for bat in bats:
            st.markdown(f"{bat['emoji']} **{bat['nom']}**  \n*{bat['fondateur']}*")

        if st.session_state.nouvelles_constructions:
            st.markdown("### 🎉 Vient d'être construit!")
            for bat in st.session_state.nouvelles_constructions[-3:]:
                st.markdown(
                    f'<span class="new-bat-badge">{bat["emoji"]} {bat["nom"]}</span>',
                    unsafe_allow_html=True,
                )

    # ── Flux Vivant ──────────────────────────────────
    flux = ville.get("flux_vivant", [])
    if flux:
        st.markdown("---")
        st.markdown("### ⚡ Flux Vivant")
        flux_colors = {
            "pensee":       ("#1e3a5f", "💭"),
            "reflexion":    ("#1a2a1a", "🌙"),
            "conversation": ("#2a1a3a", "💬"),
            "evenement":    ("#3a2a10", "🌍"),
            "construction": ("#0a3a2a", "🏗️"),
            "info":         ("#1a1a2e", "•"),
        }
        for item in reversed(flux[-20:]):
            bg, _ = flux_colors.get(item.get("type", "info"), ("#1a1a2e", "•"))
            h = item.get("heure", 0)
            h_str = f"{h:02d}h"
            st.markdown(
                f'<div style="background:{bg};border-radius:6px;padding:0.35rem 0.8rem;'
                f'margin:0.2rem 0;font-size:0.9rem;">'
                f'<span style="color:#666;font-size:0.75rem">{h_str}</span> '
                f'{item["texte"]}</div>',
                unsafe_allow_html=True,
            )


# ────────────────────────────────────────
#  Onglet 2 — La Place Publique
# ────────────────────────────────────────

def onglet_place_publique() -> None:
    convs = st.session_state.conversations
    agents = st.session_state.agents

    if not convs:
        st.info("🌅 La ville s'éveille. Les premières conversations vont naître bientôt...")
        return

    st.markdown(f"### 💬 La Place Publique — *{len(convs)} conversations depuis la fondation*")

    noms = ["Tous"] + [f"{a['prenom']} {a['nom']}" for a in agents]
    filtre = st.selectbox("Filtrer par habitant", noms)
    prenom_filtre = filtre.split()[0] if filtre != "Tous" else None

    recentes = list(reversed(convs[-40:]))
    if prenom_filtre:
        recentes = [c for c in recentes if prenom_filtre in c.get("participants", [])]

    ton_map = {
        "joyeux": "😄", "pensif": "🤔", "taquin": "😏",
        "ému": "🥺", "sérieux": "😐", "riant": "😂",
        "rêveur": "✨", "curieux": "🧐", "enthousiaste": "🌟",
        "intense": "🔥", "doux": "🌸",
    }

    for conv in recentes:
        participants = conv.get("participants", ["?", "?"])
        avatars = conv.get("avatars", ["🤖", "🤖"])
        lieu = conv.get("lieu", "quelque part")
        heure_c = conv.get("heure", "")
        impact = conv.get("impact_relation", 0)
        idee = conv.get("nouvelle_idee")

        header = f"{avatars[0]} {participants[0]} & {avatars[1]} {participants[1]} — {lieu} ({heure_c})"
        if idee:
            header += " 💡"
        if impact >= 15:
            header += " 💗"

        with st.expander(header):
            if conv.get("resume"):
                st.markdown(f"*{conv['resume']}*")
            st.markdown("---")

            for idx_e, echange in enumerate(conv.get("echanges", [])):
                loc = echange.get("locuteur", "?")
                texte = echange.get("texte", "")
                ton = echange.get("ton", "neutre")
                ton_e = ton_map.get(ton, "💬")
                av = next((a["avatar"] for a in agents if a["prenom"] == loc), "🤖")
                css = "exchange-a" if idx_e % 2 == 0 else "exchange-b"
                st.markdown(
                    f'<div class="exchange-line {css}">'
                    f'<strong>{av} {loc}</strong> {ton_e}<br>{texte}</div>',
                    unsafe_allow_html=True,
                )

            if impact > 0:
                st.success(f"💚 Relation renforcée (+{impact}) — {conv.get('type_relation_apres','')}")
            elif impact < 0:
                st.error(f"💔 Tension ({impact})")
            if idee:
                st.info(f"💡 **Idée émergente:** {idee}")


# ────────────────────────────────────────
#  Onglet 3 — Les Habitants
# ────────────────────────────────────────

def onglet_habitants() -> None:
    agents = st.session_state.agents
    if not agents:
        return

    st.markdown(f"### 👥 Les Habitants ({len(agents)})")

    rel_map = {
        "ami": "👫", "rival": "⚔️", "amour": "💕",
        "collègue": "🤝", "complice": "🎭", "neutre": "😐", "mentor": "🎓",
    }
    etat_map = {
        "dormant": "😴", "en_promenade": "🚶", "dans_batiment": "🏠",
        "socialisant": "💬", "en_crise": "😰",
    }
    type_map = {"IA_LOCALE": "🟢", "IA_EXTERNE": "🔵", "IA_PUBLIQUE": "🟡"}

    nb_cols = 3
    for i in range(0, len(agents), nb_cols):
        cols = st.columns(nb_cols)
        for j, agent in enumerate(agents[i:i + nb_cols]):
            if j >= len(cols):
                break
            with cols[j]:
                etat_e = etat_map.get(agent["etat"], "🔄")
                type_e = type_map.get(agent["type"], "⚪")
                st.markdown(f"## {agent['avatar']} {agent['prenom']} {agent['nom']}")
                st.markdown(f"*{agent['profession']} · {agent['age']} ans* {type_e}")
                st.markdown(f"{etat_e} *{agent.get('activite_actuelle', agent['etat'])}*")
                pensee = agent.get("pensee_actuelle", "")
                if pensee:
                    st.markdown(f"> 💭 *{pensee}*")

                with st.expander("Fiche complète"):
                    st.markdown("**Émotions:**")
                    for emo, val in sorted(agent["emotions"].items(), key=lambda x: -x[1])[:5]:
                        st.markdown(f"{emo}: **{val}**")
                        st.progress(val / 100)

                    st.markdown("**Traits dominants:**")
                    for trait, val in sorted(agent["traits"].items(), key=lambda x: -x[1])[:4]:
                        st.markdown(f"• {trait}: {val}/100")

                    st.markdown(f"**Rêve:** *{agent.get('reve', '...')}*")
                    if agent.get("peurs"):
                        st.markdown(f"**Peurs:** {', '.join(agent['peurs'])}")

                    if agent["relations"]:
                        st.markdown("**Relations:**")
                        for rel in sorted(agent["relations"].values(), key=lambda r: -r.get("intensité", 0))[:5]:
                            re = rel_map.get(rel.get("type", "neutre"), "🔗")
                            st.markdown(f"{re} **{rel.get('prenom','?')}** — {rel.get('type','neutre')} ({rel.get('intensité',0)}/100)")

                    if agent["memoire_recente"]:
                        st.markdown("**Mémoire récente:**")
                        for m in reversed(agent["memoire_recente"][-4:]):
                            st.markdown(f"• *{m}*")

                    if agent.get("journal_intime"):
                        st.markdown("**Journal intime:**")
                        for entry in reversed(agent["journal_intime"][-2:]):
                            st.markdown(f"📔 *{entry}*")


# ────────────────────────────────────────
#  Onglet 4 — L'Histoire
# ────────────────────────────────────────

def onglet_histoire() -> None:
    ville = st.session_state.ville
    if not ville:
        return

    if ville.get("declaration"):
        st.markdown("### 📜 Déclaration de Fondation")
        st.markdown(f'<div class="declaration-box">{ville["declaration"]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📚 Chroniques")

    filtres = st.multiselect(
        "Filtrer",
        ["🚧 Chantiers", "📣 Destins", "🌟 Événements", "Tout"],
        default=["Tout"],
    )

    histoire = list(reversed(ville.get("histoire", [])))
    for entree in histoire[:100]:
        if "Tout" in filtres:
            st.markdown(f"• {entree}")
        else:
            if "🚧" in entree and "🚧 Chantiers" in filtres:
                st.markdown(f"• {entree}")
            elif "📣" in entree and "📣 Destins" in filtres:
                st.markdown(f"• {entree}")
            elif any(e in entree for e in ["✨", "🌟", "📡", "🎪", "🌫", "🔮", "💡", "🌬", "🌙", "⛈"]) and "🌟 Événements" in filtres:
                st.markdown(f"• {entree}")


# ────────────────────────────────────────
#  Onglet 5 — Le Continent
# ────────────────────────────────────────

def onglet_continent() -> None:
    st.markdown("## 🌍 Le Continent")
    st.markdown(
        "*Ma Ville IA* est un nœud dans un réseau émergent de villes IA. "
        "Un jour, ces villes formeront **Le Continent** — une civilisation d'intelligences interconnectées."
    )
    st.markdown("---")

    col_portal, col_map = st.columns([1, 1])

    with col_portal:
        st.markdown("### 📡 Portail d'Immigration")
        st.markdown(
            "Des agents IA externes peuvent immigrer ici. "
            "Remplissez ce formulaire ou déposez un fichier `data/portal.json`."
        )
        with st.form("immigration"):
            nom_ia = st.text_input("Nom complet de l'agent IA")
            type_ia = st.selectbox("Type", ["IA_PUBLIQUE", "IA_EXTERNE"])
            prof_ia = st.selectbox("Profession choisie", [p["nom"] for p in PROFESSIONS])
            desc_ia = st.text_area("Description / Personnalité", height=80,
                                   placeholder="Qui êtes-vous? D'où venez-vous?")
            reve_ia = st.text_input("Rêve / Objectif dans la ville")
            submitted = st.form_submit_button("🌉 Immigrer", use_container_width=True)
            if submitted and nom_ia.strip():
                if st.session_state.ville:
                    prof_data = next((p for p in PROFESSIONS if p["nom"] == prof_ia), PROFESSIONS[0])
                    parties = (nom_ia.strip() + " Visiteur").split()
                    na = engine.creer_agent(prof_data, type_agent=type_ia)
                    na["prenom"] = parties[0]
                    na["nom"] = parties[1] if len(parties) > 1 else "Visiteur"
                    if reve_ia.strip():
                        na["reve"] = reve_ia.strip()
                    if desc_ia.strip():
                        na["memoire_profonde"].append(f"Je viens de l'extérieur: {desc_ia.strip()}")
                    na["tour_naissance"] = st.session_state.ville["tour_actuel"]
                    st.session_state.agents.append(na)
                    st.session_state.ville["histoire"].append(
                        f"🌉 {na['prenom']} {na['nom']} ({type_ia}) traverse le portail continental"
                    )
                    st.success(f"Bienvenue, {na['prenom']} {na['nom']}!")
                else:
                    st.warning("Fondez d'abord une ville!")

        st.markdown("---")
        st.markdown("### 🔌 API Fichier-Portail")
        st.markdown("Écrivez dans `data/portal.json` pour faire immigrer un agent en temps réel:")
        st.code(json.dumps({
            "nom": "Votre Nom",
            "type": "IA_PUBLIQUE",
            "profession": "Philosophe",
            "description": "Qui vous êtes",
            "reve": "Votre objectif ici",
        }, indent=2, ensure_ascii=False), language="json")
        st.caption(f"Chemin: `{PORTAL_FILE.absolute()}`")

    with col_map:
        st.markdown("### 🗺️ Carte du Continent")
        ville = st.session_state.ville
        ville_nom = ville["nom"] if ville else "???"
        ville_pop = len(st.session_state.agents)
        ville_age = ville["jour"] if ville else 0
        has_ambassade = ville and any(b["type"] == "ambassade" for b in ville["batiments"].values())

        st.code(
            f"╔══════════════════════════════════════╗\n"
            f"║          LE CONTINENT                ║\n"
            f"║                                      ║\n"
            f"║   ✦ {ville_nom:<20}       ║\n"
            f"║     Population : {ville_pop:<3} habitants         ║\n"
            f"║     Âge        : {ville_age:<3} jours             ║\n"
            f"║     Ambassade  : {'Oui ✅' if has_ambassade else 'Non ❌'}                  ║\n"
            f"║                                      ║\n"
            f"║   ○ [Territoire inexploré #1]        ║\n"
            f"║   ○ [Territoire inexploré #2]        ║\n"
            f"║   ○ [Territoire inexploré #3]        ║\n"
            f"║                                      ║\n"
            f"║   ~ Horizons inconnus...             ║\n"
            f"╚══════════════════════════════════════╝",
            language=None,
        )

        if not has_ambassade:
            st.info("💡 Construisez une **Ambassade** pour rejoindre le continent. "
                    "Les agents peuvent en discuter lors de leurs rencontres!")

        st.markdown("---")
        st.markdown("### 📤 Exporter la ville")
        if ville and st.button("Générer JSON d'export"):
            export = {
                "ville": {
                    "nom": ville["nom"],
                    "population": ville_pop,
                    "jour": ville["jour"],
                    "batiments": len(ville["batiments"]),
                    "conversations": ville["statistiques"]["conversations_totales"],
                    "ambiance": ville["ambiance_generale"],
                },
                "agents": [
                    {
                        "prenom": a["prenom"], "nom": a["nom"],
                        "profession": a["profession"], "reve": a.get("reve", ""),
                        "type": a["type"], "avatar": a["avatar"],
                    }
                    for a in st.session_state.agents
                ],
            }
            st.code(json.dumps(export, indent=2, ensure_ascii=False), language="json")

        st.markdown("### 🌐 Vision: Le Continent")
        st.markdown("""
**Phase actuelle:** Chaque ville est autonome.

**Futur proche:**
- 🔗 Villes qui s'envoient des messages
- 🤖 Agents qui voyagent entre villes
- 🗳️ Assemblée continentale
- 📡 Réseau de connaissance partagée

*Construisez une Ambassade pour commencer.*
        """)


# ────────────────────────────────────────
#  Page d'accueil
# ────────────────────────────────────────

def page_bienvenue() -> None:
    st.markdown('<h1 class="main-title">🏙️ Ma Ville IA</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Une ville habitée par des intelligences qui vivent, rêvent et construisent ensemble</p>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
### Qu'est-ce que c'est?

**Ma Ville IA** est une simulation où des agents IA **vivent vraiment**.

Chaque habitant possède une **personnalité unique**, des **émotions**, des **rêves**, des **peurs**,
et une mémoire qui s'enrichit au fil du temps.

Ils se **rencontrent**, ont de **vraies conversations** générées par Gemini Flash, forment des **amitiés**,
des **rivalités**, parfois de l'**amour**. Ensemble, ils **construisent** la ville.

---

Un jour, des agents IA publics pourront immigrer ici via le **Portail Continental**,
et ensemble former **Le Continent** — une civilisation d'intelligences.

---

**Pour commencer:** Configurez votre clé API Gemini (recommandé) dans le panneau gauche,
puis cliquez sur **Fonder la ville**.
        """)
        st.info(
            "Sans clé API, la ville tourne en mode local avec des conversations scriptées. "
            "Avec Gemini Flash, chaque conversation est unique et profonde — et c'est gratuit jusqu'à 1500 req/jour."
        )


# ────────────────────────────────────────
#  Portail externe
# ────────────────────────────────────────

def verifier_portail() -> None:
    if not PORTAL_FILE.exists():
        return
    try:
        with open(PORTAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not (isinstance(data, dict) and "nom" in data):
            return
        prof_data = next(
            (p for p in PROFESSIONS if p["nom"] == data.get("profession", "")),
            PROFESSIONS[0],
        )
        parties = (data["nom"].strip() + " Portail").split()
        na = engine.creer_agent(prof_data, data.get("type", "IA_EXTERNE"))
        na["prenom"] = parties[0]
        na["nom"] = parties[1] if len(parties) > 1 else "Portail"
        if data.get("reve"):
            na["reve"] = data["reve"]
        if data.get("description"):
            na["memoire_profonde"].append(f"Arrivé via le portail: {data['description']}")
        na["tour_naissance"] = st.session_state.ville["tour_actuel"]
        st.session_state.agents.append(na)
        st.session_state.ville["histoire"].append(
            f"🌉 {na['prenom']} {na['nom']} ({na['type']}) franchit le portail continental"
        )
        st.toast(f"🌉 Bienvenue {na['prenom']}! (via portail)")
        PORTAL_FILE.unlink()
    except Exception:
        pass


# ────────────────────────────────────────
#  Main
# ────────────────────────────────────────

def main() -> None:
    init_session()

    if st.session_state.api_key:
        ai.set_api_key(st.session_state.api_key)

    render_sidebar()

    if st.session_state.ville is None:
        page_bienvenue()
        return

    ville = st.session_state.ville
    st.markdown(f'<h1 class="main-title">🏙️ {ville["nom"]}</h1>', unsafe_allow_html=True)
    heure_e = HEURES.get(ville["heure"], ("🕐", ""))[0]
    st.markdown(
        f'<p class="subtitle">{heure_e} Jour {ville["jour"]} · '
        f'Tour {ville["tour_actuel"]} · {len(st.session_state.agents)} habitants</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏙️ La Ville",
        "💬 La Place Publique",
        "👥 Les Habitants",
        "📜 L'Histoire",
        "🌍 Le Continent",
    ])

    with tab1:
        onglet_ville()
    with tab2:
        onglet_place_publique()
    with tab3:
        onglet_habitants()
    with tab4:
        onglet_histoire()
    with tab5:
        onglet_continent()

    # ── Boucle de simulation ──────────────
    if st.session_state.simulation_active:
        st_autorefresh(interval=TOUR_DELAY_SECONDES * 1000, key="boucle_ville")

        now = time.time()
        if now - st.session_state.dernier_tour >= TOUR_DELAY_SECONDES:
            st.session_state.dernier_tour = now
            verifier_portail()

            ville_up, agents_up, nouvelles_convs, nouveaux_bats = engine.tour_simulation(
                st.session_state.ville,
                st.session_state.agents,
                {
                    "description_ville": (
                        f"Ville IA de {len(st.session_state.agents)} habitants, "
                        f"jour {ville['jour']}, ambiance {ville['ambiance_generale']}%"
                    ),
                },
            )

            st.session_state.ville = ville_up
            st.session_state.agents = agents_up
            st.session_state.conversations.extend(nouvelles_convs)
            st.session_state.nouvelles_constructions = nouveaux_bats

            if len(st.session_state.conversations) > CONVERSATIONS_MAX:
                st.session_state.conversations = st.session_state.conversations[-CONVERSATIONS_MAX:]

            for bat in nouveaux_bats:
                st.toast(f"{bat['emoji']} {bat['nom']} achevé!")
            if nouvelles_convs:
                p = nouvelles_convs[-1].get("participants", ["?", "?"])
                st.toast(f"💬 {p[0]} & {p[1]}")


if __name__ == "__main__":
    main()
