from flask import Flask, render_template, request, redirect, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON, ARRAY
import json
import re
import sys
# import psycopg2 as psycopg2
#fullrange = [* range(26-23,129-23)] + [* range(132-23,387-23)] + [* range(390-23,504-23)] + [* range(506-23,772-23)]

pgbkrange = [* range(1, 750)]
def getRanges( x ):
    hits = x
    ranges1 = []
    temp = []
    state = 'DEFAULT'
    for i in pgbkrange:
        if i in hits and state=='DEFAULT':
            temp.append(i)
            gap = 0
            state = 'BLOCK'
            continue
        if i in hits and state=='BLOCK':
            temp.append(i)
            gap=0
            continue
        if (i not in hits) and (state=='BLOCK') and gap==0:
            gap=1
            continue
        if (i in hits) and (state=='BLOCK') and gap==1:
            temp.append(i)
            gap = 0
            continue
        if (i not in hits) and (state=='BLOCK') and gap==1:
            ranges1.append(temp)
            state = 'DEFAULT'
            gap = 0
            temp = []
    return ranges1

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

class Adds(db.Model):
    __tablename__ = 'addtestbill'
    id = db.Column(db.Integer, primary_key=True)
    entry_name = db.Column(db.String)
    see = db.Column(db.String)
    seealso = db.Column(db.String)
    pages = db.Column(db.String)

class Entries(db.Model):
    __tablename__ = 'test4'
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
    entry_name_final = db.Column(db.String)
    see_final = db.Column(db.String)
    seealso_final = db.Column(db.String)
    base_all_hits = db.Column(ARRAY(db.Integer))
    hits_with_removals = db.Column(ARRAY(db.Integer))
    base_emphs = db.Column(ARRAY(db.Integer))
    base_emphs_json = db.Column(JSON)
    all_emphs = db.Column(ARRAY(db.Integer))
    to_delete = db.Column(db.Integer)
    added_pages = db.Column(ARRAY(db.Integer))
    added_emphs = db.Column(ARRAY(db.Integer))
    curr_ranges = db.Column(JSON)
    pages_final_pt = db.Column(db.String)
    pages_final_html = db.Column(db.String)

    is_renamed = db.Column(db.Integer)
    is_seechanged = db.Column(db.Integer)
    is_seealsochanged = db.Column(db.Integer)
    is_pageadded = db.Column(db.Integer)

    new_hits_with_removals = db.Column(ARRAY(db.Integer))
    new_emphs_json = db.Column(JSON)
    pages_new_pt = db.Column(db.String)
    pages_new_html = db.Column(db.String)



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

#REMOVE INDIVIDUAL PAGES
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

#EMPHASIZE INDIVIDUAL PAGES
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

#GET PAGE HEIGHT
@app.route('/getheight/<height_string>', methods=['POST','GET'])
def getheight(height_string):
    height = int(height_string[:-2])
    print(height_string, file=sys.stderr)
    print("Hello", file=sys.stderr)
    if height < 100:
        return "small"
    elif height > 100:
        return "large"

#REMOVE PAGE FROM RANGE
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

#EMPH SUBRANGE
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
        if not current_entry.emphasized_subranges:
            current_entry.emphasized_subranges = ''
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

#DELETE ENTRY
@app.route('/delete_entry/<int:id>', methods=['POST','GET'])
def delete_entry(id):
    current_entry = Entries.query.get_or_404(id)
    print("Hello")
    current_entry.to_delete = 1
    db.session.commit()
    return "Okay"

#REINSTATE ENTRY
@app.route('/reinstate_entry/<int:id>', methods=['POST','GET'])
def reinstate_entry(id):
    current_entry = Entries.query.get_or_404(id)
    print("Hello")
    current_entry.to_delete = 0
    db.session.commit()
    return "Okay"

#RENAME ENTRY
@app.route('/rename_entry/<rename_info>', methods=['POST', 'GET'])
def rename_entry(rename_info):
    args = rename_info.split('&')
    cEntry = Entries.query.get_or_404(int(args[0]))
    cEntry.entry_name_final = args[1]
    cEntry.is_renamed = 1
    db.session.commit()
    return args[1]

#RESET ENTRY NAME
@app.route('/reset_entry_name/<int:id>', methods=['POST', 'GET'])
def reset_entry_name(id):
    cEntry = Entries.query.get_or_404(id)
    cEntry.entry_name_final = cEntry.entry_name
    cEntry.is_renamed = 0
    db.session.commit()
    return cEntry.entry_name

#UPDATE SEE ALSO
@app.route('/update_see_also/<seealsoinfo>', methods=['POST','GET'])
def update_see_also(seealsoinfo):
    args = seealsoinfo.split('&&')
    cEntry = Entries.query.get_or_404(int(args[1]))
    updatedSA = args[0]
    cEntry.seealso_final = updatedSA
    cEntry.is_seealsochanged = 1
    db.session.commit()
    return updatedSA

