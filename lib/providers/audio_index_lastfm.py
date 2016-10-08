import json

import xbmc
import re

from ump import countries


mirror="http://ws.audioscrobbler.com/2.0/"
encoding="utf-8"
apikey="ff9469649c8c7d2120758deca5ffa586"
recnum=50

def get_country():
	language=ump.backwards.getLanguage(0).lower()
	found=False
	for country in countries.all:
		if language == country[2]:
			found=True
			if country[0]=="United States of America":
				return "United Kingdom"
			else:
				return country[0]
	if not found:
		return "United Kingdom"

def get_img(ops,default="DefaultFolder.png"):
	im=default
	for image in reversed(ops):
		if image["#text"].startswith("http"):
			im=image["#text"]
			break
	return im

def get_mbrgroups(ambid):
	mbrgroups=[]
	if not ambid == "":
		mbrgroups=ump.get_page("https://musicbrainz.org/artist/%s"%ambid,encoding)
		mbrgroups=re.findall('"application/ld\+json">(.*?)</script>',mbrgroups)[0]
		mbrgroups=mbrgroups.replace('"@id"','"mbgid"')
		mbrgroups=mbrgroups.replace('"@type"','"type"')
		mbrgroups=mbrgroups.replace('https://musicbrainz.org/release-group/','')
		js=json.loads(mbrgroups)
		mbrgroups=js["album"]
		if not isinstance(mbrgroups,list):
			mbrgroups=[mbrgroups]
	return mbrgroups

def get_mbrelease(rgid):
	mbrelease={}
	if not rgid == "":
		mbrelease=ump.get_page("https://musicbrainz.org/release-group/%s"%rgid,encoding)
		mbrelease=re.findall('"application/ld\+json">(.*?)</script>',mbrelease)[0]
		mbrelease=mbrelease.replace('"@id"','"mbid"')
		mbrelease=mbrelease.replace('"@type"','"type"')
		mbrelease=mbrelease.replace('https://musicbrainz.org/release/','')
		js=json.loads(mbrelease)
		mbrelease=js["albumRelease"]
		if isinstance(mbrelease,list):
			mbrelease=mbrelease[0]
		mbcover=js.get("image",{}).get("contentUrl","DefaultFolder.png")
		if mbcover.startswith("//"):mbcover="https:"+mbcover
		mbrelease["image"]=mbcover
	return mbrelease

def get_mbtracks(almbid):
	mbtracks=[]
	if not almbid == "":
		mbtracks=ump.get_page("https://musicbrainz.org/release/%s"%almbid,encoding)
		mbtracks=re.findall('"application/ld\+json">(.*?)</script>',mbtracks)[0]
		mbtracks=mbtracks.replace('"@id"','"mbid"')
		mbtracks=mbtracks.replace('"@type"','"type"')
		mbtracks=mbtracks.replace('https://musicbrainz.org/recording/','')
		mbtracks=json.loads(mbtracks)["track"]
		for mbtrack in mbtracks:
			duration=mbtrack.get("duration","")
			ds=0
			k=0
			for digit in sorted(re.findall("\d+",duration),reverse=True):
				ds+=int(digit)*pow(60,k)
				k+=1
			mbtrack["duration"]=ds
	return mbtracks

