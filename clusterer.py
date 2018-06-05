import os
import json
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn import metrics
from sklearn.cluster import KMeans, MiniBatchKMeans
from time import time
from sklearn.cluster import DBSCAN
import random
import requests
import re

class Clusterer:
	def __init__(self, relDocsSet, dataFolder, kmeans, hyper):
		raw_data = []
		data_folder_name = dataFolder+"/"

		for filename in os.listdir(data_folder_name):
		    f = open(data_folder_name+filename, 'r')
		    json_object = json.load(f)
		    f.close()
		    raw_data.append(json_object)
		    
		print "Number of Cluster Points ------->"
		print len(raw_data)

		self.cluster_data = raw_data
		self.kmeans = kmeans
		self.related_docs = relDocsSet
		self.hyper = hyper

	def get_final_set(self):
		return self.final_set

	def cluster(self):
		data_abstract = [clusterpoint["abstracts"] for clusterpoint in self.cluster_data]
		data_query_label = [clusterpoint["query"] for clusterpoint in self.cluster_data]
		data_query_id = [clusterpoint["queryId"] for clusterpoint in self.cluster_data]

		# Perform an IDF normalization on the output of HashingVectorizer
		hasher = HashingVectorizer(n_features=10000, stop_words='english', norm=None, binary=False)
		vectorizer = make_pipeline(hasher, TfidfTransformer())
		X = vectorizer.fit_transform(data_abstract)
		print "n_samples: %d, n_features: %d" % X.shape

		# K-Means or DBSCAN
		if self.kmeans:
			num_clusters = int(self.hyper)
			km = KMeans(n_clusters=num_clusters, init='k-means++', max_iter=100, n_init=1, verbose=True)
			t0 = time()
			km.fit(X)
			print("done in %0.3fs" % (time() - t0))
			print()
		else:
			km = DBSCAN(eps=float(self.hyper), min_samples=10).fit(X)
			num_clusters = len(set(km.labels_))
			print len(set(km.labels_))

		cluster_labels = km.labels_
		query_clusters = []
		query_clusters_pmids = []

		for i in range(0,num_clusters):
		    temp = []
		    tempset = set()
		    query_clusters_pmids.append(tempset)
		    query_clusters.append(temp)
		    
		for i in range(0,len(cluster_labels)):
		    query_clusters[cluster_labels[i]].append(data_query_label[i])
		    pmids = self.cluster_data[i]["articleIds"].split(',')
		    for pmid in pmids:
		        query_clusters_pmids[cluster_labels[i]].add(pmid)
		    
		print "cluster_id\tnum_queries\tnum_pmids"
		print "-------------------------------------------------------------"
		for i in range(0,num_clusters):
		    print str(i) + "\t\t" + str(len(query_clusters[i])) + "\t\t" + str(len(query_clusters_pmids[i]))

		relevant_docs = []
		for rel_doc in self.related_docs:
			relevant_docs.append(unicode(rel_doc))

		random.shuffle(relevant_docs)

		# learning vs testing split

		training_cnt = int(0.8*len(relevant_docs))
		relevant_known = set(relevant_docs[:training_cnt])
		relevant_blind = set(relevant_docs[training_cnt:])

		cluster_score = [float(len(relevant_known.intersection(cluster_pmids)))/float(len(cluster_pmids)) for cluster_pmids in query_clusters_pmids]
		cluster_score_relative = [score/max(cluster_score) for score in cluster_score]
		# cluster_score_relative = cluster_score
		cluster_blind_intersect = [len(relevant_blind.intersection(cluster_pmids)) for cluster_pmids in query_clusters_pmids]

		print "Cluster ID\tRelevance Score\t\tBlind Intersect"
		for i in range(0,num_clusters):
		    print str(i) + "\t\t" + str(cluster_score_relative[i]) + "\t\t\t" + str(cluster_blind_intersect[i])

		final_corpus = set()
		for i in range(0,num_clusters):
		    if cluster_score_relative[i] > 0.5:
		        for pmid in query_clusters_pmids[i]:
		            final_corpus.add(pmid)
		            
		print "Final Corpus Size ------------> "
		print len(final_corpus)
		print "Fraction intersection with relevant documents ---------> "
		print float(len(final_corpus.intersection(set(relevant_blind))))/float(len(set(relevant_blind)))

		self.final_set = final_corpus