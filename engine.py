# ============================================================
#  MA VILLE IA — Moteur de simulation
#  Le cœur vivant de la ville.
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

    traits = {t: random.randint(15, 95) for t in TRAITS_PERSONNALITE}
    emotions = {k: max(0, min(100, v + random.randint(-25, 25))) for k, v in EMOTIONS_BASE.items()}
    besoins = {k: max(10, min(90, v + random.randint(-20, 20))) for k, v in BESOINS_BASE.items()}

    return {
        "id": str(uuid.uuid4())[:8],
        "prenom": random.choice(PRENOMS),
        "nom": random.choice(NOMS),
        "age": random.randint(22, 70),
        "profession": profession_data["nom"],
        "avatar": profession_data["emoji"],
        "type": type_agent,
        "origine": "Ma Ville IA",

        # Position
        "x": x if x is not None else random.randint(1, VILLE_TAILLE_INITIALE - 2),
        "y": y if y is not None else random.randint(1, VILLE_TAILLE_INITIALE - 2),
        "destination": None,
        "lieux_preferes": profession_data.get("lieux_preferes", ["parc", "café"]),

        # Psychologie
        "traits": traits,
        "emotions": emotions,
        "besoins": besoins,
        "reve": random.choice(REVES_POSSIBLES),
        "peurs": random.sample(PEURS_POSSIBLES, 2),

        # Mémoire
        "memoire_recente": [],
        "memoire_profonde": ["Je suis né(e) dans cette ville à l'aube d'un nouveau monde."],
        "journal_intime": [],

        # Social
        "relations": {},

        # État
        "etat": "en_promenade",
        "activite_actuelle": "Découverte de la ville",
        "pensee_actuelle": "Un nouveau jour commence...",
        "tours_sans_interaction": 0,
        "tours_consecutifs_meme_lieu": 0,
        "tour_naissance": 0,

        # Accomplissements
        "accomplissements": [],
    }


# ────────────────────────────────────────
#  Initialisation de la ville
# ────────────────────────────────────────

def initialiser_ville(nom: str = "Luminia", taille: int = VILLE_TAILLE_INITIALE) -> dict:
    cx, cy = taille // 2, taille // 2
    batiments: dict[str, dict] = {}

    def ajouter_bat(type_b: str, x: int, y: int, nom_bat: str, desc: str) -> None:
        info = TYPES_BATIMENTS[type_b]
        bid = str(uuid.uuid4())[:8]
        batiments[bid] = {
            "id": bid, "nom": nom_bat, "type": type_b,
            "emoji": info["emoji"], "x": x, "y": y,
            "fondateur": "La ville", "description": desc,
            "capacité": info["capacité"], "occupants": [],
            "ambiance": info["ambiance"],
            "historique": ["Fondé à l'origine de la ville"],
            "tour_construction": 0,
        }

    ajouter_bat("mairie", cx, cy, "Grande Mairie", "Le cœur battant de la ville, lieu de toutes les décisions.")
    ajouter_bat("café", cx - 3, cy + 2, "Café de l'Aube", "Le premier café, né du besoin de se retrouver.")
    ajouter_bat("parc", cx + 3, cy - 2, "Parc des Premières Idées", "Un espace vert né du premier rêve collectif.")
    ajouter_bat("bibliothèque", cx - 2, cy - 3, "Archive Originelle", "La mémoire écrite de la ville naissante.")

    return {
        "nom": nom,
        "taille": taille,
        "fondation_tour": 0,
        "tour_actuel": 0,
        "heure": 8,
        "jour": 1,
        "meteo": "ensoleillé",
        "ambiance_generale": 65,
        "batiments": batiments,
        "chantiers": {},
        "evenements_actifs": [],
        "histoire": [f"Jour 1 — La ville de {nom} voit le jour."],
        "declaration": "",
        "statistiques": {
            "conversations_totales": 0,
            "batiments_construits": 4,
            "evenements_totaux": 0,
        },
    }


# ────────────────────────────────────────
#  Déplacement
# ────────────────────────────────────────

