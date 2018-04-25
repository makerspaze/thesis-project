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
	if request.form.get('kmeans'):
		sd1.cluster(True, request.form['hyper'])
	else:
		sd1.cluster(False, request.form['hyper'])
	# sd1.compile_data()
	session['final_set'] = sd1.get_final_set()
	return render_template('cluster_results.html')

if __name__ != '__main__':
    app.run()