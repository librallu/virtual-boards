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
#    columns = db.relationship('Column', backref='board')
    
    def __repr__(self):
        return '<Board {}>'.format(self.name)

class BoardsContent(db.Model):
    """Represents a board-column interaction"""
    __tablename__ = 'boardsContent'
    id = db.Column(db.Integer, primary_key=True)
    board = db.Column(db.Integer, db.ForeignKey('boards.id'))
    column = db.Column(db.Integer, db.ForeignKey('columns.id'))

class ColumnsContent(db.Model):
    """Represents a column-note interaction"""
    ___tablename__ = 'columnsContent'
    id = db.Column(db.Integer, primary_key=True)
    column = db.Column(db.Integer, db.ForeignKey('columns.id'))
    note = db.Column(db.Integer, db.ForeignKey('notes.id'))

class Column(db.Model):
    """Represents a column object.
    """
    __tablename__ = 'columns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
#    notes = db.relationship('Note', backref='column')
#    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
    
    def __repr__(self):
        return '<Col {}>'.format(self.name)
    

class Note(db.Model):
    """represents a Note object. It can contain text
    """
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
#    column_id = db.Column(db.Integer, db.ForeignKey('columns.id'))
    text = db.Column(db.Text)
    
    def __repr__(self):
        return '<Note {}>'.format(self.name)



class BoardsEP(Resource):
    
    @staticmethod
    def to_json():
        """
        :return: dict object representing a column in json.
        """
        boards = Board.query.all()
        columns = Column.query.all()
        notes = Note.query.all()
        boards_content = [{
            'column': i.column,
            'board': i.board
        } for i in BoardsContent.query.all() ]
        columns_content = [{
            'note': i.note,
            'column': i.column
        } for i in ColumnsContent.query.all() ]
        
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
            'boards-content': boards_content,
            'columns-content': columns_content,
        }
    
    @staticmethod
    def get():
        request_type = request.args.get('type', '')
        if request_type == 'json':
            return jsonify(BoardsEP.to_json())
        else:
            return make_response("hello")
    
    @staticmethod
    def delete():
        args = request.form
        id = args.get('id', '')
        if id:
            board_obj = Board.query.filter_by(id=id).first()
            if board_obj:
                # delete board relations if needed
                board_content = BoardsContent.query.filter_by(board=id)
                for content in board_content:
                    BoardsContentEP.delete_call(id, content.column)
                
                # delete board object
                db.session.delete(board_obj)

                db.session.commit()
                return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
            else:
                return {'code': 400, 'description': 'No resource found', 'asked': id}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'id'}
        
    @staticmethod
    def post_method():
        args = request.form
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
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'name'}

    @staticmethod
    def put():
        args = request.form
        id = args.get('id', '')
        if id:
            board_obj = Board.query.filter_by(id=id).first()
            if not board_obj:
                return {'code': 400, 'description': 'No resource found', 'asked': id}
            
            name = args.get('name', '')
            if name:
                board_obj.name = name
            else:
                return {'code': 304, 'description': 'not modified'}
            db.session.add(board_obj)
            db.session.commit()
            return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'id'}
        
    @staticmethod
    def post():
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return BoardsEP.delete()
        elif request_type == 'put':
            return BoardsEP.put()
        else:  # post request
            return BoardsEP.post_method()


        
class ColumnsEP(Resource):
    
    @staticmethod
    def post_method():
        args = request.form
        name = args.get('name', '')
        if name:
            col_obj = Column(name=name)
            db.session.add(col_obj)
            db.session.commit()
            return {'code': 201, 'description': 'created'}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'name'}
    
    @staticmethod
    def delete():
        args = request.form
        id = args.get('id', '')
        if id:
            col_obj = Column.query.filter_by(id=id).first()
            if col_obj:
                
                # delete board content if needed
                board_content = BoardsContent.query.filter_by(column=id)
                for content in board_content:
                    BoardsContentEP.delete_call(content.board, id)
                
                # delete column content if needed
                column_content = ColumnsContent.query.filter_by(column=id)
                for content in column_content:
                    ColumnsContentEP.delete_call(id, content.note)
                
                db.session.delete(col_obj)
                
                db.session.commit()
                return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
            else:
                return {'code': 400, 'description': 'No resource found', 'asked': id}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'id'}

    @staticmethod
    def put():
        args = request.form
        id = args.get('id', '')
        if id:
            col_obj = Column.query.filter_by(id=id).first()
            if not col_obj:
                return {'code': 400, 'description': 'No resource found', 'asked': id}
            
            name = args.get('name', '')
            if name:
                col_obj.name = name
            else:
                return {'code': 304, 'description': 'not modified'}
            db.session.add(col_obj)
            db.session.commit()
            return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'id'}
    
    @staticmethod
    def post():
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return ColumnsEP.delete()
        elif request_type == 'put':
            return ColumnsEP.put()
        else:
            return ColumnsEP.post_method()

        
