import requests
import os
import xmltodict
import json

def extract_and_save(parsed):
	for doc in parsed['collection']['document']:
		pmid = doc['id']
		title = ""
		abstract = ""
		annotations = []
		for passage in doc['passage']:
			if passage['infon']['#text'] == 'title':
				title = passage['text']
			elif passage['infon']['#text'] == 'abstract':
				abstract = passage['text']
			if 'annotation' in passage:
				for annot in passage['annotation']:
					if type(annot) is not unicode:
						annotations.append(annot['infon'][1]['#text'])
		newobj = {}
		newobj['pmid'] = pmid
		newobj['title'] = title
		newobj['abstract'] = abstract
		newobj['annotations'] = annotations

		query = 'extracellular matrix OR breast cancer OR ecm remodeling'
		folder_name = 'genes_tagger/'+query+'/'

		file = open(folder_name+pmid, 'w')
		json.dump(newobj, file)


pmids = set(line.strip() for line in open('cache/' + 'extracellular matrix OR breast cancer OR ecm remodeling'))
baseurl = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/Gene/"
pmid_string = ""
query = 'extracellular matrix OR breast cancer OR ecm remodeling'
folder_name = 'genes_tagger/'+query+'/'
os.mkdir(folder_name)

count = 0

for pmid in pmids:
	pmid_string += pmid+","
	count = count+1
	if count == 20:
		request_url = baseurl + pmid_string + "/BioC/"
		data = requests.get(request_url)
		try:
			parsed = xmltodict.parse(data.text)
			extract_and_save(parsed)
		except:
			print "nothing"
		count = 0
		pmid_string = ""

if pmid_string != "":
	request_url = baseurl + pmid_string + "/BioC/"
	data = requests.get(request_url)
	try:
		parsed = xmltodict.parse(data.text)
		extract_and_save(parsed)
	except:
		print "nothing"