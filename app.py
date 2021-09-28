from flask import Flask, render_template, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import json
import re
import sys
# import psycopg2 as psycopg2


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://wak:7LZBAUBS09EWun82UdLAS8TXvOsLzVDR@oregon-postgres.render.com/oupindexdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

#fullrange = [* range(26-23,129-23)] + [* range(132-23,387-23)] + [* range(390-23,504-23)] + [* range(506-23,772-23)]


html_list = []
for i in [* range(3,772-23)]:
    with open('static/page_contents/test_'+str(i)+'.html','r') as fp:
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


@app.route('/')
def index():
    entries = Entries.query.all()
    print(entries[0].entry_name, file=sys.stderr)
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
        print(first, file=sys.stderr)
        print(html_list[0])
        last = int(page_number[1])-3
        for page in [* range(first, last+1)]:
            text = text + html_list[page]
    highlights = text

    stokens = curr_entry.stokens
    repl = '( |\n|—)'
    stokens = re.sub('(_)', repl, stokens)
    stokens = stokens.split(',')
    findtokens=set()
    for stoken in stokens:
        finds = re.finditer(stoken, highlights, re.IGNORECASE)
        for elem in finds:
            findtokens.add(elem.group())
    retokens = curr_entry.highlights.split('|')
    shighlight_list = []
    rehighlight_list = []
    for token in findtokens:
        if token != '':
            shighlight_list.append(token)
    for token in retokens:
        if token!= '':
            rehighlight_list.append(token)
    print(rehighlight_list)
    for elem in shighlight_list:
        highlights = re.sub(re.escape(elem), '<span style="background-color:yellow">'+elem+'</span>', highlights, re.IGNORECASE)
    for elem in rehighlight_list:
        highlights = re.sub(re.escape(elem), '<span style="background-color:aqua">'+elem+'</span>', highlights)
    #entrynow = entrynow + ')'
    #curr_entry = re.split(',', page_number_current, 1)[1]
    #print(curr_entry)
    return highlights
    #return send_from_directory('static/page_contents', 'plaintext' + page_number + '.html')

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
    # removals_list = current_entry.removals.split(',')
    # removals = set(removals_list)
    # emphases_list = current_entry.emphasized.split(',')
    # emphases = set(emphases_list)
    #current_id = current_entry.id
    #entry_title = current_entry.entry
    #variants = current_entry.variants
    #pages = current_entry.pages
    if not current_entry.removals:
        removals=[]
    else:
        removals=current_entry.removals.split(',')
    if not current_entry.emphasized_pages:
        emphases = []
    else:
        emphases = current_entry.emphasized_pages.split(',')
    if request.method == 'POST':
        print(request.form['reqtype'], file=sys.stderr)
        if request.form['reqtype'] == 'emphasize':
            x = request.form['content']
            if not current_entry.emphasized_pages:
                current_entry.emphasized_pages = x+','
            else:
                current_entry.emphasized_pages = current_entry.emphasized_pages + x + ','
            db.session.add(current_entry)
            db.session.commit()
            return redirect('/')
            # print(x, file=sys.stderr)
            # print("Hello", file=sys.stderr)
            # return "Hello"
        elif request.form['reqtype'] == 'remove':
            x = request.form['content']
            if not current_entry.removals:
                current_entry.removals = x+','
            else:
                current_entry.removals = current_entry.removals + x + ','
            db.session.commit()
            return redirect('/')
        elif request.form['reqtype']=='subrange':
            first = request.form['firstpage']
            second = request.form['secondpage']
            current_entry.emphasized_subranges = first+'-'+second
            db.session.commit()
            return redirect(request.referrer)
    else:    
        return render_template('entry_page.html', tokens=tokens, current_entry=current_entry, emphases=emphases, removals=removals)


if __name__ == "__main__":
    app.run(debug=True)