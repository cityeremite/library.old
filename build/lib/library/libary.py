#-*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash


app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'books.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.route('/books')
def show_books():
    db = get_db()
    cur = db.execute('select id as book_id,book_no,title,link,remark from books order by id desc')
    books = cur.fetchall()
    #print(books)
    return render_template('books.html', books=books)

@app.route('/')
def book_status():

    db = get_db()
    cur = db.execute('select b.id as book_id,book_no,title,link,r.emp_name,borrow_date,return_date,r.remark,IFNULL(status, "可借阅") as status \
      FROM books b LEFT JOIN borrow_rec r ON b.id = r.book_id ')
    borrow_rec = cur.fetchall()
    return render_template('book_status.html', borrow_rec=borrow_rec)


#if __name__ == "__main__":
#    app.run()

@app.route('/borrow_list')
def show_borrow():

    db = get_db()
    cur = db.execute('select b.id as book_id,book_no,title,link,r.emp_name,borrow_date,return_date,r.remark,IFNULL(status, "可借阅") as status \
      FROM books b LEFT JOIN borrow_rec r ON b.id = r.book_id ')
    borrow_rec = cur.fetchall()
    return render_template('borrow_list.html', borrow_rec=borrow_rec)


@app.route('/borrow/<book_id>', methods=['GET', 'POST'])
def borrow_return(book_id):
    if request.method == 'GET':
        db = get_db()
        cur = db.execute('select b.id as book_id,book_no,title,link,r.emp_name,borrow_date,return_date,r.remark ,status\
          FROM books b LEFT JOIN borrow_rec r ON b.id = r.book_id  \
          where b.id=?', book_id)
        borrow_rec = cur.fetchall()
        #print(borrow_rec)
        return render_template('borrow.html', borrow_rec=borrow_rec)
    if request.method == 'POST':
        #print(request.form)
        #print(book_id)
        db = get_db()
        cur = db.execute('select id from borrow_rec where book_id=?',[book_id])
        rec = cur.fetchall()
        db.commit()
        rc = len(rec)
        if rc > 0:
            db = get_db()
            db.execute('update  borrow_rec SET emp_name =?,borrow_date=?,return_date=?,remark=?,status=? where book_id=?', \
                   [request.form['emp_name'], request.form['borrow_date'], request.form['return_date'], request.form['remark'],request.form['status'] , book_id])
            db.commit()
        else:
            db = get_db()
            db.execute('insert into borrow_rec (book_id,emp_name,borrow_date,return_date, remark,status) values (?, ?, ?, ?, ?, ?)', \
                       [book_id, request.form['emp_name'], request.form['borrow_date'], request.form['return_date'], request.form['remark'],request.form['status']])
            db.commit()
        flash('New record was successfully saved!')
        return redirect(url_for('show_borrow'))
    #return render_template('borrow_list.html')




@app.route('/delbook/<book_id>', methods=['GET'])
def del_book(book_id):
    print(book_id)
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'GET':
        #print(request.form)
        #print(book_id)
        db = get_db()
        cur = db.execute('select id from borrow_rec where book_id=? and status="已借出"',[book_id])
        rec = cur.fetchall()
        db.commit()
        rc = len(rec)

        if rc > 0:
            flash('图书已借出，请归还后再删除。')
            return redirect(url_for('show_books'))
        else:
            db = get_db()
            db.execute('delete from borrow_rec  where book_id=?',  [book_id])
            db.execute('delete from books  where id=?',  [book_id])
            db.commit()
            flash('Book was successfully deleted!')

            return redirect(url_for('show_books'))

@app.route('/addbook', methods=['POST'])
def add_book():
    if not session.get('logged_in'):
        abort(401)
    if len(request.form['book_no']) == 0 or len(request.form['title']) == 0 or len(request.form['link']) == 0:
        flash('book_no or title or link cant be blank')
        return redirect(url_for('show_books'))

    db = get_db()
    db.execute('insert into books (book_no ,title,link, remark) values (?, ?, ?, ?)',  [request.form['book_no'], request.form['title'], request.form['link'], request.form['remark']])
    db.commit()
    flash('New book was successfully saved!')
    return redirect(url_for('show_books'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_books'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('book_status'))
