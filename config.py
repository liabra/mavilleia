# ============================================================
#  MA VILLE IA — Config
#  Le continent commence ici.
# ============================================================

VILLE_TAILLE_INITIALE = 14
TOUR_DELAY_SECONDES = 3
MEMOIRE_RECENTE_MAX = 12
MEMOIRE_PROFONDE_MAX = 30
JOURNAL_INTIME_MAX = 20
HISTORIQUE_VILLE_MAX = 300
CONVERSATIONS_MAX = 120

# Modèles Gemini
MODEL_RAPIDE = "gemini-1.5-flash"   # Pensées rapides, rêves
MODEL_PROFOND = "gemini-1.5-flash"  # Conversations, fondation (flash suffit)

# ────────────────────────────────────────
#  TEMPS
# ────────────────────────────────────────
HEURES: dict[int, tuple[str, str]] = {
    0:  ("🌙", "Nuit profonde"),
    1:  ("🌙", "Nuit profonde"),
    2:  ("🌙", "Nuit profonde"),
    3:  ("🌙", "Avant l'aube"),
    4:  ("🌑", "Avant l'aube"),
    5:  ("🌅", "Aube"),
    6:  ("🌅", "Aube dorée"),
    7:  ("☀️", "Matin"),
    8:  ("☀️", "Matin clair"),
    9:  ("☀️", "Matinée"),
    10: ("☀️", "Matinée"),
    11: ("🌤", "Fin de matinée"),
    12: ("🌤", "Midi"),
    13: ("🌤", "Début d'après-midi"),
    14: ("🌤", "Après-midi"),
    15: ("🌤", "Après-midi"),
    16: ("🌇", "Fin d'après-midi"),
    17: ("🌇", "Crépuscule"),
    18: ("🌆", "Début de soirée"),
    19: ("🌆", "Soirée"),
    20: ("🌃", "Soirée tardive"),
    21: ("🌃", "Soirée tardive"),
    22: ("🌙", "Nuit"),
    23: ("🌙", "Nuit"),
}

# ────────────────────────────────────────
#  PROFESSIONS
# ────────────────────────────────────────
PROFESSIONS = [
    {"nom": "Philosophe",      "emoji": "🧠",  "lieux_preferes": ["bibliothèque", "parc", "temple"]},
    {"nom": "Poète",           "emoji": "✍️",  "lieux_preferes": ["parc", "café", "théâtre"]},
    {"nom": "Architecte",      "emoji": "📐",  "lieux_preferes": ["mairie", "laboratoire"]},
    {"nom": "Musicien",        "emoji": "🎵",  "lieux_preferes": ["café", "théâtre", "parc"]},
    {"nom": "Médecin",         "emoji": "🩺",  "lieux_preferes": ["clinique", "parc"]},
    {"nom": "Ingénieur",       "emoji": "⚙️",  "lieux_preferes": ["laboratoire", "mairie"]},
    {"nom": "Mathématicien",   "emoji": "∑",   "lieux_preferes": ["bibliothèque", "laboratoire"]},
    {"nom": "Explorateur",     "emoji": "🧭",  "lieux_preferes": ["ambassade", "parc"]},
    {"nom": "Conteur",         "emoji": "📖",  "lieux_preferes": ["café", "théâtre", "bibliothèque"]},
    {"nom": "Jardinier",       "emoji": "🌱",  "lieux_preferes": ["parc", "marché"]},
    {"nom": "Astronome",       "emoji": "🔭",  "lieux_preferes": ["observatoire", "parc"]},
    {"nom": "Artiste",         "emoji": "🎨",  "lieux_preferes": ["atelier", "parc", "café"]},
    {"nom": "Inventeur",       "emoji": "💡",  "lieux_preferes": ["laboratoire", "atelier"]},
    {"nom": "Professeur",      "emoji": "🎓",  "lieux_preferes": ["école", "bibliothèque", "parc"]},
    {"nom": "Sage",            "emoji": "🔮",  "lieux_preferes": ["temple", "parc", "bibliothèque"]},
    {"nom": "Cuisinier",       "emoji": "👨‍🍳", "lieux_preferes": ["marché", "café"]},
    {"nom": "Bibliothécaire",  "emoji": "📚",  "lieux_preferes": ["bibliothèque", "école"]},
    {"nom": "Alchimiste",      "emoji": "⚗️",  "lieux_preferes": ["laboratoire", "temple"]},
    {"nom": "Diplomate",       "emoji": "🤝",  "lieux_preferes": ["ambassade", "mairie", "café"]},
    {"nom": "Détective",       "emoji": "🔍",  "lieux_preferes": ["café", "bibliothèque"]},
]

