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


app = Flask(__name__)      
CORS(app)
app.config['COMPRESS_DEBUG'] = True
cache = SimpleCache()


MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', 27017)
MONGO_URL = 'mongodb://%s:%s' % (MONGO_HOST, MONGO_PORT)



app.config.update(dict(
    DB_HOST='localhost',
    DB_PORT=27017,
    DB_NAME='risteys',
    DEBUG=True
))



def connect_db():
    """
    Connects to the specific database.
    """

    client = MongoClient(MONGO_URL)
    return client[app.config['DB_NAME']]

def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db_conn'):
        g.db_conn = connect_db()
    return g.db_conn




# db.individuals.drop()

# cur=db.individuals.find()

# for r in cur:
# 	print(r)


def validate_date(date):
    try:
        datev = datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")
    return datev

def load_codes_in_db(dict_value):
	#db = get_db()
	db.individuals.insert_one(dict_value)


def get_codes_from_file_in_db(file,dict_map):
	registry=open(file,"r")
	header=registry.readline().split("\t")
	id_num=header.index("eid")
	icd10_num=header.index("diag_icd10")
	date_num=header.index("epistart")
	first_line=registry.readline().split("\t")
	current_id=first_line[id_num]
	icd10_first=first_line[icd10_num][0:3]
	date_first=validate_date(first_line[date_num])
	dict={'code':[icd10_first],'date':[date_first]}
	for i,line in enumerate(registry):
		cols=line.split("\t")
		id=cols[id_num]
		icd10=cols[icd10_num][0:3]
		if not icd10 or not cols[date_num]:
			continue
		try:
			val=dict_map[icd10]
		except KeyError:
			continue
		if id == current_id:
			dict['code'].append(icd10)
			dict['date'].append(validate_date(cols[date_num]))
		else:
			entry={'id': current_id,'code': dict['code'], 'date': dict['date']}
			load_codes_in_db(entry)
			dict={'code':[],'date':[]}
			current_id = id
			dict['code'].append(icd10)
			dict['date'].append(validate_date(cols[date_num]))

#get_codes_from_file_in_db("/data/hesin_registry.tsv",dict_map)



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



def count_all_icd_codes(db):
	try:
		all_icd_codes
	except NameError:
		pipeline_all=[{"$project": {"code": "$code", 
		"_id": "$id"}}, 
		{"$unwind": "$code"}, 
		{"$group": {"_id": "$_id", 
		"code": {"$addToSet": "$code"}}},
		{"$unwind": "$code"}, 
		{"$group": {"_id": "$code", "count": {"$sum": 1}}}]
		return(list(db.individuals.aggregate(pipeline_all)))
	else:
		return(all_icd_codes)


####### FUNCTIONS TO CALCULATE THE RISK RATIO AND RELATED MEASURES #######



def count_individuals_with_code(db,icd_code):
	return(db.individuals.find({'code': icd_code}).count())


def count_individuals_without_code(db,icd_code):
	return(db.individuals.find({}).count())


def remove_first_occurance_matching_list(codes_to_process,list_to_exclude):
	codes_excludeT=list_to_exclude
	for e in codes_to_process:
		if e in codes_excludeT:
			codes_to_process.remove(e)
			codes_excludeT.remove(e)
	return(set(codes_to_process))


def select_individuals_with_code(db,icd_code):
	pipeline_code=[
		{"$project": { "code": "$code", "date": "$date"}},
		{"$match": {"code": icd_code}}]
	return(list(db.individuals.aggregate(pipeline_code)))


def count_comorbid_icd_codes(db,icd_code,distance_days=7):
	out=select_individuals_with_code(db,icd_code)
	all_codes=[]
	all_codes_before=[]
	all_codes_after=[]
	for individual in out:
		codes=[x for (y,x) in sorted(zip(individual['date'],individual['code']))]
		ind_code=codes.index(icd_code)
		dates=sorted(individual['date'])
		# Keep only at least a distance of 7 days
		codes_exclude=[codes[ind] for ind, a in enumerate(dates) if abs((dates[ind_code]-a).days) <= distance_days]
		code_before=codes[:ind_code]
		code_after=codes[(ind_code+1):]
		if len(code_before) > 0:
			proc_before=remove_first_occurance_matching_list(code_before,codes_exclude)
			all_codes_before.extend(proc_before)
		if len(code_after) > 0:
			proc_after=remove_first_occurance_matching_list(code_after,codes_exclude)
			all_codes_after.extend(proc_after)
		if len(codes) > 0:
			proc_all=remove_first_occurance_matching_list(codes,codes_exclude)
			all_codes.extend(proc_all)
	a1=dict(Counter(all_codes_before))
	a2=dict(Counter(all_codes_after))
	a3=dict(Counter(all_codes))
	return(a1,a2,a3)


