import json
import os
import ast
import re

USERS_FILE = "users.json"

class User:

    def __init__(self, data):
        self.name = data.get("name", "")
        self.phone_number = data.get("phone_number", "")
        self.user_id = data.get("user_id")
        self.last_contact = data.get("last_contact")
        self.id_last_message = data.get("id_last_message")

        self.tipo_de_imovel = data.get("tipo_de_imovel", "")
        self.cidade = data.get("cidade", "")
        self.bairro = data.get("bairro", "")
        self.valor_do_imovel = data.get("valor_do_imovel", 0)
        self.proposito = data.get("proposito", "")
        self.numero_de_quartos = data.get("numero_de_quartos", "")
        self.vaga_garagem = data.get("vaga_garagem", "")
        self.mobiliado = data.get("mobiliado", "")
        self.vista_para_o_mar = data.get("vista_para_o_mar", "")
        self.tempo_para_mudar = data.get("tempo_para_mudar", "")
        self.forma_de_pagamento = data.get("forma_de_pagamento", "")
        self.resumo_da_conversa = data.get("resumo_da_conversa", "")
        self.solicitacoes_adicionais = data.get("solicitacoes_adicionais", [])
        self.enviar_imoveis = data.get("enviar_imoveis")
        self.numero_de_respostas_do_cliente = data.get("numero_de_respostas_do_cliente", 0)

    def get_last_message_id(self):
        return self.id_last_message

    def set_message_id(self, msg_id):
        self.id_last_message = msg_id

    def set_last_contact(self, last_contact):
        self.last_contact = last_contact

    def get_last_contact(self):
        return self.last_contact

    def is_new_client(self): 
        return self.phone_number == ""

    def message_new_client(): 
        return "Ola sou a IA da imobiliaria! Estou aqui para te ajudar a encontrar o imóvel ideal para suas necessidades! Em que posso ajudar?"

    def get_defined_attributes(self):
        return {k: v for k, v in self.to_dict().items() if v not in ["", [], None, 0]}

    def get_missing_attributes(self):
        return [k for k, v in self.to_dict().items() if v in ["", [], None, 0] and k not in ["user_id", "last_contact", "id_last_message"]]

    def message_partial_info(self):
        defined = self.get_defined_attributes()
        partes = []
        if "tipo_de_imovel" in defined:
            partes.append(f"um(a) {defined['tipo_de_imovel']}")
        if "cidade" in defined:
            partes.append(f"em {defined['cidade']}")
        if "valor_do_imovel" in defined:
            partes.append(f"até R${defined['valor_do_imovel']:,.0f}".replace(",", "."))
        if "proposito" in defined:
            partes.append(f"para {defined['proposito'].lower()}")
        extras = ", ".join(self.solicitacoes_adicionais[:5]) if self.solicitacoes_adicionais else ""
        base = f"Que legal que você quer {', '.join(partes)}"
        return f"{base} com {extras}! Me conta mais pra eu te ajudar melhor 😊" if extras else f"{base}! Me conta um pouco mais pra eu te ajudar melhor 😊"

    def get_client_table(self):
        return self.to_dict()

    @staticmethod
    def save_users_to_file(users):
        with open(USERS_FILE, "w") as f:
            json.dump([u.to_dict() for u in users], f, indent=4)

    @staticmethod
    def load_users_from_file():
        if not os.path.exists(USERS_FILE):
            return []
        with open(USERS_FILE, "r") as f:
            users_data = json.load(f)
        return [User(data) for data in users_data]

    @classmethod
    def find_user_by_phone(cls, users, phone_number):
        return next((u for u in users if u.phone_number == phone_number), None)

    def to_dict(self):
        return {
            "name": self.name,
            "phone_number": self.phone_number,
            "user_id": self.user_id,
            "last_contact": self.last_contact,
            "id_last_message": self.id_last_message,
            "tipo_de_imovel": self.tipo_de_imovel,
            "cidade": self.cidade,
            "bairro": self.bairro,
            "valor_do_imovel": self.valor_do_imovel,
            "proposito": self.proposito,
            "numero_de_quartos": self.numero_de_quartos,
            "vaga_garagem": self.vaga_garagem,
            "mobiliado": self.mobiliado,
            "vista_para_o_mar": self.vista_para_o_mar,
            "tempo_para_mudar": self.tempo_para_mudar,
            "forma_de_pagamento": self.forma_de_pagamento,
            "resumo_da_conversa": self.resumo_da_conversa,
            "solicitacoes_adicionais": self.solicitacoes_adicionais,
            "enviar_imoveis": self.enviar_imoveis,
            "numero_de_respostas_do_cliente": self.numero_de_respostas_do_cliente
        }

    @staticmethod
    def file_to_object():
        if not os.path.exists(USERS_FILE) or os.stat(USERS_FILE).st_size == 0:
            return []
        with open(USERS_FILE, "r") as f:
            users_data = json.load(f)
        return [User(data) for data in users_data]

    def update(self, new_data):
        for key in self.to_dict():
            setattr(self, key, new_data.get(key, getattr(self, key)))

    @staticmethod
    def string_to_object(data_string):
        match = re.search(r"\{.*\}", data_string, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            print("Erro ao converter para JSON:", e)
            return None

    def __repr__(self):
        return f"User(name={self.name}, phone_number={self.phone_number}, cidade={self.cidade}, tipo_de_imovel={self.tipo_de_imovel}, valor_do_imovel={self.valor_do_imovel}, proposito={self.proposito})"
