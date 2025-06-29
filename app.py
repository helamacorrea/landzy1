from flask import Flask, request, jsonify, send_from_directory, redirect, session, render_template
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
import psycopg2
from werkzeug.utils import secure_filename


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
app.secret_key = config('SESSION_KEY')

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
    

@app.route('/partner/register', methods=['POST'])
def register_agency():
    data = request.form

    try:
        conn = psycopg2.connect(
            dbname="landzy",
            user="landzyuser",
            password=config('SQL_KEY'),
            host="localhost"
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO parceiros (
                agency_name, cnpj, creci, city, password,
                phone, email, website, is_authorized
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['agency-name'],
            data['cnpj'],
            data['creci'],
            data['product'],
            data['password'],
            data['phone'],
            data['email'],
            data.get('website'),
            data.get('is_authorized') == 'yes'
        ))
        print("Authorization checkbox:", request.form.get("is_authorized"))
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/static/thanks.html")

    except Exception as e:
        print(f"Erro ao salvar dados do parceiro: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/partner/login', methods=['POST'])
def partner_login():
    data = request.form
    try:
        conn = psycopg2.connect(
            dbname="landzy",
            user="landzyuser",
            password=config('SQL_KEY'),
            host="localhost"
        )
        cur = conn.cursor()
        cur.execute("SELECT id FROM parceiros WHERE email=%s AND password=%s", (data['email'], data['password']))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            session['partner_id'] = result[0]
            return redirect('/partner/dashboard')
        else:
            return "Login inválido", 401

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/partner/dashboard')
def partner_dashboard():
    if 'partner_id' not in session:
        return redirect('/partner-access.html')
    return render_template('partner-dashboard.html')


@app.route('/partner/property/add')
def add_property_page():
    if 'partner_id' not in session:
        return redirect('/partner-access.html')
    return render_template('add-property.html')

@app.route('/partner/properties')
def list_properties_page():
    if 'partner_id' not in session:
        return redirect('/partner-access.html')
    return render_template('list-properties.html')

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/partner/property/add', methods=['POST'])
def add_property():
    if 'partner_id' not in session:
        return redirect('/partner-access.html')

    data = request.form
    files = request.files.getlist('photos')

    saved_paths = []
    for f in files:
        if f and f.filename:
            filename = secure_filename(f.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            f.save(save_path)
            saved_paths.append(save_path)
            

    try:
        conn = psycopg2.connect(
            dbname="landzy",
            user="landzyuser",
            password=config('SQL_KEY'),
            host="localhost"
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO imoveis (
                partner_id, type, title, description, price, city, neighborhood,
                bedrooms, bathrooms, suites, parking_spots,
                total_area, built_area, purpose, deal_details,
                available, photo_paths
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['partner_id'],
            data['type'],
            data['title'],
            data['description'],
            data['price'],
            data['city'],
            data['neighborhood'],
            data.get('bedrooms'),
            data.get('bathrooms'),
            data.get('suites'),
            data.get('parking_spots'),
            data.get('total_area'),
            data.get('built_area'),
            data.get('purpose'),
            data.get('deal_details'),
            data.get('available') == 'yes',
            json.dumps(saved_paths) 
        ))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/partner/dashboard')
    except Exception as e:
        print("Erro ao salvar imóvel:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

@app.route('/partner/properties/data')
def get_partner_properties():
    if 'partner_id' not in session:
        return jsonify([])

    try:
        conn = psycopg2.connect(
            dbname="landzy",
            user="landzyuser",
            password=config('SQL_KEY'),
            host="localhost"
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, city, price FROM imoveis WHERE partner_id = %s
        """, (session['partner_id'],))
        props = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify([
            {'id': i, 'title': t, 'city': c, 'price': p}
            for i, t, c, p in props
        ])

    except Exception as e:
        return jsonify({'error': str(e)})

conn_data = {
    "dbname": "landzy",
    "user": "landzyuser",
    "password": config("SQL_KEY"),
    "host": "localhost"
}
# Ver propriedade
@app.route('/partner/property/<int:id>')
def view_property(id):
    if 'partner_id' not in session:
        return redirect('/partner-access.html')
    conn = psycopg2.connect(**conn_data)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM imoveis WHERE id = %s AND partner_id = %s", (id, session['partner_id']))
    prop = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("view-property.html", property=prop)

# Editar propriedade
@app.route('/partner/property/<int:id>/edit', methods=['GET', 'POST'])
def edit_property(id):
    if 'partner_id' not in session:
        return redirect('/partner-access.html')
    conn = psycopg2.connect(**conn_data)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        form = request.form
        cur.execute("""
            UPDATE imoveis SET 
                type=%s, title=%s, description=%s, price=%s, city=%s, neighborhood=%s,
                bedrooms=%s, bathrooms=%s, suites=%s, garage_spaces=%s,
                total_area=%s, built_area=%s, purpose=%s, negotiation_details=%s,
                available_for_visit=%s
            WHERE id = %s AND partner_id = %s
        """, (
            form['type'], form['title'], form['description'], form['price'], form['city'],
            form['neighborhood'], form['bedrooms'], form['bathrooms'], form['suites'],
            form['garage_spaces'], form['total_area'], form['built_area'],
            form['purpose'], form['negotiation_details'],
            form.get('available_for_visit') == 'on',
            id, session['partner_id']
        ))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/partner/properties')
    else:
        cur.execute("SELECT * FROM imoveis WHERE id = %s AND partner_id = %s", (id, session['partner_id']))
        prop = cur.fetchone()
        cur.close()
        conn.close()
        return render_template("edit-property.html", property=prop)

# Excluir propriedade
@app.route('/partner/property/<int:id>/delete', methods=['POST'])
def delete_property(id):
    if 'partner_id' not in session:
        return redirect('/partner-access.html')
    conn = psycopg2.connect(**conn_data)
    cur = conn.cursor()
    cur.execute("DELETE FROM imoveis WHERE id = %s AND partner_id = %s", (id, session['partner_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/partner/properties')



port = int(os.environ.get("PORT", 10000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)