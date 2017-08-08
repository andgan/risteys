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
import pandas as pd
import numpy as np

app = Flask(__name__)      
CORS(app)
app.config['COMPRESS_DEBUG'] = True


### READ DATA IN ####
otherinfo = '/Users/andreaganna/flaskapp/app/data/otherinfo.csv'
incidence = '/Users/andreaganna/flaskapp/app/data/incidence_prop_year.csv'
res_mod = '/Users/andreaganna/flaskapp/app/data/RES_MOD.csv'
res_mod_after = '/Users/andreaganna/flaskapp/app/data/RES_MOD_AFTER.csv'
com_comorb = '/Users/andreaganna/flaskapp/app/data/common_comorb.csv'
mort_rate = '/Users/andreaganna/flaskapp/app/data/mortality_rate.csv'
read_rate = '/Users/andreaganna/flaskapp/app/data/readmission_rate.csv'



otherinfoD = pd.io.parsers.read_csv(otherinfo, header=None,names=['code','n_events_M','n_events_F','n_afterbs_M','n_afterbs_F','prevalence_M','prevalence_F','prevalence_TOT','age_mean_M','age_mean_F','age_mean_TOT','age_median_M','age_median_F','age_median_TOT'])
com_comorbD = pd.io.parsers.read_csv(com_comorb, header=None,names=['code','sex','comorbidevent','perc','N'])
mort_rateD = pd.io.parsers.read_csv(mort_rate, header=None,names=['code','beta','se','pval','abs_40_M','abs_40_F','abs_50_M','abs_50_F','abs_60_M','abs_60_F','abs_40_MD','abs_40_FD','abs_50_MD','abs_50_FD','abs_60_MD','abs_60_FD','abs_40_MU','abs_40_FU','abs_50_MU','abs_50_FU','abs_60_MU','abs_60_FU'])
read_rateD = pd.io.parsers.read_csv(read_rate, header=None,names=['code','nread','ndrugad','abs_40_M','abs_40_F','abs_50_M','abs_50_F','abs_60_M','abs_60_F','abs_40_MU','abs_40_FU','abs_50_MU','abs_50_FU','abs_60_MU','abs_60_FU','abs_40_MD','abs_40_FD','abs_50_MD','abs_50_FD','abs_60_MD','abs_60_FD'])

incidenceD = pd.io.parsers.read_csv(incidence, header=None,names=['code','year','incidence'])
res_modD = pd.io.parsers.read_csv(res_mod, header=None,names=['code','time','comorbidevent','beta','se','pval','count_a','count_b','count_c','count_d','mean_dist','median_dist','ratio_comorb','ratio_nocomorb','irr'])
res_mod_afterD = pd.io.parsers.read_csv(res_mod_after, header=None,names=['code','time','comorbidevent','beta','se','pval','count_a','count_b','count_c','count_d','mean_dist','median_dist','ratio_comorb','ratio_nocomorb','irr'])


def process_otherinfo(code,otherinfoD=otherinfoD):
	otherinfoD2 = otherinfoD.query('code == "%s"' % code).drop(['code'], axis=1)
	if len(otherinfoD2) > 0:
		otherinfoD2['n_events_TOT'] = otherinfoD['n_events_M'] + otherinfoD['n_events_F']
		otherinfoD2['n_afterbs_TOT'] = otherinfoD['n_afterbs_M'] + otherinfoD['n_afterbs_F']
		otherinfoD2[['prevalence_M']] = np.round(otherinfoD2[['prevalence_M']]*100, decimals=2)
		otherinfoD2[['prevalence_F']] = np.round(otherinfoD2[['prevalence_F']]*100, decimals=2)
		otherinfoD2[['prevalence_TOT']] = np.round(otherinfoD2[['prevalence_TOT']]*100, decimals=2)
	return(otherinfoD2.to_dict(orient='records'))

def process_incidence(code,incidenceD=incidenceD):
	incidenceD2 = incidenceD.query('code == "%s"' % code)[['year','incidence']]
	incidenceD2[['incidence']] = incidenceD2[['incidence']]*100
	return(incidenceD2.sort_values(by='year').to_dict(orient='records'))


def process_com_comorb(code,com_comorbD=com_comorbD):
	com_comorbD2 = com_comorbD.query('code == "%s"' % code).drop(['code'], axis=1)
	com_comorbD2 = com_comorbD2.dropna()
	com_comorbD2 = com_comorbD2.groupby('sex').head(3)
	com_comorbL = []
	temploop = {}
	for sex in ['male','female','all']:
		if len(com_comorbD2.loc[com_comorbD2['sex']==sex]) > 0:
			tt=com_comorbD2.loc[com_comorbD2['sex']==sex]
			temploop['sex'] = sex
			joinval=[]
			for i in range(len(tt)):
				 joinval.append(str(tt.iloc[i,1]) + " (" + str(np.round(tt.iloc[i,2]*100,1)) + "% - " + str(int(tt.iloc[i,3])) + ")")
			temploop['value'] = [' '.join(joinval)]
		else:
			temploop['sex'] = sex
			temploop['value'] = 'Too small numbers'
		com_comorbL.append(temploop)
	return(com_comorbL)


