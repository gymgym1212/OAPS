import sqlite3 as sqlite
from random import Random
import datetime
import smtplib
from email.mime.text import MIMEText
import os
assert 'SYSTEMROOT' in os.environ

conn = sqlite.connect('Freepaper.db', check_same_thread=False)
cursor = conn.cursor()

class Subject:

    def __init__(self,id,name):
        self.name=name
        self.id=id

class Article:

    def __init__(self,id,pid,email,title,abstract,author,date,upvotes,downvotes,score,show,visits,authorid):
        self.id=id
        self.pid=pid
        self.email=email
        self.title=title
        self.abstract=abstract
        self.author=author
        self.date=date
        self.upvotes=upvotes
        self.downvotes=downvotes
        self.score=score
        self.show=show
        self.visit=visits
        self.authorid=authorid
        x=len(self.email)
        ss=''
        for i in range(x):
            if self.email[i]!='@' and self.email[i]!='.' and i>0:
                ss+='x'
            else:
                ss+=self.email[i]
        self.email=ss

class Comment:

    def __init__(self,id,content,ppid,date):
        self.id=id
        self.ppid=ppid
        self.content=content
        self.date=date


class Database:
    
    def get_now_time(self):
        nowdate = datetime.datetime.now()
        date = nowdate.strftime('%Y-%m-%d %H:%M:%S')
        return date

    def in_blacklist(self,email_add):
        cursor.execute('select * from blacklist where email = "%s"'%email_add)
        addlist = cursor.fetchall()
        if len(addlist)==0:
            return 'false'
        else:
            return 'true'

    def put_into_blacklist(self,email_add):
        if self.in_blacklist(email_add)=='true':
            return
        conn.execute('insert into blacklist values("%s")'%email_add)
        conn.commit()
    
    def remove_from_blacklist(self,email_add):
        conn.execute('DELETE FROM blacklist where email ="%s"'%email_add)
        conn.commit()

    def changeto_paper(self,lst):
        l = len(lst)
        article_lst=[]
        for i in range(l):
            article = Article(lst[i][0],lst[i][1],lst[i][2],lst[i][3],lst[i][4],lst[i][5],lst[i][6],lst[i][7],lst[i][8],lst[i][9],lst[i][10],lst[i][11],lst[i][12])
            article_lst.append(article)
        return article_lst

    def save_paper(self,pid,email,title,abstract,author,subjectname):
        if self.in_blacklist(email)=='true':
            return 'Forbidden! The email is in blacklist.'
        print('add subject')
        sid=self.add_subject(subjectname)
        print('add finished')
        authorid=self.add_author(email)
        date = self.get_now_time()
        #print(date)
        conn.execute('insert into paper (pid,email,title,abstract,author,date,downvotes,upvotes,score,show,visit,authorid) values("%s","%s","%s","%s","%s","%s",0,0,0,1,0,"%s")'%(str(pid),str(email),str(title),str(abstract),str(author),str(date),str(authorid)))
        conn.commit()
        lst = cursor.execute('select * from paper where pid = "%s"'%pid).fetchall()
        print(lst)
        ppid = lst[0][0]
        self.add_paper_by_subject(ppid,sid)
        return 'successfully!'

    def active_paper(self,id):
        conn.execute('update paper set show = 1 where id ="%s"'%id)
        conn.commit()

    def get_paper(self,id):
        lst=cursor.execute('select * from paper where show = 1 and id = "%s"'%id).fetchall()
        lst = self.changeto_paper(lst)
        return lst
    
    def get_paper_by_authorid(self,authorid):
        lst = cursor.execute('select * from paper where show = 1 and authorid = "%s"'%authorid).fetchall()
        lst = self.changeto_paper(lst)
        return lst
    
    def get_hot_paper(self):
        lst = cursor.execute("SELECT * FROM paper where  show = 1 order by score DESC limit 20").fetchall()
        lst = self.changeto_paper(lst)
        return lst

    def visit_paper(self,ip,ppid):
        lst = cursor.execute('SELECT * from paper_visit where ppid = "%s" and ip = "%s"'%(ppid,ip)).fetchall()
        print(lst)
        if len(lst) > 0:
            return
        conn.execute('insert into paper_visit (ip,ppid) values ("%s","%s")'%(str(ip),str(ppid)))
        conn.commit()
        lst = cursor.execute('SELECT visit from paper where id = "%s"'%str(ppid)).fetchall()
        x=int(lst[0][0])+1
        conn.execute('update paper set visit = "%s" where id ="%s"'%(str(x),str(ppid)))
        conn.commit()

    def changeto_comments(self,lst):
        x = len(lst)
        comment_lst=[]
        for i in range(x):
            c = Comment(lst[i][0],lst[i][1],lst[i][2],lst[i][3])
            comment_lst.append(c)
        return comment_lst

    def save_comment(self,content,ppid):
        date = self.get_now_time()
        conn.execute('insert into comments (content,ppid,date) values("%s","%s","%s")'%(content,ppid,date))
        conn.commit()
    
    def get_comments(self,ppid):
        lst = cursor.execute('SELECT * from comments where ppid ="%s" order by id DESC'%ppid).fetchall()
        lst = self.changeto_comments(lst)
        return lst
    
    def delte_comments(self,id):
        conn.execute('DELETE from comments where id = "%s"'%id)
        conn.commit()
    
    def add_author(self,email):
        lst = cursor.execute('select * from author where email = "%s"'%email).fetchall()
        if len(lst) > 0 :
            return 0
        conn.execute('insert into author (email) values("%s")'%email)
        conn.commit()
        return self.get_authorid(email)

    def get_authorid(self,email):
        lst = cursor.execute('select * from author where email = "%s"'%email).fetchall()
        if len(lst) <=0:
            return 0
        return lst[0][0]

    def vote_to_paper(self,ppid,ip,flag):
        conn.execute('DELETE from paper_vote where ip="%s" and ppid = "%s"'%(ip,ppid))
        conn.commit()
        conn.execute('insert into paper_vote (ip,ppid,flag) values("%s","%s","%s")'%(ip,ppid,flag))
        conn.commit()
        self.update_paper(ppid)
    
    def update_paper(self,ppid):
        lst = cursor.execute('select * from paper_vote where ppid = "%s" and flag = 1'%ppid).fetchall()
        upvote=len(lst)
        lst = cursor.execute('select * from paper_vote where ppid = "%s" and flag = 0'%ppid).fetchall()
        downvote=len(lst)
        lst = cursor.execute('select * from comments where ppid = "%s"'%ppid).fetchall()
        comments = len(lst)
        score = 5*comments+3*upvote+downvote
        conn.execute('update paper set upvotes = "%s", downvotes = "%s", score = "%s" where id = "%s"'%(upvote,downvote,score,ppid))
        conn.commit()
    
    def add_paper_by_subject(self,ppid,sid):
        conn.execute('insert into paper_subject (ppid,sid) values("%s","%s")'%(ppid,sid))
        conn.commit()

    def changeto_subjects(self,lst):
        x = len(lst)
        subject_lst=[]
        for i in range(x):
            subject =  Subject(lst[i][0],lst[i][1])
            subject_lst.append(subject)
        return subject_lst
    
    def get_allsubjects(self):
        lst = cursor.execute('select * from subjects').fetchall()
        lst = self.changeto_subjects(lst)
        return lst
    
    def add_subject(self,name):
        lst = cursor.execute('select * from subjects where name = "%s"'%name).fetchall()
        if len(lst) > 0:
            print(lst)
            return lst[0][0]
        conn.execute('insert into subjects (name) values ("%s")'%name)
        conn.commit()
        lst = cursor.execute('select * from subjects where name = "%s"'%name).fetchall()
        print(lst)
        return lst[0][0]
    
    def get_articles_by_subject(self,subjectid):
        lst = cursor.execute('select * from paper where id in (select ppid from paper_subject where sid = "%s") '%subjectid).fetchall()
        lst = self.changeto_paper(lst)
        return lst

    def search_papers(self,content):
        ss = 'select * from paper where title like "%%%s%%"'%content+' or abstact like "%%%s%%"'%content+ 'or author like "%%%s%%"'%content
        print(ss)
        lst = cursor.execute('select * from paper where title like "%%%s%%"'%content+' or abstract like "%%%s%%"'%content+ 'or author like "%%%s%%"'%content).fetchall()
        lst = self.changeto_paper(lst)
        return lst

    def search_comments(self,content):
        lst = cursor.execute('select * from comments where content like "%%%s%%"'%content).fetchall()
        lst = self.changeto_comments(lst)
        return lst

