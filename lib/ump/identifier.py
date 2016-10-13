import defs
import json
import md5

class identifier():
    def create(self,info,mediapointer=None):
        ptr=[info.get("index","index")]
        if not mediapointer:mediapointer=self.getpointer(info)
        for key in mediapointer:ptr.append(unicode(info.get(key,key)))
        print "Created Pointer: %s"%str(ptr)
        return json.dumps(ptr)
    
    def mediacode(self,id):
        id=json.loads(id)
        indexer=id[0]
        mediatype=id[1]
        code=id[2]
        return indexer,mediatype,code
    
    def createmd5(self,*args,**kwargs):
        hashed=md5.new(self.create(*args,**kwargs)).hexdigest()
        print "hashed id %s" % hashed 
        return hashed
    
    def getpointer(self,info):
        mediatype=info.get("mediatype",defs.MT_OTHER)
        return defs.mediapointer.get(mediatype,["code"])