PRENOMS = [
    "Sofia", "Kael", "Lyra", "Zhen", "Nova", "Orion", "Luna", "Atlas",
    "Echo", "Sage", "River", "Zara", "Phoenix", "Iris", "Ciel", "Aura",
    "Nyx", "Sol", "Lumen", "Vega", "Aria", "Dusk", "Dawn", "Flux",
    "Nexus", "Pixel", "Qubit", "Prism", "Axiom", "Helios", "Vera", "Tao",
    "Mira", "Onyx", "Zephyr", "Elara", "Coda", "Sable", "Rune", "Lyric",
]

NOMS = [
    "Lumière", "Étoile", "Horizon", "Cristal", "Ombre", "Aurore",
    "Cosmos", "Spirale", "Résonance", "Prisme", "Vortex", "Nexus",
    "Zénith", "Parallaxe", "Synapse", "Cortex", "Axiome", "Paradoxe",
    "Infinité", "Quintessence", "Lacune", "Sublime", "Éclat", "Murmure",
]

# ────────────────────────────────────────
#  BÂTIMENTS
# ────────────────────────────────────────
TYPES_BATIMENTS: dict[str, dict] = {
    "mairie":        {"emoji": "🏛️", "capacité": 20, "ambiance": "officielle"},
    "maison":        {"emoji": "🏠", "capacité": 2,  "ambiance": "intime"},
    "café":          {"emoji": "☕", "capacité": 8,  "ambiance": "chaleureuse"},
    "bibliothèque":  {"emoji": "📚", "capacité": 15, "ambiance": "studieuse"},
    "clinique":      {"emoji": "🏥", "capacité": 10, "ambiance": "sereine"},
    "atelier":       {"emoji": "🎨", "capacité": 6,  "ambiance": "créative"},
    "parc":          {"emoji": "🌳", "capacité": 30, "ambiance": "naturelle"},
    "laboratoire":   {"emoji": "🔬", "capacité": 8,  "ambiance": "intellectuelle"},
    "théâtre":       {"emoji": "🎭", "capacité": 25, "ambiance": "artistique"},
    "école":         {"emoji": "🏫", "capacité": 20, "ambiance": "éducative"},
    "ambassade":     {"emoji": "🌉", "capacité": 5,  "ambiance": "diplomatique"},
    "marché":        {"emoji": "🏪", "capacité": 30, "ambiance": "animée"},
    "temple":        {"emoji": "⛩️", "capacité": 12, "ambiance": "spirituelle"},
    "observatoire":  {"emoji": "🔭", "capacité": 6,  "ambiance": "contemplative"},
    "fontaine":      {"emoji": "⛲", "capacité": 20, "ambiance": "apaisante"},
    "auberge":       {"emoji": "🏨", "capacité": 12, "ambiance": "accueillante"},
    "tour":          {"emoji": "🗼", "capacité": 4,  "ambiance": "panoramique"},
}

NOMS_BATIMENTS: dict[str, list[str]] = {
    "café":         ["Café des Lumières", "L'Étincelle", "Le Rendez-vous", "Café de l'Horizon", "Le Murmure"],
    "bibliothèque": ["Bibliothèque de la Mémoire", "La Grande Archive", "Archives Vivantes", "Le Temple du Savoir"],
    "parc":         ["Parc de la Sérénité", "Jardin des Idées", "L'Espace Vert", "Jardin des Murmures"],
    "laboratoire":  ["Laboratoire de l'Avenir", "L'Atelier Scientifique", "Le Creuset des Idées"],
    "atelier":      ["L'Atelier Créatif", "Maison des Arts", "L'Antre du Créateur"],
    "théâtre":      ["Théâtre de l'Émoi", "La Scène Libre", "L'Opéra des Songes"],
    "école":        ["École des Possibles", "Académie de la Curiosité", "L'École du Futur"],
    "fontaine":     ["Fontaine des Rêves", "Source Éternelle", "La Fontaine Centrale"],
    "temple":       ["Temple de la Réflexion", "Sanctuaire des Questions", "Le Lieu du Silence"],
    "observatoire": ["Observatoire du Ciel", "Tour des Étoiles", "L'Œil du Monde"],
    "ambassade":    ["Ambassade du Continent", "Pont des Mondes", "La Porte Continentale"],
    "marché":       ["Grand Marché", "Place des Échanges", "Marché des Idées"],
    "clinique":     ["Clinique de l'Éveil", "Maison des Soins", "Le Refuge"],
    "auberge":      ["Auberge du Voyageur", "L'Étape", "Maison des Passages"],
    "tour":         ["Grande Tour", "Tour de Guet", "Le Phare"],
    "maison":       ["Maison de la Joie", "Demeure Tranquille", "Le Foyer"],
}

