drop table if exists books;
create table books (
      id integer primary key autoincrement,
      book_no text NOT NULL ,
      title text not null,
      link text not null,
      remark text null
);

drop table if exists users;
create table users (
      id integer primary key autoincrement,
      emp_no text NOT NULL ,
      emp_name text not null,
      mail text not null
);


drop table if exists borrow_rec;
create table borrow_rec (
      id integer primary key autoincrement,
      book_id integer NOT NULL ,
      emp_id integer not null,
      borrow_date datetime not null,
      return_date datetime NOT NULL ,
      remark text  null
);