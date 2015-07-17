# coding: utf-8

from flask import Flask, request, current_app, make_response, abort, render_template, jsonify
from flask.ext.script import Manager, Shell
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask_restful import Resource, Api, reqparse, abort
import os

# FLASK RESTFUL API conf
parser = reqparse.RequestParser()
parser.add_argument('name', type=str)
parser.add_argument('text', type=str)

app = Flask(__name__, static_path='/static/')

# for SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)

manager = Manager(app)

api = Api(app, catch_all_404s=True)

# database migration 
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

class Board(db.Model):
    """Represents a Board object
    """
    __tablename__ = 'boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    columns = db.relationship('Column', backref='board')
    
    def __repr__(self):
        return '<Board {}>'.format(self.name)


class Column(db.Model):
    """Represents a column object.
    """
    __tablename__ = 'columns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    notes = db.relationship('Note', backref='column')
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
    
    def __repr__(self):
        return '<Col {}>'.format(self.name)
    

class Note(db.Model):
    """represents a Note object. It can contain text
    """
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    column_id = db.Column(db.Integer, db.ForeignKey('columns.id'))
    text = db.Column(db.Text)
    
    def __repr__(self):
        return '<Note {}>'.format(self.name)

def extra_info():
    user_agent = request.headers.get('User-Agent')
    app_name = current_app.name
    res = make_response("""
    <p>
        <h2>App name: {}</h2>
        <ul>
            <li>user-agent: {}</li>
        </ul>
    </p>
    """.format(app_name, user_agent))
    return res


class AllREST(Resource):
    
    @staticmethod
    def to_json():
        """
        :return: all the database
        """
        boards = Board.query.all()
        return {
            'boards': [BoardREST.to_json(i) for i in boards]   
        }
    
    def get(self):
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(self.to_json())
        else:
            boards = Board.query.all()
            return make_response(render_template('index.html', boards=boards))
        
    
    def post(self):
        args = parser.parse_args()
        board_obj = Board(name=args['name'])
        db.session.add(board_obj)
        db.session.commit()
        return BoardREST.to_json(board_obj), 201
        


class BoardREST(Resource):
    
    @staticmethod
    def to_json(board, columns=None):
        """
        :return: dict object representing a board in json.
        """
        # if not provided, find it in the database
        if columns is None:
            columns = Column.query.filter_by(board=board)
            
        return {
            'name': board.name,
            'id': board.id,
            'columns': [ColumnREST.to_json(i) for i in columns]
        }
        
    def get(self, board):
        board_object = Board.query.get_or_404(board)
        columns = Column.query.filter_by(board=board_object)
        
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(self.to_json(board_object, columns))
        else:  # HTML view
            return make_response(render_template('board.html', board=board_object, columns=columns))

    def post(self, board):
        board_object = Board.query.get_or_404(board)
        args = parser.parse_args()
        col_obj = Column(name=args['name'], board_id=board)
        db.session.add(col_obj)
        db.session.commit()
        return ColumnREST.to_json(col_obj), 201

    def put(self, board_id):
        args = parser.parse_args()
        board_object = Board.query.get_or_404(board_id)
        board_object.name = args['name']
        board_object.columns = args['columns']
        db.session.add(board_object)
        db.session.commit()
        return BoardREST.to_json(board_object), 201

    @staticmethod
    def delete(board_id):
        # get column object
        board_object = Board.query.get_or_404(board_id)
        
        # delete notes in column
        cols = Column.query.filter_by(board=board_object)
        for col in cols:
            db.session.delete(col)
        
        # delete column
        db.session.delete(board_object)
        
        db.session.commit()

        
class ColumnREST(Resource):
    
    @staticmethod
    def to_json(column, notes=None):
        """
        :return: dict object representing a column in json.
        """
        # if not provided, find it in the database
        if notes is None:
            notes = Note.query.filter_by(column=column)
        
        return {
            'name': column.name,
            'id': column.id,
            'notes': [NoteREST.to_json(i) for i in notes]
        }
    
    def get(self, board, column):
        board_object = Board.query.get_or_404(board)
        column_object = Column.query.get_or_404(column)
        notes = Note.query.filter_by(column=column_object)
        
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(self.to_json(column_object, notes))
        else:  # HTML view
            return make_response(render_template('column.html', board=board_object, column=column_object, notes=notes))

    def post(self, board, column):
        board_object = Board.query.get_or_404(board)
        column_object = Column.query.get_or_404(column)
        args = parser.parse_args()
        note_obj = Note(name=args['name'], column_id=column, text=args['text'])
        db.session.add(note_obj)
        db.session.commit()
        return NoteREST.to_json(note_obj), 201
    
    def put(self, col_id):
        args = parser.parse_args()
        column_object = Column.query.get_or_404(col_id)
        column_object.name = args['name']
        column_object.notes = args['notes']
        column_object.board_id = args['board_id']
        db.session.add(column_object)
        db.session.commit()
        return ColumnREST.to_json(column_object), 201

    @staticmethod
    def delete(col_id):
        # get column object
        column_object = Column.query.get_or_404(column)
        
        # delete notes in column
        notes = Note.query.filter_by(column=column_object)
        for note in notes:
            db.session.delete(note)
        
        # delete column
        db.session.delete(column_object)
        
        db.session.commit()

    
class NoteREST(Resource):
    
    @staticmethod
    def to_json(note):
        """
        :return: dict object representing a column in json.
        """
        return {
            'name': note.name,
            'id': note.id,
            'text': note.text
        }
    
    def get(self, board, column, note):
        board_object = Board.query.get_or_404(board)
        column_object = Column.query.get_or_404(column)
        note_object = Note.query.get_or_404(note)

        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(self.to_json(note_object))
        else:
            return make_response(render_template('note.html', board=board_object, column=column_object, note=note_object))
    
    def put(self, note_id):
        """
        modify a note by changing its name, text and column
        """
        args = parser.parse_args()
        note_obj = Note.query.get_or_404(note_id)
        note_obj.name = args['name']
        note_obj.text = args['text']
        note_obj.column_id = args['column']
        db.session.add(note_obj)
        db.session.commit()
        return NoteREST.to_json(note_obj), 201
    
    @staticmethod
    def delete(note_id):
        note_obj = Note.query.get_or_404(note_id)
        db.session.delete(note_obj)
        db.session.commit()
        return '', 204
        
    
api.add_resource(AllREST, '/')
api.add_resource(BoardREST, '/<board>/')
api.add_resource(ColumnREST, '/<board>/<column>/')
api.add_resource(NoteREST, '/<board>/<column>/<note>/')


@app.errorhandler(404)
def handler_404(e):
    return render_template('404.html'), 404


def make_shell_context():
    return dict(app=app, db=db, Board=Board, Column=Column, Note=Note)
manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()
    
