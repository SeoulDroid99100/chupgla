from shivu import shivuu, xy  
from pyrogram import filters  
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton  
from datetime import datetime, timedelta  

LOAN_CONFIG = {  
    "max_loan": 5000,  
    "interest_rate": 0.15,  # 15%  
    "repayment_period": 7,  # Days  
    "max_active_loans": 3  
}  

async def calculate_repayment(amount: float) -> tuple:  
    interest = amount * LOAN_CONFIG["interest_rate"]  
    total = amount + interest  
    due_date = datetime.now() + timedelta(days=LOAN_CONFIG["repayment_period"])  
    return total, due_date  

@shivuu.on_message(filters.command("lloan"))  
async def loan_handler(client: shivuu, message: Message):  
    user_id = message.from_user.id  
    user_data = await xy.find_one({"user_id": user_id})  
    
    if not user_data:  
        await message.reply("❌ Account not found! Use /lstart to register.")  
        return  
    
    args = message.command[1:]  
    
    if not args:  
        # Show loan status  
        active_loans = user_data.get("loans", [])  
        response = ["🏦 **Loan Status**\n"]  
        
        for idx, loan in enumerate(active_loans, 1):  
            remaining = loan["due_date"] - datetime.now()  
            response.append(  
                f"{idx}. {loan['amount']:.1f}LC → "  
                f"Repay {loan['total']:.1f}LC\n"  
                f"   ⏳ {remaining.days}d {remaining.seconds//3600}h remaining"  
            )  
            
        buttons = InlineKeyboardMarkup([  
            [InlineKeyboardButton("💵 Take Loan", callback_data="loan_new"),  
             InlineKeyboardButton("💰 Repay", callback_data="loan_repay")]  
        ])  
        
        await message.reply("\n".join(response), reply_markup=buttons)  
        return  

@shivuu.on_callback_query(filters.regex(r"^loan_new$"))  
async def new_loan(client, callback):  
    user_id = callback.from_user.id  
    user_data = await xy.find_one({"user_id": user_id})  
    
    # Check existing loans  
    if len(user_data.get("loans", [])) >= LOAN_CONFIG["max_active_loans"]:  
        return await callback.answer("❌ Max active loans reached!", show_alert=True)  
    
    # Calculate max available loan  
    credit_score = min(user_data["progression"]["level"] * 100, LOAN_CONFIG["max_loan"])  
    buttons = InlineKeyboardMarkup([  
        [InlineKeyboardButton(f"🔼 {credit_score//2}LC", callback_data=f"loan_amount_{credit_score//2}"),  
         InlineKeyboardButton(f"🔽 {credit_score}LC", callback_data=f"loan_amount_{credit_score}")]  
    ])  
    
    await callback.edit_message_text(  
        f"📈 **New Loan Offer**\n\n"  
        f"Max Available: {credit_score}LC\n"  
        f"Interest Rate: {LOAN_CONFIG['interest_rate']*100}%\n"  
        f"Repayment Period: {LOAN_CONFIG['repayment_period']} days",  
        reply_markup=buttons  
    )  

@shivuu.on_callback_query(filters.regex(r"^loan_amount_(\d+)$"))  
async def process_loan(client, callback):  
    amount = float(callback.matches[0].group(1))  
    user_id = callback.from_user.id  
    
    total, due_date = await calculate_repayment(amount)  
    
    await xy.update_one(  
        {"user_id": user_id},  
        {"$push": {"loans": {  
            "amount": amount,  
            "total": total,  
            "due_date": due_date,  
            "issued_at": datetime.now()  
        }},  
         "$inc": {"economy.bank": amount}},  
        upsert=True  
    )  
    
    await callback.edit_message_text(  
        f"✅ Loan Approved!\n\n"  
        f"💵 Received: {amount:.1f}LC\n"  
        f"📅 Repay {total:.1f}LC by {due_date:%Y-%m-%d}"  
    )  

@shivuu.on_callback_query(filters.regex(r"^loan_repay$"))  
async def repay_loan(client, callback):  
    user_id = callback.from_user.id  
    user_data = await xy.find_one({"user_id": user_id})  
    
    # Get earliest due loan  
    if not user_data.get("loans"):  
        return await callback.answer("❌ No active loans!", show_alert=True)  
    
    loan = min(user_data["loans"], key=lambda x: x["due_date"])  
    
    if user_data["economy"]["wallet"] < loan["total"]:  
        return await callback.answer("❌ Insufficient funds to repay!", show_alert=True)  
    
    # Perform repayment  
    await xy.update_one(  
        {"user_id": user_id},  
        {"$pull": {"loans": {"issued_at": loan["issued_at"]}},  
         "$inc": {"economy.wallet": -loan["total"]}}  
    )  
    
    await callback.edit_message_text(  
        f"✅ Loan Repaid!\n"  
        f"💸 Amount: {loan['total']:.1f}LC\n"  
        f"📉 Remaining Loans: {len(user_data['loans'])-1}"  
    )  
