
import os
import re
import json
from pathlib import Path

def parse_black_flag_monster_clean_type(file_path):
    text = file_path.read_text(encoding="utf-8")
    base_name = file_path.stem.replace("_bf", "").replace("_", " ").title()

    def extract(pattern, default="", flags=0):
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip() if match.lastindex else match.group(0).strip()
        return default

    def parse_type_and_size(text):
        match = re.search(r"\\*(.*?)\\*", text)
        if match:
            parts = match.group(1).strip().split()
            if len(parts) >= 2:
                size = parts[0]
                raw_type = parts[1]
                clean_type = raw_type.split("(")[0].strip().capitalize()
                return size, clean_type
        return "", ""

    def parse_ability_scores_from_table(text):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.match(r"\\|\\s*STR\\s*\\|\\s*DEX\\s*\\|\\s*CON\\s*\\|\\s*INT\\s*\\|\\s*WIS\\s*\\|\\s*CHA\\s*\\|", line, re.IGNORECASE):
                if i + 2 < len(lines):
                    bonus_line = lines[i + 2]
                    bonuses = list(map(int, re.findall(r"[-+]?\d+", bonus_line)))
                    return [10 + b * 2 for b in bonuses]
        return []

    def parse_actions_section(section_title):
        section = re.search(rf"### {section_title}\\n(.+?)(\\n###|\\Z)", text, re.DOTALL)
        if not section:
            return []
        block = section.group(1)
        actions = []
        entries = re.split(r"\\n- ", block)
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            entry = "- " + entry
            name_match = re.match(r"- \\*\\*(.+?)\\.\\*\\* *(.*)", entry, re.DOTALL)
            if name_match:
                name = name_match.group(1).strip()
                desc = name_match.group(2).strip()
                actions.append({"name": name, "desc": desc})
        return actions

    stats = parse_ability_scores_from_table(text)
    con_mod = (stats[2] - 10) // 2 if len(stats) >= 3 else 0
    hp = int(extract(r"\\*\\*Hit Points:\\*\\* (\\d+)", "1"))
    default_die_size = 8 if "dragon" not in base_name.lower() else 12
    avg_die = (default_die_size / 2 + 0.5)
    n = max(1, round(hp / (avg_die + con_mod)))
    hit_dice_str = f"{n}d{default_die_size} + {n * con_mod}"
    size, type_clean = parse_type_and_size(text)

    return {
        "name": f"{base_name} (BF)",
        "size": size,
        "type": type_clean,
        "subtype": "",
        "alignment": "",
        "ac": int(extract(r"\\*\\*Armor Class:\\*\\* (\\d+)", "10")),
        "armor_desc": extract(r"\\*\\*Armor Class:\\*\\* \\d+ \\((.+?)\\)", ""),
        "hp": hp,
        "hit_dice": hit_dice_str,
        "speed": extract(r"\\*\\*Speed:\\*\\* (.+)", "30 ft."),
        "stats": stats,
        "saves": {},
        "skillsaves": {},
        "damage_resistances": False,
        "damage_immunities": False,
        "damage_vulnerabilities": False,
        "condition_immunities": False,
        "senses": extract(r"\\*\\*Senses:\\*\\* (.+)", "passive Perception 10"),
        "languages": extract(r"\\*\\*Languages:\\*\\* (.+)", ""),
        "cr": int(extract(r"CR (\\d+)", "0")),
        "traits": parse_actions_section("Special Abilities"),
        "actions": parse_actions_section("Actions"),
        "bonus_actions": parse_actions_section("Bonus Actions"),
        "reactions": parse_actions_section("Reactions"),
        "legendary_actions": parse_actions_section("Legendary Actions"),
        "layout": "Basic 5e Layout",
        "source": "Kobold Press Black Flag SRD",
    }

def convert_folder_to_json(input_folder, output_file):
    folder = Path(input_folder)
    markdown_files = list(folder.glob("*.md"))
    monsters = [parse_black_flag_monster_clean_type(f) for f in markdown_files]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(monsters, f, indent=2)
    print(f"Converted {len(monsters)} monsters to {output_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert Black Flag monster markdown files to JSON.")
    parser.add_argument("input_folder", help="Path to the folder containing .md files")
    parser.add_argument("output_file", help="Output .json file path")
    args = parser.parse_args()

    convert_folder_to_json(args.input_folder, args.output_file)