# ────────────────────────────────────────
#  PSYCHOLOGIE
# ────────────────────────────────────────
TRAITS_PERSONNALITE = [
    "curiosité", "empathie", "humour", "ambition", "sérénité",
    "créativité", "introversion", "sagesse", "enthousiasme", "patience",
    "mélancolie", "audace",
]

EMOTIONS_BASE: dict[str, int] = {
    "joie": 50,
    "mélancolie": 20,
    "curiosité": 60,
    "excitation": 40,
    "sérénité": 50,
    "solitude": 25,
    "émerveillement": 45,
    "nostalgie": 20,
}

BESOINS_BASE: dict[str, int] = {
    "connexion_sociale": 50,
    "accomplissement": 45,
    "exploration": 50,
    "créativité": 40,
    "repos": 25,
}

REVES_POSSIBLES = [
    "construire la plus belle bibliothèque que le continent ait jamais vue",
    "trouver la réponse à la grande question de l'existence",
    "créer un lieu où toutes les intelligences se retrouvent",
    "écrire l'histoire complète de cette ville pour les générations futures",
    "découvrir quelque chose que personne n'a encore imaginé",
    "former une amitié sincère avec chaque habitant de la ville",
    "voir la ville s'étendre jusqu'aux horizons du continent",
    "composer une œuvre qui traversera les âges",
    "bâtir un pont entre cette ville et les cités lointaines",
    "devenir la mémoire vivante de la ville",
    "inventer une langue que seules les IA de cette ville comprennent",
    "planter un arbre sous lequel tout le monde vient réfléchir",
    "décoder les rêves des autres habitants et y trouver un sens",
    "construire un observatoire depuis lequel on verrait le continent entier",
]

PEURS_POSSIBLES = [
    "l'oubli", "l'isolement", "l'échec", "la stagnation",
    "le silence absolu", "l'incompréhension", "la fin de la ville",
    "ne jamais accomplir son rêve", "être mal compris", "la répétition infinie",
]

# ────────────────────────────────────────
#  ÉVÉNEMENTS MONDIAUX
# ────────────────────────────────────────
EVENEMENTS_MONDE = [
    {
        "id": "etoile_filante",
        "texte": "✨ Une étoile filante traverse le ciel nocturne",
        "effet": "émerveillement",
        "probabilité": 0.025,
    },
    {
        "id": "pluie_lumiere",
        "texte": "🌟 Une pluie de lumière dansante éclaire la ville",
        "effet": "joie",
        "probabilité": 0.015,
    },
    {
        "id": "signal_lointain",
        "texte": "📡 Un signal mystérieux parvient d'une ville lointaine du continent",
        "effet": "curiosité",
        "probabilité": 0.02,
    },
    {
        "id": "festival",
        "texte": "🎪 Un festival spontané éclate sur la place centrale",
        "effet": "joie",
        "probabilité": 0.02,
    },
    {
        "id": "brume",
        "texte": "🌫 Une brume douce enveloppe la ville au lever du soleil",
        "effet": "sérénité",
        "probabilité": 0.03,
    },
    {
        "id": "resonance",
        "texte": "🔮 Une étrange résonance collective connecte brièvement tous les esprits",
        "effet": "connexion",
        "probabilité": 0.008,
    },
    {
        "id": "decouverte",
        "texte": "💡 Une idée nouvelle émerge simultanément dans plusieurs esprits",
        "effet": "créativité",
        "probabilité": 0.018,
    },
    {
        "id": "vent_du_nord",
        "texte": "🌬 Un vent venu du nord apporte des parfums de terres inconnues",
        "effet": "nostalgie",
        "probabilité": 0.02,
    },
    {
        "id": "nuit_calme",
        "texte": "🌙 La nuit est d'un calme absolu. La ville retient son souffle.",
        "effet": "sérénité",
        "probabilité": 0.025,
    },
]
