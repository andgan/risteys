from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify, send_from_directory
import os
from flask_cors import CORS, cross_origin
from werkzeug.contrib.cache import SimpleCache
import pandas as pd
import numpy as np

app = Flask(__name__)      
CORS(app)
app.config['COMPRESS_DEBUG'] = True


### READ DATA IN ####
otherinfo = 'data/otherinfo.csv'
incidence = 'data/incidence_prop_year.csv'
res_mod = 'data/RES_MOD.csv'
res_mod_after = 'data/RES_MOD_AFTER.csv'
com_comorb = 'data/common_comorb.csv'
mort_rate = 'data/mortality_rate.csv'
read_rate = 'data/readmission_rate.csv'
geoevents = 'data/geoevent.csv'
bins = 'data/bins.csv'
rfreport = 'data/rfreport.csv'
ukbmean = 'data/ukbb_means.csv'

otherinfoD = pd.io.parsers.read_csv(otherinfo, header=0)
com_comorbD = pd.io.parsers.read_csv(com_comorb, header=0)
mort_rateD = pd.io.parsers.read_csv(mort_rate, header=0)
read_rateD = pd.io.parsers.read_csv(read_rate, header=0)
incidenceD = pd.io.parsers.read_csv(incidence, header=0)
res_modD = pd.io.parsers.read_csv(res_mod, header=0)
res_mod_afterD = pd.io.parsers.read_csv(res_mod_after, header=0)
geoeventD = pd.io.parsers.read_csv(geoevents, header=0)
binsD = pd.io.parsers.read_csv(bins, header=0, dtype=float)
rfreportD = pd.io.parsers.read_csv(rfreport, header=0)
ukbmeanD = pd.io.parsers.read_csv(ukbmean, header=0, dtype={'bmi_male_mean'
:str,'bmi_female_mean':str,'sbp_male_mean':str,'sbp_female_mean':str,'smoke_male_mean':float,'smoke_female_mean':float})



#### IMPORT LABELS FOR ICD CODES ####

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


dict_map=get_map_codes("data/icd10cm_order_2016.txt")



#### DEFINE FUNCTIONS NEEDED FOR DATA PROCESSING #####


def process_otherinfo(code,otherinfoD=otherinfoD):
	otherinfoD2 = otherinfoD.query('code == "%s"' % code).drop(['code'], axis=1)
	if ((otherinfoD2['n_events_M']==0).any()):
		indsex="F"
	elif ((otherinfoD2['n_events_F']==0).any()):
		indsex="M"
	else:
		indsex="MF"
	return(otherinfoD2.to_dict(orient='records'),indsex)


def process_incidence(code,incidenceD=incidenceD):
	incidenceD2 = incidenceD.query('code == "%s"' % code).drop(['code'], axis=1)
	if (np.isnan(incidenceD2['incidence']).all()):
		incidenceD2=pd.DataFrame({'n_events' : [],'incidence' : [],'year' : []})
	incidenceD2['n_events']=pd.to_numeric(incidenceD2['n_events'])
	return(incidenceD2.sort_values(by='year').to_dict(orient='records'))


def process_com_comorb(code,com_comorbD=com_comorbD):
	com_comorbD2 = com_comorbD.query('code == "%s"' % code).drop(['code'], axis=1)
	return(com_comorbD2.to_dict(orient='records'))


def process_rfreport(code,rfreportD=rfreportD):
	rfreportD2 = rfreportD.query('code == "%s"' % code).drop(['code'], axis=1)
	return(rfreportD2.to_dict(orient='records'))


def round_and_return_str(x,digits=2):
	return(np.round(x,digits).values.astype('str')[0])


def process_mort_rate(code,mort_rateD=mort_rateD):
	mort_rateD2 = mort_rateD.query('code == "%s"' % code).drop(['code'], axis=1)
	if len(mort_rateD2['beta'])==0:
		mort_rateD2=pd.DataFrame({'RR' : []})
	return(mort_rateD2.to_dict(orient='records'))



#def process_ldscore(code,ldscoreD=ldscoreD):
#	ldscoreD2 = ldscoreD.query('code == "%s"' % code).drop(['code'], axis=1)
#	return(ldscoreD2.to_dict(orient='records'))


def process_read_rate(code,read_rateD=read_rateD):
	read_rateD2 = read_rateD.query('code == "%s"' % code).drop(['code'], axis=1)
	if len(read_rateD2['abs_40_M'])>0:
		total_events=process_otherinfo(code)[0][0]['n_events_TOT']
		read_rateD2['tot_prob_read'] = read_rateD2['nread']/total_events
		read_rateD2['readmitted_prop'] = str(int(read_rateD2['nread'])) + "/" + str(int(total_events)) + "=" + round_and_return_str((read_rateD2['tot_prob_read'])*100,0) + "%"
	else:
		read_rateD2=pd.DataFrame({'abs_40_M' : []})
	return(read_rateD2.to_dict(orient='records'))



