import os
from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InputFile

def extract_keys(data, parent_key=""):
    """Recursively extracts keys from nested dictionaries and lists."""
    keys = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            keys.append(new_key)
            keys.extend(extract_keys(value, new_key))  # Recursively explore nested structures
    elif isinstance(data, list):
        # For lists, check the first element to determine the structure
        if data:
            keys.extend(extract_keys(data[0], parent_key))  # Assuming list structure is the same for all items in the list

    return keys

@shivuu.on_message(filters.command("getVX"))
async def get_full_collection_structure(client, message):
    # Fetch the first few documents from the collection to analyze the structure
    sample_docs = await lundmate_players.find().limit(5).to_list(None)

    if not sample_docs:
        await message.reply_text("⚠️ The collection is empty or inaccessible.")
        return

    # Collect all the keys from the sample documents
    all_keys = set()  # Use a set to avoid duplicate keys

    for doc in sample_docs:
        all_keys.update(extract_keys(doc))

    # Format the keys into a string
    structure_text = "🔍 **Full Structure of Lundmate Players Collection:**\n\n"
    structure_text += "\n".join([f"- {key}" for key in sorted(all_keys)])

    # Save the structure to a text file
    file_path = "/tmp/lundmate_structure.txt"
    with open(file_path, "w") as f:
        f.write(structure_text)

    # Send the document to the user
    with open(file_path, "rb") as f:
        await message.reply_document(
            document=InputFile(f),
            caption="Here is the full structure of the Lundmate Players collection."
        )

    # Clean up the temporary file
    os.remove(file_path)
