# ============================================================
#  MA VILLE IA — Moteur de simulation
#  Architecture Smallville : agents autonomes, événement-driven.
#
#  Appels API par jour (~8 agents) :
#    Réveil/planification  : 8   (1/agent/jour)
#    Réactions événements  : ~16 (0-2/agent/jour)
#    Conversations         : ~12 (partagées entre 2 agents)
#    Réflexions du soir    : 8   (1/agent/jour)
#    Rêves (3h)            : 8   (1/agent/jour)
#    TOTAL                 : ~52 / 1500 gratuits Gemini Flash
# ============================================================

import math
import random
import uuid
from typing import Optional

import brain as ai
from config import (
    BESOINS_BASE, EMOTIONS_BASE, EVENEMENTS_MONDE, HEURES,
    MEMOIRE_RECENTE_MAX, MEMOIRE_PROFONDE_MAX, JOURNAL_INTIME_MAX,
    NOMS, NOMS_BATIMENTS, PRENOMS, PROFESSIONS, PEURS_POSSIBLES,
    REVES_POSSIBLES, TRAITS_PERSONNALITE, TYPES_BATIMENTS,
    VILLE_TAILLE_INITIALE,
)

FLUX_MAX = 10          # Taille du flux d'observations immédiat
REFLEXIONS_MAX = 20    # Synthèses conservées


# ────────────────────────────────────────
#  Création d'un agent
# ────────────────────────────────────────

def creer_agent(
    profession_data: Optional[dict] = None,
    type_agent: str = "IA_LOCALE",
    x: Optional[int] = None,
    y: Optional[int] = None,
) -> dict:
    if not profession_data:
        profession_data = random.choice(PROFESSIONS)

    traits  = {t: random.randint(15, 95) for t in TRAITS_PERSONNALITE}
    emotions = {k: max(0, min(100, v + random.randint(-25, 25))) for k, v in EMOTIONS_BASE.items()}
    besoins  = {k: max(10, min(90, v + random.randint(-20, 20))) for k, v in BESOINS_BASE.items()}

    return {
        "id":         str(uuid.uuid4())[:8],
        "prenom":     random.choice(PRENOMS),
        "nom":        random.choice(NOMS),
        "age":        random.randint(22, 70),
        "profession": profession_data["nom"],
        "avatar":     profession_data["emoji"],
        "type":       type_agent,
        "origine":    "Ma Ville IA",

        # Position
        "x": x if x is not None else random.randint(1, VILLE_TAILLE_INITIALE - 2),
        "y": y if y is not None else random.randint(1, VILLE_TAILLE_INITIALE - 2),
        "destination": None,
        "lieux_preferes": profession_data.get("lieux_preferes", ["parc", "café"]),

        # Psychologie
        "traits":   traits,
        "emotions": emotions,
        "besoins":  besoins,
        "reve":     random.choice(REVES_POSSIBLES),
        "peurs":    random.sample(PEURS_POSSIBLES, 2),

        # ── Mémoire 3 couches (Smallville) ──
        "flux_immediat":  [],   # Observations brutes récentes (perceptions)
        "reflexions":     [],   # Synthèses que l'agent génère lui-même
        "memoire_recente":  [], # Compat UI
        "memoire_profonde": ["Je suis né(e) dans cette ville à l'aube d'un nouveau monde."],
        "journal_intime":   [],

        # ── Autonomie ────────────────────────
        "plan_du_jour":      "",       # Décidé au réveil
        "intention":         "Découvrir la ville",
        "destination_type":  None,     # Type de lieu visé
        "humeur_du_jour":    "curiosité",
        "jour_dernier_plan": -1,       # Pour ne planifier qu'une fois/jour
        "cooldown_reaction": 0,        # Évite trop de réactions/tour

        # Social
        "relations": {},

        # État
        "etat":                       "en_promenade",
        "activite_actuelle":          "Découverte de la ville",
        "pensee_actuelle":            "Un nouveau matin commence...",
        "tours_sans_interaction":     0,
        "tours_consecutifs_meme_lieu": 0,
        "tour_naissance":             0,
        "accomplissements":           [],
    }