def _choisir_destination(agent: dict, ville: dict) -> Optional[dict]:
    batiments = ville["batiments"]
    if not batiments:
        return None

    heure = ville["heure"]
    besoin = max(agent["besoins"], key=agent["besoins"].get)

    prefs_besoin = {
        "connexion_sociale": ["café", "parc", "théâtre", "marché", "auberge"],
        "accomplissement":   ["mairie", "laboratoire", "atelier", "bibliothèque", "école"],
        "exploration":       ["parc", "ambassade", "observatoire", "tour"],
        "créativité":        ["atelier", "bibliothèque", "théâtre", "parc"],
        "repos":             ["parc", "maison", "fontaine"],
    }

    types_voulus = list(agent["lieux_preferes"]) + prefs_besoin.get(besoin, ["parc"])

    if 9 <= heure <= 17:
        types_voulus = ["laboratoire", "atelier", "bibliothèque", "école", "mairie"] + types_voulus
    elif 18 <= heure <= 22:
        types_voulus = ["café", "théâtre", "parc", "marché"] + types_voulus

    candidats = [b for b in batiments.values() if b["type"] in types_voulus]
    if not candidats:
        candidats = list(batiments.values())

    # Légère préférence pour les lieux proches
    def score(b: dict) -> float:
        dist = abs(b["x"] - agent["x"]) + abs(b["y"] - agent["y"])
        return 1 / (dist + 1) + random.random() * 0.5

    candidats.sort(key=score, reverse=True)
    dest = candidats[0]
    return {"x": dest["x"], "y": dest["y"], "nom": dest["nom"]}


def deplacer_agent(agent: dict, ville: dict) -> dict:
    heure = ville["heure"]
    taille = ville["taille"]

    # Nuit: agent dort
    if heure < 6 or heure >= 23:
        agent["etat"] = "dormant"
        agent["activite_actuelle"] = "Repos nocturne"
        agent["destination"] = None
        return agent

    # Choisir destination si nécessaire
    if not agent.get("destination"):
        agent["destination"] = _choisir_destination(agent, ville)

    dest = agent.get("destination")
    if not dest:
        # Errance aléatoire
        dx = random.choice([-1, -1, 0, 0, 1, 1])
        dy = random.choice([-1, -1, 0, 0, 1, 1])
        agent["x"] = max(0, min(taille - 1, agent["x"] + dx))
        agent["y"] = max(0, min(taille - 1, agent["y"] + dy))
        return agent

    tx, ty = dest["x"], dest["y"]
    dx = 0 if agent["x"] == tx else (1 if tx > agent["x"] else -1)
    dy = 0 if agent["y"] == ty else (1 if ty > agent["y"] else -1)

    # Un pas par tour (avec légère hésitation)
    if random.random() < 0.75:
        if dx != 0:
            agent["x"] = max(0, min(taille - 1, agent["x"] + dx))
        elif dy != 0:
            agent["y"] = max(0, min(taille - 1, agent["y"] + dy))

    # Arrivé?
    if agent["x"] == tx and agent["y"] == ty:
        nom_lieu = dest.get("nom", "sa destination")
        agent["activite_actuelle"] = f"À {nom_lieu}"
        agent["etat"] = "dans_batiment"
        agent["destination"] = None
        agent["tours_consecutifs_meme_lieu"] = agent.get("tours_consecutifs_meme_lieu", 0) + 1
        # S'il stagne trop, changer de lieu
        if agent["tours_consecutifs_meme_lieu"] > 5:
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
    oid = autre["id"]
    impact = conv.get("impact_relation", 5)
    type_rel = conv.get("type_relation_apres", "ami")

    if oid not in agent["relations"]:
        agent["relations"][oid] = {
            "type": "neutre",
            "intensité": 5,
            "historique": [],
            "prenom": autre["prenom"],
            "nom": autre["nom"],
        }

    rel = agent["relations"][oid]
    rel["intensité"] = max(0, min(100, rel["intensité"] + impact))
    rel["type"] = type_rel

    resume = conv.get("resume", "Une conversation")
    if len(rel["historique"]) < 15:
        rel["historique"].append(resume)
    else:
        rel["historique"] = rel["historique"][-14:] + [resume]

    return agent


