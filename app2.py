import streamlit as st
from collections import defaultdict
from pathlib import Path
import base64

st.set_page_config(page_title="Deadlock Counter", layout="wide")

# =========================================================
# CONFIG
# =========================================================

IMAGE_FOLDER = Path("images")

ANTIHEAL_EARLY = ["Healbane", "Toxic Bullets", "Decay", "Spirit Burn"]
ANTIHEAL_LATE = ["Inhibitor", "Crippling Headshot"]

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #111318;
    color: #e7dfcf;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 1200px;
}

h1, h2, h3 {
    color: #f0eadc;
}

.overlay-panel {
    background: rgba(22, 25, 31, 0.95);
    border: 1px solid rgba(201, 179, 139, 0.22);
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 14px;
    overflow: hidden;
}

.section-title {
    font-size: 0.8rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #c9b38b;
    margin-bottom: 10px;
}

.top3-card {
    background: linear-gradient(180deg, rgba(38, 32, 24, 0.96), rgba(24, 21, 18, 0.96));
    border: 1px solid rgba(255, 210, 120, 0.35);
    border-radius: 16px;
    padding: 12px;
    min-height: 280px;
    box-shadow: 0 0 20px rgba(255, 196, 90, 0.08);
    overflow: hidden;
}

.top-rank {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    color: #ffd37a;
    border: 1px solid rgba(255, 211, 122, 0.28);
    background: rgba(255, 211, 122, 0.10);
    margin-bottom: 10px;
}

.compact-card {
    background: rgba(27, 31, 38, 0.92);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 10px;
    min-height: 190px;
    overflow: hidden;
}

.item-name {
    font-size: 0.9rem;
    font-weight: 700;
    color: #f0eadc;
    margin-top: 6px;
    line-height: 1.2;
    word-break: break-word;
    overflow-wrap: anywhere;
}

.item-meta {
    font-size: 0.76rem;
    color: #bdb4a2;
    line-height: 1.35;
    margin-top: 6px;
    word-break: break-word;
    overflow-wrap: anywhere;
}

.priority-badge {
    display: inline-block;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    margin-bottom: 8px;
}

.badge-green {
    background: rgba(68, 170, 90, 0.18);
    color: #9fe0ad;
    border: 1px solid rgba(68, 170, 90, 0.35);
}

.badge-yellow {
    background: rgba(220, 170, 60, 0.18);
    color: #ffd67f;
    border: 1px solid rgba(220, 170, 60, 0.35);
}

.badge-red {
    background: rgba(220, 80, 70, 0.18);
    color: #ff9d95;
    border: 1px solid rgba(220, 80, 70, 0.35);
}

.antiheal-panel-green {
    border: 1px solid rgba(68, 170, 90, 0.35);
    box-shadow: inset 0 0 0 1px rgba(68, 170, 90, 0.08);
}

.antiheal-panel-yellow {
    border: 1px solid rgba(220, 170, 60, 0.35);
    box-shadow: inset 0 0 0 1px rgba(220, 170, 60, 0.08);
}

.antiheal-panel-red {
    border: 1px solid rgba(220, 80, 70, 0.35);
    box-shadow: inset 0 0 0 1px rgba(220, 80, 70, 0.08);
}

.small-note {
    font-size: 0.76rem;
    color: #bdb4a2;
}