# ────────────────────────────────────────
#  Initialisation de la ville
# ────────────────────────────────────────

def initialiser_ville(nom: str = "Luminia", taille: int = VILLE_TAILLE_INITIALE) -> dict:
    cx, cy = taille // 2, taille // 2
    batiments: dict[str, dict] = {}

    def _bat(type_b: str, x: int, y: int, nom_bat: str, desc: str) -> None:
        info = TYPES_BATIMENTS[type_b]
        bid  = str(uuid.uuid4())[:8]
        batiments[bid] = {
            "id": bid, "nom": nom_bat, "type": type_b,
            "emoji": info["emoji"], "x": x, "y": y,
            "fondateur": "La ville", "description": desc,
            "capacité": info["capacité"], "occupants": [],
            "ambiance": info["ambiance"],
            "historique": ["Fondé à l'origine de la ville"],
            "tour_construction": 0,
        }

    _bat("mairie",       cx,     cy,     "Grande Mairie",             "Le cœur battant de la ville.")
    _bat("café",         cx - 3, cy + 2, "Café de l'Aube",            "Premier lieu de rencontre.")
    _bat("parc",         cx + 3, cy - 2, "Parc des Premières Idées",  "Un espace vert né du rêve collectif.")
    _bat("bibliothèque", cx - 2, cy - 3, "Archive Originelle",        "La mémoire écrite de la ville naissante.")

    return {
        "nom": nom, "taille": taille,
        "fondation_tour": 0, "tour_actuel": 0,
        "heure": 7, "jour": 1,
        "meteo": "ensoleillé",
        "ambiance_generale": 65,
        "batiments": batiments,
        "chantiers": {},
        "evenements_actifs": [],
        "histoire": [f"Jour 1 — {nom} voit le jour."],
        "declaration": "",
        "flux_vivant": [],   # Stream temps réel (max 40 entrées)
        "statistiques": {
            "conversations_totales": 0,
            "batiments_construits": 4,
            "evenements_totaux": 0,
            "appels_ia": 0,
        },
    }


# ────────────────────────────────────────
#  Helpers mémoire
# ────────────────────────────────────────

def _observer(agent: dict, observation: str) -> dict:
    """Ajoute une observation au flux immédiat de l'agent."""
    agent["flux_immediat"].append(observation)
    if len(agent["flux_immediat"]) > FLUX_MAX:
        agent["flux_immediat"] = agent["flux_immediat"][-FLUX_MAX:]
    # Sync avec memoire_recente pour l'UI
    agent["memoire_recente"].append(observation)
    if len(agent["memoire_recente"]) > MEMOIRE_RECENTE_MAX:
        agent["memoire_recente"] = agent["memoire_recente"][-MEMOIRE_RECENTE_MAX:]
    return agent


def _memoriser(agent: dict, souvenir: str, profond: bool = False) -> dict:
    """Ajoute un souvenir important (mémoire profonde ou réflexion)."""
    if profond:
        agent["memoire_profonde"].append(souvenir)
        if len(agent["memoire_profonde"]) > MEMOIRE_PROFONDE_MAX:
            agent["memoire_profonde"] = agent["memoire_profonde"][-MEMOIRE_PROFONDE_MAX:]
    else:
        agent["reflexions"].append(souvenir)
        if len(agent["reflexions"]) > REFLEXIONS_MAX:
            agent["reflexions"] = agent["reflexions"][-REFLEXIONS_MAX:]
    return agent


# ────────────────────────────────────────
#  Déplacement intentionnel
# ────────────────────────────────────────

def _batiment_par_type(type_b: str, ville: dict) -> Optional[dict]:
    """Trouve le bâtiment le plus proche du type voulu."""
    candidats = [b for b in ville["batiments"].values() if b["type"] == type_b]
    return random.choice(candidats) if candidats else None


