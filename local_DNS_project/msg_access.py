def msg_set(message=None,
                    domain=None, IP=None, via=None, 
                    recursiveFlag=False, rootRecursiveFlag=False, TLDRecursiveFlag=False, cachingRR_1=False, cachingRR_2=False, 
                    nextDest=None, authoritative=True, init=False):
    try:
        if init==True:
            message = {}
            message = {
                'reply' : False,
                'domain': None,
                'IP': None,
                'via': '',
                'recursiveFlag': False,
                'rootRecursiveFlag': False,
                'TLDRecursiveFlag': False,
                'cachingRR_1': None,
                'cachingRR_2': None,
                'nextDest': None,
                'authoritative': True
            }
            return message
        
        if not message:
            raise ValueError("'message' does not exist")
        
        original_msg = message.copy()
        
        if domain:
            message['domain']=domain

        if IP:
            message['IP']=IP

        if via:
            message['via'] = message.get('via') + via

        if recursiveFlag==True or recursiveFlag==False: 
            message['recursiveFlag'] = recursiveFlag
        else:
            raise ValueError("'recursiveFlag' get invalid format (use True/False)")

        if rootRecursiveFlag==True or rootRecursiveFlag==False: 
            message['rootRecursiveFlag'] = rootRecursiveFlag
        else:
            raise ValueError("'rootRecursiveFlag' get invalid format (use True/False)")

        if TLDRecursiveFlag== True or TLDRecursiveFlag==False:
            message['TLDRecursiveFlag'] = TLDRecursiveFlag
        else:
            raise ValueError("'TLDRecursiveFlag' get invalid format (use True/False)")

        if cachingRR_1:
            message['cachingRR_1'] = cachingRR_1

        if cachingRR_2:
            message['cachingRR_2'] = cachingRR_2
        
        if nextDest:
            message['nextDest'] = nextDest

        if authoritative==True or authoritative==False:
            message['authoritative'] = authoritative
        else:
            ValueError("'authoritative' get invalid format (use True/False)")

        return message
    except ValueError as e:
        print(f"Error in 'msg_set' : {e}")
        """
        return = -1로 하고 예외처리 필요
        """
        return original_msg
    

def msg_reply(message, IP, cachingRR_1=None, cachingRR_2=None, authoritative=False):
    reply_message = {
        'reply' : True,
        'domain': message['domain'],
        'IP': IP,
        'via': message['via'],
        'cachingRR_1': cachingRR_1,
        'cachingRR_2': cachingRR_2,
        'authoritative': authoritative
    }
    return reply_message


def get_value(message, type):
    try:
        if not message:
            raise ValueError("'message' does not provided")
        
        if type=="reply":
            return message['reply']
        
        if type=="domain":
            return message['domain']

        if type=="IP":
            return message['IP']

        if type=="via":
            return message['via']

        if type=="recursiveFlag":
            return message['recursiveFlag']

        if type=="rootRecursiveFlag": 
            return message['rootRecursiveFlag']

        if type=="TLDRecursiveFlag":
            return message['TLDRecursiveFlag']

        if type=="cachingRR_1":
            return message['cachingRR_1']

        if type=="cachingRR_2":
            return message['cachingRR_2']
        
        if type=="nextDest":
            return int(message['nextDest'])

        if type=="authoritative":
            return message['authoritative']
        
        raise ValueError("'type' get invalid format(use domain/IP/via/recursiveFlag/rootRecursiveFlag/TLDRecursiveFlag/cachingRR_1/cachingRR_2/nextDest/authoritative)")
    except ValueError as e:
        print(f"Error in 'get_value' : {e}")
        return -1