import streamlit as st
import sqlite3
import datetime


# -------------------------------
# Database Initialization
# -------------------------------
DB_FILE = "my_kitchen.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Pantry table
    c.execute("""
        CREATE TABLE IF NOT EXISTS pantry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            available INTEGER
        )
    """)
    # Dishes table
    c.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            story TEXT,
            link TEXT,
            recipe_text TEXT,
            cooking_time INTEGER,
            spicy_level TEXT
        )
    """)
    # Ingredients table
    c.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id INTEGER,
            ingredient TEXT,
            mandatory INTEGER,
            FOREIGN KEY (dish_id) REFERENCES dishes(id)
        )
    """)
    conn.commit()
    conn.close()

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

# PANTRY MANAGEMENT FUNCTIONS
def get_pantry():
    """
    Returns a list of pantry items with their availability status.
    Each item is a dictionary: {"name": <str>, "available": <bool>}
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, available FROM pantry ORDER BY name")
    pantry = [{"name": row[0], "available": bool(row[1])} for row in c.fetchall()]
    conn.close()
    return pantry


def add_pantry_item(item_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO pantry (name, available) VALUES (?, ?)", (item_name, 1))  # 1 = available
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_pantry_availability(item_name, available):
    """
    Updates the 'available' status of a pantry item in the database.
    :param item_name: Name of the pantry item (string)
    :param available: Boolean indicating if the item is available
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE pantry SET available=? WHERE name=?",
        (int(available), item_name)
    )
    conn.commit()
    conn.close()


def remove_pantry_item(item_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM pantry WHERE name=?", (item_name,))
    conn.commit()
    conn.close()

# DISHES MANAGEMENT FUNCTIONS

def get_all_dishes():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, story, link, recipe_text, cooking_time, spicy_level FROM dishes ORDER BY name")
    dishes = c.fetchall()
    result = []
    for dish in dishes:
        dish_id, name, story, link, recipe_text, cooking_time, spicy_level = dish
        c.execute("SELECT ingredient, mandatory FROM ingredients WHERE dish_id=? ORDER BY ingredient", (dish_id,))
        ingredients = [{"ingredient": ing, "mandatory": bool(mandatory)} for ing, mandatory in c.fetchall()]
        result.append({
            "id": dish_id,
            "name": name,
            "story": story,
            "link": link,
            "recipe_text": recipe_text,
            "ingredients": ingredients,
            "cooking_time": cooking_time,
            "spicy_level": spicy_level
        })
    conn.close()
    return result

def add_dish(name, story, recipe_text, link, cooking_time=None, spicy_level=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO dishes (name, story, recipe_text, link, cooking_time, spicy_level) VALUES (?, ?, ?, ?, ?, ?)",
        (name, story, recipe_text, link, cooking_time, spicy_level)
    )
    conn.commit()
    dish_id = c.lastrowid
    conn.close()
    return dish_id


def update_dish(dish_id, story, link, recipe_text, ingredients, cooking_time, spicy_level):
    """
    Updates a dish in the database along with its ingredients, cooking time, and spicy level.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Update main dish table
    c.execute(
        """
        UPDATE dishes 
        SET story=?, link=?, recipe_text=?, cooking_time=?, spicy_level=? 
        WHERE id=?
        """,
        (story, link, recipe_text, cooking_time, spicy_level, dish_id)
    )

    # Delete existing ingredients
    c.execute("DELETE FROM ingredients WHERE dish_id=?", (dish_id,))

    # Insert updated ingredients
    for ing in ingredients:
        c.execute(
            "INSERT INTO ingredients (dish_id, ingredient, mandatory) VALUES (?, ?, ?)",
            (dish_id, ing["ingredient"], int(ing["mandatory"]))
        )

    conn.commit()
    conn.close()


def delete_dish(dish_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM ingredients WHERE dish_id=?", (dish_id,))
    c.execute("DELETE FROM dishes WHERE id=?", (dish_id,))
    conn.commit()
    conn.close()

# INGREDIENTS MANAGEMENT FUNCTIONS

def add_ingredient(dish_id, ingredient_name, mandatory=True):
    """
    Adds a single ingredient to a dish in the database.

    :param dish_id: int, the id of the dish
    :param ingredient_name: str, name of the ingredient
    :param mandatory: bool, True if ingredient is mandatory
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ingredients (dish_id, ingredient, mandatory) VALUES (?, ?, ?)",
        (dish_id, ingredient_name, int(mandatory))
    )
    conn.commit()
    conn.close()