def process_resmod(code,res_modD,dict_mapD=dict_map):
	res_modD2 = res_modD.query('code == "%s"' % code).drop(['code'], axis=1)
	res_modD2 = res_modD2[res_modD2['comorbidevent'].isin(dict_mapD.keys())]
	if len(res_modD2['time'])>0:
		res_modD2['label'] = return_comorbid_label(res_modD2,dict_map)
		res_modD2['indexkey'] = list(range(1,len(res_modD2.index)+1))
	return(res_modD2.to_dict(orient='records'))



def process_geoevent(code,geoeventD=geoeventD):
	geoeventD2 = geoeventD.query('code == "%s"' % code).drop(['code'], axis=1)
	return(geoeventD2.to_dict(orient='records'))




def bins_for_hist(binsD=binsD):
	binsD1=binsD[['bmi_male_bin_mids','bmi_male_bin_count']]
	binsD1.columns = ['mid','count']
	binsD2=binsD[['bmi_female_bin_mids','bmi_female_bin_count']]
	binsD2.columns = ['mid','count']
	binsD3=binsD[['sbp_male_bin_mids','sbp_male_bin_count']]
	binsD3.columns = ['mid','count']
	binsD4=binsD[['sbp_female_bin_mids','sbp_female_bin_count']]
	binsD4.columns = ['mid','count']
	return([binsD1.to_dict(orient='records'),binsD2.to_dict(orient='records'),binsD3.to_dict(orient='records'),binsD4.to_dict(orient='records')])

bins_for_histT=bins_for_hist(binsD)


