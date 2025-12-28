import re

# Text that uses the {{Color}} template
BA_VUP = re.compile(r"<@ba\.vup>(.*?)</>")
BA_POISE = re.compile(r"<@ba\.poise>(.*?)</>") # Stagger
BA_KEY = re.compile(r"<@ba\.key>(.*?)</>")
BA_HEAL = re.compile(r"<@ba\.heal>(.*?)</>")
BA_INFO = re.compile(r"<@ba\.info>(.*?)</>")
BA_PD = re.compile(r"<@ba\.pd>(.*?)</>") # Physical Damage
BA_CRYST = re.compile(r"<@ba\.cryst>(.*?)</>") # Cryo Damage
BA_PULSE = re.compile(r"<@ba\.pulse>(.*?)</>") # Electric Damage
BA_FIRE = re.compile(r"<@ba\.fire>(.*?)</>") # Heat Damage
BA_NATUR = re.compile(r"<@ba\.natur>(.*?)</>") # Nature Damage
BA_ETHER = re.compile(r"<@ba\.ether>(.*?)</>") # Aether Damage

# Text that uses the {{Glossary}} template
BA_LASTCOMBO = re.compile(r"<#ba\.lastcombo>(.*?)</>")
BA_POISEKNOT = re.compile(r"<#ba\.poiseknot>(.*?)</>")
BA_RETURN = re.compile(r"<#ba\.return>(.*?)</>")
BA_DOT = re.compile(r"<#ba\.dot>(.*?)</>")
BA_STATUSLEVEL = re.compile(r"<#ba\.statuslevel>(.*?)</>")
BA_CONSUME = re.compile(r"<#ba\.consume>(.*?)</>")
BA_PHYSICALSTATUS = re.compile(r"<#ba\.physicalstatus>(.*?)</>")
BA_NOGUARD = re.compile(r"<#ba\.noguard>(.*?)</>")
BA_AIRBORNE = re.compile(r"<#ba\.airborne>(.*?)</>")
BA_KNOCKDOWN = re.compile(r"<#ba\.knockdown>(.*?)</>")
BA_CRUSH = re.compile(r"<#ba\.crush>(.*?)</>")
BA_FRACTURE = re.compile(r"<#ba\.fracture>(.*?)</>")
BA_SPELLINFLICT = re.compile(r"<#ba\.spellinflict>(.*?)</>")
BA_FIREINFLICT = re.compile(r"<#ba\.fireinflict>(.*?)</>")
BA_PULSEINFLICT = re.compile(r"<#ba\.pulseinflict>(.*?)</>")
BA_CRYSTINFLICT = re.compile(r"<#ba\.crystinflict>(.*?)</>")
BA_NATURALINFLICT = re.compile(r"<#ba\.naturalinflict>(.*?)</>")
BA_SPELLSTATUS = re.compile(r"<#ba\.spellstatus>(.*?)</>")
BA_BURNING = re.compile(r"<#ba\.burning>(.*?)</>")
BA_CONDUCT = re.compile(r"<#ba\.conduct>(.*?)</>")
BA_FROZEN = re.compile(r"<#ba\.frozen>(.*?)</>")
BA_CORRUPT = re.compile(r"<#ba\.corrupt>(.*?)</>")
BA_SPELLBURST = re.compile(r"<#ba\.spellburst>(.*?)</>")
BA_FIREBURST = re.compile(r"<#ba\.fireburst>(.*?)</>")
BA_PULSEBURST = re.compile(r"<#ba\.pulseburst>(.*?)</>")
BA_CRYSTBURST = re.compile(r"<#ba\.crystburst>(.*?)</>")
BA_NATURALBURST = re.compile(r"<#ba\.naturalburst>(.*?)</>")
BA_ENHANCE = re.compile(r"<#ba\.enhance>(.*?)</>")
BA_SPELLENHANCE = re.compile(r"<#ba\.spellenhance>(.*?)</>")
BA_FIREENHANCE = re.compile(r"<#ba\.fireenhance>(.*?)</>")
BA_PULSEENHANCE = re.compile(r"<#ba\.pulseenhance>(.*?)</>")
BA_CRYSTENHANCE = re.compile(r"<#ba\.crystenhance>(.*?)</>")
BA_NATURALENHANCE = re.compile(r"<#ba\.naturalenhance>(.*?)</>")
BA_PHYSICALVUL = re.compile(r"<#ba\.physicalvul>(.*?)</>")
BA_SPELLVUL = re.compile(r"<#ba\.spellvul>(.*?)</>")
BA_FIREVUL = re.compile(r"<#ba\.firevul>(.*?)</>")
BA_PULSEVUL = re.compile(r"<#ba\.pulsevul>(.*?)</>")
BA_CRYSTVUL = re.compile(r"<#ba\.crystvul>(.*?)</>")
BA_NATURALVUL = re.compile(r"<#ba\.naturalvul>(.*?)</>")
BA_DISPEL = re.compile(r"<#ba\.dispel>(.*?)</>")
BA_COMBO = re.compile(r"<#ba\.combo>(.*?)</>")
BA_GUARD = re.compile(r"<#ba\.guard>(.*?)</>")
BA_SHIELD = re.compile(r"<#ba\.shield>(.*?)</>")
BA_SLOW = re.compile(r"<#ba\.slow>(.*?)</>")
BA_WEAK = re.compile(r"<#ba\.weak>(.*?)</>")
BA_ORIGINIUM = re.compile(r"<#ba\.originium>(.*?)</>")
BA_CRYSTBREAK = re.compile(r"<#ba\.crystbreak>(.*?)</>")

