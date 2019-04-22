content = '123'
ss = 'select * from paper where title like "%%%s%%"'%content+' or abstact like "%%%s%%"'%content+ 'or author like "%%%s%%"'%content
print(ss)