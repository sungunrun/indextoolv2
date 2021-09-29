from flask import Flask, render_template, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
import json
import re
import sys
# import psycopg2 as psycopg2
#fullrange = [* range(26-23,129-23)] + [* range(132-23,387-23)] + [* range(390-23,504-23)] + [* range(506-23,772-23)]


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://wak:7LZBAUBS09EWun82UdLAS8TXvOsLzVDR@oregon-postgres.render.com/oupindexdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


html_list = []
for i in [* range(3,772-23)]:
    with open('static/page_contents/page_'+str(i)+'.html','r') as fp:
        page_indicator = '<br><br><span style="color:red">Page '+str(i)+'</span><br><br>'
        page = page_indicator + fp.read()
        html_list.append(page)

class Entries(db.Model):
    __tablename__ = 'test2'
    id = db.Column(db.Integer, primary_key=True)
    entry_name = db.Column(db.String)
    see = db.Column(db.String)
    seealso = db.Column(db.String)
    stokens = db.Column(db.String)
    retokens = db.Column(db.String)
    pages_all = db.Column(db.String)
    highlights = db.Column(db.String)
    pages_lists = db.Column(db.String)
    pages_ranges = db.Column(db.String)
    removals = db.Column(db.String)
    emphasized_pages = db.Column(db.String)
    emphasized_subranges = db.Column(db.String)
    range_dict = db.Column(JSON)


@app.route('/')
def index():
    entries = Entries.query.order_by(Entries.id).all()
    return render_template('entry_list.html', entries=entries)

@app.route('/render/<page_number_current>')
def render_page(page_number_current):
    twoargs = re.split(',', page_number_current, 1)
    page_number = twoargs[0].split('-')
    entrynow = twoargs[1]
    curr_entry = Entries.query.get_or_404(int(entrynow))
    text = ''
    
    if len(page_number)==1:
        text=html_list[int(page_number[0])-3]
    if len(page_number)==2:
        first = int(page_number[0])-3
        last = int(page_number[1])-3
        for page in [* range(first, last+1)]:
            text = text + html_list[page]
    highlights = text

    stokensstring = curr_entry.stokens
    if stokensstring != '':
        stokens = stokensstring.split(',')
        for stoken in stokens:
            if stoken=='':
                continue
            print("NEW LOOP", file=sys.stderr)

            repl = '( |\n|—|\.|\,)'
            searchterm = re.sub('(_)', repl, stoken)
            print(searchterm, file=sys.stderr)
            finds = re.finditer(searchterm, highlights, flags=re.IGNORECASE)
            matchset = set()
            for find in finds:
                matchset.add(find.group())
            print(matchset, file=sys.stderr)
            if len(matchset) > 0:
                for match in matchset:
                    if '\n' in match:
                        replacement = ''
                        for component in match.split('\n'):
                            if component=='':
                                replacement = replacement+'\n'
                            else:
                                replacement = replacement + "<span style=\"background-color:yellow\">"+component+"</span>"
                    else:
                        replacement = "<span style=\"background-color:yellow\">"+match+"</span>"
                    print(repr(replacement), file=sys.stderr)
                    highlights = re.sub(re.escape(match), replacement, highlights, flags=re.IGNORECASE)
    
    retokensstring = curr_entry.highlights
    if retokensstring != '':
        retokens = retokensstring.split('|')
        for retoken in retokens:
            replacement2 = "<span style=\"background-color:aqua\">"+retoken+"</span>"
            highlights = re.sub(re.escape(retoken), replacement2, highlights)
    return highlights
    #return send_from_directory('static/page_contents', 'plaintext' + page_number + '.html')

@app.route('/remove/<int:id>', methods=['POST','GET'])
def remove(id):
    current_entry = Entries.query.get_or_404(id)
    if request.method == 'POST':
        x = request.form['content']
        if not current_entry.removals:
            current_entry.removals = x+','
        else:
            current_entry.removals = current_entry.removals + x + ','
        db.session.commit()
        return redirect('/')