def efdb_format(text: str) -> str:
    if not text:
        return text

    # Text that uses the {{Color}} template
    text = BA_VUP.sub(r"{{Color|\1|1d}}", text)
    text = BA_POISE.sub(r"{{Color|\1|2}}", text) # Stagger
    text = BA_KEY.sub(r"{{Color|\1|7}}", text)
    text = BA_HEAL.sub(r"{{Color|\1|1c}}", text)
    text = BA_INFO.sub(r"{{Color|\1|9}}", text)
    text = BA_PD.sub(r"{{Color|\1|1}}", text) # Physical Damage
    text = BA_CRYST.sub(r"{{Color|\1|4}}", text) # Cryo Damage
    text = BA_PULSE.sub(r"{{Color|\1|6}}", text) # Electric Damage
    text = BA_FIRE.sub(r"{{Color|\1|3}}", text) # Heat Damage
    text = BA_NATUR.sub(r"{{Color|\1|5}}", text) # Nature Damage
    text = BA_ETHER.sub(r"{{Color|\1|1e}}", text) # Aether Damage

    # Text that uses the {{Glossary}} template
    text = BA_LASTCOMBO.sub(r"{{G|Final Strike|\1}}", text)
    text = BA_POISEKNOT.sub(r"{{G|Stagger Node|\1}}", text)
    text = BA_RETURN.sub(r"{{G|SP Return|\1}}", text)
    text = BA_DOT.sub(r"{{G|DMG Over Time|\1}}", text)
    text = BA_STATUSLEVEL.sub(r"{{G|Status Level|\1}}", text)
    text = BA_CONSUME.sub(r"{{G|Debuff Consumption|\1}}", text)
    text = BA_PHYSICALSTATUS.sub(r"{{G|Physical Status|\1}}", text)
    text = BA_NOGUARD.sub(r"{{G|Vulnerable|\1}}", text)
    text = BA_AIRBORNE.sub(r"{{G|Lift|\1}}", text)
    text = BA_KNOCKDOWN.sub(r"{{G|Knock Down|\1}}", text)
    text = BA_CRUSH.sub(r"{{G|Crush|\1}}", text)
    text = BA_FRACTURE.sub(r"{{G|Breach|\1}}", text)
    text = BA_SPELLINFLICT.sub(r"{{G|Arts Infliction|\1}}", text)
    text = BA_FIREINFLICT.sub(r"{{G|Heat Infliction|\1}}", text)
    text = BA_PULSEINFLICT.sub(r"{{G|Electric Infliction|\1}}", text)
    text = BA_CRYSTINFLICT.sub(r"{{G|Cryo Infliction|\1}}", text)
    text = BA_NATURALINFLICT.sub(r"{{G|Nature Infliction|\1}}", text)
    text = BA_SPELLSTATUS.sub(r"{{G|Arts Reaction|\1}}", text)
    text = BA_BURNING.sub(r"{{G|Combustion|\1}}", text)
    text = BA_CONDUCT.sub(r"{{G|Electrification|\1}}", text)
    text = BA_FROZEN.sub(r"{{G|Solidification|\1}}", text)
    text = BA_CORRUPT.sub(r"{{G|Corrosion|\1}}", text)
    text = BA_SPELLBURST.sub(r"{{G|Arts Burst|\1}}", text)
    text = BA_FIREBURST.sub(r"{{G|Heat Burst|\1}}", text)
    text = BA_PULSEBURST.sub(r"{{G|Electric Burst|\1}}", text)
    text = BA_CRYSTBURST.sub(r"{{G|Cryo Burst|\1}}", text)
    text = BA_NATURALBURST.sub(r"{{G|Nature Burst|\1}}", text)
    text = BA_ENHANCE.sub(r"{{G|Amp|\1}}", text)
    text = BA_SPELLENHANCE.sub(r"{{G|Arts Amp|\1}}", text)
    text = BA_FIREENHANCE.sub(r"{{G|Heat Amp|\1}}", text)
    text = BA_PULSEENHANCE.sub(r"{{G|Electric Amp|\1}}", text)
    text = BA_CRYSTENHANCE.sub(r"{{G|Cryo Amp|\1}}", text)
    text = BA_NATURALENHANCE.sub(r"{{G|Nature Amp|\1}}", text)
    text = BA_PHYSICALVUL.sub(r"{{G|Physical Susceptibility|\1}}", text)
    text = BA_SPELLVUL.sub(r"{{G|Arts Susceptibility|\1}}", text)
    text = BA_FIREVUL.sub(r"{{G|Heat Susceptibility|\1}}", text)
    text = BA_PULSEVUL.sub(r"{{G|Electric Susceptibility|\1}}", text)
    text = BA_CRYSTVUL.sub(r"{{G|Cryo Susceptibility|\1}}", text)
    text = BA_NATURALVUL.sub(r"{{G|Nature Susceptibility|\1}}", text)
    text = BA_DISPEL.sub(r"{{G|Dispel|\1}}", text)
    text = BA_COMBO.sub(r"{{G|Link|\1}}", text)
    text = BA_GUARD.sub(r"{{G|Protect|\1}}", text)
    text = BA_SHIELD.sub(r"{{G|Shield|\1}}", text)
    text = BA_SLOW.sub(r"{{G|Slow|\1}}", text)
    text = BA_WEAK.sub(r"{{G|Weaken|\1}}", text)
    text = BA_ORIGINIUM.sub(r"{{G|Originium Crystal|\1}}", text)
    text = BA_CRYSTBREAK.sub(r"{{G|Shatter|\1}}", text)

    return text