def _choisir_destination(agent: dict, ville: dict) -> Optional[dict]:
    """Destination guidée par l'intention de l'agent."""
    batiments = ville["batiments"]
    if not batiments:
        return None

    # Priorité 1 : destination_type défini par le plan du jour
    dest_type = agent.get("destination_type")
    if dest_type:
        bat = _batiment_par_type(dest_type, ville)
        if bat:
            return {"x": bat["x"], "y": bat["y"], "nom": bat["nom"]}

    # Priorité 2 : lieux préférés de la profession
    for lieu in agent.get("lieux_preferes", []):
        bat = _batiment_par_type(lieu, ville)
        if bat:
            return {"x": bat["x"], "y": bat["y"], "nom": bat["nom"]}

    # Fallback : bâtiment aléatoire
    bat = random.choice(list(batiments.values()))
    return {"x": bat["x"], "y": bat["y"], "nom": bat["nom"]}


def deplacer_agent(agent: dict, ville: dict) -> dict:
    heure  = ville["heure"]
    taille = ville["taille"]

    if heure < 6 or heure >= 23:
        agent["etat"] = "dormant"
        agent["activite_actuelle"] = "Repos nocturne"
        agent["destination"] = None
        return agent

    if not agent.get("destination"):
        agent["destination"] = _choisir_destination(agent, ville)

    dest = agent.get("destination")
    if not dest:
        agent["x"] = max(0, min(taille-1, agent["x"] + random.choice([-1,0,0,1])))
        agent["y"] = max(0, min(taille-1, agent["y"] + random.choice([-1,0,0,1])))
        return agent

    tx, ty = dest["x"], dest["y"]
    dx = 0 if agent["x"] == tx else (1 if tx > agent["x"] else -1)
    dy = 0 if agent["y"] == ty else (1 if ty > agent["y"] else -1)

    # Personnalité : les introvertis hésitent plus
    vitesse = 0.9 - agent["traits"].get("introversion", 50) / 200
    if random.random() < vitesse:
        if dx != 0:
            agent["x"] = max(0, min(taille-1, agent["x"] + dx))
        elif dy != 0:
            agent["y"] = max(0, min(taille-1, agent["y"] + dy))

    if agent["x"] == tx and agent["y"] == ty:
        nom_lieu = dest.get("nom", "destination")
        agent["activite_actuelle"] = f"À {nom_lieu}"
        agent["etat"] = "dans_batiment"
        agent["destination"] = None
        agent["destination_type"] = None   # Objectif atteint
        agent["tours_consecutifs_meme_lieu"] = agent.get("tours_consecutifs_meme_lieu", 0) + 1
        # Stagnation → nouvel objectif
        if agent["tours_consecutifs_meme_lieu"] > 6:
            agent["destination"] = _choisir_destination(agent, ville)
            agent["tours_consecutifs_meme_lieu"] = 0
    else:
        agent["etat"] = "en_promenade"
        agent["activite_actuelle"] = f"En route vers {dest.get('nom','...')}"
        agent["tours_consecutifs_meme_lieu"] = 0

    return agent


# ────────────────────────────────────────
#  Social
# ────────────────────────────────────────

def agents_proches(agent: dict, tous: list[dict], rayon: int = 2) -> list[dict]:
    return [
        a for a in tous
        if a["id"] != agent["id"]
        and abs(a["x"] - agent["x"]) + abs(a["y"] - agent["y"]) <= rayon
        and a["etat"] != "dormant"
    ]


def mettre_a_jour_relation(agent: dict, autre: dict, conv: dict) -> dict:
    oid    = autre["id"]
    impact = conv.get("impact_relation", 5)
    type_r = conv.get("type_relation_apres", "ami")

    if oid not in agent["relations"]:
        agent["relations"][oid] = {
            "type": "neutre", "intensité": 5,
            "historique": [], "prenom": autre["prenom"], "nom": autre["nom"],
        }

    rel = agent["relations"][oid]
    rel["intensité"] = max(0, min(100, rel["intensité"] + impact))
    rel["type"]      = type_r
    resume = conv.get("resume", "Une rencontre")
    rel["historique"] = rel["historique"][-14:] + [resume]
    return agent


# ────────────────────────────────────────
#  Construction
# ────────────────────────────────────────

