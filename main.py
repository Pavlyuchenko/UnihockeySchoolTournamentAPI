from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
cors = CORS(app)


class Tym(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    hraci = db.relationship('Hrac', backref='Tym', lazy=True, cascade="all, delete-orphan")

    nazev = db.Column(db.String(12), nullable=False)
    potvrzeno = db.Column(db.Boolean, nullable=False, default=False)
    zaplaceno = db.Column(db.Boolean, nullable=False, default=False)
    time_created = db.Column(db.DateTime, default=datetime.utcnow)

    played_matches = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    loses = db.Column(db.Integer, default=0)
    goals_shot = db.Column(db.Integer, default=0)
    goals_got = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)

    domaci = db.relationship('Zapas', backref='Domaci', lazy='dynamic', cascade="all, delete-orphan", foreign_keys='Zapas.domaci')
    hoste = db.relationship('Zapas', backref='Hoste', lazy='dynamic', cascade="all, delete-orphan", foreign_keys='Zapas.hoste')

    def __repr__(self):
        return '<Tým %r, %r>' % (self.nazev, self.zaplaceno)  # self.group_id

    def jsonify(self):
        hraci = Hrac.query.filter_by(tym_id=self.id)
        hraci_arr = []

        for hrac in hraci:
            hraci_arr.append({'jmeno': hrac.jmeno, 'trida': hrac.trida})

        return {
            "id": self.id,
            "nazev": self.nazev,
            "potvrzeno": self.potvrzeno,
            "zaplaceno": self.zaplaceno,
            "hraci": hraci_arr
        }


class Hrac(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    tym_id = db.Column(db.Integer, db.ForeignKey('tym.id'), nullable=False)

    jmeno = db.Column(db.String(200), nullable=False)
    trida = db.Column(db.String(5), nullable=False)


class Zapas(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    domaci = db.Column(db.Integer, db.ForeignKey('tym.id'))
    hoste = db.Column(db.Integer, db.ForeignKey('tym.id'))

    order = db.Column(db.Integer)

    def jsonify(self):
        return {
            'id': self.id,
            'domaci': self.Domaci.nazev,
            'hoste': self.Hoste.nazev,
            'order': self.order
        }


class Statistika(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    navstevnici = db.Column(db.Integer, nullable=False)


@app.route('/main', methods=['GET', 'POST'])
@cross_origin()
def main():

    domaci = Tym.query.filter_by(id=1).first()
    hoste = Tym.query.filter_by(id=2).first()

    zapas = Zapas(domaci=domaci.id, hoste=hoste.id, order=10)
    db.session.add(zapas)
    db.session.commit()

    zapasy = Zapas.query.order_by(Zapas.order)
    res = []
    count = 0

    for i in zapasy:
        count += 1
        res.append(i.jsonify())
        if count == 5:
            break

    return jsonify({'zapasy': res})


@app.route('/register', methods=['GET', 'POST'])
@cross_origin()
def register():
    json = request.json

    ''' Deletes everything
    db.session.query(Tym).delete()
    db.session.commit()'''
    tym = Tym(nazev=json['nazevTymu'], potvrzeno=False, zaplaceno=False)
    db.session.add(tym)
    db.session.commit()

    for i in json['hraci']:
        if i['jmeno']:
            hrac = Hrac(tym_id=tym.id, jmeno=i['jmeno'], trida=i['trida'])
            db.session.add(hrac)
    db.session.commit()

    return jsonify({'hello': 'react is kinda great'})


@app.route('/update_potvrzeno', methods=['GET', 'POST'])
@cross_origin()
def update_potvrzeno():
    json = request.json

    tym = Tym.query.filter_by(id=json['idTymu']).first()
    tym.potvrzeno = True
    db.session.commit()

    return jsonify({'hello': 'react is kinda great'})


@app.route('/zaplaceni_potvrzeno', methods=['GET', 'POST'])
@cross_origin()
def zaplaceni_potvrzeno():
    json = request.json

    tym = Tym.query.filter_by(id=json['idTymu']).first()
    tym.zaplaceno = not tym.zaplaceno
    db.session.commit()

    return jsonify({'hello': 'react is kinda great'})


@app.route('/delete_tym', methods=['GET', 'POST'])
@cross_origin()
def delete_tym():
    json = request.json

    tym = Tym.query.filter_by(id=json['idTymu']).first()
    db.session.delete(tym)
    db.session.commit()

    return jsonify({'hello': 'react is kinda great'})


@app.route('/admin', methods=['GET', 'POST'])
@cross_origin()
def admin():

    tymy = Tym.query.order_by(Tym.zaplaceno).order_by(Tym.nazev)

    print(tymy)

    result = []

    for i in tymy:
        result.append(i.jsonify())

    ''' Reset potvrzeno 
    tymy = Tym.query.all()

    for i in tymy:
        i.potvrzeno = False
    db.session.commit()'''

    reg_tymy = db.session.query(Tym).count()

    if db.session.query(Statistika).count() == 0:
        statistika = Statistika(navstevnici=0)
        db.session.add(statistika)
        db.session.commit()
        navstiveno = "initialized"
    else:
        navstiveno = Statistika.query.first().navstevnici

    return jsonify({'tymy': result, 'registrovane_tymy': reg_tymy, 'navstiveno': navstiveno})


@app.route('/statistika', methods=['GET', 'POST'])
@cross_origin()
def statistika():
    json = request.json

    if json['navstevnik']:
        statistika = Statistika.query.first()
        statistika.navstevnici += 1
        db.session.commit()

    return '200'


@app.route('/choose_team', methods=['GET', 'POST'])
@cross_origin()
def choose_team():

    tymy = Tym.query.order_by(Tym.zaplaceno).order_by(Tym.nazev)

    result = []

    for i in tymy:
        result.append(i.jsonify())

    return jsonify({'tymy': result})


if __name__ == '__main__':
    app.run()
