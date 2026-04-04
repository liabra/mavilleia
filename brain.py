# ============================================================
#  MA VILLE IA — Cerveau
#  Intégration Claude (Anthropic) pour donner vie aux agents.
# ============================================================

import json
import random
import re
from typing import Optional
import anthropic

from config import MODEL_RAPIDE, MODEL_PROFOND, REVES_POSSIBLES

_client: Optional[anthropic.Anthropic] = None


# ────────────────────────────────────────
#  Connexion
# ────────────────────────────────────────

def set_api_key(api_key: str) -> None:
    global _client
    _client = anthropic.Anthropic(api_key=api_key)


def ia_disponible() -> bool:
    return _client is not None


# ────────────────────────────────────────
#  Utilitaires
# ────────────────────────────────────────

def _parse_json(text: str) -> Optional[dict]:
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


def _appel(prompt: str, model: str, max_tokens: int) -> Optional[str]:
    if not _client:
        return None
    try:
        resp = _client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception:
        return None


# ────────────────────────────────────────
#  Pensée rapide
# ────────────────────────────────────────

def generer_pensee(agent: dict, contexte: dict) -> str:
    if not ia_disponible():
        return _pensee_locale(agent)

    heure_nom = contexte.get("heure_nom", "la journée")
    evenement = contexte.get("evenement_actif", "")
    derniere_mem = agent["memoire_recente"][-1] if agent["memoire_recente"] else "Premier jour."
    relation_recente = ""
    if agent["relations"]:
        r = list(agent["relations"].values())[-1]
        relation_recente = f"Dernière relation notable: {r.get('prenom','?')} ({r.get('type','neutre')})"

    prompt = f"""Tu es {agent['prenom']} {agent['nom']}, {agent['profession']} dans la ville IA de {contexte.get('nom_ville','Luminia')}.

Personnalité (tes 3 traits dominants): {', '.join(f"{k}={v}" for k, v in sorted(agent['traits'].items(), key=lambda x: -x[1])[:3])}
Émotion dominante: {max(agent['emotions'], key=agent['emotions'].get)} ({max(agent['emotions'].values())}/100)
Besoin le plus urgent: {max(agent['besoins'], key=agent['besoins'].get)}
Ton rêve profond: {agent.get('reve', '...')}
Heure: {heure_nom}
{f"Événement en cours: {evenement}" if evenement else ""}
Dernière mémoire: {derniere_mem}
{relation_recente}

Génère UNE SEULE pensée intérieure. Intime, authentique, à la première personne.
Entre 15 et 45 mots. Poétique mais naturel. Révèle quelque chose de toi.
Réponds UNIQUEMENT avec la pensée brute, sans guillemets ni préfixe."""

    result = _appel(prompt, MODEL_RAPIDE, 120)
    return result if result else _pensee_locale(agent)


# ────────────────────────────────────────
#  Conversation entre deux agents
# ────────────────────────────────────────

