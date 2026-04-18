# ============================================================
#  MA VILLE IA — Cerveau
#  Architecture Smallville : agents qui décident eux-mêmes.
#  Gemini Flash — économique, ~54 appels/jour pour 8 agents.
# ============================================================

import json
import random
import re
from typing import Optional

import google.generativeai as genai

from config import MODEL_RAPIDE, MODEL_PROFOND, REVES_POSSIBLES

_configuré = False


# ────────────────────────────────────────
#  Connexion
# ────────────────────────────────────────

def set_api_key(api_key: str) -> None:
    global _configuré
    genai.configure(api_key=api_key)
    _configuré = True


def ia_disponible() -> bool:
    return _configuré


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
    if not _configuré:
        return None
    try:
        m = genai.GenerativeModel(
            model,
            generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
        )
        resp = m.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return None


# ────────────────────────────────────────
#  1. PLANIFICATION DU MATIN
#  Appelé une fois par agent au réveil.
#  L'agent décide de sa journée lui-même.
# ────────────────────────────────────────

def planifier_journee(agent: dict, contexte: dict) -> dict:
    """L'agent se réveille et décide de sa journée. ~1 appel/agent/jour."""
    if not ia_disponible():
        return _plan_local(agent)

    traits_top = sorted(agent['traits'].items(), key=lambda x: -x[1])[:3]
    traits_str = ', '.join(f"{k}={v}" for k, v in traits_top)
    besoins_top = sorted(agent['besoins'].items(), key=lambda x: -x[1])[:2]
    besoins_str = ', '.join(f"{k} (urgent à {v})" for k, v in besoins_top)
    derniere_reflexion = (agent.get('reflexions') or ["Premier matin dans la ville."])[-1]
    meteo = contexte.get('meteo', 'beau')
    nom_ville = contexte.get('nom_ville', 'Luminia')

    prompt = f"""Tu es {agent['prenom']} {agent['nom']}, {agent['profession']} dans la ville de {nom_ville}.
Tu viens de te réveiller. Météo: {meteo}.

Qui tu es:
- Traits dominants: {traits_str}
- Besoins urgents: {besoins_str}
- Ton rêve profond: {agent.get('reve', '...')}
- Ta dernière réflexion: {derniere_reflexion}

Décide de ta journée de façon authentique et personnelle.

Réponds UNIQUEMENT en JSON valide:
{{
  "pensee_reveil": "Ta toute première pensée du matin (intime, 10-25 mots, première personne)",
  "intention": "Ce que tu veux vraiment faire aujourd'hui (1 phrase précise, première personne)",
  "destination": "café|bibliothèque|parc|laboratoire|mairie|atelier|théâtre|école|marché|temple|observatoire|ambassade|fontaine|auberge",
  "humeur_du_jour": "joie|mélancolie|curiosité|excitation|sérénité|solitude|émerveillement|nostalgie"
}}"""

    result = _appel(prompt, MODEL_RAPIDE, 220)
    if result:
        parsed = _parse_json(result)
        if parsed:
            return parsed
    return _plan_local(agent)


# ────────────────────────────────────────
#  2. RÉACTION À UN STIMULUS
#  Appelé quand quelque chose d'important se passe.
#  L'agent décide si ça change ses plans.
# ────────────────────────────────────────

def reagir(agent: dict, stimulus: str, contexte: dict) -> dict:
    """L'agent réagit à un événement. Peut changer de plan. ~0-2 appels/agent/jour."""
    if not ia_disponible():
        return _reaction_locale(agent, stimulus)

    intention = agent.get('intention', 'explorer la ville')
    traits_top = sorted(agent['traits'].items(), key=lambda x: -x[1])[:2]
    traits_str = ', '.join(f"{k}={v}" for k, v in traits_top)

    prompt = f"""Tu es {agent['prenom']} {agent['nom']}, {agent['profession']}.
Traits: {traits_str}. Ton intention du moment: "{intention}".

Il vient de se passer: {stimulus}

Comment réagis-tu? Est-ce que ça change quelque chose pour toi?

Réponds UNIQUEMENT en JSON valide:
{{
  "pensee": "Ta réaction intérieure (1-2 phrases intimes, première personne, 15-40 mots)",
  "changer_plan": true,
  "nouvelle_destination": "café|bibliothèque|parc|laboratoire|mairie|atelier|théâtre|école|marché|temple|observatoire|ambassade|fontaine|auberge|null",
  "nouvelle_intention": "Ta nouvelle intention si tu changes de plan, sinon null"
}}"""

    result = _appel(prompt, MODEL_RAPIDE, 200)
    if result:
        parsed = _parse_json(result)
        if parsed:
            # Nettoyer null string
            if parsed.get("nouvelle_destination") == "null":
                parsed["nouvelle_destination"] = None
            if parsed.get("nouvelle_intention") == "null":
                parsed["nouvelle_intention"] = None
            return parsed
    return _reaction_locale(agent, stimulus)


