import time
from flask import Flask, render_template, request, flash, redirect, url_for,session
import sqlite3 as sql
import re
import hashlib


app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'
app.secret_key = 'please-generate-a-random-secret_key'

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    return render_template('index.html')


# route for user login
@app.route('/login', methods=['POST', 'GET'])
def login():
    hashed_pwd = hashlib.md5(request.form['password'].encode()).hexdigest()  # get hashed password
    student = re.search("[0-9][0-9][0-9]+@nittany.edu", request.form['username'])  # use regular expression to identify the student email
    if request.method == 'POST':
        username = request.form['username']
        if student:
            result = stu_name(username, hashed_pwd)
            if result is not None:
                flash('User has logged in successfully!')
                studentdata = student_info(username)
                courseinfo = course_info(username)
                session["username"] = username
                session["password"] = hashed_pwd
                return render_template('dashStudent.html', data=studentdata, courseinfo=courseinfo) # return student's dashboard with student's info and courses info
            else:
                flash('Invalid user!', 'error')
                return render_template('index.html')
        else:
            result = pro_name(username,hashed_pwd)
            if result is not None:
                teacourdata=course_proinfo(username)
                session["username"] = username
                session["password"] = hashed_pwd
                flash('User has logged in successfully!')
                return render_template('dashProf.html',data=teacourdata)
            else:
                flash('Invalid user!', 'error')
                return render_template('index.html')
    else:
        return render_template('index.html')


def stu_name(username, password):
    connect = sql.connect('database.db')
    connect.execute('SELECT * FROM Students WHERE Email=? AND Password=?', [username, password])
    cursor = connect.execute('SELECT * FROM Students WHERE Email=? AND Password=?', [username, password])
    return cursor.fetchone()

def pro_name(username, password):
    connect = sql.connect('database.db')
    connect.execute('SELECT * FROM Professors WHERE Email=? AND Password=?', [username, password])
    cursor = connect.execute('SELECT * FROM Professors WHERE Email=? AND Password=?', [username, password])
    return cursor.fetchone()

def student_info(username): # get student information
    connect = sql.connect('database.db')
    cur = connect.execute('SELECT [Full Name], Age, Major, Gender, Street, Zip, Email from Students WHERE Email = ?',(username,))
    return cur.fetchone()



def course_proinfo(username): # get the course taught by the professor
    connect = sql.connect('database.db')
    cur = connect.execute('select CourseID, CourseDescription, TeachingTeamID, Email, Office from CourseProInfo WHERE Email = ?',(username,))
    return cur.fetchone()


def course_info(username): # get course information for courses that student is currently taking
    connect= sql.connect('database.db')
    cur = connect.execute('SELECT CourseID, Exam_Grade, Course_Description, ProEmail, Office from stu_courseinfo WHERE Email = ?',(username,))
    return cur.fetchall()


@app.route('/checkinfo', methods=['POST','GET'])
def checkinfo():

    if request.method == 'POST':
        connect = sql.connect('database.db')
        cur = connect.cursor()
        email = request.form['username']
        # oldpwd = request.form['oldpwd']
        newpwd = request.form['newpwd']
        confirmpwd = request.form['confirmpwd']
        hashed_pwd = hashlib.md5(newpwd.encode()).hexdigest()
        if newpwd==confirmpwd:
            cur.execute('UPDATE Students SET Password = ? WHERE Email =?',(hashed_pwd, email))
            connect.commit()
            flash('Password changed successfully')
            time.sleep(3)
        else:
            flash('Something went wrong. Please try again.')
        return redirect('/')
    else:
        email = request.args.get("email")
        return render_template('studentInfo.html',data=email)


@app.route('/procheckinfo', methods=['POST','GET'])
def procheckinfo():

    if request.method == 'POST':
        connect = sql.connect('database.db')
        cur = connect.cursor()
        email = request.form['username']
        # oldpwd = request.form['oldpwd']
        newpwd = request.form['newpwd']
        confirmpwd = request.form['confirmpwd']
        hashed_pwd = hashlib.md5(newpwd.encode()).hexdigest()
        if newpwd==confirmpwd:
            cur.execute('UPDATE Professors SET Password = ? WHERE Email =?',(hashed_pwd, email))
            connect.commit()
            flash('Password changed successfully')
            time.sleep(3)
        else:
            flash('Something went wrong. Please try again.')
        return redirect('/')
    else:
        email = request.args.get("email")
        return render_template('proinfo.html',data=email)

