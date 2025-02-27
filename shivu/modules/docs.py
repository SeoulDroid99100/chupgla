from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message
import json
from bson import ObjectId

# Custom JSON encoder to handle ObjectId
def json_serializer(obj):
    if isinstance(obj, ObjectId):
        return str(obj)  # Convert ObjectId to string
    raise TypeError("Type not serializable")

@shivuu.on_message(filters.command("check_docs"))
async def check_docs(client: shivuu, message: Message):
    # Fetch all documents in the collection (limit to 10 for now, adjust as needed)
    documents = await xy.find({}).to_list(length=10)  # Fetching first 10 documents for display
    
    if not documents:
        await message.reply("❌ No documents found in the collection.")
        return
    
    # Prepare response to show entire document contents
    response = "📑 **Documents in Database**:\n\n"
    
    for doc in documents:
        # Display the entire document content
        response += f"Document Content:\n{json.dumps(doc, default=json_serializer, indent=2)}\n\n"
        response += "-" * 40 + "\n"
    
    # Send the document contents as a reply
    await message.reply(response.strip())