def compute_risk_ratio(key,count_a,all_icd_codes,all_individuals_with_code,all_individuals):
	for element_all in all_icd_codes:
		if key==element_all['_id']:
			all_count_yes=element_all['count']
			all_count_no=all_individuals-all_count_yes
			count_b=all_count_yes-count_a
			count_c=all_individuals_with_code-count_a
			count_d=all_count_no-count_c
			se=math.sqrt(((count_b/count_a)/all_count_yes)+((count_d/count_c)/all_count_no))
			RR=(count_a/all_count_yes)/(count_c/all_count_no)
			z=(math.log(RR)/se)
			pval=2*stats.norm.cdf(-abs(z))
			return({'code':key,'RR':RR,'pval':pval,'perc_on_all':count_a/all_count_yes,'n_events':count_a})



def output_risk_ratio(db,icd_code,min_individuals_with_code=10):
	all_icd_codes=count_all_icd_codes(db)
	comorbid_codes_before, comorbid_codes_after, comorbid_codes_all =count_comorbid_icd_codes(db,icd_code)
	all_individuals_with_code=count_individuals_with_code(db,icd_code)
	all_individuals=db.individuals.count()
	list_RR_all=[]
	list_RR_before=[]
	list_RR_after=[]
	for key in comorbid_codes_all:
		try:
			count_a_before=comorbid_codes_before[key]
			if count_a_before > min_individuals_with_code:
				list_RR_before.append(compute_risk_ratio(key,count_a_before,all_icd_codes,all_individuals_with_code,all_individuals))
		except KeyError:
			continue
		try:
			count_a_after=comorbid_codes_after[key]
			if count_a_after > min_individuals_with_code:
				list_RR_after.append(compute_risk_ratio(key,count_a_after,all_icd_codes,all_individuals_with_code,all_individuals))
		except KeyError:
			continue
		try:
			count_a_all=comorbid_codes_all[key]
			if count_a_all > min_individuals_with_code:
				list_RR_all.append(compute_risk_ratio(key,count_a_all,all_icd_codes,all_individuals_with_code,all_individuals))
		except KeyError:
			continue
	toreturn={'before':list_RR_before,'after':list_RR_after,'all':list_RR_all}
	return(toreturn)



###### FUNCTION TO CALCULATE DATES ########

def return_date_by_code(db,icd_code):
	with_code=select_individuals_with_code(db, icd_code)
	dateout=[]
	for element in with_code:
		code_index=element['code'].index(icd_code)
		dateout.append((element['date'][code_index].year))
	counter_dates=dict(Counter(dateout))
	dict_dates=[{'year':k,'count':v} for k,v in counter_dates.items()]
	return(sorted(dict_dates, key=lambda k: k['year'],reverse=True))


def return_icd_label(icd_code):
	try:
		icd_label = dict_map[icd_code]['label']
	except KeyError:
		return None
	return icd_label


@app.route('/')
def home():
	db = get_db()
	number_all_indiv=db.individuals.count()
	return render_template('home.html', number_all_indiv=number_all_indiv)
 

@app.route('/awesome')
def awesome():
	code = request.args.get('query')
	code = code[0:3].upper()
	return redirect('/code/{}'.format(code))


@app.route('/code/<code>')
def individual_page(code,min_number_of_individuals_for_reporting=20):
	db = get_db()
	label_icds = return_icd_label(code)
	if label_icds is None:
		abort(404)
	number_icds = count_individuals_with_code(db, code)
	if number_icds < min_number_of_individuals_for_reporting:
		abort(405)
	else:
		prevalence=number_icds/db.individuals.count()
		#hist_comorb_before, hist_comorb_after, hist_comorb_all = output_risk_ratio(db,code)
		hist_comorb = output_risk_ratio(db,code)
		count_date=return_date_by_code(db,code)
	return render_template("code.html", code=code,number_id=number_icds, prevalence=prevalence, hist_comorb=hist_comorb, label=label_icds,count_date=count_date)



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