import os
import json
from apiadapter import APIAdapter
from flask import Flask, session
from flask import request
from flask import render_template
from director import SearchDirector

# inp - search_term, rel_docs_pmid OR search_term, rel_genes

app = Flask(__name__)
app.secret_key = "super secret key"
sd1 = SearchDirector()

@app.route('/')
def main_page():
	return render_template('main_page.html')

@app.route('/search', methods=['POST'])
def search():
	gene_file = request.files['gene_dict']
	gene_file.save('gene_dict.txt')

	query = request.form['query']
	with open("gene_dict.txt") as f:
		genes = f.read().splitlines()

	# sd1 = SearchDirector("extracellular matrix OR breast cancer OR ecm remodeling", genes, True)
	sd1.setParams(query, genes, True)
	# sd1 = SearchDirector(query, genes, True)
	return render_template('search_dir.html')

@app.route('/cluster', methods=['POST'])
def cluster():
	# try the cache first
	if (request.form.get('use_cache') == "on") & os.path.exists('cache/' + sd1.get_search_term()):
		final_set = set(line.strip() for line in open('cache/' + sd1.get_search_term()))
		return render_template('cluster_results.html', final_set=final_set, num_pmids=len(final_set))

	if request.form.get('kmeans'):
		sd1.cluster(True, request.form['hyper'])
	else:
		sd1.cluster(False, request.form['hyper'])
	# sd1.compile_data()
	final_set = sd1.get_final_set()

	cache_file = open('cache/' + sd1.get_search_term(), 'w')
	for pmid in final_set:
		cache_file.write("%s\n" % pmid)

	return render_template('cluster_results.html', final_set=final_set, num_pmids=len(final_set))

@app.route('/tag_genes', methods=['POST', 'GET'])
def tag_genes():
	if not os.path.exists('genes_tagger/'+sd1.get_search_term()):
		APIAdapter.run_gene_tagger(sd1.get_search_term())

	tagged_genes = []
	for filename in os.listdir('genes_tagger/'+sd1.get_search_term()):
		tagged = open('genes_tagger/'+sd1.get_search_term()+'/'+filename, 'r')
		data = tagged.read()
		if data[:8] != "\"[Error]":
			print type(tagged_genes)
			print type(json.loads(json.loads(data)))
			tagged_genes = tagged_genes+json.loads(json.loads(data))


	return render_template('gene_tagger.html', tagged_genes=tagged_genes)

if __name__ != '__main__':
    app.run()