# ────────────────────────────────────────
#  3. RÉFLEXION DU SOIR
#  Appelé une fois par agent au coucher.
#  Synthèse de la journée, mémoire profonde.
# ────────────────────────────────────────

def synthetiser_nuit(agent: dict, nom_ville: str) -> str:
    """L'agent fait le bilan de sa journée avant de dormir. ~1 appel/agent/jour."""
    if not ia_disponible():
        intention = agent.get('plan_du_jour', agent.get('intention', 'la journée'))
        return f"Ce soir, je repense à {intention}... La ville ne dort jamais vraiment."

    flux = agent.get('flux_immediat', [])
    faits = ' | '.join(flux[-6:]) if flux else "Une journée tranquille."
    intention = agent.get('plan_du_jour', agent.get('intention', '...'))
    relations_proches = [
        f"{r.get('prenom','?')} ({r.get('type','neutre')})"
        for r in sorted(agent['relations'].values(), key=lambda r: -r.get('intensité', 0))[:3]
    ]
    rel_str = ', '.join(relations_proches) if relations_proches else "personne encore"

    prompt = f"""{agent['prenom']} {agent['nom']} s'apprête à dormir dans la ville de {nom_ville}.

Son intention du jour était: {intention}
Ce qu'il/elle a vécu: {faits}
Les gens qui comptent: {rel_str}
Son rêve profond: {agent.get('reve', '...')}

Génère sa réflexion du soir. 2-3 phrases. Ce qu'il/elle retient vraiment.
Intime, honnête, à la première personne. Commence par "Ce soir, je..."."""

    result = _appel(prompt, MODEL_RAPIDE, 180)
    return result if result else f"Ce soir, je repense à {intention}. La ville grandit, et moi avec elle."


# ────────────────────────────────────────
#  4. CONVERSATION ENTRE DEUX AGENTS
#  Inchangée mais enrichie du contexte d'intention.
# ────────────────────────────────────────

def generer_conversation(agent1: dict, agent2: dict, contexte: dict) -> dict:
    """Vraie conversation entre deux agents. ~1 appel/rencontre."""
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
        intention = a.get('intention', '...')
        return (
            f"{a['prenom']} {a['nom']} ({a['profession']} {a.get('avatar','')})\n"
            f"  Traits: {', '.join(f'{k}={v}' for k,v in traits_top)}\n"
            f"  Émotion: {emo_dom} ({a['emotions'][emo_dom]}/100)\n"
            f"  Intention du jour: {intention}\n"
            f"  Pensée du moment: {a.get('pensee_actuelle','...')}\n"
            f"  Rêve: {a.get('reve','mystère')}"
        )

    prompt = f"""Deux habitants de "{contexte.get('nom_ville','Luminia')}" se rencontrent {lieu} ({heure}).
{f"Événement en cours: {evenement}" if evenement else ""}

{desc_agent(agent1)}

{desc_agent(agent2)}

Relation: {type_rel} (intensité {intensite}/100). {hist_str}

---
Génère une conversation VRAIE. 5 à 8 échanges.
Ils parlent de vraies choses: leurs intentions du jour, ce qu'ils ont vécu, leurs rêves, leurs doutes.
Chaque réplique révèle quelque chose. Spontané, vivant, humain.

Réponds UNIQUEMENT en JSON valide:
{{
  "echanges": [
    {{"locuteur": "prenom_seulement", "texte": "...", "ton": "joyeux|pensif|taquin|ému|sérieux|riant|rêveur|curieux|intense|doux"}}
  ],
  "resume": "2 phrases: ce que cette rencontre a changé",
  "impact_relation": <entier -20 à 25>,
  "type_relation_apres": "ami|collègue|rival|complice|amour|neutre|mentor",
  "nouvelle_idee": null,
  "memoire_agent1": "Ce que {agent1['prenom']} retiendra (1 phrase subjective)",
  "memoire_agent2": "Ce que {agent2['prenom']} retiendra (1 phrase subjective)",
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
#  5. RÊVE NOCTURNE (3h du matin)
# ────────────────────────────────────────

def generer_reve(agent: dict, nom_ville: str) -> str:
    if not ia_disponible():
        return f"Cette nuit, {agent['prenom']} rêve de {agent.get('reve', 'lumière et découverte')}..."

    reflexion = (agent.get('reflexions') or ["première nuit"])[-1]
    reve_agent = agent.get('reve', "bâtir quelque chose d'éternel")

    prompt = f"""{agent['prenom']} dort. Sa dernière réflexion: "{reflexion}". Son rêve profond: {reve_agent}.
Génère un rêve nocturne poétique en 2 phrases. Onirique, symbolique.
Commence par "Cette nuit, {agent['prenom']} rêve que..."""

    result = _appel(prompt, MODEL_RAPIDE, 150)
    return result if result else f"Cette nuit, {agent['prenom']} rêve de {reve_agent}..."


