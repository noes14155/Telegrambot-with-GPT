import time
import g4f
from g4f.Provider import (
    AItianhu,
    Acytoo,
    Aichat,
    Ails,
    Aivvm,
    Bard,
    Bing,
    ChatBase,
    ChatgptAi,
    ChatgptLogin,
    CodeLinkAva,
    DeepAi,
    H2o,
    HuggingChat,
    Opchatgpts,
    OpenAssistant,
    OpenaiChat,
    Raycast,
    Theb,
    Vercel,
    Vitalentum,
    Wewordle,
    Ylokh,
    You,
    Yqcloud,
    
)
providers = [
    #AItianhu,
    Acytoo,
    Aichat,
    #Ails,
    #Aivvm,
    #Bard,
    Bing,
    ChatBase,
    ChatgptAi,
    #ChatgptLogin,
    #CodeLinkAva,
    DeepAi,
    #H2o,
    #HuggingChat,
    #Opchatgpts,
    #OpenAssistant,
    #OpenaiChat,
    #Raycast,
    #Theb,
    #Vercel,
    Vitalentum,
    #Wewordle,
    #Ylokh,
    You,
    Yqcloud
    ]
for provider in providers:
    print('Trying', provider)
    start_time = time.time()
    try:
        response = g4f.ChatCompletion.create(messages=[{"role": "user", "content": "Hello"}], model = 'gpt-4', provider=provider)
    except Exception as e:
        print(e)
        continue
        
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Provider: {provider.__name__}")
    print(f"Response: {response}")
    print(f"Time taken: {time_taken} seconds")
    print()