def course_info_cp(username): # get course information for courses that student is currently taking
    connect= sql.connect('database.db')
    query = 'SELECT s.CourseID, Exam_Grade, Course_Description, ProEmail, Office,c.late_drop_deadline from stu_courseinfo as s  left join Courses as c on s.CourseID=c.CourseID  WHERE s.Email = "%s"'% (username,)
    cur = connect.execute(query)
    return cur.fetchall()

@app.route('/course_list/',methods=['GET','POST'])
def course_list():
    email = session.get('username')
    courseinfo = course_info_cp(email)
    return render_template('courselist.html',courseinfo=courseinfo)

@app.route('/del_course/',methods=['GET','POST'])
def del_course():
    from datetime import datetime
    import time
    now = datetime.now()
    cid = request.args.get("cid")
    email = session.get('username')
    courseinfo = course_info_cp(email)

    connect = sql.connect('database.db')
    cursor = connect.cursor()
    query = 'SELECT s.CourseID, Exam_Grade, Course_Description, ProEmail, Office,c.late_drop_deadline from stu_courseinfo as s  left join Courses as c on s.CourseID=c.CourseID  WHERE s.Email = "%s" and c.CourseID="%s"' % (
    email,cid)
    cursor.execute(query)
    ret = cursor.fetchall()
    if ret and len(ret)==1:
        time_str = ret[0][-1].replace("/","-")
        import re
        time_str = re.sub(r"\d+$",'2020',time_str)
        # "11/21/19"

        drop_date = datetime.strptime(str(time_str),"%m-%d-%Y")
        if now.date() >= drop_date.date():
            flash('del failed')
            return render_template('courselist.html',courseinfo=courseinfo)
        else:
            q_query = 'select * from stu_courseinfo where CourseID="%s" and Email="%s"' % (cid,email)

            ret = cursor.execute(q_query)
            print(ret.fetchall())

            del_query = 'delete from stu_courseinfo where CourseID="%s" and Email="%s"' % (cid,email)
            print(del_query)
            cursor = connect.cursor()
            ret = cursor.execute(del_query)
            connect.commit()

            q_query = 'select * from Comments where Student_Email="%s" and Courses="%s"' % (email,cid)
            ret = cursor.execute(q_query)
            print(ret.fetchall())
            del_comments = 'delete from Comments where Student_Email="%s" and Courses="%s"' % (email,cid)
            connect.commit()
            print(del_comments)
            ret = cursor.execute(query)
            connect.commit()
            print('del success')
            flash('del success')
            return redirect(url_for("course_list"))
    return render_template('courselist.html',courseinfo=courseinfo)


@app.route('/return_index', methods=['POST', 'GET'])
def return_index():
    username = request.args.get('username')
    flash('User has logged in successfully!')
    studentdata = student_info(username)
    courseinfo = course_info(username)
    return render_template('dashStudent.html', data=studentdata, courseinfo=courseinfo) # return student's dashboard with student's info and courses info

# determine whether it is a student or a teacher
@app.route('/stu_or_pro',methods=['POST','GET'])
def stu_or_pro():
    email = request.args.get("email")
    student = re.search("[0-9][0-9][0-9]+@nittany.edu", email)
    if student:
        return redirect('/viewassignments?email=%s'%email)
    else:
        return redirect('/creaeteassignments?email=%s'%email)


def homework_info(username):
    connect = sql.connect('database.db')
    cur = connect.execute('select a.CourseID, a.SecNo, b.Hw_No,b.Hw_Details from Enrolls a left join Homeworks b on a.CourseID=b.CourseID and a.SecNo=b.SecNo where Student_Email="%s"' % username)
    return cur.fetchall()

def exams_info(username):
    connect = sql.connect('database.db')
    cur = connect.execute('select a.CourseID, a.SecNo, b.Exam_No,b.Exam_Details from Enrolls a left join Exams b on a.CourseID=b.CourseID and a.SecNo=b.SecNo where Student_Email="%s"' % username)
    return cur.fetchall()


# this route is for professor use only
@app.route('/creaeteassignments',methods=['POST','GET'])
def createassign():
    username = request.args.get("email")
    print(username)

    return render_template('createAssign.html' )


# this route is for student use only
@app.route('/viewassignments',methods=['POST','GET'])
def viewassign():
    username = request.args.get("email")
    homeworkdata = homework_info(username)
    examdata = exams_info(username)

    return render_template('studentViewAssign.html',Homeworks=homeworkdata, Exams=examdata)

# this route is for professor use only
def get_stu_score(username): # get course information for courses that student is currently taking
    connect= sql.connect('database.db')
    cur = connect.execute('SELECT Email, Exam_Grade,CourseID from stu_courseinfo')
    return cur.fetchall()

@app.route('/submitscores/', methods=['POST','GET'])
def submitscore():
    username = session.get('username')
    if request.method == "GET":
        courseinfo = get_stu_score(username)
    return render_template('profScorePage.html',courseinfo=courseinfo)


