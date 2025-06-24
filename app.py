from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from user.user import User
from bot.agent import AIBot
from bot.imoveis_search import Imoveis
from unidecode import unidecode
import re
import os
from decouple import config

import smtplib
from email.mime.text import MIMEText


import json

# def str_para_dict(texto):
#     try:
#         return json.loads(texto)
#     except json.JSONDecodeError:
#         # Corrige aspas simples por aspas duplas, se necessário
#         texto_corrigido = texto.replace("'", '"')
#         return json.loads(texto_corrigido)

import json
from typing import Union, Dict, Any

def parse_properties(options):
    properties = []
    for option in options:
        lines = option.split('\n')
        prop = {
            'image_url': next((line for line in lines if line.startswith('http')), None),
            'details': '\n'.join(line for line in lines if not line.startswith('http') and line != '------------------------------------')
        }
        if prop['image_url']:
            properties.append(prop)
    return properties

def str_para_dict(texto: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(texto, dict):
        return texto
    
    if not texto or not isinstance(texto, str):
        return {}
    
    # Primeiro, tenta fazer o parse diretamente
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass  # Vamos tentar corrigir
    
    # Remove marcadores de código (```json e ```) e texto após o JSON
    texto_limpo = re.sub(r'^```(json)?|```$', '', texto.strip(), flags=re.MULTILINE)
    texto_limpo = texto_limpo.strip()
    
    # Tenta extrair apenas a parte JSON da string
    try:
        # Padrão que captura desde a primeira { até a última }
        match = re.search(r'(\{.*\})', texto_limpo, re.DOTALL)
        if match:
            json_str = match.group(1)
            
            # Etapa crucial: preservar quebras de linha em strings sem quebrar a estrutura JSON
            # 1. Primeiro protege as strings com quebras de linha
            def proteger_strings(match):
                content = match.group(1)
                # Escapa quebras de linha apenas dentro das strings
                content = content.replace('\n', '\\n').replace('\r', '\\r')
                return f'"{content}"'
            
            # Aplica apenas nas strings (entre aspas)
            json_protegido = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', proteger_strings, json_str, flags=re.DOTALL)
            
            # Aplica as correções padrão
            json_corrigido = (
                json_protegido
                .replace("'", '"')
                .replace("None", "null")
                .replace("True", "true")
                .replace("False", "false")
            )
            
            # Remove vírgulas traiçoeiras
            json_corrigido = re.sub(r',\s*([}\]])', r'\1', json_corrigido)
            json_corrigido = re.sub(r',\s*}(?=\s*$)', '}', json_corrigido)
            
            # Verificação final para garantir que é um JSON válido
            try:
                return json.loads(json_corrigido)
            except json.JSONDecodeError as e:
                print(f"Falha na conversão após todas as correções: {e}")
                print(f"Texto sendo processado: {json_corrigido}")
                return {}
        return {}
    
    except Exception as e:
        print(f"Erro inesperado ao converter string: {e}")
        return {}


app = Flask(__name__, static_folder='static')
print('Started LandBase API')

# Carrega usuários (se necessário)
users = User.file_to_object() if hasattr(User, 'file_to_object') else []

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'home.html')

@app.route('/api/chat', methods=['POST'])
def chat_webhook():
    print("Chat endpoint called")
    data = request.json
    #print(f"DATA: {data}")
    
    # Dados básicos do front-end
    user_id = data.get('user_id', 'web_user')
    message = data.get('message', '')
    timestamp = datetime.now().isoformat()

    # Inicializa serviços
    bot = AIBot()
    imoveis = Imoveis()

    # Obtém o histórico da sessão ou cria um novo
    session_history = data.get('history', [])
    
    # Adiciona a nova mensagem do usuário ao histórico
    session_history.append({
        'role': 'user',
        'content': message,
        'timestamp': timestamp
    })
    #print(f"SESSION HISTORY {session_history}")

    # Obtém resposta da IA