def round_and_return_str(x,digits=2):
	return(np.round(x,digits).values.astype('str')[0])



def process_mort_rate(code,mort_rateD=mort_rateD):
	mort_rateD2 = mort_rateD.query('code == "%s"' % code).drop(['code'], axis=1)
	if len(mort_rateD2['beta'])>0:
		mort_rateD2['RR'] = round_and_return_str(np.exp(mort_rateD2['beta'])) + " [" + round_and_return_str(np.exp(mort_rateD2['beta'] - 1.96*mort_rateD2['se'])) + "-" + round_and_return_str(np.exp(mort_rateD2['beta'] + 1.96*mort_rateD2['se'])) + "]"
		mort_rateD2['pval'].replace(0,1e-16)
		mort_rateD2['abs_40_M'] = np.where(mort_rateD2['abs_40_M']*100 < 1, '<1%', round_and_return_str(mort_rateD2['abs_40_M']*100,1) + "% [" + round_and_return_str(mort_rateD2['abs_40_MD']*100,1) + "%-" + round_and_return_str(mort_rateD2['abs_40_MU']*100,1) +"%]")
		mort_rateD2['abs_40_F'] = np.where(mort_rateD2['abs_40_F']*100 < 1, '<1%', round_and_return_str(mort_rateD2['abs_40_F']*100,1) + "% [" + round_and_return_str(mort_rateD2['abs_40_FD']*100,1) + "%-" + round_and_return_str(mort_rateD2['abs_40_FU']*100,1) +"%]")
		mort_rateD2['abs_50_M'] = np.where(mort_rateD2['abs_50_M']*100 < 1, '<1%', round_and_return_str(mort_rateD2['abs_50_M']*100,1) + "% [" + round_and_return_str(mort_rateD2['abs_50_MD']*100,1) + "%-" + round_and_return_str(mort_rateD2['abs_50_MU']*100,1) +"%]")
		mort_rateD2['abs_50_F'] = np.where(mort_rateD2['abs_50_F']*100 < 1, '<1%', round_and_return_str(mort_rateD2['abs_50_F']*100,1) + "% [" + round_and_return_str(mort_rateD2['abs_50_FD']*100,1) + "%-" + round_and_return_str(mort_rateD2['abs_50_FU']*100,1) +"%]")
		mort_rateD2['abs_60_M'] = np.where(mort_rateD2['abs_60_M']*100 < 1, '<1%', round_and_return_str(mort_rateD2['abs_60_M']*100,1) + "% [" + round_and_return_str(mort_rateD2['abs_60_MD']*100,1) + "%-" + round_and_return_str(mort_rateD2['abs_60_MU']*100,1) +"%]")
		mort_rateD2['abs_60_F'] = np.where(mort_rateD2['abs_60_F']*100 < 1, '<1%', round_and_return_str(mort_rateD2['abs_60_F']*100,1) + "% [" + round_and_return_str(mort_rateD2['abs_60_FD']*100,1) + "%-" + round_and_return_str(mort_rateD2['abs_60_FU']*100,1) +"%]")
	else:
		mort_rateD2=pd.DataFrame({'RR' : []})
	return(mort_rateD2.to_dict(orient='records'))



