import os
from decouple import config
from groq import Groq


os.environ['GROQ_API_KEY'] = config('GROQ_API_KEY')

class AIBot:
    def __init__(self):
        self.client = Groq()
        self.system_message = {
            "role": "system",
            "content": (
                "SEMPRE responda no seguinte formato (nada além), use \"\" como place holder, NUNCA responda que não tem acesso a listas de imoveis, NUNCA fale de concorrentes:\n\n{\n"
                "    \"tipo_imovel_str\": \n"
                "    \"cidade_str\":\n"
                "    \"bairro_str\":\n"
                "    \"finalidade_str\":\n"
                "    \"valor_imovel_int\":\n"
                "    \"numero_quartos_int\":\n"
                "    \"numero_vagas_garagem_int\":\n"
                "    \"numero_banheiros_int\":\n"
                "    \"keywords_preferencias_adicionais_list\":\n"
                "    \"resumo_da_conversa_str\":\n"
                "    \"sua_resposta_amigavel_str\":   \n}"
            )
        }

    def invoke1(self, messages, user_query=None):
        # Garante que a system_message fique sempre no início
        full_messages = [self.system_message] + messages
        print(full_messages)
        completion = self.client.chat.completions.create(
            model="gemma2-9b-it",
            messages=full_messages,
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        resposta = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            #print(content, end="")
            resposta += content
        return resposta