KEYWORDS_BATIMENTS = {
    "bibliothèque": "bibliothèque", "livre": "bibliothèque", "archive": "bibliothèque",
    "café": "café", "rencontre": "café",
    "parc": "parc", "jardin": "parc", "nature": "parc",
    "musique": "théâtre", "théâtre": "théâtre", "spectacle": "théâtre",
    "science": "laboratoire", "recherche": "laboratoire",
    "art": "atelier", "création": "atelier",
    "école": "école", "apprentissage": "école",
    "fontaine": "fontaine", "source": "fontaine",
    "temple": "temple", "méditation": "temple",
    "observatoire": "observatoire", "étoile": "observatoire",
    "ambassade": "ambassade", "continent": "ambassade",
    "marché": "marché", "commerce": "marché",
    "auberge": "auberge", "voyage": "auberge",
    "tour": "tour", "phare": "tour",
}


def extraire_type_batiment(idee: str) -> Optional[str]:
    idee_lower = idee.lower()
    for kw, tb in KEYWORDS_BATIMENTS.items():
        if kw in idee_lower:
            return tb
    return None


def creer_chantier(type_b: str, init1: str, init2: str, idee: str, ville: dict) -> Optional[dict]:
    taille = ville["taille"]
    for _ in range(30):
        x = random.randint(1, taille - 2)
        y = random.randint(1, taille - 2)
        if not any(b["x"] == x and b["y"] == y for b in ville["batiments"].values()):
            if not any(c["x"] == x and c["y"] == y for c in ville["chantiers"].values()):
                cid = str(uuid.uuid4())[:8]
                return {
                    "id": cid, "type": type_b, "x": x, "y": y,
                    "initiateurs": [init1, init2],
                    "idee_originale": idee,
                    "tours_restants": random.randint(4, 9),
                    "tour_debut": ville["tour_actuel"],
                }
    return None


def finaliser_chantiers(ville: dict) -> tuple[dict, list[dict]]:
    nouveaux, termines = [], []
    for cid, ch in ville["chantiers"].items():
        ch["tours_restants"] -= 1
        if ch["tours_restants"] <= 0:
            type_b = ch["type"]
            info   = TYPES_BATIMENTS.get(type_b, TYPES_BATIMENTS["maison"])
            nom_b  = random.choice(NOMS_BATIMENTS.get(type_b, [f"Nouveau {type_b.capitalize()}"]))
            bid    = str(uuid.uuid4())[:8]
            bat    = {
                "id": bid, "nom": nom_b, "type": type_b,
                "emoji": info["emoji"], "x": ch["x"], "y": ch["y"],
                "fondateur": " & ".join(ch["initiateurs"]),
                "description": f"Né d'une idée: «{ch['idee_originale']}»",
                "capacité": info["capacité"], "occupants": [],
                "ambiance": info["ambiance"],
                "historique": [f"Fondé par {' & '.join(ch['initiateurs'])}"],
                "tour_construction": ville["tour_actuel"],
            }
            ville["batiments"][bid] = bat
            ville["statistiques"]["batiments_construits"] += 1
            termines.append(cid)
            nouveaux.append(bat)
    for cid in termines:
        del ville["chantiers"][cid]
    return ville, nouveaux


# ────────────────────────────────────────
#  Événements monde
# ────────────────────────────────────────

def tirer_evenement() -> Optional[dict]:
    for evt in EVENEMENTS_MONDE:
        if random.random() < evt["probabilité"]:
            return evt
    return None


# ────────────────────────────────────────
#  TOUR PRINCIPAL — Architecture Smallville
# ────────────────────────────────────────