#UPDATE SEE
@app.route('/update_see/<seeinfo>', methods=['POST','GET'])
def update_see(seeinfo):
    args = seeinfo.split('&&')
    cEntry = Entries.query.get_or_404(int(args[1]))
    updatedS = args[0]
    cEntry.see_final = updatedS
    cEntry.is_seechanged = 1
    db.session.commit()
    return updatedS

#RESET SEE
@app.route('/reset_see/<int:id>', methods=['POST','GET'])
def reset_see(id):
    cEntry = Entries.query.get_or_404(id)
    oldsee = cEntry.see
    print(oldsee,file=sys.stderr)
    cEntry.see_final = oldsee
    cEntry.is_seechanged = 0
    db.session.commit()
    return oldsee

#RESET SEE ALSO
@app.route('/reset_see_also/<int:id>', methods=['POST','GET'])
def reset_see_also(id):
    cEntry = Entries.query.get_or_404(id)
    oldseealso = cEntry.seealso
    print(oldseealso,file=sys.stderr)
    cEntry.seealso_final = oldseealso
    cEntry.is_seealsochanged = 0
    db.session.commit()
    return oldseealso

#ADD PAGES
@app.route('/add_pages/<pageinfo>', methods=['POST','GET'])
def add_pages(pageinfo):
    args = pageinfo.split('&&')
    cEntry = Entries.query.get_or_404(int(args[1]))
    emphasized_pages = cEntry.emphasized_pages.split(',')
    emphasized_pages_ranges = []
    for elem in emphasized_pages:
        if elem == '':
            continue
        if '-' in elem:
            hyphensplit = elem.split('-')
            first = int(hyphensplit[0])
            second = int(hyphensplit[1])+1
            emphasized_pages_ranges.append([* range(first,second) ] )
        else:
            emphasized_pages_ranges.append([int(elem)])
    additions = args[0].split(',')
    additions2 = []
    for elem in additions:
        if elem == '' or elem == '\n':
            continue
        else:
            additions2.append(elem.strip())
    for elem in additions2:
        if re.search('[^0-9\-\*\_\(\)\; ]', elem):
            return "Error1"
        if elem.count('*')%2!=0:
            return "Error4"
        if elem.count('(') != elem.count(')'):
            return "Error3"
        if '-' in elem:
            elemsplit = elem.split('-')
            if elemsplit[0]=='' or elemsplit[1]=='':
                return "Error2"
    added_pages = []
    added_emphs = []
    for elem in additions2:
        if '-' in elem:
            if '(' in elem:
                pgrange = elem.split('(')[0].strip()
                pglower = int(pgrange.split('-')[0])
                pgupper = int(pgrange.split('-')[1])+1
                added_pages.extend([* range(pglower,pgupper) ])
                emphstr = elem.split('(')[1][:-1]
                for emphelem in emphstr.split(';'):
                    cleaned = re.sub('\*','',emphelem)
                    if '-' in cleaned:
                        cleanlower = int(cleaned.split('-')[0])
                        cleanupper = int(cleaned.split('-')[1])+1
                        added_emphs.append([*range(cleanlower,cleanupper)])
                    else:
                        added_emphs.append([int(cleaned)])
            else:
                pgrange = re.sub('\*','',elem.strip())
                pglower = int(pgrange.split('-')[0])
                pgupper = int(pgrange.split('-')[1])+1
                added_pages.extend([* range(pglower,pgupper) ])
                if '*' in elem:
                    emphrange = re.sub('\*','',elem.strip())
                    emphlower = int(emphrange.split('-')[0])
                    emphupper = int(emphrange.split('-')[1])+1
                    added_emphs.append([* range(emphlower,emphupper) ])
        else:
            added_pages.append(int(re.sub('\*','',elem.strip())))
            if '*' in elem:
                added_emphs.append([int(re.sub('\*','',elem.strip()))])
    hitsWithRemovals = cEntry.new_hits_with_removals
    hitsWithAdditions = sorted(list(set(hitsWithRemovals).union(set(added_pages))))
    newRanges = getRanges(hitsWithAdditions)
    baseEmphs = cEntry.base_emphs
    baseEmphsJSON = cEntry.new_emphs_json
    newEmphs = []
    newEmphs.extend(baseEmphsJSON)
    newEmphs.extend(emphasized_pages_ranges)
    newEmphs.extend(added_emphs)
    # tempEmphs = []
    # for i in [* range(0,len(newEmphs))]:
    #     if i == len(newEmphs)-1:
    #         tempEmphs.append(sorted(newEmphs, key= lambda it: it[-1])[i])
    #         continue
    #     currlist = sorted(sorted(newEmphs, key= lambda it: it[-1])[i])
    #     nextlist = sorted(sorted(newEmphs, key= lambda it: it[-1])[i+1])
    #     if currlist[-1]+1 == nextlist[0]:
    #         tempEmphs.append(currlist.extend(nextlist))
    #     else:
    #         tempEmphs.append(currlist)
    # print(newEmphs)
    # print(tempEmphs)
    # baseEmphs grabs ONLY from emphasized_pages, which reflects non-subrange-tool emphases
    # baseEmphsJSON is list of lists. Each sub-list corresponds to an emphasized subrange
    # from the subrange tools (pulled from the JSON)

    pt_string = ''
    html_string=''
    for elem in newRanges:
        if len(elem)==1:
            inJSONsr = 0
            for json_sr in newEmphs:
                if elem == json_sr:
                    inJSONsr = 1
                    continue
            if inJSONsr:
                pt_string = pt_string + '*'+str(elem[0])+'*, '
                html_string = html_string + '<i>'+str(elem[0])+'</i>, '
            else:
                pt_string = pt_string + str(elem[0])+', '
                html_string = html_string + str(elem[0])+', '
        else:
            inJSONsr = 0
            #MIGHT BE TROUBLE HERE. hits with removals has noncontinunous ranges. curr_range also has holes, and the json-based ranges also do. So == should work here.
            printed_subrange_pt = '(*'
            printed_subrange_html = '(<i>'
            for json_sr in newEmphs:
                if set(elem).issubset(set(json_sr)):
                    inJSONsr = 1
                    continue
                elif set(elem).intersection(set(json_sr)):
                    inJSONsr = 2
                    if json_sr[0]==json_sr[-1]:
                        printed_subrange_pt = printed_subrange_pt + str(json_sr[0]) + '; '
                        printed_subrange_html = printed_subrange_html + str(json_sr[0]) + '; '
                    else:
                        printed_subrange_pt = printed_subrange_pt + str(json_sr[0]) + '-' + str(json_sr[-1]) + '; '
                        printed_subrange_html = printed_subrange_html + str(json_sr[0]) + '-' + str(json_sr[-1]) + '; '
            if printed_subrange_pt[-2:] == '; ':
                printed_subrange_pt = printed_subrange_pt[:-2]
            if printed_subrange_html[-2:] == '; ':
                printed_subrange_html = printed_subrange_html[:-2]
            if inJSONsr == 1:
                pt_string = pt_string + '*'+str(elem[0])+'-'+str(elem[-1])+'*, '            
                html_string = html_string + '<i>' + str(elem[0]) + '-' + str(elem[-1]) + '</i>, '
                continue
            elif inJSONsr == 2:
                pt_string = pt_string + str(elem[0])+'-'+str(elem[-1])+ ' ' + printed_subrange_pt + '*), '
                html_string = html_string + str(elem[0])+'-'+str(elem[-1])+ ' ' + printed_subrange_html + '</i>), '
            else:
                pt_string = pt_string +str(elem[0])+'-'+str(elem[-1])+', '
                html_string = html_string +  str(elem[0]) + '-' + str(elem[-1]) + ', '
    
    #all three are lists
    # print(type(hitsWithRemovals))
    # print(type(baseEmphs))
    # print(type(baseEmphsJSON))

    # print(args[0])
    # print(args[1])
    # print(added_pages)
    # print(added_emphs)
    # print(hitsWithRemovals)
    # print(hitsWithAdditions)
    # print(newRanges)
    # print('\n')
    # print(newEmphs)
    # print(pt_string)

    cEntry.new_hits_with_removals = hitsWithAdditions
    cEntry.new_emphs_json = newEmphs
    cEntry.pages_new_pt = pt_string
    cEntry.pages_new_html = html_string
    db.session.commit()

    returndict = {"htmlstring": html_string, "ptstring":pt_string}
    return jsonify(returndict)