def get_ingredients(dish_id):
    """
    Fetch all ingredients for a given dish.

    :param dish_id: int, the id of the dish
    :return: list of dicts with keys 'ingredient' and 'mandatory'
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT ingredient, mandatory FROM ingredients WHERE dish_id=? ORDER BY ingredient", (dish_id,))
    ingredients = [{"ingredient": ing, "mandatory": bool(mandatory)} for ing, mandatory in c.fetchall()]
    conn.close()
    return ingredients


# Initialize DB
init_db()

st.set_page_config(page_title="My Kitchen", layout="wide")

# -------------------------------
# Sidebar Navigation
# -------------------------------
tab = st.sidebar.radio(
    "🍴 My Kitchen Navigation",
    ["🍲 What Can I Cook?", "📚 Dish Library", "🥫 Pantry", "🛒 Shopping", "➕ Add Dishes", "✏️ Edit Dishes", "⚙️ Settings"]
)

# -------------------------------
# Tab 1: What Can I Cook?
# -------------------------------
if tab == "🍲 What Can I Cook?":
    st.header("🍲 What Can I Cook?")
    pantry = get_pantry()
    dishes = get_all_dishes()

    # -------------------------------
    # Pantry-based suggestions
    # -------------------------------
    if not pantry:
        st.info("Add some pantry items first.")
    else:
        pantry_normalized = [p["name"].lower() for p in pantry if p["available"]]
        can_cook = []

        for dish in dishes:
            mandatory_ings = [i["ingredient"].lower() for i in dish["ingredients"] if i["mandatory"]]
            optional_ings = [i["ingredient"].lower() for i in dish["ingredients"] if not i["mandatory"]]

            missing_mandatory = [i for i in mandatory_ings if i not in pantry_normalized]
            missing_optional = [i for i in optional_ings if i not in pantry_normalized]

            if not missing_mandatory:
                can_cook.append((dish, missing_optional))  # store dish and missing optional for later

        # -------------------------------
        # Can cook dishes (mandatory ingredients present)
        # -------------------------------
        if can_cook:
            st.subheader("✅ You can cook:")
            for dish, missing_optional in can_cook:
                expander_title = dish["name"]
                if missing_optional:
                    expander_title += f" →  🚨 Missing optional: {', '.join(missing_optional)}"

                with st.expander(expander_title):
                    if dish["ingredients"]:
                        st.write("**Ingredients:**")
                        for ing in dish["ingredients"]:
                            st.write(f"- {ing['ingredient']} ({'Mandatory' if ing['mandatory'] else 'Optional'})")
                    if dish.get("story"):
                        st.write(f"**Story:** {dish['story']}")
                    if dish.get("recipe_text"):
                        st.write(f"**Recipe:** {dish['recipe_text']}")
                    if dish.get("link"):
                        st.markdown(f"[View Recipe]({dish['link']})", unsafe_allow_html=True)
                    if dish.get("cooking_time"):
                        st.write(f"**Estimated Cooking Time:** {dish['cooking_time']} minutes")
                    if dish.get("spicy_level"):
                        st.write(f"**Spicy Level:** {dish['spicy_level']}")

        # -------------------------------
        # Add spacing / section divider
        # -------------------------------
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown("---")  # horizontal line as visual separator

        # -------------------------------
        # Slider for Mostly Have threshold (moved here)
        # -------------------------------
        mostly_have_threshold = st.slider(
            "Set minimum percentage of ingredients you mostly have:",
            min_value=50,
            max_value=100,
            value=75,
            step=5
        ) / 100  # convert to 0-1 scale

        # -------------------------------
        # Mostly Have Dishes (≥ threshold)
        # -------------------------------
        mostly_have = []
        for dish in dishes:
            all_ings = [i["ingredient"].lower() for i in dish["ingredients"]]
            available_count = sum(1 for i in all_ings if i in pantry_normalized)
            percent_available = available_count / len(all_ings) if all_ings else 0

            # Skip dishes already in can_cook
            if any(dish == d for d, _ in can_cook):
                continue

            if percent_available >= mostly_have_threshold:
                missing_ings = [i["ingredient"] for i in dish["ingredients"] if i["ingredient"].lower() not in pantry_normalized]
                mostly_have.append((dish, missing_ings))

        if mostly_have:
            st.subheader(f"🔹 Mostly Have Ingredients (≥{int(mostly_have_threshold*100)}%)")
            for dish, missing in mostly_have:
                expander_title = f"{dish['name']} →  🚨 🚨 Missing: {', '.join(missing)}"
                with st.expander(expander_title):
                    if dish["ingredients"]:
                        st.write("**Ingredients:**")
                        for ing in dish["ingredients"]:
                            st.write(f"- {ing['ingredient']} ({'Mandatory' if ing['mandatory'] else 'Optional'})")
                    if dish.get("story"):
                        st.write(f"**Story:** {dish['story']}")
                    if dish.get("recipe_text"):
                        st.write(f"**Recipe:** {dish['recipe_text']}")
                    if dish.get("link"):
                        st.markdown(f"[View Recipe]({dish['link']})", unsafe_allow_html=True)
                    if dish.get("cooking_time"):
                        st.write(f"**Estimated Cooking Time:** {dish['cooking_time']} minutes")
                    if dish.get("spicy_level"):
                        st.write(f"**Spicy Level:** {dish['spicy_level']}")
        # -------------------------------
        # Generate Shopping List from Mostly Have Ingredients
        # -------------------------------
        if mostly_have:  # Only show if there are mostly-have dishes
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.subheader("🛒 Generate Shopping List for Mostly Have Dishes")

            if st.button("Generate Shopping List from Mostly Have"):
                shopping_list = {}  # Missing ingredients grouped by dish

                for dish, missing in mostly_have:
                    if missing:  # Only include dishes with missing ingredients
                        shopping_list[dish["name"]] = missing

                if shopping_list:
                    # Build shopping list text
                    shopping_text = ""
                    for dish_name, ings in shopping_list.items():
                        shopping_text += f"{dish_name}:\n"
                        for ing in ings:
                            # Optional marker
                            ing_obj = next((i for i in dishes if i["name"] == dish_name), None)
                            if ing_obj:
                                ing_data = next((x for x in ing_obj["ingredients"] if x["ingredient"] == ing), None)
                                if ing_data and not ing_data["mandatory"]:
                                    ing += " [O]"
                            shopping_text += f"- {ing}\n"
                        shopping_text += "\n"

                    # Editable text area
                    shopping_area = st.text_area(
                        "Editable Shopping List",
                        value=shopping_text,
                        height=300,
                        key="shopping_area_mostly_have"
                    )

                    # Gmail mailto button
                    import urllib.parse

                    recipient = "somranga.retco@gmail.com, nikitashah.me@gmail.com"
                    subject = urllib.parse.quote("Shopping List")
                    body = urllib.parse.quote(shopping_area)  # Use the text area value directly
                    mailto_link = f"mailto:{recipient}?subject={subject}&body={body}"

                    st.markdown(
                        f'<a href="{mailto_link}" target="_blank">'
                        f'<button>📧 Send via Email</button></a>',
                        unsafe_allow_html=True
                    )

                else:
                    st.info("All ingredients for Mostly Have dishes are present in your pantry!")

# -------------------------------
# Tab 2: Dish Library
# -------------------------------
if tab == "📚 Dish Library":
    st.header("📚 Dish Library")
    pantry = get_pantry()
    dishes = get_all_dishes()

    # -------------------------------
    # Dishes Library
    # -------------------------------
    if not dishes:
        st.info("No dishes available.")
    else:
        for dish in dishes:
            with st.expander(dish["name"]):
                if dish["ingredients"]:
                    st.write("**Ingredients:**")
                    for ing in dish["ingredients"]:
                        st.write(f"- {ing['ingredient']} ({'Mandatory' if ing['mandatory'] else 'Optional'})")
                if dish.get("story"):
                    st.write(f"**Story:** {dish['story']}")
                if dish.get("recipe_text"):
                    st.write(f"**Recipe:** {dish['recipe_text']}")
                if dish.get("link"):
                    st.markdown(f"[View Recipe]({dish['link']})", unsafe_allow_html=True)
                # NEW FIELDS
                if dish.get("cooking_time"):
                    st.write(f"**Estimated Cooking Time:** {dish['cooking_time']} minutes")
                if dish.get("spicy_level"):
                    st.write(f"**Spicy Level:** {dish['spicy_level']}")


# -------------------------------
# Tab 2: Pantry
# -------------------------------
elif tab == "🥫 Pantry":
    st.header("🥫 Pantry Management")

    # --- Add pantry items with clearing ---
    pantry_field = {"type": "text", "label": "Enter pantry items (comma separated)", "value": ""}
    pantry_placeholder = st.empty()

    with st.form("add_pantry_form"):
        pantry_input = pantry_placeholder.text_input(pantry_field["label"], value=pantry_field["value"], key="pantry_input")
        submitted = st.form_submit_button("Add Pantry Items")

        if submitted and pantry_input.strip():
            new_items = []
            existing_names = [p["name"] for p in get_pantry()]
            for i in pantry_input.split(","):
                item = i.strip().title()
                if item and item not in existing_names:
                    add_pantry_item(item)  # Add to DB
                    new_items.append(item)
                elif item in existing_names:
                    st.warning(f"You already have '{item}' in your pantry.")

            if new_items:
                st.success(f"Added: {', '.join(new_items)}")

            # Clear the text input
            pantry_placeholder.text_input(pantry_field["label"], value="", key="pantry_input_clear")

    # --- Display pantry table with checkboxes ---
    st.subheader("My Pantry")
    pantry = get_pantry()  # Returns list of dicts: [{'name': ..., 'available': ...}]
    if pantry:
        for idx, item in enumerate(pantry, 1):
            col1, col2 = st.columns([5,1])
            # Checkbox for availability
            available = col1.checkbox(f"{idx}. {item['name']}", value=bool(item['available']), key=f"chk_{item['name']}")
            # Update DB if changed
            if available != bool(item['available']):
                update_pantry_availability(item['name'], available)
            # Delete button
            if col2.button("🗑️", key=f"remove_{item['name']}"):
                remove_pantry_item(item['name'])
                st.success(f"Removed '{item['name']}'")
                break  # Break so the list refreshes on next render
    else:
        st.info("Your pantry is empty. Add items above.")

# -------------------------------
# Tab 3: Shopping
# -------------------------------
elif tab == "🛒 Shopping":
    st.header("🛒 Generate Shopping List")

    # Get all dishes
    dishes = get_all_dishes()
    dish_names = [dish["name"] for dish in dishes]

    # Multi-select box for selecting dishes
    selected_dishes = st.multiselect(
        "Select dishes to generate shopping list:",
        options=dish_names
    )
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Generate Shopping List") and selected_dishes:
        pantry = get_pantry()
        available_items = [p["name"] for p in pantry if p["available"]]

        shopping_list = {}  # Missing ingredients grouped by dish
        all_ingredients = {}  # All ingredients grouped by dish

        for dish in dishes:
            if dish["name"] in selected_dishes:
                missing_ings = []
                dish_ings_display = []

                for ing in dish["ingredients"]:
                    label = f"{ing['ingredient']}" + (" [O]" if not ing['mandatory'] else "")
                    dish_ings_display.append(label)

                    if ing["ingredient"] not in available_items:
                        missing_ings.append(label)

                if missing_ings:
                    shopping_list[dish["name"]] = missing_ings
                all_ingredients[dish["name"]] = dish_ings_display

        # -------------------------------
        # Shopping List Section (editable + download)
        # -------------------------------
        st.subheader("📝 Shopping List (Missing Ingredients)")

        if shopping_list:
            # Build shopping list text
            shopping_text = ""
            for dish_name, ings in shopping_list.items():
                shopping_text += f"{dish_name}:\n"
                for ing in ings:
                    shopping_text += f"- {ing}\n"
                shopping_text += "\n"

            # Editable text area
            shopping_area = st.text_area("Editable Shopping List", value=shopping_text, height=300, key="shopping_area")

            # Gmail mailto button: SOM
            import urllib.parse

            recipient = "somranga.retco@gmail.com, nikitashah.me@gmail.com"
            subject = urllib.parse.quote("Shopping List")
            body = urllib.parse.quote(shopping_area)  # Use the text area value directly
            mailto_link = f"mailto:{recipient}?subject={subject}&body={body}"

            st.markdown(
                f'<a href="{mailto_link}" target="_blank">'
                f'<button>📧 Send to Som via Email</button></a>',
                unsafe_allow_html=True
            )


        else:
            st.info("All ingredients are available in your pantry!")

        # -------------------------------
        # Full Ingredients Section (cross-check)
        # -------------------------------
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.subheader("📋 All Ingredients (Grouped by Dish)")

        if all_ingredients:
            for dish_name, ings in all_ingredients.items():
                st.write(f"**{dish_name}**")
                for ing in ings:
                    st.write(f"- {ing}")
        else:
            st.info("No dishes selected.")


# -------------------------------
# Tab 4: Dishes
# -------------------------------
elif tab == "➕ Add Dishes":
    st.header("➕ Add Dishes")

    # Define input fields
    dish_fields = {
        "dish_name": {"type": "text", "label": "Dish name (Mandatory)", "value": ""},
        "story": {"type": "textarea", "label": "Story/Description", "value": ""},
        "mandatory": {"type": "textarea", "label": "Mandatory Ingredients (comma separated, Mandatory)", "value": ""},
        "optional": {"type": "textarea", "label": "Optional Ingredients (comma separated, Optional)", "value": ""},
        "recipe_text": {"type": "textarea", "label": "Recipe (Optional free text)", "value": ""},
        "link": {"type": "text", "label": "Link (YouTube or website)", "value": ""}
    }

    # Placeholders for clearing fields
    placeholders = {key: st.empty() for key in dish_fields}

    with st.form("add_dish_form"):
        inputs = {}
        for key, props in dish_fields.items():
            if props["type"] == "text":
                inputs[key] = placeholders[key].text_input(props["label"], value=props["value"], key=f"{key}_input")
            elif props["type"] == "textarea":
                inputs[key] = placeholders[key].text_area(props["label"], value=props["value"], key=f"{key}_input")

        # Non-text inputs
        cooking_time_input = st.number_input("Estimated Cooking Time (minutes)", min_value=5, step=5, value=5, key="cooking_time_input")
        spicy_level_input = st.selectbox("Spicy Level", ["Mild", "Medium", "Hot"], key="spicy_level_input")

        submitted = st.form_submit_button("Add Dish")

        if submitted:
            if not inputs["dish_name"].strip():
                st.warning("Dish name is required!")
            elif not inputs["mandatory"].strip():
                st.warning("Mandatory ingredients are required!")
            else:
                # Process ingredients
                mandatory_list = [i.strip().title() for i in inputs["mandatory"].split(",") if i.strip()]
                optional_list = [i.strip().title() for i in inputs["optional"].split(",") if i.strip()]
                ingredients_combined = [{"ingredient": i, "mandatory": True} for i in mandatory_list]
                ingredients_combined += [{"ingredient": i, "mandatory": False} for i in optional_list]

                # Insert dish into DB
                dish_id = add_dish(
                    name=inputs["dish_name"].title(),
                    story=inputs["story"],
                    recipe_text=inputs["recipe_text"],
                    link=inputs["link"],
                    cooking_time=cooking_time_input,
                    spicy_level=spicy_level_input
                )

                # Insert ingredients into DB
                for ing in ingredients_combined:
                    add_ingredient(
                        dish_id=dish_id,
                        ingredient_name=ing["ingredient"],
                        mandatory=ing["mandatory"]
                    )

                st.success(f"Dish '{inputs['dish_name'].title()}' added successfully!")

                # Clear text fields
                for key, ph in placeholders.items():
                    if dish_fields[key]["type"] in ["text", "textarea"]:
                        ph.text_input(dish_fields[key]["label"], value="", key=f"{key}_input_clear") if dish_fields[key]["type"] == "text" else ph.text_area(dish_fields[key]["label"], value="", key=f"{key}_input_clear")

# -------------------------------
# Tab 4: Edit Dishes
# -------------------------------
elif tab == "✏️ Edit Dishes":
    st.header("✏️ Edit Dishes")

    dishes = get_all_dishes()
    if not dishes:
        st.info("No dishes available to edit.")
    else:
        # Select dish
        dish_options = {dish["name"]: dish for dish in dishes}
        selected_name = st.selectbox("Select a dish to edit", list(dish_options.keys()))
        dish = dish_options[selected_name]

        # Pre-fill fields
        dish_fields = {
            "story": {"type": "textarea", "label": "Story/Description", "value": dish.get("story", "")},
            "recipe_text": {"type": "textarea", "label": "Recipe (Optional free text)", "value": dish.get("recipe_text", "")},
            "link": {"type": "text", "label": "Link (YouTube or website)", "value": dish.get("link", "")},
            "mandatory": {"type": "textarea", "label": "Mandatory Ingredients (comma separated)",
                          "value": ", ".join([i["ingredient"] for i in dish["ingredients"] if i["mandatory"]])},
            "optional": {"type": "textarea", "label": "Optional Ingredients (comma separated)",
                         "value": ", ".join([i["ingredient"] for i in dish["ingredients"] if not i["mandatory"]])}
        }

        # Placeholders
        placeholders = {key: st.empty() for key in dish_fields}

        with st.form("edit_dish_form"):
            inputs = {}
            for key, props in dish_fields.items():
                if props["type"] == "text":
                    inputs[key] = placeholders[key].text_input(props["label"], value=props["value"], key=f"{key}_edit")
                elif props["type"] == "textarea":
                    inputs[key] = placeholders[key].text_area(props["label"], value=props["value"], key=f"{key}_edit")

            # Non-text inputs
            cooking_time_input = st.number_input(
                "Estimated Cooking Time (minutes)",
                min_value=5,
                step=5,
                value=dish.get("cooking_time", 5),
                key="cooking_time_edit"
            )
            spicy_level_input = st.selectbox(
                "Spicy Level",
                ["Mild", "Medium", "Hot"],
                index=["Mild", "Medium", "Hot"].index(dish.get("spicy_level", "Mild")),
                key="spicy_level_edit"
            )

            submitted = st.form_submit_button("Update Dish")

            if submitted:
                # Process ingredients
                mandatory_list = [i.strip().title() for i in inputs["mandatory"].split(",") if i.strip()]
                optional_list = [i.strip().title() for i in inputs["optional"].split(",") if i.strip()]
                ingredients_combined = [{"ingredient": i, "mandatory": True} for i in mandatory_list]
                ingredients_combined += [{"ingredient": i, "mandatory": False} for i in optional_list]

                # Call update function
                update_dish(
                    dish_id=dish["id"],
                    story=inputs["story"],
                    link=inputs["link"],
                    recipe_text=inputs["recipe_text"],
                    ingredients=ingredients_combined,
                    cooking_time=cooking_time_input,
                    spicy_level=spicy_level_input
                )

                st.success(f"Dish '{dish['name']}' updated successfully!")

# Delete Dish
    st.header("🗑️ Delete Dishes")

    dishes = get_all_dishes()
    dish_names = [d["name"] for d in dishes]

    selected_name = st.selectbox("Select a dish", dish_names)
    dish = next(d for d in dishes if d["name"] == selected_name)

    # Delete button
    if st.button(f"🗑️ Delete '{dish['name']}'"):
        delete_dish(dish["id"])
        st.success(f"Dish '{dish['name']}' deleted.")

        # Remove from local list to update dropdown without rerun
        dishes = [d for d in dishes if d["id"] != dish["id"]]
        dish_names = [d["name"] for d in dishes]


#SETTINGS TAB

if tab == "⚙️ Settings":
    st.header("⚙️ Settings & Backup")

    st.subheader("Export Data Backup")
    st.write("Download a backup of your SQLite database.")

    # Generate filename with date and time
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    backup_filename = f"my_kitchen_backup_{timestamp}.db"

    # Export DB button
    with open(DB_FILE, "rb") as f:
        db_bytes = f.read()

    st.download_button(
        label="💾 Download DB Backup",
        data=db_bytes,
        file_name=backup_filename,
        mime="application/octet-stream"
    )
