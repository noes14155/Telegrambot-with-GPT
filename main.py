import telebot
import quora
import os

BOT_TOKEN=os.environ['BOT_TOKEN']
POE_TOKEN=os.environ['POE_TOKEN']
#Create new instance of bot
bot = telebot.TeleBot(BOT_TOKEN)
#models avaiable a poe.com
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
   print('No POE-TOKEN found! Add it in your env file')
   exit
if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit
#function takes user prompt and poe model name, returns chat response
def stream(prompt,model):     
        if api_name == 'quora':          
          response = quora.Completion.create(model=model,
                                             prompt=prompt,
                                             token=POE_TOKEN)
          text = response.completion.choices[0].text
          return text
#selecting model handler
@bot.callback_query_handler(func=lambda call: True)
def model_selector(message):
    model=message.data
    bot.send_message( message.message.chat.id,model+' is active')
#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
def start_handler(update):
    bot.send_message(update.chat.id, text="Hello, Welcome to GPT4free")
#help command handler
@bot.message_handler(commands=['help'])
def help_handler(update):
    bot.send_message(update.chat.id, text="/start : starts the bot\n\
    /changebot : change to available bots in poe.com\n\
    /help : list all commands")
#changebot command handler
@bot.message_handler(commands=['changebot'])
def changebot_handler(message):
    inline_kb = telebot.types.InlineKeyboardMarkup() 
    #making buttons with the model dictionary 
    for i in models:
        inline_kb.add(telebot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    bot.send_message(message.chat.id,'Currently'+i+'is active'+' (gpt-4 and clause-v1.2 requires a paid subscription)', reply_markup=inline_kb)
#Messages other than commands handled 
@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    text = stream(message.text,model)
    bot.send_message(message.chat.id,text)
bot.infinity_polling()