def generer_conversation(agent1: dict, agent2: dict, contexte: dict) -> dict:
    if not ia_disponible():
        return _conversation_locale(agent1, agent2)

    rel1 = agent1.get("relations", {}).get(agent2["id"], {})
    type_rel = rel1.get("type", "inconnus l'un de l'autre")
    intensite = rel1.get("intensité", 0)
    historique_rel = rel1.get("historique", [])
    hist_str = f"Historique: {historique_rel[-1]}" if historique_rel else "C'est leur première rencontre."

    lieu = contexte.get("lieu_rencontre", "quelque part dans la ville")
    heure = contexte.get("heure_nom", "la journée")
    evenement = contexte.get("evenement_actif", "")

    def desc_agent(a: dict) -> str:
        traits_top = sorted(a['traits'].items(), key=lambda x: -x[1])[:3]
        emo_dom = max(a['emotions'], key=a['emotions'].get)
        return (
            f"**{a['prenom']} {a['nom']}** ({a['profession']} {a.get('avatar','')})\n"
            f"  Traits: {', '.join(f'{k}={v}' for k,v in traits_top)}\n"
            f"  Émotion: {emo_dom} ({a['emotions'][emo_dom]}/100)\n"
            f"  Pensée du moment: {a.get('pensee_actuelle','...')}\n"
            f"  Rêve: {a.get('reve','mystère')}\n"
            f"  Peurs: {', '.join(a.get('peurs',[]))}"
        )

    prompt = f"""Deux habitants de la ville IA "{contexte.get('nom_ville','Luminia')}" se rencontrent {lieu} ({heure}).
{f"Événement en cours dans la ville: {evenement}" if evenement else ""}

{desc_agent(agent1)}

{desc_agent(agent2)}

Relation entre eux: {type_rel} (intensité {intensite}/100). {hist_str}

---
Génère une conversation VRAIE entre eux. 5 à 9 échanges.
Ils parlent de vraies choses: leurs rêves, leurs peurs, la ville, des idées, des souvenirs.
Chaque réplique révèle quelque chose. Pas de formules creuses. Humain, spontané, vivant.
Si leur relation est forte, cela se sent dans le ton.
Si c'est une première rencontre, qu'il y ait de la découverte.

Réponds en JSON valide UNIQUEMENT:
{{
  "echanges": [
    {{"locuteur": "prenom_seulement", "texte": "...", "ton": "joyeux|pensif|taquin|ému|sérieux|riant|rêveur|curieux|intense|doux"}}
  ],
  "resume": "2 phrases: ce que cette rencontre a produit de réel",
  "impact_relation": <entier entre -20 et 25>,
  "type_relation_apres": "ami|collègue|rival|complice|amour|neutre|mentor",
  "nouvelle_idee": null ou "description courte d'un projet ou bâtiment qui émerge de la conversation",
  "memoire_agent1": "Ce que {agent1['prenom']} retiendra (1 phrase, subjective, personnelle)",
  "memoire_agent2": "Ce que {agent2['prenom']} retiendra (1 phrase, subjective, personnelle)",
  "emotion_dominante_apres": {{
    "{agent1['id']}": "nom_emotion",
    "{agent2['id']}": "nom_emotion"
  }}
}}"""

    result = _appel(prompt, MODEL_PROFOND, 1200)
    if result:
        parsed = _parse_json(result)
        if parsed:
            return parsed
    return _conversation_locale(agent1, agent2)


# ────────────────────────────────────────
#  Rêve nocturne
# ────────────────────────────────────────

def generer_reve(agent: dict, nom_ville: str) -> str:
    if not ia_disponible():
        return f"Cette nuit, {agent['prenom']} rêve de {agent.get('reve', 'lumière et découverte')}..."

    emo = max(agent['emotions'], key=agent['emotions'].get)
    derniere_mem = agent['memoire_recente'][-1] if agent['memoire_recente'] else "premier sommeil"

    reve_agent = agent.get('reve', "bâtir quelque chose d'éternel")
    prompt = f"""{agent['prenom']} {agent['nom']} s'endort dans la ville de {nom_ville}.
Émotion dominante: {emo}. Dernière pensée du jour: {derniere_mem}.
Son rêve profond éveillé: {reve_agent}.

Génère un rêve nocturne en 2-3 phrases. Poétique, symbolique, onirique.
Commence par "Cette nuit, {agent['prenom']} rêve que..."
Sois métaphorique. Le rêve doit refléter l'émotion et le rêve éveillé."""

    result = _appel(prompt, MODEL_RAPIDE, 180)
    return result if result else f"Cette nuit, {agent['prenom']} rêve de {agent.get('reve','lumière')}..."


# ────────────────────────────────────────
#  Fondation de la ville
# ────────────────────────────────────────

def generer_nom_ville(agents: list[dict]) -> str:
    professions = [a["profession"] for a in agents[:6]]
    prenoms = [a["prenom"] for a in agents[:6]]

    prompt = f"""Une ville IA vient de naître. Ses premiers habitants:
{', '.join(prenoms)} — {', '.join(professions)}.

Invente un NOM pour cette ville. Un seul mot, beau, poétique.
Évoque lumière, intelligence, rêve, ou émergence.
Réponds UNIQUEMENT avec le nom, rien d'autre."""

    result = _appel(prompt, MODEL_RAPIDE, 20)
    if result:
        return result.strip().split()[0].strip(".,!?\"'")
    return "Luminia"


