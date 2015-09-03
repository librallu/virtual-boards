# coding: utf-8

from flask import Flask, request, current_app, make_response, abort, render_template, jsonify, redirect
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
        :return: all the database at json format
        """
        boards = Board.query.all()
        return {
            'boards': [BoardREST.to_json(i) for i in boards]   
        }
    
    @staticmethod
    def get():
        """
        get the database content
        """
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(AllREST.to_json())
        else:
            boards = Board.query.all()
            return make_response(render_template('index.html', boards=boards))
    
    @staticmethod
    def post_operation():
        """
        Create a new board
        """
        args = parser.parse_args()
        board_obj = Board(name=args['name'])
        db.session.add(board_obj)
        db.session.commit()
        return AllREST.get()
        
    @staticmethod
    def post():
        return AllREST.post_operation()


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
        
    @staticmethod
    def get(board_id):
        board = Board.query.get_or_404(board_id)
        columns = Column.query.filter_by(board=board)
        
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(BoardREST.to_json(board, columns))
        else:  # HTML view
            return make_response(render_template('board.html', board=board, columns=columns))

    @staticmethod
    def post_operation(board_id):
        board = Board.query.get_or_404(board_id)
        args = parser.parse_args()
        col_obj = Column(name=args['name'], board_id=board_id)
        db.session.add(col_obj)
        db.session.commit()
        return BoardREST.get(board_id)
    
    @staticmethod
    def post(board_id):
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return BoardREST.delete(board_id)
        if request_type == 'put':
            return BoardREST.put(board_id)
        else:
            return BoardREST.post_operation(board_id)

    @staticmethod
    def put(board_id):
        board_obj = Board.query.get_or_404(board_id)
        args = request.form
        if 'name' in args and args['name']:
            board_obj.name = args['name']
        db.session.add(board_obj)
        db.session.commit()
        return BoardREST.get(board_id)
#        args = parser.parse_args()
#        board_object = Board.query.get_or_404(board_id)
#        board_object.name = args['name']
#        board_object.columns = args['columns']
#        db.session.add(board_object)
#        db.session.commit()
#        return BoardREST.to_json(board_object), 201

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
        
        # return main page
        return AllREST.get()

        
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
    
    @staticmethod
    def get(board_id, column_id):
        board_object = Board.query.get_or_404(board_id)
        column_object = Column.query.get_or_404(column_id)
        
        # if column not in board: raise 404
        if column_object not in Column.query.filter_by(board=board_object):
            abort(404)
        
        notes = Note.query.filter_by(column=column_object)
        
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(ColumnREST.to_json(column_object, notes))
        else:  # HTML view
            return make_response(render_template('column.html', board=board_object, column=column_object, notes=notes))

    @staticmethod
    def post_operation(board_id, column_id):
        board_object = Board.query.get_or_404(board_id)
        column_object = Column.query.get_or_404(column_id)
        args = parser.parse_args()
        note_obj = Note(name=args['name'], column_id=column_id, text=args['text'])
        db.session.add(note_obj)
        db.session.commit()
        return ColumnREST.get(board_id, column_id)
        
    @staticmethod
    def post(board_id, column_id):
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return ColumnREST.delete(board_id, column_id)
        elif request_type == 'put':
            return ColumnREST.put(board_id, column_id)
        else:
            return ColumnREST.post_operation(board_id, column_id)
    
    @staticmethod
    def put(board_id, col_id):
        args = request.form
        column_object = Column.query.get_or_404(col_id)
        if 'name' in args and args['name']:
            column_object.name = args['name']
        if 'board_id' in args and args['board_id']:
            column_object.board_id = int(args['board_id'])
        db.session.add(column_object)
        db.session.commit()
#        if 'board_id' in args and int(args['board_id']):
        return redirect("/{}/{}/".format(column_object.board_id, col_id))
#        return ColumnREST.get(board_id, col_id)

    @staticmethod
    def delete(board_id, col_id):
        # get column object
        column_object = Column.query.get_or_404(col_id)
        
        # delete notes in column
        notes = Note.query.filter_by(column=column_object)
        for note in notes:
            db.session.delete(note)
        
        # delete column
        db.session.delete(column_object)
        
        db.session.commit()
        
        return BoardREST.get(board_id)

    
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
    
    @staticmethod
    def get(board_id, column_id, note_id):
        board_object = Board.query.get_or_404(board_id)
        column_object = Column.query.get_or_404(column_id)
        note_object = Note.query.get_or_404(note_id)
        
        # if hierarchy inconsitent
        if column_object not in Column.query.filter_by(board=board_object):
            abort(404)
        if note_object not in Note.query.filter_by(column=column_object):
            abort(404)

        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(NoteREST.to_json(note_object))
        else:
            return make_response(render_template('note.html', board=board_object, column=column_object, note=note_object))
    
    @staticmethod
    def post(board_id, column_id, note_id):
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return NoteREST.delete(board_id, column_id, note_id)
        else:
            return NoteREST.put(board_id, column_id, note_id)
    
    @staticmethod
    def put(board_id, column_id, note_id):
        """
        modify a note by changing its name, text and column
        """
        args = request.form
        note_obj = Note.query.get_or_404(note_id)
        if 'name' in args and args['name']:
            note_obj.name = args['name']
        if 'text' in args and args['text']:
            note_obj.text = args['text']
        if 'column_id' in args and args['column_id']:
            note_obj.column_id = int(args['column_id'])
        db.session.add(note_obj)
        db.session.commit()
        return redirect("/{}/{}/{}/".format(board_id, note_obj.column_id, note_id))
#        return NoteREST.get(board_id, column_id, note_obj)
    
    @staticmethod
    def delete(board_id, column_id, note_id):
        note_obj = Note.query.get_or_404(note_id)
        db.session.delete(note_obj)
        db.session.commit()
        return ColumnREST.get(board_id, column_id)
        

class BoardsEP(Resource):
    
    @staticmethod
    def to_json():
        """
        :return: dict object representing a column in json.
        """
        boards = Board.query.all()
        columns = Column.query.all()
        notes = Note.query.all()
        board_interactions = [{
            'column': i.id,
            'board': i.board_id
        } for i in columns ]
        column_interactions = [{
            'note': i.id,
            'column': i.column_id
        } for i in notes ]
        
        return {
            'boards': [{
                        'id': i.id,
                        'name': i.name
                    } for i in boards ],
            'columns': [{
                        'id': i.id,
                        'name': i.name
                    } for i in columns ],
            'notes': [{
                        'id': i.id,
                        'name': i.name,
                        'text': i.text
                } for i in notes ],
            'board-interactions': board_interactions,
            'column-interactions': column_interactions,
        }
    
    @staticmethod
    def get():
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(BoardsEP.to_json())
        else:
            return make_response("hello")
    
    @staticmethod
    def post():
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            pass
        elif request_type == 'put':
            pass
        else:  # post request
            args = parser.parse_args()
            name = args.get('name', '')
            if name:
                # check if there is no board with this name
                if Board.query.filter_by(name=name).first():
                    return {'code': 400, 'description': 'name already exists'}
                
                board_obj = Board(name=name)
                db.session.add(board_obj)
                db.session.commit()
                return {'code': 201, 'description': 'created'}
            else:
                return {'code': 400, 'description': 'some fields are missing'}

        
api.add_resource(BoardsEP, '/v1/boards/')
#api.add_resource(AllREST, '/')
#api.add_resource(BoardREST, '/<board_id>/')
#api.add_resource(ColumnREST, '/<board_id>/<column_id>/')
#api.add_resource(NoteREST, '/<board_id>/<column_id>/<note_id>/')


@app.errorhandler(404)
def handler_404(e):
    return render_template('404.html'), 404


def make_shell_context():
    return dict(app=app, db=db, Board=Board, Column=Column, Note=Note)
manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()
    