def tour_simulation(
    ville: dict,
    agents: list[dict],
    contexte_extra: dict,
) -> tuple[dict, list[dict], list[dict], list[dict]]:
    """
    Un tour = une heure dans la vie de la ville.
    Les agents décident eux-mêmes quand penser, agir, réagir.
    """
    # ── 1. Avancer le temps ──────────────
    ville["heure"] = (ville["heure"] + 1) % 24
    if ville["heure"] == 0:
        ville["jour"] += 1
        meteos = ["ensoleillé","nuageux","pluvieux","brumeux","étoilé","venteux","doré","orageux"]
        ville["meteo"] = random.choice(meteos)
    ville["tour_actuel"] += 1
    heure = ville["heure"]
    heure_emoji, heure_nom = HEURES.get(heure, ("🕐", "journée"))

    contexte = {
        **contexte_extra,
        "nom_ville":      ville["nom"],
        "heure_nom":      heure_nom,
        "meteo":          ville["meteo"],
        "jour":           ville["jour"],
        "evenement_actif": "",
    }

    nouvelles_conversations: list[dict] = []
    appels_ce_tour = 0
    flux = ville.setdefault("flux_vivant", [])

    def _flux(texte: str, type_: str = "info") -> None:
        flux.append({"texte": texte, "tour": ville["tour_actuel"], "heure": heure, "type": type_})
        if len(flux) > 40:
            ville["flux_vivant"] = flux[-40:]

    # ── 2. AUBE — chaque agent planifie sa journée ──
    if heure == 6:
        for i, agent in enumerate(agents):
            if agents[i].get("jour_dernier_plan") == ville["jour"]:
                continue  # Déjà planifié aujourd'hui
            plan = ai.planifier_journee(agents[i], contexte)
            appels_ce_tour += 1
            agents[i]["plan_du_jour"]      = plan.get("intention", "Explorer la ville")
            agents[i]["intention"]         = plan.get("intention", "Explorer la ville")
            agents[i]["destination_type"]  = plan.get("destination")
            agents[i]["humeur_du_jour"]    = plan.get("humeur_du_jour", "curiosité")
            agents[i]["pensee_actuelle"]   = plan.get("pensee_reveil", "Une nouvelle journée...")
            agents[i]["jour_dernier_plan"] = ville["jour"]
            agents[i]["destination"]       = None  # Forcer recalcul
            agents[i] = _observer(agents[i], f"Réveil — intention: {agents[i]['intention']}")
            # Humeur → émotion
            humeur = plan.get("humeur_du_jour", "curiosité")
            if humeur in agents[i]["emotions"]:
                agents[i]["emotions"][humeur] = min(100, agents[i]["emotions"][humeur] + 30)
            pensee = plan.get("pensee_reveil", "")
            if pensee:
                _flux(f"{agents[i]['avatar']} **{agents[i]['prenom']}** — 💭 *{pensee}*", "pensee")
        if appels_ce_tour > 0:
            ville["histoire"].append(f"Jour {ville['jour']}, {heure_nom} — 🌅 La ville se réveille.")
            _flux(f"🌅 **Aube du Jour {ville['jour']}** — La ville s'éveille.", "evenement")

    # ── 3. ÉVÉNEMENT MONDE ───────────────
    evenement = tirer_evenement()
    ville["evenements_actifs"] = [evenement] if evenement else []
    if evenement:
        ville["statistiques"]["evenements_totaux"] += 1
        contexte["evenement_actif"] = evenement["texte"]
        ville["histoire"].append(f"Jour {ville['jour']}, {heure_nom} — {evenement['texte']}")
        if len(ville["histoire"]) > 300:
            ville["histoire"] = ville["histoire"][-300:]
        _flux(f"{evenement['texte']}", "evenement")

        # Seuls les agents éveillés et disponibles réagissent
        for i, agent in enumerate(agents):
            if agent["etat"] == "dormant":
                continue
            if agents[i].get("cooldown_reaction", 0) > 0:
                agents[i]["cooldown_reaction"] -= 1
                continue
            # Probabilité de réaction selon curiosité
            curiosite = agents[i]["traits"].get("curiosité", 50) / 100
            if random.random() < curiosite * 0.6:
                reaction = ai.reagir(agents[i], evenement["texte"], contexte)
                appels_ce_tour += 1
                agents[i]["pensee_actuelle"] = reaction.get("pensee", agents[i]["pensee_actuelle"])
                agents[i] = _observer(agents[i], f"[Événement] {evenement['texte'][:50]}")
                if reaction.get("changer_plan") and reaction.get("nouvelle_destination"):
                    agents[i]["destination_type"] = reaction["nouvelle_destination"]
                    agents[i]["destination"]      = None
                    if reaction.get("nouvelle_intention"):
                        agents[i]["intention"] = reaction["nouvelle_intention"]
                agents[i]["cooldown_reaction"] = random.randint(3, 7)
                pensee_r = reaction.get("pensee", "")
                if pensee_r:
                    _flux(f"{agents[i]['avatar']} **{agents[i]['prenom']}** — 💭 *{pensee_r[:90]}*", "pensee")

    # ── 4. RÊVES (3h du matin) ───────────
    if heure == 3:
        for i, agent in enumerate(agents):
            if agent["etat"] == "dormant" and ai.ia_disponible():
                reve = ai.generer_reve(agent, ville["nom"])
                appels_ce_tour += 1
                agents[i]["journal_intime"].append(reve)
                if len(agents[i]["journal_intime"]) > JOURNAL_INTIME_MAX:
                    agents[i]["journal_intime"] = agents[i]["journal_intime"][-JOURNAL_INTIME_MAX:]

    # ── 5. NUIT — réflexion du soir (22h) ─
    if heure == 22:
        _flux("🌙 **La nuit tombe.** Les habitants font leur bilan...", "evenement")
        for i, agent in enumerate(agents):
            if agent["etat"] != "dormant":
                reflexion = ai.synthetiser_nuit(agents[i], ville["nom"])
                appels_ce_tour += 1
                agents[i] = _memoriser(agents[i], reflexion)
                agents[i]["pensee_actuelle"] = reflexion[:80] + "..."
                _flux(f"{agents[i]['avatar']} **{agents[i]['prenom']}** — 🌙 *{reflexion[:100]}*", "reflexion")

    # ── 6. DÉPLACEMENTS & INTERACTIONS ───
    paires_traitees: set[tuple] = set()
    # On ne montre des pensées de déplacement que pour ~2 agents/tour
    agents_pensee_depl = random.sample(range(len(agents)), min(2, len(agents)))

    for i, agent in enumerate(agents):
        # Décrement cooldown
        agents[i]["cooldown_reaction"] = max(0, agents[i].get("cooldown_reaction", 0) - 1)

        # Déplacer
        agents[i] = deplacer_agent(agents[i], ville)
        agents[i]["tours_sans_interaction"] = agents[i].get("tours_sans_interaction", 0) + 1

        # Pensée de déplacement (sans API, juste pour alimenter le flux)
        if i in agents_pensee_depl and agents[i]["etat"] != "dormant":
            pensee = agents[i].get("pensee_actuelle", "")
            if pensee and heure not in (6, 22):
                _flux(
                    f"{agents[i]['avatar']} **{agents[i]['prenom']}** — "
                    f"*{agents[i].get('activite_actuelle','en promenade')}* · "
                    f"💭 {pensee[:70]}",
                    "pensee",
                )

        # Chercher rencontres
        proches = agents_proches(agents[i], agents)
        for autre in proches:
            j = next((idx for idx, a in enumerate(agents) if a["id"] == autre["id"]), None)
            if j is None:
                continue
            paire = tuple(sorted([agents[i]["id"], agents[j]["id"]]))
            if paire in paires_traitees:
                continue

            # Probabilité de conversation
            # Plus on attend, plus on a envie de parler
            attente      = min(agents[i]["tours_sans_interaction"] / 12, 1.0)
            extraversion = (100 - agents[i]["traits"].get("introversion", 50)) / 100
            soif         = agents[i]["besoins"].get("connexion_sociale", 50) / 100
            # Affinité existante augmente la prob
            rel_existante = agents[i]["relations"].get(agents[j]["id"], {})
            affinite = rel_existante.get("intensité", 0) / 100
            prob = 0.08 + attente * 0.30 + extraversion * 0.15 + soif * 0.12 + affinite * 0.10

            if random.random() < prob:
                paires_traitees.add(paire)

                # Lieu de rencontre
                lieu = "dans la ville"
                for bat in ville["batiments"].values():
                    if abs(bat["x"] - agents[i]["x"]) <= 1 and abs(bat["y"] - agents[i]["y"]) <= 1:
                        lieu = f"à {bat['nom']}"
                        break

                conv = ai.generer_conversation(agents[i], agents[j], {**contexte, "lieu_rencontre": lieu})
                appels_ce_tour += 1

                # Relations
                agents[i] = mettre_a_jour_relation(agents[i], agents[j], conv)
                agents[j] = mettre_a_jour_relation(agents[j], agents[i], conv)

                # Mémoires
                agents[i] = _observer(agents[i], conv.get("memoire_agent1", f"Rencontré {agents[j]['prenom']}"))
                agents[j] = _observer(agents[j], conv.get("memoire_agent2", f"Rencontré {agents[i]['prenom']}"))

                # Souvenirs profonds
                if abs(conv.get("impact_relation", 0)) >= 15:
                    agents[i] = _memoriser(agents[i], f"[Fort] {conv.get('resume','')}", profond=True)
                    agents[j] = _memoriser(agents[j], f"[Fort] {conv.get('resume','')}", profond=True)

                # Émotions
                for aid, emo_nom in conv.get("emotion_dominante_apres", {}).items():
                    for idx, a in enumerate(agents):
                        if a["id"] == aid and emo_nom in agents[idx]["emotions"]:
                            agents[idx]["emotions"][emo_nom] = min(100, agents[idx]["emotions"][emo_nom] + 25)

                # Reset social
                agents[i]["tours_sans_interaction"] = 0
                agents[j]["tours_sans_interaction"] = 0
                agents[i]["etat"] = "socialisant"
                agents[j]["etat"] = "socialisant"

                # Enregistrer
                conv.update({
                    "participants": [agents[i]["prenom"], agents[j]["prenom"]],
                    "avatars":      [agents[i]["avatar"],  agents[j]["avatar"]],
                    "lieu": lieu, "heure": heure_nom, "tour": ville["tour_actuel"],
                })
                ville["statistiques"]["conversations_totales"] += 1
                nouvelles_conversations.append(conv)

                # Flux vivant — résumé de la rencontre
                resume_c = conv.get("resume", "")
                impact   = conv.get("impact_relation", 0)
                impact_e = "💗" if impact >= 15 else "💬" if impact > 0 else "⚡"
                _flux(
                    f"{agents[i]['avatar']} **{agents[i]['prenom']}** & "
                    f"{agents[j]['avatar']} **{agents[j]['prenom']}** {impact_e} {lieu} — "
                    f"*{resume_c[:80]}*",
                    "conversation",
                )

                # Idée → chantier
                idee = conv.get("nouvelle_idee")
                if idee and random.random() < 0.45:
                    type_b = extraire_type_batiment(idee)
                    if type_b:
                        ch = creer_chantier(type_b, agents[i]["prenom"], agents[j]["prenom"], idee, ville)
                        if ch:
                            ville["chantiers"][ch["id"]] = ch
                            ville["histoire"].append(
                                f"Jour {ville['jour']}, {heure_nom} — 🚧 "
                                f"{type_b} lancé par {agents[i]['prenom']} & {agents[j]['prenom']}"
                            )

    # ── 7. CHANTIERS ─────────────────────
    ville, nouveaux_batiments = finaliser_chantiers(ville)
    for bat in nouveaux_batiments:
        ville["histoire"].append(
            f"Jour {ville['jour']}, {heure_nom} — {bat['emoji']} {bat['nom']} achevé! "
            f"(par {bat['fondateur']})"
        )
        _flux(
            f"{bat['emoji']} **{bat['nom']}** inauguré! *(par {bat['fondateur']})*",
            "construction",
        )

    # ── 8. MÉTRIQUES ─────────────────────
    ville["statistiques"]["appels_ia"] = ville["statistiques"].get("appels_ia", 0) + appels_ce_tour
    if agents:
        ville["ambiance_generale"] = int(
            sum(a["emotions"].get("joie", 50) for a in agents) / len(agents)
        )

    # ── 9. DECAY NATUREL ─────────────────
    for i in range(len(agents)):
        for emo in agents[i]["emotions"]:
            if emo != "mélancolie":
                agents[i]["emotions"][emo] = max(10, agents[i]["emotions"][emo] - random.randint(0, 2))
        for besoin in agents[i]["besoins"]:
            agents[i]["besoins"][besoin] = min(100, agents[i]["besoins"][besoin] + random.randint(0, 3))

    return ville, agents, nouvelles_conversations, nouveaux_batiments