def run(ump):
	globals()['ump'] = ump
	if ump.page == "root":
		ump.index_item("Search","search",args={"search":True})
		ump.index_item("Top Artists","topartist")
		ump.index_item("Top Tracks","toptrack")
		ump.index_item("Top Artists in %s"%get_country(),"geoartist",args={"country":get_country()})
		if not get_country() == "United Kingdom":
			ump.index_item("Top Artists in UK","geoartist",args={"country":"United Kingdom"})
		ump.index_item("Top Artists in Countries","country",args={"page":"geoartist"})
		ump.index_item("Top Tracks in %s"%get_country(),"geotrack",args={"country":get_country()})
		if not get_country() == "United Kingdom":
			ump.index_item("Top Artist in UK","geotrack",args={"country":"United Kingdom"})
		ump.index_item("Top Artist in Countries","country",args={"page":"geotrack"})
		ump.index_item("Styles by Artists","tags",args={"where":"artists"})
		ump.index_item("Styles by Albums","tags",args={"where":"albums"})
		ump.index_item("Styles by Tracks","tags",args={"where":"tracks"})
		ump.set_content(ump.defs.CC_FILES)

	elif ump.page=="tags":
		q={"method":"tag.getTopTags","api_key":apikey,"format":"json"}
		js=json.loads(ump.get_page(mirror,None,query=q))
		for result in js["toptags"]["tag"]:
			ump.index_item(result["name"].title(),"tags_%s"%ump.args["where"],args={"tag":result["name"]})
		ump.set_content(ump.defs.CC_FILES)

	elif ump.page=="tags_artists":
		q={"method":"tag.getTopArtists","api_key":apikey,"format":"json","limit":100,"tag":ump.args["tag"]}
		js=json.loads(ump.get_page(mirror,None,query=q))
		for result in js["topartists"]["artist"]:
			if not "mbid" in result: continue
			im=get_img(result.get("image",[]))
			if im=="":
				continue
			ump.index_item(result["name"],"artist",args={"mbid":result["mbid"],"name":result["name"],"artim":im},icon=im, thumb=im)
		ump.set_content(ump.defs.CC_ARTISTS)

	elif ump.page=="tags_albums":
		q={"method":"tag.getTopAlbums","api_key":apikey,"format":"json","limit":100,"tag":ump.args["tag"]}
		js=json.loads(ump.get_page(mirror,None,query=q))
		for result in js["albums"]["album"]:
			name="%s - %s"%(result["artist"]["name"],result["name"])
			im=get_img(result.get("image",[]))
			if im == "":
				continue
			ump.index_item(name,"album",info={"code":result["mbid"],"title":name},icon=im, thumb=im,args={"artist":result["artist"]["name"],"album":result["name"]})
		ump.set_content(ump.defs.CC_ALBUMS)

	elif ump.page=="tags_tracks":
		q={"method":"tag.getTopTracks","api_key":apikey,"format":"json","tag":ump.args["tag"]}
		js=json.loads(ump.get_page(mirror,None,query=q))
		playlist=[]
		for result in js["tracks"]["track"]:
			im=get_img(result.get("image",[]))
			if im=="":
				continue
			info={"code":result["mbid"],"title":result["name"],"artist":result["artist"]["name"],"album":""}
			art={"icon":im, "thumb":im}
			playlist.append({"info":info,"art":art})
		ump.index_item("Play Top 10","urlselect",args={"playlist":playlist[:10]},info={"title":"Top Tracks","code":""})
		ump.index_item("Play All %d"%len(playlist),"urlselect",args={"playlist":playlist},info={"title":"Top Tracks","code":""})
		for item in playlist:
			ump.index_item("%s - %s"%(item["info"]["artist"],item["info"]["title"]),"urlselect",info=item["info"],art=item["art"])
		ump.set_content(ump.defs.CC_ARTISTS)

	elif ump.page=="topartist":
		q={"method":"chart.getTopArtists","api_key":apikey,"format":"json","limit":100}
		js=json.loads(ump.get_page(mirror,None,query=q))
		for result in js["artists"]["artist"]:
			im=get_img(result.get("image",[]))
			if im=="":
				continue
			ump.index_item(result["name"],"artist",args={"mbid":result["mbid"],"name":result["name"],"artim":im},icon=im, thumb=im)
		ump.set_content(ump.defs.CC_ARTISTS)
	
	elif ump.page=="toptrack":
		q={"method":"chart.getTopTracks","api_key":apikey,"format":"json"}
		js=json.loads(ump.get_page(mirror,None,query=q))
		playlist=[]
		for result in js["tracks"]["track"]:
			im=get_img(result.get("image",[]))
			if im=="":
				continue
			info={"code":result["mbid"],"title":result["name"],"artist":result["artist"]["name"],"album":""}
			art={"icon":im, "thumb":im}
			playlist.append({"info":info,"art":art})
		ump.index_item("Play Top 10","urlselect",args={"playlist":playlist[:10]},info={"title":"Top Tracks","code":""})
		ump.index_item("Play All %d"%len(playlist),"urlselect",args={"playlist":playlist},info={"title":"Top Tracks","code":""})
		for item in playlist:
			ump.index_item("%s - %s"%(item["info"]["artist"],item["info"]["title"]),"urlselect",info=item["info"],art=item["art"])
		ump.set_content(ump.defs.CC_ARTISTS)

	elif ump.page=="country":
		page=ump.args["page"]
		ump.args.pop("page")
		processed=[]
		for country in countries.all:
			if country[0] in ["United States of America","United Kingdom",get_country() ] or "," in country[0]:
				continue
			if not country[0] in processed:
				ump.args["country"]=country[0]
				ump.index_item(country[0],page,args=ump.args,info=ump.info,art=ump.art)
				processed.append(country[0])
		ump.set_content(ump.defs.CC_FILES)

	elif ump.page=="geoartist":
		q={"method":"geo.getTopArtists","country":ump.args["country"],"api_key":apikey,"format":"json","limit":100}
		js=json.loads(ump.get_page(mirror,None,query=q))
		for result in js["topartists"]["artist"]:
			im=get_img(result.get("image",[]))
			if im=="":
				continue
			ump.index_item(result["name"],"artist",args={"mbid":result["mbid"],"name":result["name"],"artim":im},icon=im, thumb=im)
		ump.set_content(ump.defs.CC_ARTISTS)

	elif ump.page=="geotrack":
		q={"method":"geo.getTopTracks","country":ump.args["country"],"api_key":apikey,"format":"json","limit":100}
		js=json.loads(ump.get_page(mirror,None,query=q))
		playlist=[]
		for result in js["tracks"]["track"]:
			im=get_img(result.get("image",[]))
			if im=="":
				continue
			info={"code":result["mbid"],"title":result["name"],"artist":result["artist"]["name"],"album":""}
			art={"icon":im, "thumb":im}
			playlist.append({"info":info,"art":art})
		
		ump.index_item("Play Top 40","urlselect",args={"playlist":playlist[:40]},info={"title":"Top Tracks","code":""})
		ump.index_item("Play All %d"%len(playlist),"urlselect",args={"playlist":playlist},info={"title":"Top Tracks","code":""})
		for item in playlist:
			ump.index_item("%s - %s"%(item["info"]["artist"],item["info"]["title"]),"urlselect",info=item["info"],art=item["art"])
		ump.set_content(ump.defs.CC_ARTISTS)


	elif ump.page == "search":
		conf,what=ump.get_keyboard('default', 'Search Audio', True)
		ump.index_item("Search %s in Artists" % what,"searchresult",args={"what":what,"where":"artist"})
		ump.index_item("Search %s in Albums" % what,"searchresult",args={"what":what,"where":"album"})
		ump.index_item("Search %s in Tracks" % what,"searchresult",args={"what":what,"where":"track"})
		ump.set_content(ump.defs.CC_ALBUMS)
		
	elif ump.page == "searchresult":
		what=ump.args["what"]
		where=ump.args["where"]
		q={"method":where+".search",where:what,"api_key":apikey,"format":"json"}
		js=json.loads(ump.get_page(mirror,None,query=q))

		try:
			results=js["results"][where+"matches"][where]
		except:
			return None
		if not isinstance(results,list):
			return None

		if where=="artist":
			for result in results:
				im=get_img(result.get("image",[]))
				if im=="":
					continue
				ump.index_item(result["name"],where,args={"mbid":result["mbid"],"name":result["name"],"artim":im},icon=im, thumb=im)
			ump.set_content(ump.defs.CC_ARTISTS)
		if where=="album":
			for result in results:
				name="%s - %s"%(result["artist"],result["name"])
				im=get_img(result.get("image",[]))
				if im == "":
					continue
				ump.index_item(name,where,info={"code":result["mbid"],"title":name},icon=im, thumb=im)
			ump.set_content(ump.defs.CC_ALBUMS)
		if where=="track":
			for result in results:
				mbid=result["mbid"]
				title=result["name"]
				artist=result["artist"]
				im=get_img(result.get("image",[]))
				if im == "":
					continue
				audio={}
				audio["info"]={"year":"","tracknumber":-1,"duration":"","album":"","artist":artist,"title":title,"code":mbid}
				audio["art"]={"thumb":im,"poster":im}
				ump.index_item(artist+ " - "+title,"urlselect",icon=im, thumb=im,art=audio["art"],info=audio["info"])
			ump.set_content(ump.defs.CC_SONGS)
		
	elif ump.page == "artist":
		ambid=ump.args["mbid"]
		name=ump.args["name"]
		artim=ump.args["artim"]
		q={"method":"artist.getTopAlbums","mbid":ambid,"api_key":apikey,"format":"json"}
		js=json.loads(ump.get_page(mirror,None,query=q))
		results=js.get("topalbums",{"album":[]})["album"]
		if not len(results):
			q={"method":"artist.getTopAlbums","artist":name,"api_key":apikey,"format":"json"}
			js=json.loads(ump.get_page(mirror,None,query=q))
			results=js.get("topalbums",{"album":[]})["album"]
		audio={}
		audio["info"]={"year":"","duration":"","album":"","artist":name,"title":"","code":ambid}
		audio["art"]={"thumb":artim,"poster":artim}
		playlist=[]
		q={"method":"artist.getTopTracks","mbid":ambid,"api_key":apikey,"format":"json"}
		toptracks=json.loads(ump.get_page(mirror,None,query=q)).get("toptracks",{"track":[]})["track"]
		if not len(toptracks):
			q={"method":"artist.getTopTracks","artist":name,"api_key":apikey,"format":"json"}
			toptracks=json.loads(ump.get_page(mirror,None,query=q)).get("toptracks",{"track":[]})["track"]
		for track in toptracks:
			item={}
			item["info"]={"year":"","duration":"",	"album":"",	"artist":track["artist"]["name"],"title":track["name"],	"code":track.get("mbid","-1")}
			im=get_img(track.get("image",[]))
			item["art"]={"thumb":im,"poster":im}
			playlist.append(item)
		ump.index_item("Play Top Tracks from: %s"%name,"urlselect",info=audio["info"],art=audio["art"],args={"playlist":playlist,"mname":"Top Tracks from: %s"%name})
		
		mbrgroups=get_mbrgroups(ambid)

		#sync mbalbums with lastfm albums		
		newalbums=[]
		for mbrgroup in mbrgroups:
			found=False
			for result in results:
				if ump.is_same(mbrgroup["name"],result["name"]):
					result["mbgid"]=mbrgroup["mbgid"]
					found=True
			if not found:
				mbrgroup["mbid"]=""
				newalbums.append(mbrgroup)
		results.extend(newalbums)

		for result in results:
			audio={}
			mbid=result.get("mbid","")
			im=get_img(result.get("image",[]))
			if im == "":
				continue
			audio["info"]={"year":"","duration":"","album":result["name"],"artist":name,"title":"","code":mbid,"mbgid":result.get("mbgid","")}
			audio["art"]={"thumb":im,"poster":im}
			ump.index_item(name + " - " +result["name"],"album",args={"artist":name,"album":result["name"]},icon=im,thumb=im,info=audio["info"],art=audio["art"])
			#todo also list albums which in mb but not on last fm
		ump.set_content(ump.defs.CC_ALBUMS)		


	elif ump.page == "album":
		if not ump.info["mbgid"]=="":
			release=get_mbrelease(ump.info["mbgid"])
			results=get_mbtracks(release["mbid"])
			albumimage=release["image"]
			ambid=release["mbid"]
		elif not ump.info["code"] == "":
			# not sure this will ever hit :/
			q={"method":"album.getinfo","mbid":ump.info["code"],"api_key":apikey,"format":"json"}
			js=json.loads(ump.get_page(mirror,None,query=q))
			alb=js.get("album",None)
			albumimage=get_img(alb.get("image",[]))
			results=get_mbtracks(ump.info["code"])
			ambid=ump.info["code"]
		else:
			q={"method":"album.getinfo","artist":ump.args["artist"],"album":ump.args["album"],"api_key":apikey,"format":"json"}
			js=json.loads(ump.get_page(mirror,None,query=q))
			alb=js.get("album",None)
			albumimage=get_img(alb.get("image",[]))
			results=alb.get("tracks",{"track":[]})["track"]
			ambid=""
		if albumimage=="DefaultFolder.png":
			albumimage=ump.art.get("poster","DefaultFolder.png")
		if len(results):
			relyear=2000
			#first try mb tracks then lastfm
			tracks=[x["name"] for x in results]
			i=0
			audio={}
			audio["info"]={"year":relyear,"tracknumber":-1,	"duration":"","album":ump.info["album"],"artist":ump.info["artist"],"title":"","code":ambid,"tracks":tracks}
			audio["art"]={"thumb":albumimage,"poster":albumimage}
			playlist=[]
			for result in results:
				i+=1
				audio={}
				mbid=result.get("mbid","")
				audio["info"]={"year":relyear,"tracknumber":i,"duration":int(result["duration"]),"album":ump.info["album"],"artist":ump.info["artist"],"title":result["name"],"code":result.get("mbid","")}
				audio["art"]={"thumb":albumimage,"poster":albumimage}
				playlist.append(audio)
			ump.index_item("Play Album: %s"%ump.info["album"],"urlselect",info=audio["info"],art=audio["art"],args={"playlist":playlist,"mname":"%s - %s [ALBUM]"%(ump.info["artist"],ump.info["album"])})
			for item in playlist:
				ump.index_item(item["info"]["artist"]+" - "+item["info"]["title"],"urlselect",info=item["info"],art=item["art"])
		else:
			return None
		ump.set_content(ump.defs.CC_ALBUMS)