def create_report_text(code,otherinfo,mort_rate,read_rate,res_mod,resmod_after,geoevent,indsex):

	prevtot=otherinfo[0]['prevalence_TOT']

	if prevtot < 0.1:
		prestr = "rarely (<0.1% prevalence) assigned,"
	elif prevtot > 5:
		prestr = "commonly (>5% prevalence) assigned,"
	else:
		prestr = "observed"

	if (indsex=="M"):
		sexstr="only in men"
	elif (indsex=="F"):
		sexstr="only in women"
	else:
		ratiosex = otherinfo[0]['n_events_M']/(otherinfo[0]['n_events_F']+otherinfo[0]['n_events_M'])

		if ratiosex > 0.6:
			sexstr = "predominenly in men"
		elif ratiosex < 0.4:
			sexstr =  "predominenly in women"
		else:
			sexstr =  "similarly in men and women"


	agestr ="with an average of " + str(int(otherinfo[0]['age_mean_TOT'])) + " years old."


	seq = max([x['prop_on_total'] for x in geoevent])
	commoncounty = [x['center'] for x in geoevent if x['prop_on_total']==seq]

	commoncountystr = "The diagnosis is more likely to be made in the area covered by the " + str(commoncounty[0]) + " assessment center."

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
		icdmax1=""
		for k in res_mod:
			if k['time'] == '8-999999999999'and k['pval'] < 0.00005:
				if k['RR'] > max_value:
					max_value = k['RR']
					icdmax1 = k['comorbidevent']
					labelmax = k['label']
		if icdmax1:
			resmodstr = icdmax1 + " (%s)" % labelmax

	resmodafterstr=""
	if len(resmod_after)>0:
		max_value = -100
		icdmax2=""
		for k in resmod_after:
			if k['time'] == '8-999999999999'and k['pval'] < 0.00005:
				if k['RR'] > max_value:
					max_value = k['RR']
					icdmax2 = k['comorbidevent']
					labelmax = k['label']
		if icdmax2:
			resmodafterstr = icdmax2 + " (%s)" % labelmax

	resmodout=""
	if resmodafterstr and resmodstr:
		if icdmax1==icdmax2:
			resmodout="Patients diagnosed with this code have frequently been diagnosed and are more likely to be diagnosed with %s." % resmodstr
		else:
			resmodout="Patients diagnosed with this code have frequently been diagnosed with %s and are more likely to be diagnosed with %s." % (resmodstr,resmodafterstr)
	elif resmodstr:
			resmodout="Patients diagnosed with this code have frequently been diagnosed with %s" % (resmodstr)
	elif resmodafterstr:
			resmodout="Patients diagnosed with this code are more likely to be diagnosed with %s." % (resmodafterstr)


	return_string = "The %s code is %s %s %s %s %s %s %s" % (code,prestr,sexstr,agestr,commoncountystr,mortstr,readstr,resmodout)

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
	
	otherinfoT,indsex = process_otherinfo(code)


	if len(otherinfoT) == 0:
		abort(405)

	incidenceT = process_incidence(code,incidenceD=incidenceD)
	resmodT = process_resmod(code,res_modD=res_modD)
	resmod_afterT = process_resmod(code,res_modD=res_mod_afterD)
	com_comorbT = process_com_comorb(code,com_comorbD=com_comorbD)
	mort_rateT = process_mort_rate(code,mort_rateD=mort_rateD)
	read_rateT = process_read_rate(code,read_rateD=read_rateD)
	geoeventT = process_geoevent(code,geoeventD=geoeventD)
	rfreportT = process_rfreport(code,rfreportD=rfreportD)
	report_outT = create_report_text(code,otherinfo=otherinfoT,mort_rate=mort_rateT,read_rate=read_rateT,res_mod=resmodT,resmod_after=resmod_afterT,geoevent=geoeventT,indsex=indsex)

	## Set empty variables
	n_events_M=0
	n_events_M_per=0
	n_afterbs_M=0
	n_afterbs_M_per=0
	prevalence_M=0
	meanage_M=0

	n_events_F=0
	n_events_F_per=0
	n_afterbs_F=0
	n_afterbs_F_per=0
	prevalence_F=0
	meanage_F=0

	n_events_TOT=int(otherinfoT[0]['n_events_TOT'])
	n_afterbs_TOT=int(otherinfoT[0]['n_afterbs_TOT'])
	prevalence_TOT=otherinfoT[0]['prevalence_TOT']
	meanage_TOT=int(otherinfoT[0]['age_mean_TOT'])

	
	# Report sex-specific information
	if (indsex=="F"):
		n_events_F=int(otherinfoT[0]['n_events_F'])
		n_events_F_per=int(np.round((int(otherinfoT[0]['n_events_F'])/int(otherinfoT[0]['n_events_TOT']))*100))
		n_afterbs_F=int(otherinfoT[0]['n_afterbs_F'])
		n_afterbs_F_per=int(np.round((int(otherinfoT[0]['n_afterbs_F'])/int(otherinfoT[0]['n_afterbs_TOT']))*100))
		prevalence_F=otherinfoT[0]['prevalence_F']
		meanage_F=int(otherinfoT[0]['age_mean_F'])
		

	elif(indsex=="M"):
		n_events_M=int(otherinfoT[0]['n_events_M'])
		n_events_M_per=int(np.round((int(otherinfoT[0]['n_events_M'])/int(otherinfoT[0]['n_events_TOT']))*100))
		n_afterbs_M=int(otherinfoT[0]['n_afterbs_M'])
		n_afterbs_M_per=int(np.round((int(otherinfoT[0]['n_afterbs_M'])/int(otherinfoT[0]['n_afterbs_TOT']))*100))
		prevalence_M=otherinfoT[0]['prevalence_M']
		meanage_M=int(otherinfoT[0]['age_mean_M'])

	elif(indsex=="MF"):

		n_events_F=int(otherinfoT[0]['n_events_F'])
		n_events_F_per=int(np.round((int(otherinfoT[0]['n_events_F'])/int(otherinfoT[0]['n_events_TOT']))*100))
		n_afterbs_F=int(otherinfoT[0]['n_afterbs_F'])
		n_afterbs_F_per=int(np.round((int(otherinfoT[0]['n_afterbs_F'])/int(otherinfoT[0]['n_afterbs_TOT']))*100))
		prevalence_F=otherinfoT[0]['prevalence_F']
		meanage_F=int(otherinfoT[0]['age_mean_F'])

		n_events_M=int(otherinfoT[0]['n_events_M'])
		n_events_M_per=int(np.round((int(otherinfoT[0]['n_events_M'])/int(otherinfoT[0]['n_events_TOT']))*100))
		n_afterbs_M=int(otherinfoT[0]['n_afterbs_M'])
		n_afterbs_M_per=int(np.round((int(otherinfoT[0]['n_afterbs_M'])/int(otherinfoT[0]['n_afterbs_TOT']))*100))
		prevalence_M=otherinfoT[0]['prevalence_M']
		meanage_M=int(otherinfoT[0]['age_mean_M'])
	

	return render_template("code.html", code=code, 
		n_events_M=n_events_M,n_events_F=n_events_F,n_events_TOT=n_events_TOT,
		n_events_M_per=n_events_M_per,n_events_F_per=n_events_F_per,

		n_afterbs_M=n_afterbs_M,n_afterbs_F=n_afterbs_F,n_afterbs_TOT=n_afterbs_TOT,

		n_afterbs_M_per=n_afterbs_M_per,n_afterbs_F_per=n_afterbs_F_per,

		prevalence_M=prevalence_M,prevalence_F=prevalence_F,prevalence_TOT=prevalence_TOT,
		meanage_M=meanage_M,meanage_F=meanage_F,meanage_TOT=meanage_TOT,

		incidence=incidenceT, res_mod=resmodT, res_mod_after=resmod_afterT, com_comorb=com_comorbT, mort_rate=mort_rateT, read_rate=read_rateT, label=label_icds, report_out=report_outT, geoevent=geoeventT, rfreport=rfreportT, histbin=bins_for_histT, indsex=indsex, ukbmeans=ukbmeanD.to_dict(orient='records'))




@app.route('/loaderio-322c202bf1bcde73594aff6fc692ca87.html')
def return_loader_token():
	return render_template('loaderio-322c202bf1bcde73594aff6fc692ca87.html')


@app.route('/methods')
def return_methods():
	return render_template('methods.html')


@app.route('/acknowledgements')
def return_acknowledgements():
	return render_template('acknowledgements.html')

	
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
  app.run(host='0.0.0.0', port=80)
  #app.run(debug=True)