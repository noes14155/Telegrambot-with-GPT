from bot import botfn
import datetime
from duckduckgo_search import DDGS

bn = botfn.botfn()
result = bn.search_ddg("time")
#with DDGS() as ddgs:
#    result ='test'
#    results = ddgs.text(keywords='time',region='wt-wt',safesearch='off',timelimit='m',backend='api')
#    for r in results:     
#        print(r)    
#        #result += r
print(result)