class NotesEP(Resource):
    
    @staticmethod
    def post_method():
        args = request.form
        name = args.get('name', '')
        if name:
            text = args.get('text', '')  # get the note text
            note_obj = Note(name=name, text=text)
            db.session.add(note_obj)
            db.session.commit()
            return {'code': 201, 'description': 'created'}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'name'}
    
    @staticmethod
    def delete():
        args = request.form
        id = args.get('id', '')
        if id:
            note_obj = Note.query.filter_by(id=id).first()
            if note_obj:
                db.session.delete(note_obj)
                # delete column relations if needed
                # TODO
                
                db.session.commit()
                return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
            else:
                return {'code': 400, 'description': 'No resource found', 'asked': id}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'id'}

    @staticmethod
    def put():
        args = request.form
        id = args.get('id', '')
        if id:
            note_obj = Note.query.filter_by(id=id).first()
            if not note_obj:
                return {'code': 400, 'description': 'No resource found', 'asked': id}
            
            name = args.get('name', '')
            text = args.get('text', '')
            modified = False
            if name:
                note_obj.name = name
                modified = True
            if text:
                note_obj.text = text
                modified = True
            if not modified:
                return {'code': 304, 'description': 'not modified'}
            db.session.add(note_obj)
            db.session.commit()
            return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
        else:
            return {'code': 400, 'description': 'some fields are missing', 'missing': 'id'}
    
    @staticmethod
    def post():
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return NotesEP.delete()
        elif request_type == 'put':
            return NotesEP.put()
        else:
            return NotesEP.post_method()


class BoardsContentEP(Resource):
    
    @staticmethod
    def delete_call(board, column):
        if board and column:
            # check if board or column corresponds to correct id
            if not Board.query.filter_by(id=board).first():
                return {'code': 400, 'description': 'board with id {} does not exist'.format(board)}
            if not Column.query.filter_by(id=column).first():
                return {'code': 400, 'description': 'column with id {} does not exist'.format(column)}
            
            content_obj = BoardsContent.query.filter_by(board=board, column=column).first()
            db.session.delete(content_obj)
            db.session.commit()
            return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
        else:
            missing = []
            if not board:
                missing.append('board')
            if not column:
                missing.append('column')
            return {'code': 400, 'description': 'some fields are missing', 'missing': ', '.join(missing)}
    
    @staticmethod
    def delete():
        args = request.form
        board = args.get('board', '')
        column = args.get('column', '')
        return BoardsContentEP.delete_call(board, column)
    
    @staticmethod
    def post_method():
        args = request.form
        board = args.get('board', '')
        column = args.get('column', '')
        if board and column:
            # check if board or column corresponds to correct id
            if not Board.query.filter_by(id=board).first():
                return {'code': 400, 'description': 'board with id {} does not exist'.format(board)}
            if not Column.query.filter_by(id=column).first():
                return {'code': 400, 'description': 'column with id {} does not exist'.format(column)}
            
            if BoardsContent.query.filter_by(board=board, column=column).first():
                return {'code': 400, 'description': 'relationship already exists between board {} and column {}'.format(board, column)}
            content_obj = BoardsContent(board=board, column=column)
            db.session.add(content_obj)
            db.session.commit()
            return {'code': 201, 'description': 'created'}
        else:
            missing = []
            if not board:
                missing.append('board')
            if not column:
                missing.append('column')
            return {'code': 400, 'description': 'some fields are missing', 'missing': ', '.join(missing)}
    
    @staticmethod
    def post():
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return BoardsContentEP.delete()
        else:
            return BoardsContentEP.post_method()


class ColumnsContentEP(Resource):
    
    @staticmethod
    def delete_call(column, note):
        if note and column:
            # check if note or column corresponds to correct id
            if not Note.query.filter_by(id=note).first():
                return {'code': 400, 'description': 'note with id {} does not exist'.format(note)}
            if not Column.query.filter_by(id=column).first():
                return {'code': 400, 'description': 'column with id {} does not exist'.format(column)}
            
            content_obj = ColumnsContent.query.filter_by(note=note, column=column).first()
            db.session.delete(content_obj)
            db.session.commit()
            return {'code': 204, 'description': 'No content: The request was processed successfully, but no response body is needed.'}
        else:
            missing = []
            if not note:
                missing.append('note')
            if not column:
                missing.append('column')
            return {'code': 400, 'description': 'some fields are missing', 'missing': ', '.join(missing)}
        
    @staticmethod
    def delete():
        args = request.form
        column = args.get('column', '')
        note = args.get('note', '')
        return ColumnsContentEP.delete_call(column, note)

    
    @staticmethod
    def post_method():
        args = request.form
        note = args.get('note', '')
        column = args.get('column', '')
        if note and column:
            # check if note or column corresponds to correct id
            if not Note.query.filter_by(id=note).first():
                return {'code': 400, 'description': 'note with id {} does not exist'.format(note)}
            if not Column.query.filter_by(id=column).first():
                return {'code': 400, 'description': 'column with id {} does not exist'.format(column)}
            
            if ColumnsContent.query.filter_by(note=note, column=column).first():
                return {'code': 400, 'description': 'relationship already exists between note {} and column {}'.format(note, column)}
            content_obj = ColumnsContent(note=note, column=column)
            db.session.add(content_obj)
            db.session.commit()
            return {'code': 201, 'description': 'created'}
        else:
            missing = []
            if not note:
                missing.append('note')
            if not column:
                missing.append('column')
            return {'code': 400, 'description': 'some fields are missing', 'missing': ', '.join(missing)}
    
    @staticmethod
    def post():
        args = request.form
        request_type = args.get('request-type', '')
        if request_type == 'delete':
            return ColumnsContentEP.delete()
        else:
            return ColumnsContentEP.post_method()
        
        
api.add_resource(BoardsEP, '/v1/boards/')
api.add_resource(ColumnsEP, '/v1/columns/')
api.add_resource(NotesEP, '/v1/notes/')
api.add_resource(BoardsContentEP, '/v1/boards-content/')
api.add_resource(ColumnsContentEP, '/v1/columns-content/')


@app.errorhandler(404)
def handler_404(e):
    return render_template('404.html'), 404


def make_shell_context():
    return dict(app=app, db=db, Board=Board, Column=Column, Note=Note)
manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()
    
