#!/usr/bin/env python3.4
#pip install Flask

import logging
import hashlib
from flask import Flask, request, redirect, session, url_for
from werkzeug.serving import run_simple
from wsgiref.handlers import CGIHandler
#from flup.server.fcgi import WSGIServer
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

host = "192.168.2.105"
host = "localhost"
port = 8080

PROJECTNAME = "taxi"
DBNAME = PROJECTNAME+".sqlite"

logger = logging.getLogger(PROJECTNAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(PROJECTNAME+".log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

app = Flask(__name__)
#UPLOAD_FOLDER = "./static/"
#ALLOWED_EXTENSIONS = set([".wargamerpl2"])
#app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

engine = create_engine("sqlite:///"+DBNAME, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()
class Fahrer(Base):
    __tablename__ = "fahrer"
    ID = Column("ID", Integer, primary_key=True)
    vorname = Column("vorname", String)
    nachname = Column("nachname", String)
    passwort = Column("passwort", String)
    rechte = Column("rechte", Integer)
    status = Column("status", Integer)
class Auto(Base):
    __tablename__ = "autos"
    ID = Column("ID", Integer, primary_key=True)
    nummer = Column("nummer", Integer)
    typ = Column("typ", Integer)
    kennzeichen = Column("kennzeichen", String)
    status = Column("status", Integer)
class Kunde(Base):
    __tablename__ = "kunden"
    ID = Column("ID", Integer, primary_key=True)
    name = Column("name", String)
class Schichtabrechnung(Base):
    __tablename__ = "schichtabrechnungen"
    ID = Column("ID", Integer, primary_key=True)
    fahrerID = Column("fahrerID", Integer, ForeignKey("fahrer.id"))
    autoID = Column("autoID", Integer, ForeignKey("autos.id"))
    begin = Column("beginn", Integer)
    ende = Column("ende", Integer)
    gesamtKM = Column("gesamtKM", Integer)
    besetztKM = Column("besetztKM", Integer)
    touren = Column("touren", Integer)
    tacho = Column("tacho", Integer)
    schicht = Column("schicht", Integer)
    tanken = Column("tanken", Float)
    liter = Column("liter", Float)
    waschen = Column("waschen", Float)
    saugen = Column("saugen", Float)
    parken = Column("parken", Float)
    sonstiges = Column("sonstiges", Float)
class Pause(Base):
    __tablename__ = "pausen"
    ID = Column("ID", Integer, primary_key=True)
    abrechnungsID = Column("abrechnungsID", Integer, ForeignKey("schichtabrechnungen.id"))
    beginn = Column("beginn", Integer)
    ende = Column("ende", Integer)
class Einnahme(Base):
    __tablename__ = "einnahmen"
    ID = Column("ID", Integer, primary_key=True)
    abrechnungID = Column("abrechnungID", Integer, ForeignKey("schichtabrechnungen.id"))
    brutto = Column("brutto", Float)
    netto = Column("netto", Float)
    zahlungsart = Column("zahlungsart", Integer)
    kundenID = Column("kundenID", Integer, ForeignKey("kunden.id"))

@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        if ("firstname" in request.form and "lastname" in request.form and "password" in request.form):
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            password = request.form["password"]
            h = hashlib.new("sha256")
            h.update(request.form["password"].encode("utf-8"))
            password = h.hexdigest()
            userCount = session.query(Fahrer).filter(and_(Fahrer.vorname == firstname, Fahrer.nachname == lastname)).count()
            if (userCount > 0):
                user = session.query(Fahrer).filter(and_(Fahrer.vorname == firstname, Fahrer.nachname == lastname)).first()
                if (user.passwort == password):
                    session["firstname"] = user.vorname
                    session["lastname"] = user.nachname
                    session["permissions"] = user.rechte
                    logging.getLogger(PROJECTNAME).info(firstname+" "+lastname+" logged in")
                    return redirect(redirect_url(), code=302)
                else:
                    logging.getLogger(PROJECTNAME).warning(firstname+" "+lastname+" tried to log in with wrong password")
                    return redirect(redirect_url(), code=302)
            else:
                return redirect(redirect_url(), code=302)

def redirect_url(default="index"):
    return request.args.get("next") or \
           request.referrer or \
           url_for(default)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    logging.getLogger(PROJECTNAME).info(session["firstname"]+" "+session["lastname"]+" logged out")
    session.pop("firstname", None)
    session.pop("lastname", None)
    session.pop("permissions", None)
    return redirect(redirect_url(), code=302)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if ("firstname" in request.form and "lastname" in request.form and "password" in request.form and "password2" in request.form):
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            password = request.form["password"]
            password2 = request.form["password2"]
            userCount = session.query(Fahrer).filter(and_(Fahrer.vorname == firstname, Fahrer.nachname == lastname)).count()
            if (userCount == 0 and password == password2):
                h = hashlib.new("sha256")
                h.update(request.form["password"].encode("utf-8"))
                password = h.hexdigest()
                fahrer = Fahrer(vorname=firstname, nachname=lastname, passwort=password, status=1)
                session.add(fahrer)
                session.commit()
                logging.getLogger(PROJECTNAME).info(firstname+" "+lastname+" registered")
                return redirect(request.url_root, code=302)
            else:
                logging.getLogger(PROJECTNAME).info(firstname+" "+lastname+" tried to register")
                return redirect(request.url_root+"register", code=302)
    html = beginHTML(request)
    html += "\
        <div class='container'>\n\
            <div class='row'>\n\
                <div class='col-xs-4'></div>\n\
                <div class='col-xs-4'>\n\
                    <form action='' method='post'>\n\
                        <div class='form-group'>\n\
                            <label for='firstname'>Vorname</label>\n\
                            <input type='text' class='form-control' id='firstname' name='firstname' placeholder='Vorname'>\n\
                        </div>\n\
                        <div class='form-group'>\n\
                            <label for='lastname'>Nachname</label>\n\
                            <input type='text' class='form-control' id='lastname' name='lastname' placeholder='Nachname'>\n\
                        </div>\n\
                        <div class='form-group'>\n\
                            <label for='password'>Passwort</label>\n\
                            <input type='password' class='form-control' id='password' name='password' placeholder='Passwort'>\n\
                        </div>\n\
                        <div class='form-group'>\n\
                            <label for='passwordRepeat'>Passwort wiederholen</label>\n\
                            <input type='password' class='form-control' id='passwordRepeat' name='password2' placeholder='Passwort'>\n\
                        </div>\n\
                        <button type='submit' class='btn btn-default'>Registrieren</button>\n\
                    </form>\n\
                </div>\n\
                <div class='col-xs-4'></div>\n\
            </div>\n\
        </div>\n"
    html += endHTML(request)
    return html

def beginHTML(request):
    html = "\
<html>\n\
    <head>\n\
        <meta charset='utf-8'>\n\
        <meta http-equiv='X-UA-Compatible' content='IE=edge'>\n\
        <meta name='viewport' content='width=device-width, initial-scale=1'>\n\
        <link href='"+request.url_root+"static/css/bootstrap.min.css' rel='stylesheet'>\n\
        <link href='https://cdn.datatables.net/1.10.13/css/dataTables.bootstrap4.min.css' rel='stylesheet'>\n\
        <style>\n\
            html\n\
            {\n\
                position: relative;\n\
                min-height: 100%;\n\
            }\n\
            body\n\
            {\n\
                font-family: ChampFleuryPro1529,Arial,sans-serif;\n\
                padding-top: 7.5%;\n\
                padding-bottom: 5%;\n\
                margin-bottom: 60px\n\
            }\n\
            .footer {\n\
                position: absolute;\n\
                bottom: 0;\n\
                width: 100%;\n\
                background-color: #f5f5f5;\n\
            }\n\
        </style>\n\
        <title>Taxi Wichelmann</title>\n\
    </head>\n\
    <body>\n\
        <script src='https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js'></script>\n\
        <script src='"+request.url_root+"static/js/bootstrap.min.js'></script>\n\
        <script src='https://cdn.datatables.net/1.10.13/js/jquery.dataTables.min.js'></script>\n\
        <script src='https://cdn.datatables.net/1.10.13/js/dataTables.bootstrap4.min.js'></script>\n"
    html += navBar(request)
    return html

def endHTML(request):
    html = "\
        <footer class='footer'>\n\
            <div class='container'>\n\
                <span class='text-muted'><a href='"+request.url_root+"impressum'>Impressum</a></span>\n\
            </div>\n\
        </footer>\n\
    </body>\n\
</html>\n"
    return html

def navBar(request):
    html = "\
        <nav class='navbar navbar-default navbar-fixed-top'>\n\
            <div class='container'>\n\
                <div class='navbar-header'>\n\
                      <button type='button' class='navbar-toggle collapsed' data-toggle='collapse' data-target='#navbar' aria-expanded='false' aria-controls='navbar'>\n\
                        <span class='sr-only'>Toggle navigation</span>\n\
                        <span class='icon-bar'></span>\n\
                        <span class='icon-bar'></span>\n\
                        <span class='icon-bar'></span>\n\
                    </button>\n\
                    <a class='navbar-brand' href='"+request.url_root+"'>Taxi Wichelmann</a>\n\
                </div>\n\
                <div id='navbar' class='navbar-collapse collapse'>\n\
                    <ul class='nav navbar-nav'>\n\
                        <li><a href='"+request.url_root+"cars'>Autos</a></li>\n\
                        <li><a href='"+request.url_root+"schichtabrechnung'>Schichtabrechnung</a></li>\n\
                        <li class='Tournaments'>\n\
                            <a href='#' class='dropdown-toggle' data-toggle='dropdown' role='button' aria-haspopup='true' aria-expanded='false'>Turniere <span class='caret'></span></a>\n\
                            <ul class='dropdown-menu'>\n"
    html += "\
                            </ul>\n\
                        </li>\n\
                     </ul>\n"
    if (getPermissions() >= 42):
        html += "\
                    <form class='navbar-form navbar-nav' action='"+request.url_root+"createTournament' method='post'>\n\
                        <div class='form-group'>\n\
                            <input type='text' placeholder='Tournament' class='form-control' name='name'>\n\
                        </div>\n\
                        <button type='submit' class='btn btn-success'>Erstellen</button>\n\
                    </form>\n"
    if (getFirstname() == "" and getLastname() == ""):
        html += "\
                    <ul class='nav navbar-right'>\n\
                        <li><a href='"+request.url_root+"register'>Registrieren</a></li>\n\
                    </ul>\n\
                    <form class='navbar-form navbar-right' action='"+request.url_root+"login' method='post'>\n\
                        <div class='form-group'>\n\
                            <input type='text' placeholder='Vorname' class='form-control' name='firstname'>\n\
                        </div>\n\
                        <div class='form-group'>\n\
                            <input type='text' placeholder='Nachname' class='form-control' name='lastname'>\n\
                        </div>\n\
                        <div class='form-group'>\n\
                            <input type='password' placeholder='Passwort' class='form-control' name='password'>\n\
                        </div>\n\
                        <button type='submit' class='btn btn-success'>Anmelden</button>\n\
                    </form>\n"
    else:
        html += "\
                    <ul class='nav navbar-right'>\n\
                        <li><a href='"+request.url_root+"logout'>Abmelden</a></li>\n\
                    </ul>\n"
    html += "\
                </div><!--/.nav-collapse -->\n\
            </div>\n\
        </nav>\n"
    return html

def getPermissions():
    permissions = 0
    if ("permissions" in session):
        permissions = session["permissions"]
    return permissions

def getFirstname():
    firstname = ""
    if ("firstname" in session):
        firstname = session["firstname"]
    return firstname

def getLastname():
    lastname = ""
    if ("lastname" in session):
        lastname = session["lastname"]
    return lastname

@app.route("/", methods=["GET"])
def root():
    html = beginHTML(request)
    html += endHTML(request)
    return html

@app.route("/cars", methods=["GET","POST"])
def cars():
    if (request.method == "POST"):
        if ("nummmer" in request.form and "typ" in request.form and "kennzeichen" in request.form):
            ID = -1
            if ("id" in request.form):
                ID = request.form("id")
            nummer = request.form("nummer")
            typ = request.form("typ")
            kennzeichen = request.form("kennzeichen")
            if (ID == -1):
                auto = Auto(nummer=nummer, typ=typ, kennzeichen=kennzeichen, status=1)
                session.add(auto)
                session.commit()
            else:
                session.query(Auto).filter(Auto.ID == ID).update({"nummer":nummer,"typ":typ,"kennzeichen":kennzeichen})
                session.commit()
    html = beginHTML(request)
    html += "\
        <div class='container'>\n\
            <div class='row'>\n\
                <div class='col-xs-4'></div>\n\
                <div class='col-xs-4'>\n\
                    <script type='text/javascript' class='init'>\n\
                        $(document).ready(function() {\n\
                            $('#table1').DataTable({'order':[[4,'desc']]});\n\
                        } );\n\
                    </script>\n\
                    <table id='table1' class='table table-striped'>\n\
                        <thead>\n\
                            <tr>\n\
                                <th>\n\
                                    Nummer\n\
                                </th>\n\
                                <th>\n\
                                    Typ\n\
                                </th>\n\
                                <th>\n\
                                    Kennzeichen\n\
                                </th>\n\
                                <th>\n\
                                    ID\n\
                                </th>\n\
                            </tr>\n\
                        </thead>\n\
                        <tbody>\n"
    for auto in session.query(Auto).order_by(Auto.id).all():
        kennzeichen = auto.kennzeichen
        nummer = auto.nummer
        typ = auto.typ
        ID = auto.ID
        html += "\
                            <form action='' method='post'>\n\
                                <tr>\n\
                                    <td>\n\
                                        <div class='form-group'>\n\
                                            <input type='text' class='form-control' id='nummmer' name='nummmer' placeholder='Nummer'>\n\
                                        </div>\n\
                                    </td>\n\
                                    <td>\n\
                                        <div class='form-group'>\n\
                                            <select name='typ' id='typ'>\n\
                                                <option value='0'>Taxi</option>\n\
                                                <option value='1'>Limousine</option>\n\
                                            </select>\
                                        </div>\n\
                                    </td>\n\
                                    <td>\n\
                                        <div class='form-group'>\n\
                                            <input type='text' class='form-control' id='kennzeichen' name='kennzeichen' placeholder='Kennzeichen'>\n\
                                        </div>\n\
                                    </td>\n\
                                    <td>\n\
                                        <input type='hidden' name='id' value='"+ID+"'>\n\
                                        <button type='submit' class='btn btn-default'>Ändern</button>\n\
                                    </td>\n\
                                </tr>\n\
                            </form>\n"
    html += "\
                            <form action='' method='post'>\n\
                                <tr>\n\
                                    <td>\n\
                                        <div class='form-group'>\n\
                                            <input type='text' class='form-control' id='nummmer' name='nummmer' placeholder='Nummer'>\n\
                                        </div>\n\
                                    </td>\n\
                                    <td>\n\
                                        <div class='form-group'>\n\
                                            <select name='typ' id='typ'>\n\
                                                <option value='0'>Taxi</option>\n\
                                                <option value='1'>Limousine</option>\n\
                                            </select>\
                                        </div>\n\
                                    </td>\n\
                                    <td>\n\
                                        <div class='form-group'>\n\
                                            <input type='text' class='form-control' id='kennzeichen' name='kennzeichen' placeholder='Kennzeichen'>\n\
                                        </div>\n\
                                    </td>\n\
                                    <td>\n\
                                        <button type='submit' class='btn btn-default'>Hinzufügen</button>\n\
                                    </td>\n\
                                </tr>\n\
                            </form>\n\
                        </tbody>\n\
                    </table>\n\
                </div>\n\
                <div class='col-xs-4'></div>\n\
            </div>\n\
        </div>\n"
    html += endHTML(request)
    return html

@app.route("/impressum", methods=["GET"])
def impressum():
    html = beginHTML(request)
    html += "\
        <div class='container'>\n\
            <div class='row'>\n\
                <div class='col-xs-1'></div>\n\
                <div class='col-xs-10'>\n\
                    <div class='impressum'><h1>Impressum</h1><p>Angaben gemäß § 5 TMG</p><p>Daniel Tkocz <br> \n\
                    Schiffergasse 15<br> \n\
                    65201 Wiesbaden <br> \n\
                    </p><p> <strong>Vertreten durch: </strong><br>\n\
                    Daniel Tkocz<br>\n\
                    </p><p><strong>Kontakt:</strong> <br>\n\
                    Telefon: 0611-609534<br>\n\
                    E-Mail: <a href='mailto:daniel.tkocz42@gmail.com'>daniel.tkocz42@gmail.com</a></br></p><p><strong>Haftungsausschluss: </strong><br><br><strong>Haftung für Inhalte</strong><br><br>\n\
                    Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.<br><br><strong>Haftung für Links</strong><br><br>\n\
                    Unser Angebot enthält Links zu externen Webseiten Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar. Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.<br><br><strong>Urheberrecht</strong><br><br>\n\
                    Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.<br><br><strong>Datenschutz</strong><br><br>\n\
                    Die Nutzung unserer Webseite ist in der Regel ohne Angabe personenbezogener Daten möglich. Soweit auf unseren Seiten personenbezogene Daten (beispielsweise Name, Anschrift oder eMail-Adressen) erhoben werden, erfolgt dies, soweit möglich, stets auf freiwilliger Basis. Diese Daten werden ohne Ihre ausdrückliche Zustimmung nicht an Dritte weitergegeben. <br>\n\
                    Wir weisen darauf hin, dass die Datenübertragung im Internet (z.B. bei der Kommunikation per E-Mail) Sicherheitslücken aufweisen kann. Ein lückenloser Schutz der Daten vor dem Zugriff durch Dritte ist nicht möglich. <br>\n\
                    Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten durch Dritte zur Übersendung von nicht ausdrücklich angeforderter Werbung und Informationsmaterialien wird hiermit ausdrücklich widersprochen. Die Betreiber der Seiten behalten sich ausdrücklich rechtliche Schritte im Falle der unverlangten Zusendung von Werbeinformationen, etwa durch Spam-Mails, vor.<br>\n\
                    </p><br> \n\
                    Website Impressum erstellt durch <a href='http://www.impressum-generator.de'>impressum-generator.de</a> von der <a href='http://www.kanzlei-hasselbach.de/standorte/koeln-rodenkirchen'>Kanzlei Hasselbach, Köln-Rodenkirchen</a> </div>\n\
                </div>\n\
                <div class='col-xs-1'></div>\n\
            </div>\n\
        </div>\n"
    html += endHTML(request)
    return html

if __name__ == "__main__":
    app.config["SECRET_KEY"] = "BlaBlub42"
    run_simple(host, port, app, use_reloader=True)
    #CGIHandler().run(app)
    #WSGIServer(app).run()