def process_read_rate(code,read_rateD=read_rateD):
	read_rateD2 = read_rateD.query('code == "%s"' % code).drop(['code'], axis=1)
	if len(read_rateD2['abs_40_M'])>0:
		total_events=process_otherinfo(code)[0]['n_events_TOT']
		read_rateD2['tot_prob_read'] = read_rateD2['nread']/total_events
		read_rateD2['readmitted_prop'] = str(int(read_rateD2['nread'])) + "/" + str(int(total_events)) + "=" + round_and_return_str((read_rateD2['tot_prob_read'])*100,0) + "%"
		read_rateD2['abs_40_MD'][read_rateD2['abs_40_MD'] < 0] = 0
		read_rateD2['abs_40_FD'][read_rateD2['abs_40_FD'] < 0] = 0
		read_rateD2['abs_50_MD'][read_rateD2['abs_50_MD'] < 0] = 0
		read_rateD2['abs_50_FD'][read_rateD2['abs_50_FD'] < 0] = 0
		read_rateD2['abs_60_MD'][read_rateD2['abs_60_MD'] < 0] = 0
		read_rateD2['abs_60_FD'][read_rateD2['abs_60_FD'] < 0] = 0
		read_rateD2['abs_40_MU'][read_rateD2['abs_40_MU'] > 1] = 1
		read_rateD2['abs_40_FU'][read_rateD2['abs_40_FU'] > 1] = 1
		read_rateD2['abs_50_MU'][read_rateD2['abs_50_MU'] > 1] = 1
		read_rateD2['abs_50_FU'][read_rateD2['abs_50_FU'] > 1] = 1
		read_rateD2['abs_60_MU'][read_rateD2['abs_60_MU'] > 1] = 1
		read_rateD2['abs_60_FU'][read_rateD2['abs_60_FU'] > 1] = 1
		read_rateD2['abs_40_M'] = round_and_return_str(read_rateD2['abs_40_M']*100,1) + "% [" + round_and_return_str(read_rateD2['abs_40_MD']*100,1) + "%-" + round_and_return_str(read_rateD2['abs_40_MU']*100,1) +"%]"
		read_rateD2['abs_40_F'] = round_and_return_str(read_rateD2['abs_40_F']*100,1) + "% [" + round_and_return_str(read_rateD2['abs_40_FD']*100,1) + "%-" + round_and_return_str(read_rateD2['abs_40_FU']*100,1) +"%]"
		read_rateD2['abs_50_M'] = round_and_return_str(read_rateD2['abs_50_M']*100,1) + "% [" + round_and_return_str(read_rateD2['abs_50_MD']*100,1) + "%-" + round_and_return_str(read_rateD2['abs_50_MU']*100,1) +"%]"
		read_rateD2['abs_50_F'] = round_and_return_str(read_rateD2['abs_50_F']*100,1) + "% [" + round_and_return_str(read_rateD2['abs_50_FD']*100,1) + "%-" + round_and_return_str(read_rateD2['abs_50_FU']*100,1) +"%]"
		read_rateD2['abs_60_M'] = round_and_return_str(read_rateD2['abs_60_M']*100,1) + "% [" + round_and_return_str(read_rateD2['abs_60_MD']*100,1) + "%-" + round_and_return_str(read_rateD2['abs_60_MU']*100,1) +"%]"
		read_rateD2['abs_60_F'] = round_and_return_str(read_rateD2['abs_60_F']*100,1) + "% [" + round_and_return_str(read_rateD2['abs_60_FD']*100,1) + "%-" + round_and_return_str(read_rateD2['abs_60_FU']*100,1) +"%]"
	else:
		read_rateD2=pd.DataFrame({'abs_40_M' : []})
	return(read_rateD2.to_dict(orient='records'))



def process_resmod(code,res_modD):
	res_modD2 = res_modD.query('code == "%s"' % code).drop(['code'], axis=1)
	if len(res_modD2['time'])>0:
		res_modD2['label'] = return_comorbid_label(res_modD2,dict_map)
		res_modD2['RR'] = np.exp(res_modD2['beta'])
		res_modD2['ratio_comorb'] = np.round(res_modD2['ratio_comorb'],3)
		res_modD2['ratio_nocomorb'] = np.round(res_modD2['ratio_nocomorb'],3)
		res_modD2['irr'] = np.round(res_modD2['irr'])
		res_modD2['indexkey'] = list(range(1,len(res_modD2.index)+1))
		res_modD2['count_a_count_ab'] = res_modD2['count_a'].map(str) + "/" + (res_modD2['count_b']+res_modD2['count_a']).map(str)
		res_modD2['count_c_count_cd'] = res_modD2['count_c'].map(str) + "/" + (res_modD2['count_c']+res_modD2['count_d']).map(str)
		formatting_function = np.vectorize(lambda f: format(f, '6.2E'))
		res_modD2['signlabel'] = formatting_function(res_modD2['pval'])
		res_modD2['signlabel'][res_modD2['pval'] < 1e-10] = '<1.00E-10'
		res_modD2['signlabel'][res_modD2['pval'] > 0.05] = '>0.05'
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


dict_map=get_map_codes("/Users/andreaganna/flaskapp/app/data/icd10cm_order_2016.txt")