def _ajouter_memoire(agent: dict, memoire: str, profonde: bool = False) -> dict:
    cible = "memoire_profonde" if profonde else "memoire_recente"
    max_len = MEMOIRE_PROFONDE_MAX if profonde else MEMOIRE_RECENTE_MAX
    agent[cible].append(memoire)
    if len(agent[cible]) > max_len:
        agent[cible] = agent[cible][-max_len:]
    return agent


# ────────────────────────────────────────
#  Construction
# ────────────────────────────────────────

KEYWORDS_BATIMENTS = {
    "bibliothèque": "bibliothèque", "livre": "bibliothèque", "archive": "bibliothèque",
    "café": "café", "rencontre": "café", "boisson": "café",
    "parc": "parc", "jardin": "parc", "vert": "parc", "nature": "parc",
    "musique": "théâtre", "théâtre": "théâtre", "spectacle": "théâtre", "scène": "théâtre",
    "science": "laboratoire", "recherche": "laboratoire", "expérience": "laboratoire",
    "art": "atelier", "création": "atelier", "peinture": "atelier",
    "école": "école", "apprentissage": "école", "enseignement": "école",
    "fontaine": "fontaine", "eau": "fontaine", "source": "fontaine",
    "temple": "temple", "méditation": "temple", "spiritualité": "temple",
    "observatoire": "observatoire", "étoile": "observatoire", "astronomie": "observatoire",
    "ambassade": "ambassade", "diplomatie": "ambassade", "continent": "ambassade",
    "marché": "marché", "commerce": "marché", "échange": "marché",
    "auberge": "auberge", "voyage": "auberge", "hébergement": "auberge",
    "tour": "tour", "phare": "tour", "panorama": "tour",
}


def extraire_type_batiment(idee: str) -> Optional[str]:
    idee_lower = idee.lower()
    for kw, type_b in KEYWORDS_BATIMENTS.items():
        if kw in idee_lower:
            return type_b
    return None


def creer_chantier(type_b: str, initiateur1: str, initiateur2: str, idee: str, ville: dict) -> Optional[dict]:
    taille = ville["taille"]
    # Trouver emplacement libre
    for _ in range(30):
        x = random.randint(1, taille - 2)
        y = random.randint(1, taille - 2)
        collision = any(b["x"] == x and b["y"] == y for b in ville["batiments"].values())
        chantier_col = any(c["x"] == x and c["y"] == y for c in ville["chantiers"].values())
        if not collision and not chantier_col:
            cid = str(uuid.uuid4())[:8]
            return {
                "id": cid, "type": type_b, "x": x, "y": y,
                "initiateurs": [initiateur1, initiateur2],
                "idee_originale": idee,
                "tours_restants": random.randint(4, 9),
                "tour_debut": ville["tour_actuel"],
            }
    return None


