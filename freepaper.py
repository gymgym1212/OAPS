from flask import Flask, request, render_template, redirect, jsonify,Response, send_file, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import uuid
import model

logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
limiter = Limiter(
    app,
    key_func=get_remote_address,   #根据访问者的IP记录访问次数
    default_limits=["200 per day", "50 per hour"]  #默认限制，一天最多访问200次，一小时最多访问50次
)
UPLOAD_PATH='files' #where papers stored
minganlist = ['peace','and','love']
db = model.Database()
@app.route('/')
def method_name():
    hot_paper = db.get_hot_paper()
    return render_template('homepage.html',articles=hot_paper)

@app.route('/articles/<id>')
def article_detail(id):
    ip = request.remote_addr
    db.visit_paper(ip,id)
    lst = db.get_paper(id)
    lst2 = db.get_comments(id)
    return render_template('article_detail.html',articles=lst,comments=lst2)

@app.route('/donate')
def donate():
    return render_template('donation.html')

#404 error redirection
@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'),404

@app.route('/author/<authorid>')
def author_page(authorid):
    lst = db.get_paper_by_authorid(authorid)
    return render_template('author_page.html',articles=lst)

@app.route('/download/<pid>',methods=['GET'])
@limiter.limit("5 per minutes")
def download_file(pid):
    return send_from_directory(UPLOAD_PATH, pid+'.pdf', as_attachment=True)

@app.route('/subject')
def subject():
    lst = db.get_allsubjects()
    return render_template('subject.html',subjects=lst)

@app.route('/subject/add', methods=['POST'])
def add_subject():
    name = request.form['subject']
    db.add_subject(name)
    return redirect('/subject')

@app.route('/article/subject/<subjectid>')
def get_articles_by_subject(subjectid):
    lst = db.get_articles_by_subject(subjectid)
    return render_template('subject_detail.html',articles=lst)


@app.route('/submit/comments',methods=['POST'])
@limiter.limit("5 per minutes")
def submit_comments():
    id = request.form['id']
    content = request.form['content']
    db.save_comment(content,id)
    return redirect('/articles/'+id)

@app.route('/article/upvote',methods=['POST'])
def article_upvote():
    id = request.form['id']
    ip = request.remote_addr
    print(id)
    db.vote_to_paper(id,ip,1)
    return redirect('/')

@app.route('/article/downvote',methods=['POST'])
def article_downvote():
    id = request.form['id']
    ip = request.remote_addr
    print(id)
    db.vote_to_paper(id,ip,0)
    return redirect('/')

@app.route('/search',methods=['POST'])
def search_result():
    content = request.form['content']
    lst1 = db.search_papers(content)
    lst2 = db.search_comments(content)

    return render_template('search_result.html',articles=lst1,comments=lst2)

@app.route('/upload',methods=['POST'])
@limiter.limit("5 per minutes")
def upload_file():
    if request.method != 'POST':
        return jsonify({'code': -1, 'filename': '', 'msg': 'Method not allowed'})

    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'code': -1, 'filename': '', 'msg': 'No file part'})
    author = request.form['author']
    abstract = request.form['abstract']
    title = request.form['title']
    email = request.form['email']
    subjects = request.form['subject']
    if author == '':
        return jsonify({'code': -1, 'filename': '', 'msg': 'No author part'})
    if abstract == '':
        return jsonify({'code': -1, 'filename': '', 'msg': 'No abstract part'})
    if title == '':
        return jsonify({'code': -1, 'filename': '', 'msg': 'No title part'})
    if email == '':
        return jsonify({'code': -1, 'filename': '', 'msg': 'No email part'})
    if subjects == '':
        return jsonify({'code': -1, 'filename': '', 'msg': 'No subject part'})

    for i in minganlist:
        if i in author:
            return redirect('/')
    for i in minganlist:
        if i in abstract:
            return redirect('/')
    for i in minganlist:
        if i in title:
            return redirect('/')
            
    file = request.files['file']
    size = len(file.read())
    if size>20*1024*1024:
        return jsonify({'code': -1, 'filename': '', 'msg': 'file is too large!'})
    # if user does not select file, browser also submit a empty part without filename
    if file.filename == '':
        logger.debug('No selected file')
        return jsonify({'code': -1, 'filename': '', 'msg': 'No selected file'})
    try:
        if file and allowed_file(file.filename):
            origin_file_name = file.filename
            print('filename is %s' % origin_file_name)
            # filename = secure_filename(file.filename)
            filename = str(uuid.uuid1())
            pid=filename
            filename+='.pdf'

            if os.path.exists(UPLOAD_PATH):
                print('%s path exist' % UPLOAD_PATH)
                pass
            else:
                print('%s path not exist, do make dir' % UPLOAD_PATH)
                os.makedirs(UPLOAD_PATH)

            file.save(os.path.join(UPLOAD_PATH, filename))
            ss=db.save_paper(pid,email,title,abstract,author,subjects)

            print('%s %s' % (filename,ss))
            return redirect('/')
        else:
            print('%s not allowed' % file.filename)
            return jsonify({'code': -1, 'filename': '', 'msg': 'File not allowed'})
    except Exception as e:
        print('upload file exception: %s' % e)
        return jsonify({'code': -1, 'filename': '', 'msg': 'Error occurred'})
        

ALLOWED_EXTENSIONS = set(['pdf'])#允许文件上传的格式
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run(debug=True)