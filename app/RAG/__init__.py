from flask import Blueprint
import redis 

RAG_bp = Blueprint('RAG',__name__)

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

from . import routes