class EmailManager:
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    length = len(chars)
    random = Random()

    port=465
    mail_host='smtp.qq.com'
    username='369713635@qq.com'
    passwd='tbqnmppsscdwcaih'
    content='the verify email from FreePaper'
    title='gym'
    
    def __init__(self):
        pass

    def getStr(self):
        s=""
        for i in range(20):
            s+=EmailManager.chars[EmailManager.random.randint(0,EmailManager.length-1)]
        #print(s)
        return s

    def sendTo(self,email):
        msg = MIMEText(EmailManager.content+' and your code is '+EmailManager.getStr(EmailManager))  # 邮件内容
        print(msg)
        msg['Subject'] = EmailManager.title   # 邮件主题
        msg['From'] = EmailManager.username   # 发送者账号
        msg['To'] = email      # 接收者账号列表
        smtp = smtplib.SMTP_SSL(EmailManager.mail_host, port=EmailManager.port)   # 连接邮箱，传入邮箱地址，和端口号
        smtp.login(EmailManager.username, EmailManager.passwd)          # 登录发送者的邮箱账号，密码
        # 参数分别是 发送者，接收者，第三个是把上面的发送邮件的 内容变成字符串
        smtp.sendmail(EmailManager.username, email, msg.as_string())
        smtp.quit() # 发送完毕后退出smtp
        print('email send success.')

if __name__ == '__main__':
    d= Database()