from flask import make_response
@app.route('/edit_score/', methods=['POST','GET'])
def edit_score():
    print(request.args)
    score = request.args.get('score').strip()
    email = request.args.get('email').strip()
    cid = request.args.get('cid').strip()
    up_sql = 'UPDATE stu_courseinfo SET Exam_Grade = "%s" WHERE CourseID="%s" and Email="%s"' % (score,cid,email)
    connect = sql.connect('database.db')
    cursor = connect.cursor()
    ret = cursor.execute(up_sql)
    connect.commit()
    response = make_response('ok')
    return response

@app.route('/dropcourses/',methods=['POST','GET'])
def dropcourse():
    email = session.get('username')
    courseinfo = course_info_cp(email)
    if request.method == "GET":
        return render_template('dropCourse.html',courseinfo=courseinfo)
    else:
        cid = request.form.get("CourseName",'')
        cname = request.form.get("ConfirmCourseName",'')
        from datetime import datetime
        import time
        now = datetime.now()
        connect = sql.connect('database.db')
        cursor = connect.cursor()
        query = 'SELECT s.CourseID, Exam_Grade, Course_Description, ProEmail, Office,c.late_drop_deadline from stu_courseinfo as s  left join Courses as c on s.CourseID=c.CourseID  WHERE s.Email = "%s" and c.CourseID="%s"' % (
            email, cid)
        cursor.execute(query)
        ret = cursor.fetchall()
        if ret and len(ret) == 1:
            time_str = ret[0][-1].replace("/", "-")
            import re
            time_str = re.sub(r"\d+$", '2020', time_str)
            # "11/21/19"

            drop_date = datetime.strptime(str(time_str), "%m-%d-%Y")
            if now.date() >= drop_date.date():
                flash('del failed')
                return render_template('courselist.html', courseinfo=courseinfo)
            else:
                q_query = 'select * from stu_courseinfo where CourseID="%s" and Email="%s"' % (cid, email)

                ret = cursor.execute(q_query)
                print(ret.fetchall())

                del_query = 'delete from stu_courseinfo where CourseID="%s" and Email="%s"' % (cid, email)
                print(del_query)
                cursor = connect.cursor()
                ret = cursor.execute(del_query)
                connect.commit()

                q_query = 'select * from Comments where Student_Email="%s" and Courses="%s"' % (email, cid)
                cursor.execute(q_query)
                ret = cursor.fetchall()
                print(ret)
                if ret:
                    del_comments = 'delete from Comments where Student_Email="%s" and Courses="%s"' % (email, cid)
                    cursor.execute(del_query)
                    connect.commit()
                return redirect(url_for("dropcourse"))

        return render_template('dropCourse.html', courseinfo=courseinfo)

@app.route('/studentcreateposts/',methods=['POST','GET'])
def createposts():

    email = session.get('username')
    reark_list = []
    connect = sql.connect('database.db')
    cur = connect.cursor()
    student = re.search("[0-9][0-9][0-9]+@nittany.edu", email)
    if student:

        cur.execute('select CourseID from Exam_grades where Student_Email=?',(email,))
        exam = cur.fetchall()
        cur.execute('select CourseID from Homework_grades where Student_Email=?',(email,))
        homework = cur.fetchall()
        for e in exam:
            reark_list.append(e[0])
        for h in homework:
            reark_list.append(h[0])
        cur.execute('select * from Posts where Courses in %s' % str(tuple(reark_list)))
        post_list = cur.fetchall()

        return render_template('CreatePostStu.html',data=post_list,email=email)
    else:
        cur.execute('select CourseID from CourseProInfo where Email =?',(email,))
        course = cur.fetchall()
        for c in course:
            reark_list.append(c[0])
        if len(reark_list) ==1:
            sqltow= 'select * from Posts where Courses = "%s"' % str(reark_list[0])
        else:
            sqltow='select * from Posts where Courses in %s' % str(tuple(reark_list))
        cur.execute(sqltow)
        post_list = cur.fetchall()

        return render_template('CreatePostPro.html',data=post_list,email=email)

@app.route('/dashStudent',methods=['POST','GET'])
def dashStudent():
    username = session.get('username')
    studentdata = student_info(username)
    courseinfo = course_info(username)
    teachercour = course_proinfo(username)
    student = re.search("[0-9][0-9][0-9]+@nittany.edu",username)
    if student:
        return render_template('dashStudent.html',data=studentdata, courseinfo=courseinfo)
    else:
        return render_template('dashProf.html', data=teachercour)


