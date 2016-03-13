import os
import xbmc
import xbmcaddon
from xml.dom import minidom
from ump import defs

addon = xbmcaddon.Addon('plugin.program.ump')
addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )
cats=[defs.CT_AUDIO, defs.CT_IMAGE, defs.CT_VIDEO]
types=["index","link","url"]

def update_settings(lst):
	#first remove unused providers from settings.xml
	res=minidom.parse(os.path.join(addon_dir,"resources","settings.xml"))
	inxml=[]
	for xcat in res.getElementsByTagName("category"):
		if xcat.getAttribute("id").lower() in types:
			for item in xcat.getElementsByTagName("setting"):
				if not item.getAttribute("id").lower().split("_") in lst:
					print "@@@@erased@@@@"+item.getAttribute("id").lower()
					xcat.removeChild(item)
				else:
					inxml.append(item.getAttribute("id").lower().split("_"))

	#then remove disabled providers from list and determine new providers to be added to xml
	addnew=[]
	lst2=[]
	for prv in lst:
		if not prv in inxml:
			addnew.append(prv)
		set=addon.getSetting("%s_%s_%s"%(prv[0],prv[1],prv[2]))
		if not set.lower()=="false":
			lst2.append(prv)
	
	#finally add new providers to xml
	for prv in addnew:
		for xcat in res.getElementsByTagName("category"):
			if xcat.getAttribute("id").lower()==prv[1]:
				newnode = res.createElement("setting")
				newnode.setAttribute("id", ("%s_%s_%s"%(prv[0],prv[1],prv[2])))
				newnode.setAttribute("type", "bool")
				newnode.setAttribute("label", "%s:%s"%(prv[0].upper(),prv[2].title()))
				newnode.setAttribute("default", "true")
				xcat.appendChild(newnode)
				print "@@@@added@@@@"+"%s_%s_%s"%(prv[0],prv[1],prv[2])
	res.writexml( open(os.path.join(addon_dir,"resources","settings.xml"), 'w'),encoding="UTF-8")
	return lst2

def find(cat,type):
	if cat is None:
		return [None,None,None]
	lst=[]
	for root, dirs, files in os.walk(os.path.join(addon_dir, 'resources', 'lib' ,'providers')):
		for file in files:
			if file.endswith('.py') and len(file.split("_"))==3 and file.split("_")[0] in cats and file.split("_")[1] in types:
				lst.append(file[:-3].split("_"))
	lst=update_settings(lst)
	lst2=[]
	for item in lst:
		if item[0]==cat and item[1]==type:
			lst2.append(item)
	return lst2

def is_loadable(cat,type,name,providers=None):
	providers=[providers,find(cat,type)][providers is None]
	return [cat,type,name] in providers

def load(cat,type,name):
	fname=cat+"_"+type+"_"+str(name)
	module=__import__("providers",fromlist=[fname])
	return getattr(module,fname)