#!/bin/bash

# Configuration
printf "Enter wiki edit summary: "
read SUMMARY
# Set a default if the input is empty
SUMMARY=${SUMMARY:-"Manual Update"}
CORE_DIR="core"
PARSER_DIR="../Sophia-Parser"

echo "STEP 1: Running Sophia-Parser..."

# Parse the data
echo "Parsing Enemies"
python3 "$PARSER_DIR/endfield_enemy_parser.py"
echo "Parsing Gear"
python3 "$PARSER_DIR/endfield_gear_parser.py"
echo "Parsing Items"
python3 "$PARSER_DIR/endfield_item_parser.py"
echo "Parsing Operators"
python3 "$PARSER_DIR/endfield_operator_parser.py"
echo "Parsing Weapons"
python3 "$PARSER_DIR/endfield_weapon_parser.py"
echo "Parse Complete!"
echo "Sleeping for 20 seconds to help prevent rate limit"
sleep 20

# Login to pwb 
echo "STEP 2: Login to PWB..."
python3 pwb.py login
echo "Login Complete."
sleep 2

echo "STEP 3: Push Files To Endfield Wiki..."
# Core
echo "Pushing enemy data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/full_enemy_page_data.txt" -force -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing gear data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/full_gear_page_data.txt" -force -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing weapon data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/full_weapon_page_data.txt" -force -notitle -summary:"$SUMMARY" -simulate -showdiff
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/module_weapon_skill_data.txt" -force -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing operator data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/full_operator_page_data.txt" -force -notitle -summary:"$SUMMARY" -simulate -showdiff

# Items
echo "Pushing employment contract data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/employment_contract_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing oeprator token data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/operator_tokens_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing operator snapshot data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/operator_snapshots_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing progression material data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/progression_materials_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing rare material data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/rare_materials_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing gatherable data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/gatherables_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing natural data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/naturals_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing aic product data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/aic_products_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing facility data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/facilities_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing quest item data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/quest_items_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing gift data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/gifts_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing seed data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/seeds_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing container data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/containers_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing consumable data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/consumables_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing package data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/packages_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing system blueprint data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/system_blueprints_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing formula data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/formulas_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing photo data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/photo_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing profile data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/profile_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing etchspace data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/etchspace_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing sanity data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/sanity_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing currency data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/currency_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing headhunting data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/headhunting_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Pushing miscellaneous data to the wiki..."
python3 pwb.py pagefromfile -file:"$PARSER_DIR/output/miscellaneous_page_data.txt" -notitle -summary:"$SUMMARY" -simulate -showdiff
echo "Upload Complete!"