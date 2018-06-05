from apiadapter import APIAdapter
from clusterer import Clusterer
import os
import itertools
import requests
import xmltodict
import json

class SearchDirector:
	def __init__(self):
		return

	def setParams(self, searchTerm, infoSet, isGeneSet):
		self.searchTerm = searchTerm
		if isGeneSet:
			self.geneSet = infoSet
			self.relDocsSet = self.get_rel_docs_from_gset(infoSet)
		else:
			self.relDocsSet = infoSet

	def compile_data(self):
		# call mesh_exp_combn to get diff mesh exps
		# make api calls, get the data folder
		if not os.path.exists(APIAdapter.get_data_foldername(self.get_search_term())):
				os.mkdir(APIAdapter.get_data_foldername(self.get_search_term()))

		combs = self.mesh_exp_combn()

		count = 0
		unique_pmids = set()

		for query in combs:

			count += 1
			# if count < 588:
			# 	continue

			pmids = APIAdapter.get_search_results(query, 400)

			# TODO: this belongs in apiadapter
			baseurl = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
			baseurl += "db=pubmed&rettype=abstract&retmode=text&id="
			
			ids = ""
			for pmid in pmids:
				ids += str(pmid) + ","
				unique_pmids.add(pmid) 
			data = requests.get(baseurl+ids).text

			jsonObject = {}
			jsonObject['queryId'] = count
			jsonObject['query'] = query
			jsonObject['articleIds'] = ids
			jsonObject['abstracts'] = data

			with open(APIAdapter.get_data_foldername(self.get_search_term())+"/"+str(count)+'.json', 'w') as outfile:
				json.dump(jsonObject, outfile)
			
			
			print count

		print "unique_pmids ------> " + str(len(unique_pmids))



	def get_rel_docs(self):
		return self.relDocsSet

	def get_search_term(self):
		return self.searchTerm

	def get_final_set(self):
		return self.clusterer.get_final_set()

	def get_rel_docs_from_gset(self, geneSet):
		rel_docs = []

		# download abstracts from pubmed in groups of 200
		APIAdapter.download_abstracts(self.get_search_term(), 200)

		# use the downloaded abstracts
		abstracts_folder_name = APIAdapter.get_abstracts_foldername(self.get_search_term())
		for file in os.listdir(abstracts_folder_name):
			rf = open(abstracts_folder_name+"/"+file, 'r')

			# sanitize content
			content = rf.read().replace('\n', ' ')
			content = content.replace('(', ' ')
			content = content.replace(')', ' ')
			content = content.replace('.', ' ')
			content = content.replace(',', ' ')
			content = ' '.join(content.split())
			content = content.lower()

			result, gene = self.flag_relevant(content)
			count = 0
			if result:
				count += 1
				print count
				print file + " " + gene
				rel_docs.append(int(file))
		return rel_docs

	# helper function
	def flag_relevant(self, content):
		for gene in self.geneSet:
			if gene+" " in content:
				return True, gene
		return False, None

	def mesh_exp_combn(self):
		# mesh exp from search term
		mesh_exp = APIAdapter.get_mesh_exp(self.searchTerm)

		terms = mesh_exp.split('OR')

		terms = [term.replace('(', '') for term in terms]
		terms = [term.replace(')', '') for term in terms]
		terms = [term.strip() for term in terms]
		terms = ['('+term+')' if 'AND' in term else term for term in terms]

		combs = []

		for i in range(1, len(terms)+1):
			tmp = [list(x) for x in itertools.combinations(terms,i)]
			combs.extend(tmp)

		mesh_exps = []
		for comb in combs:
			s = ""
			for x in range(0,len(comb)-1):
				s+="("
			count = 0
			for term in comb:
				if count == 0:
					s += term
				else:
					s += " OR " + term + ")"
				count += 1
			mesh_exps.append(s)

		print "Combns" + str(len(mesh_exps))
		return mesh_exps

	def cluster(self, kmeans, hyper):
		clus1 = Clusterer(self.get_rel_docs(), APIAdapter.get_data_foldername(self.get_search_term()), kmeans, hyper)
		clus1.cluster()
		self.clusterer = clus1
