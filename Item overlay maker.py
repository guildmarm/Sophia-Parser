# README: Put the itemiconcompositebig files into the itemiconbig folder, and put this script in the itemiconbig folder

from PIL import Image
import os

def ensure_png(filename):
    # If user typed an extension, keep it
    if os.path.splitext(filename)[1]:
        return filename
    return filename + ".png"

def scale_image(img, scale):
    return img.resize((int(img.width * scale), int(img.height * scale)),Image.LANCZOS)

# User input
mode = input("Enter mode (Operator/Gear/Med/Food/Upgrade/Template/Blueprint/Essence): ")

if mode in ("Template", "Upgrade"):
    next
else:
    rarity = int(input("Enter rarity: "))

if mode == "Operator":
    rarity_preset = {
        4: "item_potential_4star",
        5: "item_potential_5star",
        6: "item_potential_6star",
    }
    x = 0
    y = 0
if mode == "Gear":
    rarity_preset = {
        1: "item_icon_bg_equip_qualitycolor_grey",
        2: "item_icon_bg_equip_qualitycolor_green",
        3: "item_icon_bg_equip_qualitycolor_blue",
        4: "item_icon_bg_equip_qualitycolor_purple",
        5: "item_icon_bg_equip_qualitycolor_gold",
    }
    x = 75
    y = 40
if mode == "Med":
    rarity_preset = {
        1: "item_icon_bg_medicine_qualitycolor_grey",
        2: "item_icon_bg_medicine_qualitycolor_green",
        3: "item_icon_bg_medicine_qualitycolor_blue",
        4: "item_icon_bg_medicine_qualitycolor_purple",
        5: "item_icon_bg_medicine_qualitycolor_gold",
    }
    x = 75
    y = 40
if mode == "Food":
    rarity_preset = {
        1: "item_icon_bg_food_qualitycolor_grey",
        2: "item_icon_bg_food_qualitycolor_green",
        3: "item_icon_bg_food_qualitycolor_blue",
        4: "item_icon_bg_food_qualitycolor_purple",
        5: "item_icon_bg_food_qualitycolor_gold",
    }
    x = 75
    y = 40
if mode == "Upgrade":
    x = 0
    y = 0
if mode == "Template":
    x = 75
    y = 40
if mode == "Blueprint":
    rarity_preset = {
        1: "item_icon_bg_blueprint_gray",
        2: "item_icon_bg_blueprint_green",
        3: "item_icon_bg_blueprint_blue",
        4: "item_icon_bg_blueprint_purple",
        5: "item_icon_bg_blueprint_yellow",
        6: "item_icon_bg_blueprint_orange",
        7: "item_icon_bg_blueprint_cyan",
    }
    x = 0
    y = 0
if mode == "Essence":
    rarity_preset = {
        1: "item_gem_rarity_2",
        2: "item_gem_rarity_2",
        3: "item_gem_rarity_3",
        4: "item_gem_rarity_4",
        5: "item_gem_rarity_5",
    }
    x = 9   # X = 8 or 9 and Y = -8 or -9 is interchangable, need further research
    y = -8  # but for now the difference is negligible

if mode in ("Template", "Upgrade"):
    if mode == "Template":
        base_path = ensure_png("item_icon_bg_blueprint")
        overlay_path = ensure_png(input("Enter facility image name or path: ").strip())
    if mode == "Upgrade":
        base_path = ensure_png(input("Enter base item name or path: ").strip())
        overlay_path = ensure_png("item_icon_mark_upgrade")
else:
    base_path = ensure_png(rarity_preset[rarity])
    overlay_path = ensure_png(input("Enter overlay image name or path: ").strip())
output_path = ensure_png(input("Enter output filename: ").strip())

# Load images
base = Image.open(base_path).convert("RGBA")
overlay = Image.open(overlay_path).convert("RGBA")
mode = mode.strip().capitalize()
if mode in ("Gear", "Med", "Food", "Template"):
    overlay = scale_image(overlay, 0.7)

# Paste overlay using its alpha channel
x2 = 0
y2 = 0
base.paste(overlay, (x, y), overlay)

if mode in ("Gear", "Med", "Food", "Template"):
    unlock = Image.open(ensure_png("item_icon_mark_unlocked")).convert("RGBA")
    base.paste(unlock, (x2, y2), unlock)

base.save(output_path)

print("Image saved as:", output_path)