div[data-testid="stImage"] img {
    border-radius: 10px;
    border: 2px solid rgba(201, 179, 139, 0.45);
    background: rgba(255,255,255,0.02);
    max-width: 100%;
    height: auto;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(27, 31, 38, 0.92);
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================

def score(priority):
    return {1: 3, 2: 2, 3: 1}.get(priority, 0)

def img_path(name):
    file_name = (
        name.lower()
        .replace(" / ", "_")
        .replace("/", "_")
        .replace("'", "")
        .replace("-", "_")
        .replace(" ", "_")
    )
    path = IMAGE_FOLDER / f"{file_name}.png"
    return str(path) if path.exists() else None

def render_item_image(name, size=72):
    path = img_path(name)
    if path:
        st.image(path, width=size)
    else:
        st.markdown(f"**{name}**")

def antiheal_level(count):
    if count >= 3:
        return "MANDATORY", "badge-red", "antiheal-panel-red"
    elif count == 2:
        return "RECOMMENDED", "badge-yellow", "antiheal-panel-yellow"
    return "OPTIONAL", "badge-green", "antiheal-panel-green"
def get_image_base64(name):
    path = img_path(name)
    if not path:
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_html_card(name, total=None, data=None, rank=None, large=False):
    img_b64 = get_image_base64(name)

    if img_b64:
        image_html = f'<img src="data:image/png;base64,{img_b64}" class="card-image {"large" if large else ""}">'
    else:
        image_html = f'<div class="card-image-fallback {"large" if large else ""}">{name}</div>'

    rank_html = f'<div class="top-rank">TOP {rank}</div>' if rank else ""

    meta_html = ""
    if data is not None and total is not None:
        meta_html = (
            f'<div class="item-meta">'
            f'Score: {total:.1f}<br>'
            f'Overlap: {data["overlap"]}<br>'
            f'Weight: {data["best_weight"]}'
            f'</div>'
        )

    card_class = "top3-card-html" if large else "compact-card-html"

    html = f"""
    <div class="{card_class}">
        {rank_html}
        {image_html}
        <div class="item-name">{name}</div>
        {meta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
# =========================================================
# DATA
# =========================================================

HERO_DATA = {
    "Abrams": {
        "counters": [
            {"item": "Reactive Barrier", "weight": 2},
            {"item": "Rebuttal", "weight": 1},
        ],
        "late": [],
        "categories": {"antiheal": 1},
    },

    "Bebop": {
        "counters": [
            {"item": "Reactive Barrier", "weight": 1},
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 2},
            {"item": "Dispel Magic", "weight": 2},
            {"item": "Counterspell", "weight": 1},
            {"item": "Knockdown", "weight": 2},
        ],
        "late": ["Spellbreaker"],
        "categories": {},
    },

    "Billy": {
        "counters": [
            {"item": "Reactive Barrier", "weight": 2},
            {"item": "Rebuttal", "weight": 1},
            {"item": "Counterspell", "weight": 1},
            {"item": "Suppressor", "weight": 1},
        ],
        "late": [],
        "categories": {"antiheal": 1},
    },

    "Calico": {
        "counters": [
            {"item": "Slowing Hex", "weight": 2},
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 2},
        ],
        "late": ["Cursed Relic"],
        "categories": {},
    },

    "Celeste": {
        "counters": [
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
            {"item": "Knockdown", "weight": 2},
            {"item": "Counterspell", "weight": 2},
        ],
        "late": [],
        "categories": {"antiheal": 3},
    },

    "Doorman": {
        "counters": [
            {"item": "Slowing Hex", "weight": 1},
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 2},
        ],
        "late": ["Spellbreaker"],
        "categories": {},
    },

    "Drifter": {
        "counters": [
            {"item": "Round Barrel", "weight": 1},
            {"item": "Suppressor", "weight": 1},
            {"item": "Weapon Shielding", "weight": 2},
            {"item": "Dispel Magic", "weight": 3},
        ],
        "late": ["Plated Armour"],
        "categories": {},
    },

    "Dynamo": {
        "counters": [
            {"item": "Slowing Hex", "weight": 1},
            {"item": "Counterspell", "weight": 1},
            {"item": "Knockdown", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Graves": {
        "counters": [
            {"item": "Weapon Shielding", "weight": 1},
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 2},
            {"item": "Counterspell", "weight": 2},
        ],
        "late": [],
        "categories": {"antiheal": 1},
    },

    "Grey Talon": {
        "counters": [
            {"item": "Knockdown", "weight": 1},
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 2},
        ],
        "late": ["Spellbreaker"],
        "categories": {},
    },

    "Haze": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Round Barrel", "weight": 1},
            {"item": "Suppressor", "weight": 1},
            {"item": "Reactive Barrier", "weight": 2},
            {"item": "Metalskin", "weight": 3},
        ],
        "late": ["Knockdown"],
        "categories": {},
    },

    "Cassady": {
        "counters": [
            {"item": "Reactive Barrier", "weight": 1},
            {"item": "Slowing Hex", "weight": 2},
            {"item": "Knockdown", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Infernus": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Dispel Magic", "weight": 1},
            {"item": "Slowing Hex", "weight": 1},
            {"item": "Counterspell", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Ivy": {
        "counters": [
            {"item": "Round Barrel", "weight": 2},
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 1},
            {"item": "Knockdown", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Frozone": {
        "counters": [
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
        ],
        "late": [],
        "categories": {"antiheal": 1},
    },

    "Lady Geist": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Spirit Shielding Enchanter's Emblem", "weight": 1},
        ],
        "late": [],
        "categories": {"antiheal": 1},
    },

    "Lash": {
        "counters": [
            {"item": "Slowing Hex", "weight": 1},
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 2},
            {"item": "Knockdown", "weight": 2},
        ],
        "late": ["Spellbreaker"],
        "categories": {},
    },

    "McGinnes": {
        "counters": [
            {"item": "Suppressor", "weight": 1},
            {"item": "Knockdown", "weight": 1},
            {"item": "Alchemical Fire", "weight": 2},
        ],
        "late": [],
        "categories": {"antiheal": 2},
    },

    "Mina": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
            {"item": "Round Barrel", "weight": 2},
            {"item": "Slowing Hex", "weight": 2},
        ],
        "late": ["Spellbreaker", "Cursed Relic"],
        "categories": {},
    },

    "Mirage": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Suppressor", "weight": 1},
            {"item": "Dispel Magic", "weight": 2},
        ],
        "late": ["Plated Armour"],
        "categories": {},
    },

    "Mokrill": {
        "counters": [
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Revival Beam", "weight": 2},
            {"item": "Bullet Resist Shredder", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Page": {
        "counters": [
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
        ],
        "late": [],
        "categories": {},
    },

    "Paradox": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Weapon Shielding", "weight": 1},
            {"item": "Reactive Barrier Enchanter's Emblem", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Pocket": {
        "counters": [
            {"item": "Slowing Hex", "weight": 1},
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
            {"item": "Divine Barrier", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Rem": {
        "counters": [
            {"item": "Monster Rounds", "weight": 1},
            {"item": "Slowing Hex", "weight": 1},
        ],
        "late": [],
        "categories": {"antiheal": 2},
    },

    "Seven": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Reactive Barrier Enchanter's Emblem", "weight": 1},
        ],
        "late": ["Knockdown"],
        "categories": {},
    },

    "Shiv": {
        "counters": [
            {"item": "Spirit Shielding Enchanters Emblem", "weight": 1},
            {"item": "Slow Resist", "weight": 1},
        ],
        "late": [],
        "categories": {"antiheal": 2},
    },

    "Silver": {
        "counters": [
            {"item": "Slowing Hex", "weight": 1},
            {"item": "Weapon Shielding", "weight": 1},
            {"item": "Metalskin", "weight": 2},
        ],
        "late": [],
        "categories": {"antiheal": 2},
    },

    "Sinclair": {
        "counters": [
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 1},
        ],
        "late": [],
        "categories": {},
    },

    "Venator": {
        "counters": [
            {"item": "Round Barrel", "weight": 1},
            {"item": "Suppressor", "weight": 1},
            {"item": "Metalskin", "weight": 2},
        ],
        "late": ["Plated Armour"],
        "categories": {},
    },

    "Victor": {
        "counters": [],
        "late": ["Cursed Relic"],
        "categories": {"antiheal": 1},
    },

    "Vindicta": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 2},
            {"item": "Knockdown", "weight": 1},
            {"item": "Dispel Magic", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Viscous": {
        "counters": [
            {"item": "Rebuttal", "weight": 2},
            {"item": "Round Barrel", "weight": 2},
            {"item": "Suppressor", "weight": 1},
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
        ],
        "late": [],
        "categories": {},
    },

    "Vyper": {
        "counters": [
            {"item": "Healing Rite Extra Regen", "weight": 1},
            {"item": "Weapon Shielding", "weight": 1},
            {"item": "Round Barrel", "weight": 1},
            {"item": "Dispel Magic", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Warden": {
        "counters": [],
        "late": ["Plated Armour", "Juggernaut"],
        "categories": {"antiheal": 1},
    },

    "Wraith": {
        "counters": [
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Counterspell", "weight": 2},
            {"item": "Spirit Shielding", "weight": 2},
        ],
        "late": [],
        "categories": {},
    },

    "Kiriko": {
        "counters": [
            {"item": "Reactive Barrier Enchanters Emblem", "weight": 1},
            {"item": "Silence Wave", "weight": 2},
        ],
        "late": ["Cursed Relic"],
        "categories": {"antiheal": 1},
    },
}

# =========================================================
# CORE LOGIC
# =========================================================

def calculate_base(hero_list):
    items = defaultdict(lambda: {
        "score": 0,
        "overlap": 0,
        "heroes": [],
        "best_weight": 99
    })

    antiheal = 0
    late = defaultdict(list)

    for hero in hero_list:
        data = HERO_DATA[hero]

        for counter in data["counters"]:
            item = counter["item"]
            weight = counter["weight"]

            items[item]["score"] += score(weight)
            items[item]["overlap"] += 1
            items[item]["heroes"].append(hero)
            items[item]["best_weight"] = min(items[item]["best_weight"], weight)

        for late_item in data["late"]:
            late[late_item].append(hero)

        if data["categories"].get("antiheal"):
            antiheal += 1

    results = []
    for item, d in items.items():
        results.append((item, d["score"], d))

    results.sort(key=lambda x: (x[1], x[2]["overlap"], -x[2]["best_weight"]), reverse=True)
    return results, late, antiheal


def calculate_team_with_lane_bonus(selected, lane):
    items = defaultdict(lambda: {
        "score": 0,
        "lane_bonus": 0.0,
        "overlap": 0,
        "heroes": [],
        "best_weight": 99
    })

    antiheal = 0
    lane_antiheal = 0
    late = defaultdict(list)

    for hero in selected:
        data = HERO_DATA[hero]

        for counter in data["counters"]:
            item = counter["item"]
            weight = counter["weight"]

            items[item]["score"] += score(weight)
            items[item]["overlap"] += 1
            items[item]["heroes"].append(hero)
            items[item]["best_weight"] = min(items[item]["best_weight"], weight)

            if hero in lane:
                items[item]["lane_bonus"] += 0.5

        for late_item in data["late"]:
            late[late_item].append(hero)

        if data["categories"].get("antiheal"):
            antiheal += 1
            if hero in lane:
                lane_antiheal += 1

    results = []
    for item, d in items.items():
        total = d["score"] + d["lane_bonus"]
        results.append((item, total, d))

    results.sort(key=lambda x: (x[1], x[2]["overlap"], -x[2]["best_weight"]), reverse=True)
    return results, late, antiheal, lane_antiheal
# =========================================================
# RENDERERS
# =========================================================

def render_top3(results):
    st.markdown('''
<div class="overlay-panel">
    <div class="section-title">Top 3 Recommended</div>
''', unsafe_allow_html=True)

    top3 = results[:3]
    if not top3:
        st.info("No recommendations yet.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    cols = st.columns(3)
    for i, (name, total, data) in enumerate(top3):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f'<div class="top-rank">TOP {i+1}</div>', unsafe_allow_html=True)
                render_item_image(name, size=116)
                st.markdown(f'<div class="item-name">{name}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="item-meta">'
                    f'Score: {total:.1f}<br>'
                    f'Overlap: {data["overlap"]}<br>'
                    f'Weight: {data["best_weight"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.markdown('</div>', unsafe_allow_html=True)

def render_compact_section(title, results, limit=6):
    st.markdown(f'''
<div class="overlay-panel">
    <div class="section-title">{title}</div>
''', unsafe_allow_html=True)

    filtered = results[:limit]

    if not filtered:
        st.info("Nothing to show.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    cols = st.columns(min(4, len(filtered)))
    for i, (name, total, data) in enumerate(filtered):
        with cols[i % len(cols)]:
            with st.container(border=True):
                render_item_image(name, size=78)
                st.markdown(f'<div class="item-name">{name}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="item-meta">'
                    f'Score: {total:.1f}<br>'
                    f'Overlap: {data["overlap"]}<br>'
                    f'Weight: {data["best_weight"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.markdown('</div>', unsafe_allow_html=True)

def render_antiheal(team_count, lane_count):
    label, badge_class, panel_class = antiheal_level(team_count)
    show_early = lane_count == 2 or team_count >= 3

    st.markdown(f"""
    <div class="overlay-panel {panel_class}">
        <div class="section-title">Antiheal</div>
    """, unsafe_allow_html=True)

    st.markdown(f'<span class="priority-badge {badge_class}">{label}</span>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="small-note">Team: {team_count} | Lane: {lane_count}</div>',
        unsafe_allow_html=True
    )

    if show_early:
        st.markdown("**Early**")
        cols = st.columns(len(ANTIHEAL_EARLY))
        for i, item in enumerate(ANTIHEAL_EARLY):
            with cols[i]:
                render_item_image(item, size=64)
                st.caption(item)

    st.markdown("**Late**")
    cols = st.columns(len(ANTIHEAL_LATE))
    for i, item in enumerate(ANTIHEAL_LATE):
        with cols[i]:
            render_item_image(item, size=64)
            st.caption(item)

    st.markdown("</div>", unsafe_allow_html=True)

def render_late(late_map):
    st.markdown("""
    <div class="overlay-panel">
        <div class="section-title">Late-Game Must-Have</div>
    """, unsafe_allow_html=True)

    late_items = list(late_map.keys())
    if not late_items:
        st.info("No late-game items required.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols = st.columns(min(4, len(late_items)))
    for i, item in enumerate(late_items):
        with cols[i % len(cols)]:
            with st.container(border=True):
                render_item_image(item, size=78)
                st.markdown(f'<div class="item-name">{item}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="item-meta">Triggered by: {len(late_map[item])}</div>',
                    unsafe_allow_html=True
                )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# UI
# =========================================================

st.title("Deadlock Counter")

heroes = sorted(HERO_DATA.keys())

cols = st.columns(3)
picked = []
for i in range(6):
    with cols[i % 3]:
        picked.append(st.selectbox(f"Enemy {i+1}", [""] + heroes, key=f"enemy_{i}"))

selected = [x for x in picked if x]
if len(selected) != len(set(selected)):
    st.error("You selected the same enemy hero more than once. Please choose unique heroes.")
    st.stop()
st.subheader("Lane")
lane_col1, lane_col2 = st.columns(2)
with lane_col1:
    lane1 = st.selectbox("Lane 1", [""] + selected, key="lane1")
with lane_col2:
    lane2 = st.selectbox("Lane 2", [""] + selected, key="lane2")

lane = [x for x in [lane1, lane2] if x]
if len(lane) != len(set(lane)):
    st.error("You selected the same lane hero twice. Please choose two different lane heroes.")
    st.stop()

if st.button("Recommend", type="primary"):
    if not selected:
        st.warning("Pick at least one enemy hero.")
    else:
        team_results, late_map, antiheal_count, lane_antiheal = calculate_team_with_lane_bonus(selected, lane)
        lane_results, _, _ = calculate_base(lane) if lane else ([], defaultdict(list), 0)

        st.caption("Enemy Team: " + ", ".join(selected))
        if lane:
            st.caption("Lane: " + ", ".join(lane))

        render_top3(team_results)

        left, right = st.columns([1.4, 1])

        with left:
            render_compact_section("Lane Priority", lane_results, limit=6)
            render_compact_section("Match Priority", team_results[3:], limit=8)

        with right:
            render_antiheal(antiheal_count, lane_antiheal)
            render_late(late_map)