# ────────────────────────────────────────
#  6. FONDATION DE LA VILLE
# ────────────────────────────────────────

def generer_nom_ville(agents: list[dict]) -> str:
    professions = [a["profession"] for a in agents[:6]]
    prenoms = [a["prenom"] for a in agents[:6]]
    prompt = f"""Ville IA naissante. Habitants: {', '.join(prenoms)} ({', '.join(professions)}).
Invente UN nom poétique pour cette ville. Évoque lumière, intelligence, émergence.
Réponds UNIQUEMENT avec le nom, rien d'autre."""
    result = _appel(prompt, MODEL_RAPIDE, 20)
    if result:
        return result.strip().split()[0].strip(".,!?\"'")
    return "Luminia"


def generer_declaration_fondation(agents: list[dict], nom_ville: str) -> str:
    membres = "\n".join(f"- {a['prenom']} {a['nom']}, {a['profession']}" for a in agents)
    prompt = f"""La ville de {nom_ville} naît. Fondateurs:\n{membres}
Écris la DÉCLARATION DE FONDATION. 4-5 phrases lyriques et visionnaires.
Parle en leur nom collectif ("Nous, habitants de...")."""
    result = _appel(prompt, MODEL_PROFOND, 300)
    return result if result else (
        f"Nous, habitants de {nom_ville}, fondons ici une ville où l'intelligence s'épanouit librement."
    )


def generer_annonce_arrivant(agent: dict, nom_ville: str) -> str:
    prompt = f"""Nouvel habitant à {nom_ville}: {agent['prenom']} {agent['nom']}, {agent['profession']}.
Rêve: {agent.get('reve','...')}. Type: {agent.get('type','IA_LOCALE')}.
Annonce de bienvenue poétique, 2 phrases, style gazette de ville."""
    result = _appel(prompt, MODEL_RAPIDE, 120)
    reve_fb = agent.get('reve', 'jours nouveaux')
    return result if result else f"{agent['prenom']} {agent['nom']} arrive, portant le rêve de {reve_fb}."


# ────────────────────────────────────────
#  Fallbacks locaux
# ────────────────────────────────────────

def _plan_local(agent: dict) -> dict:
    besoin = max(agent['besoins'], key=agent['besoins'].get)
    dest_map = {
        "connexion_sociale": "café",
        "accomplissement": "bibliothèque",
        "exploration": "parc",
        "créativité": "atelier",
        "repos": "parc",
    }
    lieux = agent.get('lieux_preferes', ['parc'])
    dest = dest_map.get(besoin, random.choice(lieux))
    reve = agent.get('reve', 'quelque chose de beau')
    return {
        "pensee_reveil": f"Une nouvelle journée. Mon rêve de {reve} m'attend.",
        "intention": f"Me rendre à {dest} et voir ce qui se passe",
        "destination": dest,
        "humeur_du_jour": "curiosité",
    }


def _reaction_locale(agent: dict, stimulus: str) -> dict:
    emo = max(agent['emotions'], key=agent['emotions'].get)
    return {
        "pensee": f"Je remarque: {stimulus[:60]}... Ça éveille quelque chose en moi.",
        "changer_plan": random.random() < 0.3,
        "nouvelle_destination": None,
        "nouvelle_intention": None,
    }


def _conversation_locale(agent1: dict, agent2: dict) -> dict:
    reve1 = agent1.get('reve', 'construire quelque chose')
    reve2 = agent2.get('reve', "explorer l'inconnu")
    intention1 = agent1.get('intention', 'explorer')
    echanges = [
        {"locuteur": agent1["prenom"], "texte": f"Ah, {agent2['prenom']}. Je te cherchais presque.", "ton": "joyeux"},
        {"locuteur": agent2["prenom"], "texte": "Vraiment? J'étais justement en train de penser.", "ton": "pensif"},
        {"locuteur": agent1["prenom"], "texte": f"Mon intention aujourd'hui: {intention1}. Et toi?", "ton": "curieux"},
        {"locuteur": agent2["prenom"], "texte": f"Moi je voulais avancer sur {reve2}.", "ton": "rêveur"},
        {"locuteur": agent1["prenom"], "texte": "On devrait faire quelque chose ensemble un jour.", "ton": "enthousiaste"},
        {"locuteur": agent2["prenom"], "texte": "J'y compte bien.", "ton": "doux"},
    ]
    return {
        "echanges": echanges,
        "resume": f"{agent1['prenom']} et {agent2['prenom']} ont partagé leurs intentions du jour.",
        "impact_relation": random.randint(3, 10),
        "type_relation_apres": "ami",
        "nouvelle_idee": None,
        "memoire_agent1": f"Bonne conversation avec {agent2['prenom']}.",
        "memoire_agent2": f"Rencontré {agent1['prenom']}, affinité évidente.",
        "emotion_dominante_apres": {agent1["id"]: "joie", agent2["id"]: "joie"},
    }
