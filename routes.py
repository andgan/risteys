from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify, send_from_directory
from pymongo import *
import os
from flask_cors import CORS, cross_origin
from werkzeug.contrib.cache import SimpleCache
import datetime
import operator
from collections import Counter
import itertools
import math
import scipy.stats as stats
import pandas
import numpy

app = Flask(__name__)      
CORS(app)
app.config['COMPRESS_DEBUG'] = True
cache = SimpleCache()



### READ DATA IN ####
otherinfo = '/Users/andreaganna/flaskapp/app/data/otherinfo.csv'
incidence = '/Users/andreaganna/flaskapp/app/data/incidence_prop_year.csv'
res_mod = '/Users/andreaganna/flaskapp/app/data/RES_MOD.csv'



otherinfoD = pandas.io.parsers.read_csv(otherinfo, header=None,names=['code','n_events','prevalence'])
incidenceD = pandas.io.parsers.read_csv(incidence, header=None,names=['code','year','incidence'])
res_modD = pandas.io.parsers.read_csv(res_mod, header=None,names=['code','time','comorbidevent','RR','se','pval','count_a','count_b','count_c','count_d','ratio_comorb','ratio_nocomorb','irr'])


def process_otherinfo(code,otherinfoD=otherinfoD):
	otherinfoD2 = otherinfoD.query('code == "%s"' % code)[['n_events','prevalence']]
	otherinfoD2[['prevalence']] = numpy.round(otherinfoD2[['prevalence']]*100)
	return(otherinfoD2.to_dict(orient='records'))

def process_incidence(code,incidenceD=incidenceD):
	incidenceD2 = incidenceD.query('code == "%s"' % code)[['year','incidence']]
	incidenceD2[['incidence']] = incidenceD2[['incidence']]*100
	return(incidenceD2.sort_values(by='year').to_dict(orient='records'))

def process_resmod(code,res_modD=res_modD):
	res_modD2 = res_modD.query('code == "%s"' % code)[['code','time','comorbidevent','RR','se','pval','count_a','count_b','count_c','count_d','ratio_comorb','ratio_nocomorb','irr']]
	if len(res_modD2['time'])>0:
		res_modD2['yes_data'] = 'TRUE'
		res_modD2['label'] = return_comorbid_label(res_modD2,dict_map)
		res_modD2['RR'] = numpy.exp(res_modD2['RR'])
		res_modD2['ratio_comorb'] = numpy.round(res_modD2['ratio_comorb'],3)
		res_modD2['ratio_nocomorb'] = numpy.round(numpy.exp(res_modD2['ratio_nocomorb']),3)
		res_modD2['irr'] = numpy.round(res_modD2['irr'])
	else:
		res_modD2['yes_data'] = 'FALSE'
	return(res_modD2.to_dict(orient='records'))



def get_map_codes(file):
	dict={}
	map_file=open(file,"r")
	for i,line in enumerate(map_file):
		cols=line.strip("\n").split("\t")
		icd_code=cols[0]
		is_main_cat=cols[1]
		label=cols[2]
		len_code=len(icd_code)
		if len_code==3:
			dict[icd_code]={'label':label,'is_main_cat':is_main_cat}
	return dict


dict_map=get_map_codes("/data/icd10cm_order_2016.txt")



def return_icd_label(icd_code,dict_map):
	try:
		icd_label = dict_map[icd_code]['label']
	except KeyError:
		return None
	return icd_label


def return_comorbid_label(data,dict_map):
	label=[]
	for com_code in data['comorbidevent']:
		try:
			label.append(dict_map[com_code]['label'])
		except KeyError:
			label.append('label not found')
	return label



@app.route('/')
def home():
	number_all_indiv='498,828'
	return render_template('home.html', number_all_indiv=number_all_indiv)
 

@app.route('/awesome')
def awesome():
	code = request.args.get('query')
	code = code[0:3].upper()
	return redirect('/code/{}'.format(code))


@app.route('/code/<code>')
def individual_page(code,dict_map=dict_map,min_number_of_individuals_for_reporting=20):
	label_icds = return_icd_label(code,dict_map)
	if label_icds is None:
		abort(404)
	
	otherinfoT = process_otherinfo(code)

	if len(otherinfoT) == 0:
		abort(405)

	incidenceT = process_incidence(code)
	resmodT = process_resmod(code)

	return render_template("code.html", code=code, n_events=int(otherinfoT[0]['n_events']), prevalence=otherinfoT[0]['prevalence'], incidence=incidenceT, res_mod=resmodT, label=label_icds)




@app.route('/not_found/<code>')
@app.errorhandler(404)
def not_found_page(code):
	return render_template(
	'not_found.html',
	code=code
	)

@app.route('/too_few/<code>')
@app.errorhandler(405)
def too_few_ind(code):
	return render_template(
	'too_few.html',
	code=code
	)



if __name__ == '__main__':
  app.run(debug=True)