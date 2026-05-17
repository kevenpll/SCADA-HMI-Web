from flask import Blueprint, jsonify, make_response
from services.logger import sys_logger

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    sys_logger.warning(f"404 Erro: Endpoint não encontrado.")
    return make_response(jsonify({'error': 'Endpoint ou página não encontrada', 'code': 404}), 404)

@errors_bp.app_errorhandler(500)
def internal_error(error):
    sys_logger.error(f"500 Erro Interno do Servidor: {str(error)}")
    return make_response(jsonify({'error': 'Erro interno do servidor', 'code': 500}), 500)
