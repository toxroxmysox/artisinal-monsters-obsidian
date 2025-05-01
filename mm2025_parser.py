
import os
import re
import json
from pathlib import Path

def parse_mm2025_saves_from_table(text):
    abilities = ["Str", "Dex", "Con", "Int", "Wis", "Cha"]
    saves = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("|STAT|"):
            data_lines = lines[i + 2:i + 8]
            for idx, stat_line in enumerate(data_lines):
                parts = stat_line.strip().split("|")
                if len(parts) >= 5:
                    label = abilities[idx]
                    try:
                        base_mod = int(parts[3].strip().replace("+", "").replace("−", "-"))
                        save_bonus = int(parts[4].strip().replace("+", "").replace("−", "-"))
                        if base_mod != save_bonus:
                            saves[label] = save_bonus
                    except ValueError:
                        continue
            break
    return saves

def parse_mm2025_monster(text, name):
    def extract(pattern, default="", flags=0):
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else default

    def parse_type_and_size():
        match = re.search(r"\\*(.*?)\\*", text)
        if match:
            parts = match.group(1).split(",")[0].split()
            if len(parts) >= 2:
                return parts[0], parts[1].capitalize()
        return "", ""

    def parse_hit_points():
        match = re.search(r"\\*\\*Hit Points:\\*\\* (\\d+) \\(([^)]+)\\)", text)
        return (int(match.group(1)), match.group(2)) if match else (0, "")

    def parse_ability_scores():
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("|STAT|"):
                data_lines = lines[i + 2:i + 8]
                scores = []
                for stat_line in data_lines:
                    match = re.search(r"\\|\\s*\\w+\\s*\\|\\s*(\\d+)", stat_line)
                    if match:
                        scores.append(int(match.group(1)))
                return scores
        return [10, 10, 10, 10, 10, 10]

    def parse_block(header):
        block = re.search(rf"## {header}\\n(.+?)(\\n## |\\Z)", text, re.DOTALL)
        if not block:
            return []
        entries = re.findall(r"\\*\\*\\*(.+?)\\.\\*\\*\\* *(.*?)\\n(?=\\*\\*\\*|$)", block.group(1), re.DOTALL)
        return [{"name": name.strip(), "desc": desc.strip()} for name, desc in entries]

    def parse_skills(line):
        skill_dict = {}
        for part in line.split(","):
            match = re.match(r"(\\w+(?: \\w+)*?) \\+(\\d+)", part.strip())
            if match:
                skill, bonus = match.groups()
                skill_dict[skill] = int(bonus)
        return skill_dict

    def parse_list_field(label):
        line = extract(rf"\\*\\*{label}\\*\\*: (.+)", "")
        if not line:
            return False
        return [x.strip() for x in line.split(";")] if ";" in line else line

    size, type_ = parse_type_and_size()
    hp, hit_dice = parse_hit_points()
    stats = parse_ability_scores()
    traits = parse_block("Traits")
    actions = parse_block("Actions")
    bonus_actions = parse_block("Bonus Actions")
    reactions = parse_block("Reactions")
    legendaries = parse_block("Legendary Actions")

    return {
        "name": name + " (MM2025)",
        "size": size,
        "type": type_,
        "subtype": "",
        "alignment": extract(r"\\*.*?,\\s*(.*?)\\*", ""),
        "ac": int(extract(r"\\*\\*Armor Class:\\*\\* (\\d+)", "10")),
        "armor_desc": "",
        "hp": hp,
        "hit_dice": hit_dice,
        "speed": extract(r"\\*\\*Speed:\\*\\* (.+)", "30 ft."),
        "stats": stats,
        "saves": parse_mm2025_saves_from_table(text),
        "skillsaves": parse_skills(extract(r"\\*\\*Skills\\*\\*: (.+)", "")),
        "damage_resistances": parse_list_field("Resistances"),
        "damage_immunities": parse_list_field("Immunities"),
        "damage_vulnerabilities": parse_list_field("Vulnerabilities"),
        "condition_immunities": parse_list_field("Condition Immunities"),
        "senses": extract(r"\\*\\*Senses:\\*\\* (.+)", "passive Perception 10"),
        "languages": extract(r"\\*\\*Languages:\\*\\* (.+)", ""),
        "cr": int(extract(r"\\*\\*CR\\*\\* (\\d+)", "0")),
        "traits": traits,
        "actions": actions,
        "bonus_actions": bonus_actions,
        "reactions": reactions,
        "legendary_actions": legendaries,
        "layout": "Basic 5e Layout",
        "source": "Monster Manual 2025"
    }

def convert_mm2025_folder_to_json(input_folder, output_file):
    folder = Path(input_folder)
    markdown_files = list(folder.glob("*.md"))
    monsters = []
    for f in markdown_files:
        text = f.read_text(encoding="utf-8")
        monster = parse_mm2025_monster(text, f.stem.replace("_", " ").title())
        monsters.append(monster)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(monsters, f, indent=2)
    print(f"Converted {len(monsters)} monsters to {output_file}")