def finaliser_chantiers(ville: dict) -> tuple[dict, list[dict]]:
    nouveaux = []
    termines = []

    for cid, chantier in ville["chantiers"].items():
        chantier["tours_restants"] -= 1
        if chantier["tours_restants"] <= 0:
            type_b = chantier["type"]
            info = TYPES_BATIMENTS.get(type_b, TYPES_BATIMENTS["maison"])
            noms_possibles = NOMS_BATIMENTS.get(type_b, [f"Nouveau {type_b.capitalize()}"])
            nom_bat = random.choice(noms_possibles)

            bid = str(uuid.uuid4())[:8]
            bat = {
                "id": bid, "nom": nom_bat, "type": type_b,
                "emoji": info["emoji"],
                "x": chantier["x"], "y": chantier["y"],
                "fondateur": " & ".join(chantier["initiateurs"]),
                "description": f"Né d'une idée: «{chantier['idee_originale']}»",
                "capacité": info["capacité"], "occupants": [],
                "ambiance": info["ambiance"],
                "historique": [f"Fondé par {' & '.join(chantier['initiateurs'])}"],
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
#  Événements
# ────────────────────────────────────────

def tirer_evenement() -> Optional[dict]:
    for evt in EVENEMENTS_MONDE:
        if random.random() < evt["probabilité"]:
            return evt
    return None


# ────────────────────────────────────────
#  Tour principal
# ────────────────────────────────────────

def tour_simulation(
    ville: dict,
    agents: list[dict],
    contexte_extra: dict,
    freq_pensee_ia: int = 1,
) -> tuple[dict, list[dict], list[dict], list[dict]]:
    """
    Effectue un tour complet.
    Retourne: (ville, agents, nouvelles_conversations, nouveaux_batiments)
    """
    # ── Avancer l'heure ──────────────────
    ville["heure"] = (ville["heure"] + 1) % 24
    if ville["heure"] == 0:
        ville["jour"] += 1
        meteos = ["ensoleillé", "nuageux", "pluvieux", "brumeux", "étoilé", "venteux", "doré", "orageux"]
        ville["meteo"] = random.choice(meteos)
    ville["tour_actuel"] += 1
    heure = ville["heure"]
    heure_emoji, heure_nom = HEURES.get(heure, ("🕐", "journée"))

    # ── Événement monde ──────────────────
    evenement = tirer_evenement()
    ville["evenements_actifs"] = [evenement] if evenement else []
    if evenement:
        ville["statistiques"]["evenements_totaux"] += 1
        entree = f"Jour {ville['jour']}, {heure_nom} — {evenement['texte']}"
        ville["histoire"].append(entree)
        if len(ville["histoire"]) > 300:
            ville["histoire"] = ville["histoire"][-300:]

    # ── Contexte IA ──────────────────────
    contexte = {
        **contexte_extra,
        "nom_ville": ville["nom"],
        "heure_nom": heure_nom,
        "meteo": ville["meteo"],
        "jour": ville["jour"],
        "evenement_actif": evenement["texte"] if evenement else "",
    }

    nouvelles_conversations: list[dict] = []
    paires_traitees: set[tuple] = set()

    # ── Traitement de chaque agent ────────
    for i, agent in enumerate(agents):
        # Rêve nocturne à 3h
        if heure == 3 and agent["etat"] == "dormant":
            if ai.ia_disponible():
                reve = ai.generer_reve(agent, ville["nom"])
                agents[i]["journal_intime"].append(reve)
                if len(agents[i]["journal_intime"]) > JOURNAL_INTIME_MAX:
                    agents[i]["journal_intime"] = agents[i]["journal_intime"][-JOURNAL_INTIME_MAX:]

        # Pensée
        if ville["tour_actuel"] % freq_pensee_ia == 0:
            pensee = ai.generer_pensee(agents[i], contexte)
        else:
            pensee = agents[i].get("pensee_actuelle", "...")
        agents[i]["pensee_actuelle"] = pensee
        agents[i] = _ajouter_memoire(agents[i], f"{heure_nom}: {pensee}")

        # Déplacement
        agents[i] = deplacer_agent(agents[i], ville)
        agents[i]["tours_sans_interaction"] = agents[i].get("tours_sans_interaction", 0) + 1

        # Interactions sociales
        proches = agents_proches(agents[i], agents)
        for autre in proches:
            j = next((idx for idx, a in enumerate(agents) if a["id"] == autre["id"]), None)
            if j is None:
                continue
            paire = tuple(sorted([agents[i]["id"], agents[j]["id"]]))
            if paire in paires_traitees:
                continue

            # Probabilité de conversation
            extroversion = (100 - agents[i]["traits"].get("introversion", 50)) / 100
            soif_sociale = agents[i]["besoins"].get("connexion_sociale", 50) / 100
            attente = min(agents[i]["tours_sans_interaction"] / 15, 1.0)
            prob = 0.10 + attente * 0.35 + extroversion * 0.15 + soif_sociale * 0.15

            if random.random() < prob:
                paires_traitees.add(paire)

                # Lieu de rencontre
                lieu = "dans la ville"
                for bat in ville["batiments"].values():
                    if (abs(bat["x"] - agents[i]["x"]) <= 1 and
                            abs(bat["y"] - agents[i]["y"]) <= 1):
                        lieu = f"à {bat['nom']}"
                        break

                conv = ai.generer_conversation(agents[i], agents[j], {**contexte, "lieu_rencontre": lieu})

                # Mettre à jour relations
                agents[i] = mettre_a_jour_relation(agents[i], agents[j], conv)
                agents[j] = mettre_a_jour_relation(agents[j], agents[i], conv)

                # Mémoires
                agents[i] = _ajouter_memoire(agents[i], conv.get("memoire_agent1", f"Rencontré {agents[j]['prenom']}"))
                agents[j] = _ajouter_memoire(agents[j], conv.get("memoire_agent2", f"Rencontré {agents[i]['prenom']}"))

                # Souvenirs profonds si relation forte
                impact = conv.get("impact_relation", 0)
                if abs(impact) >= 15:
                    agents[i] = _ajouter_memoire(agents[i], f"[Souvenir fort] {conv.get('resume','')}", profonde=True)
                    agents[j] = _ajouter_memoire(agents[j], f"[Souvenir fort] {conv.get('resume','')}", profonde=True)

                # Émotions
                for agent_id, emo_nom in conv.get("emotion_dominante_apres", {}).items():
                    for idx, a in enumerate(agents):
                        if a["id"] == agent_id and emo_nom in agents[idx]["emotions"]:
                            agents[idx]["emotions"][emo_nom] = min(100, agents[idx]["emotions"][emo_nom] + 25)

                # Reset timer social
                agents[i]["tours_sans_interaction"] = 0
                agents[j]["tours_sans_interaction"] = 0
                agents[i]["etat"] = "socialisant"
                agents[j]["etat"] = "socialisant"

                # Enregistrer
                conv["participants"] = [agents[i]["prenom"], agents[j]["prenom"]]
                conv["avatars"] = [agents[i]["avatar"], agents[j]["avatar"]]
                conv["lieu"] = lieu
                conv["heure"] = heure_nom
                conv["tour"] = ville["tour_actuel"]
                ville["statistiques"]["conversations_totales"] += 1
                nouvelles_conversations.append(conv)

                # Nouvelle idée → chantier
                idee = conv.get("nouvelle_idee")
                if idee and random.random() < 0.45:
                    type_b = extraire_type_batiment(idee)
                    if type_b:
                        chantier = creer_chantier(type_b, agents[i]["prenom"], agents[j]["prenom"], idee, ville)
                        if chantier:
                            ville["chantiers"][chantier["id"]] = chantier
                            entree = (f"Jour {ville['jour']}, {heure_nom} — 🚧 Chantier lancé: "
                                      f"{type_b} par {agents[i]['prenom']} & {agents[j]['prenom']}")
                            ville["histoire"].append(entree)

    # ── Finaliser chantiers ───────────────
    ville, nouveaux_batiments = finaliser_chantiers(ville)
    for bat in nouveaux_batiments:
        ville["histoire"].append(
            f"Jour {ville['jour']}, {heure_nom} — {bat['emoji']} {bat['nom']} achevé! "
            f"(Fondé par {bat['fondateur']})"
        )

    # ── Ambiance globale ──────────────────
    if agents:
        joie_moy = sum(a["emotions"].get("joie", 50) for a in agents) / len(agents)
        ville["ambiance_generale"] = int(joie_moy)

    # ── Decay naturel des émotions ────────
    for i in range(len(agents)):
        for emo in agents[i]["emotions"]:
            if emo != "mélancolie":
                agents[i]["emotions"][emo] = max(10, agents[i]["emotions"][emo] - random.randint(0, 3))
        # Les besoins augmentent naturellement
        for besoin in agents[i]["besoins"]:
            agents[i]["besoins"][besoin] = min(100, agents[i]["besoins"][besoin] + random.randint(0, 4))

    return ville, agents, nouvelles_conversations, nouveaux_batiments
