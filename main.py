from flask import render_template, Flask, request, redirect, url_for
from flask_mail import Mail, Message
from config import Conf
import psycopg2
import datetime
import calendar

app = Flask(__name__)
app.config['DEBUG'] = True
app.config.from_object(Conf)
mail = Mail(app)


@app.route('/')
@app.route('/<month>')
@app.route('/<month>/<year>')
def index(month=None, year=None):
    conn = psycopg2.connect(Conf.PSYCOPG_URI2)
    cur = conn.cursor()
    today = datetime.datetime.today()
    current_day = today.day
    current_month = today.month
    current_year = today.year
    month = int(month) if month else None
    year = int(year) if year else None
    if month:
        if month < 13 and month > 0:
            if year:
                current_year = year
            current_month = month
            current_day = current_day if month == today.month else None
            today = datetime.datetime(current_year, current_month, 1)
    days = calendar.monthrange(current_year, current_month)[1]
    first_weekday = datetime.datetime(current_year, current_month, 1).weekday()
    month_year_text = today.strftime("%B") + ' %s' % current_year

    first_date = '%s-%s-%s' % (current_year, current_month, 1)
    # last_date = '%s-%s-%s' % (current_year, current_month, days)
    query = "select * from reservations.v_conference where date(scheduled) >= %s and date_part('year', scheduled) = %s order by scheduled asc"
    attrs = [first_date, first_date.split('-')[0]]
    cur.execute(query, attrs)
    event = sqltodict(cur)
    cur.close()
    conn.close()
    return render_template('index.html', days=days, first_weekday=first_weekday, month_year_text=month_year_text,
                           current_day=current_day, current_month=current_month, current_year=current_year, events=event)


@app.route('/event/<eid>')
def event(eid):
    conn = psycopg2.connect(Conf.PSYCOPG_URI2)
    cur = conn.cursor()
    cur.execute("select * from reservations.v_conference where id = %s", [eid])
    event = sqltodict(cur)[0]
    cur.close()
    conn.close()
    return render_template('event.html', event=event)


@app.route('/event_delete/<eid>')
def event_delete(eid):
    conn = psycopg2.connect(Conf.PSYCOPG_URI2)
    cur = conn.cursor()
    cur.execute("delete from reservations.conference where id = %s", [int(eid)])
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))


@app.route('/event_edit/<eid>')
def event_edit(eid):
    users = get_users()
    conn = psycopg2.connect(Conf.PSYCOPG_URI2)
    cur = conn.cursor()
    cur.execute("select * from reservations.v_conference where id = %s", [eid])
    event = sqltodict(cur)[0]
    cur.close()
    conn.close()
    return render_template('event_edit.html', event=event, users=users)


@app.route('/event_new')
@app.route('/event_new/<newdate>')
def event_new(newdate=None):
    if newdate:
        newdate = newdate.split('-')[0]+'-' +newdate.split('-')[1].zfill(2)+'-' +newdate.split('-')[2].zfill(2)
    users = get_users()
    return render_template('event_new.html', users=users, newdate=newdate)


@app.route('/save_event/<eid>', methods=['POST'])
@app.route('/save_event', methods=['POST'])
def save_event(eid=None):
    reserved = 0
    new = True
    try:
        title = request.form.get('title') if request.form.get('title') != '' else None
        room = request.form.get('room') if request.form.get('room') != '' else None
        scheduled = request.form.get('sch_date') + ' ' + request.form.get('sch_time')
        endtime = request.form.get('sch_date') + ' ' + request.form.get('end_time')
        notes = request.form.get('notes') if request.form.get('notes') != '' else None
        participants = request.form.getlist('participants[]')
        attrs = [scheduled, room, notes, title, endtime, participants]
        conn = psycopg2.connect(Conf.PSYCOPG_URI2)
        cur = conn.cursor()
        if eid:
            query = "delete from reservations.conference WHERE id = %s;"
            cur.execute(query, [eid])
            conn.commit()
            new = False

        query = """
                insert into reservations.conference(scheduled, room, notes, title, endtime, participants)
                VALUES (%s, %s, %s, %s, %s, %s) returning id;
                """

        cur.execute("select reservations.get_conf_avail(%s, %s, %s)", [scheduled, endtime, int(room)])
        reserved = cur.fetchone()[0]
        # for inf in conn.notices:
        #     print(inf)
        # print(conn.info.error_message)
        if reserved == 0:
            cur.execute(query, attrs)
            eid = cur.fetchone()[0]
            conn.commit()
        else:
            conn.rollback()
        cur.close()
        conn.close()
    except Exception as exc:
        pass
    if eid and reserved == 0:
        return redirect(url_for('event', eid=eid))
    else:
        if new:
            return redirect(url_for('event_new', eid=eid))
        else:
            return redirect(url_for('event_edit', eid=eid))


def sqltodict(cursor):
    res_temp = []
    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    for row in rows:
        res_temp.append(dict(zip(column_names, row)))
    return res_temp


@app.template_filter('get_day')
def get_day(dt):
    day = dt.strftime('%d')
    if day[0] == '0':
        return int(day[1])
    return int(day)


@app.template_filter('get_date')
def get_date(dt):
    dt = dt.strftime('%Y-%m-%d')
    return dt


@app.template_filter('get_time')
def get_time(dt):
    time = dt.strftime('%H:%M')
    return time


@app.route('/send_mail/<eid>')
def send_mail(eid):
    conn = psycopg2.connect(Conf.PSYCOPG_URI2)
    cur = conn.cursor()
    cur.execute("select * from reservations.v_conference where id = %s", [eid])
    event = sqltodict(cur)[0]
    cur.close()
    conn.close()

    try:
        temp = render_template('mail_template.html', event=event)
        msg = Message('%s - %s' % (event['title'], event['scheduled']), sender=Conf.MAIL_DEFAULT_SENDER, recipients=event['participants'])
        msg.html = temp
        mail.send(msg)
        return render_template('event.html', event=event)
    except Exception as exc:
        return render_template('event.html', event=event)


def get_users():
    query = "select concat(last_name || ' ' || first_name) fullname, email from geousers.v_phonebook order by fullname"
    conn = psycopg2.connect(Conf.PSYCOPG_URI2)
    cur = conn.cursor()
    cur.execute(query)
    users = sqltodict(cur)
    cur.close()
    conn.close()
    return users


if __name__ == "__main__":
    app.run('0.0.0.0', '8000')