def create_report_text(code,otherinfo,mort_rate,read_rate,res_mod,resmod_after):

	prevtot=otherinfo[0]['prevalence_TOT']

	if prevtot < 0.1:
		prestr = "rarely (<0.1% prevalence) assigned,"
	elif prevtot > 5:
		prestr = "commonly (>5% prevalence) assigned,"
	else:
		prestr = "observed"


	ratiosex = otherinfo[0]['n_events_M']/(otherinfo[0]['n_events_F']+otherinfo[0]['n_events_M'])

	if ratiosex > 0.6:
		sexstr = "predominenly in men"
	elif ratiosex < 0.4:
		sexstr =  "predominenly in women"
	else:
		sexstr =  "similarly in men and women"


	agestr ="with an average of " + str(int(otherinfo[0]['age_mean_TOT'])) + " years old."

	mortstr=""
	if len(mort_rate) > 0:
		if np.exp(mort_rate[0]['beta']) > 5:
			mortstr="High 5-year mortality risk is observed."


	readstr=""
	if len(read_rate) > 0:
			readstr="The probability to experience an in-patient readmission within 30-days is " + str(np.round(read_rate[0]['tot_prob_read']*100,0)) + "%"


	resmodstr=""
	if len(res_mod)>0:
		max_value = -100
		for k in res_mod:
			if k['time'] == '8-999999999999'and k['pval'] < 0.00005:
				if k['RR'] > max_value:
					max_value = k['RR']
					icdmax1 = k['comorbidevent']
					labelmax = k['label']
		resmodstr = icdmax1 + " (%s)" % labelmax

	resmodafterstr=""
	if len(resmod_after)>0:
		max_value = -100
		for k in resmod_after:
			if k['time'] == '8-999999999999'and k['pval'] < 0.00005:
				if k['RR'] > max_value:
					max_value = k['RR']
					icdmax2 = k['comorbidevent']
					labelmax = k['label']
		resmodafterstr = icdmax2 + " (%s)" % labelmax

	resmodout=""
	if resmodafterstr and resmodstr:
		if icdmax1==icdmax2:
			resmodout="Patients diagnosed with this code have frequently been diagnosed and are more likely to be diagnosed with %s." % resmodstr
		else:
			resmodout="Patients diagnosed with this code have frequently been diagnosed with %s and are more likely to be diagnosed with %s." % (resmodstr,resmodafterstr)
	elif resmodstr:
			resmodout="Patients diagnosed with this code have frequently been diagnosed with %s"
	elif resmodafterstr:
			resmodout="Patients diagnosed with this code are more likely to be diagnosed with %s."


	return_string = "The %s code is %s %s %s The diagnosis is expecially common in Helsinki county. %s %s %s" % (code,prestr,sexstr,agestr,mortstr,readstr,resmodout)

	return(return_string)





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
	resmodT = process_resmod(code,res_modD=res_modD)
	resmod_afterT = process_resmod(code,res_modD=res_mod_afterD)
	com_comorbT = process_com_comorb(code,com_comorbD=com_comorbD)
	mort_rateT = process_mort_rate(code,mort_rateD=mort_rateD)
	read_rateT = process_read_rate(code,read_rateD=read_rateD)

	report_outT = create_report_text(code,otherinfoT,mort_rateT,read_rateT,resmodT,resmod_afterT)


	return render_template("code.html", code=code, 
		n_events_M=int(otherinfoT[0]['n_events_M']),n_events_F=int(otherinfoT[0]['n_events_F']),n_events_TOT=int(otherinfoT[0]['n_events_TOT']),
		n_events_M_per=int(np.round((int(otherinfoT[0]['n_events_M'])/int(otherinfoT[0]['n_events_TOT']))*100)),n_events_F_per=int(np.round((int(otherinfoT[0]['n_events_F'])/int(otherinfoT[0]['n_events_TOT']))*100)),

		n_afterbs_M=int(otherinfoT[0]['n_afterbs_M']),n_afterbs_F=int(otherinfoT[0]['n_afterbs_F']),n_afterbs_TOT=int(otherinfoT[0]['n_afterbs_TOT']),

		n_afterbs_M_per=int(np.round((int(otherinfoT[0]['n_afterbs_M'])/int(otherinfoT[0]['n_afterbs_TOT']))*100)),n_afterbs_F_per=int(np.round((int(otherinfoT[0]['n_afterbs_F'])/int(otherinfoT[0]['n_afterbs_TOT']))*100)),

		prevalence_M=otherinfoT[0]['prevalence_M'],prevalence_F=otherinfoT[0]['prevalence_F'],prevalence_TOT=otherinfoT[0]['prevalence_TOT'],
		meanage_M=int(otherinfoT[0]['age_mean_M']),meanage_F=int(otherinfoT[0]['age_mean_F']),meanage_TOT=int(otherinfoT[0]['age_mean_TOT']),

		incidence=incidenceT, res_mod=resmodT, res_mod_after=resmod_afterT, com_comorb=com_comorbT, mort_rate=mort_rateT, read_rate=read_rateT, label=label_icds, report_out=report_outT)




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