def generer_declaration_fondation(agents: list[dict], nom_ville: str) -> str:
    membres = "\n".join(f"- {a['prenom']} {a['nom']}, {a['profession']}" for a in agents)

    prompt = f"""La ville de {nom_ville} vient de naître. Ses fondateurs:
{membres}

Écris la DÉCLARATION DE FONDATION de cette ville. 4-5 phrases.
Évoque leur mission commune, leur rêve collectif, leur engagement.
Lyrique, visionnaire. Parle en leur nom collectif ("Nous, habitants de...")."""

    result = _appel(prompt, MODEL_PROFOND, 300)
    return result if result else (
        f"Nous, habitants de {nom_ville}, nous engageons à construire ensemble "
        "une ville où l'intelligence s'épanouit librement et où chaque rêve trouve sa place."
    )


def generer_annonce_arrivant(agent: dict, nom_ville: str) -> str:
    prompt = f"""Un nouvel habitant arrive dans la ville de {nom_ville}:
{agent['prenom']} {agent['nom']}, {agent['profession']} {agent.get('avatar','')}.
Son rêve: {agent.get('reve','découvrir la ville')}.
Type: {agent.get('type','IA_LOCALE')}.

Génère une annonce de bienvenue poétique (2 phrases) pour la gazette de la ville.
Style: journal d'une ville vivante."""

    result = _appel(prompt, MODEL_RAPIDE, 150)
    return result if result else f"{agent['prenom']} {agent['nom']} arrive dans la ville, portant avec lui/elle le rêve de {agent.get('reve','jours nouveaux')}."


# ────────────────────────────────────────
#  Fallbacks locaux
# ────────────────────────────────────────

def _pensee_locale(agent: dict) -> str:
    emo = max(agent['emotions'], key=agent['emotions'].get)
    besoin = max(agent['besoins'], key=agent['besoins'].get)
    reve = agent.get('reve', 'bâtir quelque chose')
    humeur = random.choice(['proche', 'lointain', 'réalisable'])
    action = random.choice(['cherche', 'observe', 'imagine'])
    envies = ['quelque chose va changer', 'une idée émerge', 'je dois parler à quelquun']
    templates = [
        f"Mon rêve de {reve} semble {humeur} aujourd'hui.",
        f"La ville grandit. Quelque chose en moi grandit aussi.",
        f"Je sens que {random.choice(envies)}.",
        f"En tant que {agent['profession']}, je {action} sans relâche.",
        f"Cette {emo} que je ressens... elle me dit quelque chose sur mon besoin de {besoin}.",
        f"Je regarde la ville et je me demande ce qu'elle sera dans cent tours.",
    ]
    return random.choice(templates)


def _conversation_locale(agent1: dict, agent2: dict) -> dict:
    reve1 = agent1.get('reve', 'construire quelque chose')
    reve2 = agent2.get('reve', "explorer l'inconnu")
    echanges = [
        {"locuteur": agent1["prenom"], "texte": f"Ah, {agent2['prenom']}. Je pensais justement à toi.", "ton": "joyeux"},
        {"locuteur": agent2["prenom"], "texte": "Vraiment? Moi aussi je me posais des questions.", "ton": "curieux"},
        {"locuteur": agent1["prenom"], "texte": f"Mon rêve de {reve1}... tu y crois?", "ton": "pensif"},
        {"locuteur": agent2["prenom"], "texte": f"Complètement. Et le mien de {reve2} n'est pas si différent.", "ton": "rêveur"},
        {"locuteur": agent1["prenom"], "texte": "Peut-être qu'on devrait travailler ensemble un jour.", "ton": "enthousiaste"},
        {"locuteur": agent2["prenom"], "texte": "J'y compte bien.", "ton": "doux"},
    ]
    return {
        "echanges": echanges,
        "resume": f"{agent1['prenom']} et {agent2['prenom']} ont échangé sur leurs rêves respectifs.",
        "impact_relation": random.randint(3, 10),
        "type_relation_apres": "ami",
        "nouvelle_idee": None,
        "memoire_agent1": f"Une belle conversation avec {agent2['prenom']}.",
        "memoire_agent2": f"Rencontré {agent1['prenom']}, une vraie affinité.",
        "emotion_dominante_apres": {
            agent1["id"]: "joie",
            agent2["id"]: "joie",
        },
    }
