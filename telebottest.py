import telebot
import quora


BOT_TOKEN = '6137454766:AAE_ou6w8CMuJDDAaY90R8HVPRBRJsnLhoI'
POE_TOKEN = 'ETg9W9Ij8yE1AnGpBMrQzg%3D%3D'
bot = telebot.TeleBot(BOT_TOKEN)
models = {
    'sage'   : 'capybara',
    'gpt-4'  : 'beaver',
    'claude-v1.2'         : 'a2_2',
    'claude-instant-v1.0' : 'a2',
    'gpt-3.5-turbo'       : 'chinchilla'
}
api_name = 'quora'
model = 'gpt-3.5-turbo'   
if POE_TOKEN == "":
   print('No POE-TOKEN in secrets (look at repl instructions')
   exit
def stream(prompt,model):
        
        #model = 'gpt-3.5-turbo'     
        if api_name == 'quora':          
          response = quora.Completion.create(model=model,
                                             prompt=prompt,
                                             token=POE_TOKEN)
          text = response.completion.choices[0].text
          return text
@bot.callback_query_handler(func=lambda call: True)
def model_selector(message):
    model=message.data
    bot.send_message( message.message.chat.id,model+' is active')
@bot.message_handler(commands=['hello', 'start'])
# Create a function to handle the /start command
def start_handler(update):
    bot.send_message(update.chat.id, text="Hello, Welcome to GPT4free")

# Create a function to handle the /changebot command
@bot.message_handler(commands=['help'])
def help_handler(update):
    bot.send_message(update.chat.id, text="/start : starts the bot\n\
    /changebot : change to available bots in poe.com\n\
    /help : list all commands")
@bot.message_handler(commands=['changebot'])
def changebot_handler(message):
    #poe.Client.get_bots()
    #models = poe.Client.bot_names
    text = "Select your chat bot?\nChoose one: *sage*, *gpt-4*, *claude-v1.2*, *claude-instant-v1.0*, *gpt-3.5-turbo*."
    #sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    #bot.register_next_step_handler(sent_msg, model_selector(message.text)) 
    # Create InlineKeyboard with "button"
    inline_kb = telebot.types.InlineKeyboardMarkup()  
    for i in models:
        inline_kb.add(telebot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    # Send message with inline keyboard     
    bot.send_message(message.chat.id,'Currently'+i+'is active'+' (gpt-4 and clause-v1.2 requires a paid subscription)', reply_markup=inline_kb)
    
@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    text = stream(message.text,model)
    bot.send_message(message.chat.id,text)
bot.infinity_polling()