@app.route('/emphasize/<int:id>', methods=['POST','GET'])
def emphasize(id):
    current_entry = Entries.query.get_or_404(id)
    if request.method == 'POST':
        x = request.form['content']
        if not current_entry.emphasized_pages:
            current_entry.emphasized_pages = x+','
        else:
            current_entry.emphasized_pages = current_entry.emphasized_pages + x + ','
        db.session.commit()
        return redirect('/')

@app.route('/getheight/<height_string>', methods=['POST','GET'])
def getheight(height_string):
    height = int(height_string[:-2])
    print(height_string, file=sys.stderr)
    print("Hello", file=sys.stderr)
    if height < 100:
        return "small"
    elif height > 100:
        return "large"

@app.route('/rangeremove/<removal_info>', methods=['POST','GET'])
def rangeremove(removal_info):
    rmvargs = removal_info.split(':')[1]
    rmvargs = rmvargs.split('_')
    rmv_id = int(rmvargs[0])
    rmv_pg = rmvargs[1]
    rmv_hit = rmvargs[2]
    entry = Entries.query.get_or_404(rmv_id)
    if type(entry.range_dict)!=type({"a":"b"}):
        entryDict = json.loads(entry.range_dict)
    else:
        entryDict = entry.range_dict
    entryDict[rmv_pg]['removals'].append(rmv_hit)
    if entryDict[rmv_pg]['isEdited']!='1':
        entryDict[rmv_pg]['isEdited']='1'
    entry.range_dict = json.dumps(entryDict)
    db.session.commit()
    return rmv_hit

@app.route('/emph_subrange/<emph_info>', methods=['POST','GET'])
def emph_subrange(emph_info):
    if request.method == 'POST':
        emphargs = emph_info.split('&')
        print(emphargs, file=sys.stderr)
        pagearg = emphargs[0].split('=')[1]
        first = emphargs[1].split('=')[1]
        second = emphargs[2].split('=')[1]
        print(first)
        emphid = int(emphargs[3])
        current_entry = Entries.query.get_or_404(emphid)
        if current_entry.emphasized_subranges == '':
            current_entry.emphasized_subranges = current_entry.emphasized_subranges  + first+'-'+second + ','
        else:
            current_entry.emphasized_subranges = current_entry.emphasized_subranges + ',' + first+'-'+second
        if type(current_entry.range_dict)!=type({"a":"b"}):
            entryDict = json.loads(current_entry.range_dict)
        else:
            entryDict = current_entry.range_dict
        newEmphSRs = entryDict[pagearg]['emph_sr_strings']+','+first+'-'+second 
        entryDict[pagearg]['emph_sr_strings'] = newEmphSRs
        if entryDict[pagearg]['isEdited']!='1':
            entryDict[pagearg]['isEdited']='1'
        current_entry.range_dict = json.dumps(entryDict)
        db.session.commit()
        return newEmphSRs

@app.route('/indiv_entry/<int:id>', methods=['POST', 'GET'])
def indiv_entry(id):
    current_entry = Entries.query.get_or_404(id)
    stokens = current_entry.stokens
    stokens = stokens.split(',')
    stokens = [token for token in stokens if token!='']
    retokens = current_entry.retokens
    retokens=retokens.split(',')
    retokens = [token for token in retokens if token!='']
    tokens = stokens + retokens
    if current_entry.range_dict:
        if type(current_entry.range_dict)!=type({"a":"b"}):
            entryDict = json.loads(current_entry.range_dict)
        else:
            entryDict = current_entry.range_dict
        subrangeDict = entryDict
    else:
        subrangeDict = {}


    if not current_entry.removals:
        removals=[]
    else:
        removals=current_entry.removals.split(',')
    if not current_entry.emphasized_pages:
        emphases = []
    else:
        emphases = current_entry.emphasized_pages.split(',')

    return render_template('entry_page.html', subrangeDict=subrangeDict, tokens=tokens, current_entry=current_entry, emphases=emphases, removals=removals)


if __name__ == "__main__":
    app.run(debug=True)