#EDIT PAGES
@app.route('/editpages/<editinfo>', methods=['POST','GET'])
def editpages(editinfo):
    args = editinfo.split('&&')
    cEntry = Entries.query.get_or_404(int(args[1]))
    newStringPT = args[0]
    print(newStringPT)
    newStringHTML = ''
    starState = 0
    for char in newStringPT:
        if char == '*' and starState == 0:
            newStringHTML = newStringHTML + '<i>'
            starState = 1
        elif char == '*' and starState == 1:
            newStringHTML = newStringHTML + '</i>'
            starState = 0
        else:
            newStringHTML = newStringHTML + char
    print(newStringHTML)
    cEntry.pages_new_html = newStringHTML
    cEntry.pages_new_pt = newStringPT
    db.session.commit()
    return newStringHTML

#RENDER ADD ENTRY
@app.route('/add_entry/', methods=['POST', 'GET'])
def add_entry():
    adds = Adds.query.order_by(Adds.id).all()
    return render_template('add_entry.html', adds=adds)

@app.route('/add_entrydb/<info>', methods=['POST','GET'])
def add_entrydb(info):
    print(info)
    fields = info.split('&')
    entryname = re.sub('\+', ' ', fields[0].split('=')[1])
    see = re.sub('\+', ' ', fields[1].split('=')[1])
    seealso = re.sub('\+', ' ', fields[2].split('=')[1])
    pages = re.sub('\+', ' ', fields[3].split('=')[1])
    test = Adds.query.order_by(Adds.id.desc()).all()
    newid = test[0].id + 1
    new_row = Adds(id=newid,entry_name=entryname,see=see,seealso=seealso,pages=pages)
    db.session.add(new_row)
    db.session.commit()
    # print(jsonify(add_info))
    # print("hello")
    return redirect('/add_entry/')

#RENDER INDIV ENTRY
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