# try:
    # Prepara o histórico no formato esperado pela IA
    ai_history = [{'role': msg['role'], 'content': msg['content']} for msg in session_history]
    #print(f"AI HISTORY {ai_history}")
    resposta_ia = bot.invoke1(ai_history, message)
    
    # Adiciona a resposta da IA ao histórico
    session_history.append({
        'role': 'assistant',
        'content': resposta_ia,
        'timestamp': datetime.now().isoformat()
    })
        
    # except Exception as e:
    #     print(f"Error in AI response: {e}")
    #     resposta_ia = "Desculpe, ocorreu um erro ao processar sua solicitação."
    #     session_history.append({
    #         'role': 'you',
    #         'content': resposta_ia,
    #         'timestamp': datetime.now().isoformat()
    #     })
    try:
        # Tenta converter a string para dicionário
        user_dict = str_para_dict(resposta_ia)
    except Exception as e:
        print(f"Erro ao converter string para dicionário: {e}")
        
        # Tentativa alternativa: remover acentos antes da conversão
        try:
            resposta_sem_acentos = unidecode(resposta_ia)
            user_dict = str_para_dict(resposta_sem_acentos)
        except Exception as e2:
            print(f"Erro mesmo após remover acentos: {e2}")
            user_dict = {}  # Dicionário vazio como fallback
            # Ou outra ação de recuperação adequada ao seu caso

    print(resposta_ia)
    quartos = int(user_dict["numero_quartos_int"]) if str(user_dict["numero_quartos_int"]).strip() and int(user_dict["numero_quartos_int"]) != 0 else None
    banheiros = int(user_dict["numero_banheiros_int"]) if str(user_dict["numero_banheiros_int"]).strip() and int(user_dict["numero_banheiros_int"]) != 0 else None
    valor = int(user_dict["valor_imovel_int"]) if str(user_dict["valor_imovel_int"]).strip() and int(user_dict["valor_imovel_int"]) != 0 else None
    vagas = int(user_dict["numero_vagas_garagem_int"]) if str(user_dict["numero_vagas_garagem_int"]).strip() and int(user_dict["numero_vagas_garagem_int"]) != 0 else None

    print(quartos)
    print(banheiros)
    print(valor)
    print(vagas)

    #Tratar cada dado lembretes: ou, até, mil
    #mudar agente para enviar int

    #adicionar busca aproximada 

    #não adicionar imoveis repetidos

    #formatação adequada 
    #enviar link junto

    #fazer imagem aparecer em vez de link

    #deixar bonito
    

    caracteristicas = [quartos, banheiros, vagas, valor]
    preenchidos = [c for c in caracteristicas if c not in (None, "")]

    if len(preenchidos) >= 2:
        options = imoveis.buscar_exato(quartos, banheiros, vagas, valor)
        len_op = len(options)
        print(options)
        if len_op < 3:
            #add the remaning
            remaning_spaces = (3 - len_op)
            print(f"Remaning spaces: {remaning_spaces}")
            aprox_options = imoveis.buscar_aproximado(quartos, banheiros, vagas, valor)

            print(f"Aprox_options: {aprox_options}")

            del aprox_options[:len_op]

            slice_aprox = aprox_options[:remaning_spaces]
            print(f"Slice aproximado: {slice_aprox}")
            options += slice_aprox
            print(f"Options final: {options}")
    else:
        options = ""

    # Resposta formatada para o front-end
    return jsonify({
        'status': 'success',
        'response': user_dict["sua_resposta_amigavel_str"],
        'options': options,  # Envia as opções separadamente
        'properties': parse_properties(options),  # Adiciona os imóveis parseados
        'history': session_history,
        'timestamp': timestamp
    })

@app.route('/api/imoveis', methods=['GET'])
def get_imoveis():
    print("HOW DID IT HAPPENDDD?!")
    """Endpoint para buscar imóveis (adaptar conforme sua classe Imoveis)"""
    try:
        filters = request.args.to_dict()
        imoveis = Imoveis().search(filters)  # Supondo que sua classe tenha método search
        return jsonify({
            'status': 'success',
            'data': imoveis
        })
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/api/schedule_visit', methods=['POST'])
def schedule_visit():
    data = request.json
    content = f"""
    Nova visita agendada:

    Nome: {data['name']}
    Email: {data['email']}
    Telefone: {data['phone']}
    Imóvel ID: {data['propertyId']}
    Data da visita: {data['date']}
    Comentário: {data['comment']}
    """

    msg = MIMEText(content)
    msg['Subject'] = 'Agendamento de Visita'
    msg['From'] = 'landbase.ia@gmail.com'
    msg['To'] = 'helamacorrea@gmail.com'

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('landbase.ia@gmail.com', config('GMAIL_PASSWORD'))
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.quit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error'}), 500

port = int(os.environ.get("PORT", 10000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)