@app.route('/addpost',methods=['POST','GET'])
def addpost():
    email = session.get('username')
    option = request.form.get("FirstName")
    post_coutent = request.form.get("LastName") or ""
    #添加新评论
    connect = sql.connect('database.db')
    cur = connect.cursor()
    sqltow = "select Post_ID from Posts ORDER BY Post_ID DESC LIMIT 1"
    cur.execute(sqltow)
    exam = cur.fetchall()
    num = int(exam[0][0]) + 1
    sqls = 'INSERT INTO Posts(Post_ID,Courses,Post_Info,Student_Email) VALUES (%d,"%s","%s","%s")' % (num,option,post_coutent,email)
    cur.execute(sqls)
    connect.commit()
    return redirect('/studentcreateposts/')


def pro_get_homework(username): # Get the homework professor
    connect = sql.connect('database.db')
    cur = connect.execute('select b.CourseID, b.SecNo,b.Hw_No,b.Hw_Details from  Homeworks b left join  CourseProInfo a   on a.CourseID = b.CourseID where Email= ?',(username,))
    return cur.fetchall()

def pro_get_exams(username): # Get the exams professor
    connect = sql.connect('database.db')
    cur = connect.execute('select b.CourseID, b.SecNo,b.Exam_No,b.Exam_Details from  Exams b left join  CourseProInfo a   on a.CourseID = b.CourseID where Email= ?',(username,))
    return cur.fetchall()

@app.route('/creatAssign',methods=['POST','GET'])
def creatAssign():
    username = session.get('username')
    prohomework = pro_get_homework(username)
    procourse = pro_get_exams(username)
    return render_template('createAssign.html', homeworkdata=prohomework, coursedata=procourse )


@app.route('/createHomExa',methods=['POST','GET'])
def createHomExa():
    flag = request.form.get("flag")
    if flag == "mune_x1":
        hcoursName = request.form.get("hCourseName")
        hsectionNumber = request.form.get("hSectionNumber")
        homeworkNumber = request.form.get("HomeworkNumber")
        homeworkInformation = request.form.get("HomeworkInformation")

        connect = sql.connect('database.db')
        cur = connect.cursor()
        sqls = 'INSERT INTO Homeworks(CourseID, SecNo, Hw_No, Hw_Details) VALUES ("%s",%s,%s,"%s")' % (
        hcoursName, hsectionNumber, homeworkNumber, homeworkInformation)
        cur.execute(sqls)
        connect.commit()
    if flag == "mune_x2":
        ecoursename = request.form.get("eCoursename")
        esectionNumber = request.form.get("eSectionNumber")
        examNumber = request.form.get("ExamNumber")
        examDetails = request.form.get("ExamDetails")
        connect = sql.connect('database.db')
        cur = connect.cursor()
        sqls = 'INSERT INTO Exams(CourseID, SecNo, Exam_No, Exam_Details) VALUES ("%s",%s,"%s","%s")' % (
            ecoursename, esectionNumber, examNumber, examDetails)
        cur.execute(sqls)
        connect.commit()
    return redirect('/creatAssign')




#this route is used for professor to make announcement only
@app.route('/makeannounce', methods=['POST', 'GET'])
def announce():
    if request.method == 'POST':
        CourseID = request.form['cid']
        SectionID = request.form['sid']
        AnnounceInfo = request.form['ainfo']
        ProfName = request.form['pname']
        result = makeannounce(CourseID, SectionID, AnnounceInfo, ProfName)
        if result:
            return render_template('announceProf.html', result=result)
    return render_template('announceProf.html')


def makeannounce(CourseID, SectionID, AnnounceInfo, ProfName):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS Announcement(Announce_ID INTEGER PRIMARY KEY, Course_ID TEXT, Section_ID INTEGER, Announce_Info TEXT, Prof_Name TEXT);')
    connection.execute('INSERT INTO Announcement (Course_ID, Section_ID, Announce_Info, Prof_Name) VALUES (?,?,?,?);', (CourseID, SectionID, AnnounceInfo, ProfName))
    connection.commit()
    cursor = connection.execute('SELECT * FROM Announcement WHERE Prof_Name = ?', (ProfName, ))
    return cursor.fetchall()


# this route is used for student to see announcement only
@app.route('/seeannounce',methods=['POST','GET'])
def seeannounce():
    if request.method == "POST":
        CourseID = request.form['cid']
        announce = announcecheck(CourseID)
        if announce:
            return render_template('announceStu.html', announce=announce)
    return render_template('announceStu.html')


def announcecheck(CourseID):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Announcement WHERE Course_ID=?', (CourseID,))
    return cursor.fetchall()











if __name__ == "__main__":
    app.run(debug=True)
