import sqlite3

class Imoveis:
    def __init__(self, db_path='imoveis.db'):
        self.db_path = db_path

    def limpar_preco(self, preco_str):
        return float(preco_str.replace('R$', '').replace('.', '').replace(',', '.').strip())

    def buscar(self, quartos_desejados=None, banheiros_desejados=None, vagas_desejadas=None, preco_desejado=None, limite=3):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM imoveis")
        imoveis = cursor.fetchall()
        #print(imoveis)
        colunas = [desc[0] for desc in cursor.description]

        idx_quartos = colunas.index('quartos')
        idx_banheiros = colunas.index('banheiros')
        idx_vagas = colunas.index('vagas')
        idx_preco = colunas.index('preco')
        idx_descricao = colunas.index('descricao')
        idx_localizacao = colunas.index('localizacao') if 'localizacao' in colunas else 0
        idx_imagem = colunas.index('imagem')

        def distancia(imovel):
            try:
                quartos = int(imovel[idx_quartos])
                banheiros = int(imovel[idx_banheiros])
                vagas = int(imovel[idx_vagas])
                preco = self.limpar_preco(imovel[idx_preco])
            except Exception as e:  
                # print(f"Erro ao calcular distância para imóvel: {imovel}")
                # print(f"Erro: {e}")
                return float('inf') 

            # Filtrar pelo preço máximo, descartar imóveis acima do limite
            if preco_desejado is not None:
                try:
                    if preco > float(preco_desejado):
                        return float('inf')
                except:
                    return float('inf')

            dist = 0
            if quartos_desejados is not None:
                dist += abs(quartos - int(quartos_desejados))
            if banheiros_desejados is not None:
                dist += abs(banheiros - int(banheiros_desejados))
            if vagas_desejadas is not None:
                dist += abs(vagas - int(vagas_desejadas))
            return dist

        imoveis_filtrados = sorted(imoveis, key=lambda imovel: (distancia(imovel), self.limpar_preco(imovel[idx_preco])))
        # print(f"imoveis_filtrados: {imoveis_filtrados}")
        resultados = []

        for imovel in imoveis_filtrados:
            if len(resultados) >= limite:
                break
            if distancia(imovel) == float('inf'):
                continue

            texto = (
                f"🏡 *Imóvel:*\n"
                f"📍 Localização: {imovel[idx_localizacao]}\n"
                f"🛏️ Quartos: {imovel[idx_quartos]}\n"
                f"🚿 Banheiros: {imovel[idx_banheiros]}\n"
                f"🚗 Vagas: {imovel[idx_vagas]}\n"
                f"💲 Preço: R$ {imovel[idx_preco]}\n"
                f"📝 Descrição: {imovel[idx_descricao]}\n"
                f"{imovel[idx_imagem]}\n"
                f"------------------------------------"
            )
            resultados.append(texto)

        conn.close()
        # print(f"return da função: {resultados}")
        return resultados

    def buscar_exato(self, quartos_desejados=None, banheiros_desejados=None, vagas_desejadas=None, preco_desejado=None, limite=3):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM imoveis")
        imoveis = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        idx_quartos = colunas.index('quartos')
        idx_banheiros = colunas.index('banheiros')
        idx_vagas = colunas.index('vagas')
        idx_preco = colunas.index('preco')
        idx_descricao = colunas.index('descricao')
        idx_localizacao = colunas.index('localizacao') if 'localizacao' in colunas else 0
        idx_imagem = colunas.index('imagem')

        def corresponde(imovel):
            try:
                quartos = int(imovel[idx_quartos])
                banheiros = int(imovel[idx_banheiros])
                vagas = int(imovel[idx_vagas])
                preco = self.limpar_preco(imovel[idx_preco])
            except:
                return False

            if quartos_desejados is not None and quartos != int(quartos_desejados):
                return False
            if banheiros_desejados is not None and banheiros != int(banheiros_desejados):
                return False
            if vagas_desejadas is not None and vagas != int(vagas_desejadas):
                return False
            if preco_desejado is not None and preco > float(preco_desejado):
                return False

            return True

        imoveis_filtrados = [im for im in imoveis if corresponde(im)]
        imoveis_filtrados.sort(key=lambda im: self.limpar_preco(im[idx_preco]))

        resultados = []
        for imovel in imoveis_filtrados[:limite]:
            texto = (
                f"🏡 *Imóvel:*\n"
                f"📍 Localização: {imovel[idx_localizacao]}\n"
                f"🛏️ Quartos: {imovel[idx_quartos]}\n"
                f"🚿 Banheiros: {imovel[idx_banheiros]}\n"
                f"🚗 Vagas: {imovel[idx_vagas]}\n"
                f"💲 Preço: {imovel[idx_preco]}\n"
                f"📝 Descrição: {imovel[idx_descricao]}\n"
                f"{imovel[idx_imagem]}\n"
                f"------------------------------------"
            )
            resultados.append(texto)

        conn.close()
        return resultados
    
    def buscar_aproximado(self, quartos_desejados=None, banheiros_desejados=None, vagas_desejadas=None, preco_desejado=None, limite=3):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM imoveis")
        imoveis = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        idx_quartos = colunas.index('quartos')
        idx_banheiros = colunas.index('banheiros')
        idx_vagas = colunas.index('vagas')
        idx_preco = colunas.index('preco')
        idx_descricao = colunas.index('descricao')
        idx_localizacao = colunas.index('localizacao') if 'localizacao' in colunas else 0
        idx_imagem = colunas.index('imagem')

        def distancia(imovel):
            try:
                quartos = int(imovel[idx_quartos])
                banheiros = int(imovel[idx_banheiros])
                vagas = int(imovel[idx_vagas])
                preco = self.limpar_preco(imovel[idx_preco])
            except:
                return float('inf')

            dist = 0
            if quartos_desejados is not None:
                dist += abs(quartos - int(quartos_desejados))
            if banheiros_desejados is not None:
                dist += abs(banheiros - int(banheiros_desejados))
            if vagas_desejadas is not None:
                dist += abs(vagas - int(vagas_desejadas))
            if preco_desejado is not None:
                dist += abs(preco - float(preco_desejado)) / 50000  # normaliza o peso do preço

            return dist

        imoveis_filtrados = sorted(imoveis, key=distancia)

        resultados = []
        for imovel in imoveis_filtrados[:limite]:
            texto = (
                f"🏡 *Imóvel:*\n"
                f"📍 Localização: {imovel[idx_localizacao]}\n"
                f"🛏️ Quartos: {imovel[idx_quartos]}\n"
                f"🚿 Banheiros: {imovel[idx_banheiros]}\n"
                f"🚗 Vagas: {imovel[idx_vagas]}\n"
                f"💲 Preço: {imovel[idx_preco]}\n"
                f"📝 Descrição: {imovel[idx_descricao]}\n"
                f"{imovel[idx_imagem]}\n"
                f"------------------------------------"
            )
            resultados.append(texto)

        conn.close()
        return resultados
    

    def ids_exato(self, quartos_desejados=None, banheiros_desejados=None, vagas_desejadas=None, preco_desejado=None, limite=3):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM imoveis")
        imoveis = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        idx_quartos = colunas.index('quartos')
        idx_banheiros = colunas.index('banheiros')
        idx_vagas = colunas.index('vagas')
        idx_preco = colunas.index('preco')
        idx_descricao = colunas.index('descricao')
        idx_localizacao = colunas.index('localizacao') if 'localizacao' in colunas else 0
        idx_imagem = colunas.index('imagem')

        def corresponde(imovel):
            try:
                quartos = int(imovel[idx_quartos])
                banheiros = int(imovel[idx_banheiros])
                vagas = int(imovel[idx_vagas])
                preco = self.limpar_preco(imovel[idx_preco])
            except:
                return False

            if quartos_desejados is not None and quartos != int(quartos_desejados):
                return False
            if banheiros_desejados is not None and banheiros != int(banheiros_desejados):
                return False
            if vagas_desejadas is not None and vagas != int(vagas_desejadas):
                return False
            if preco_desejado is not None and preco > float(preco_desejado):
                return False

            return True

        imoveis_filtrados = [im for im in imoveis if corresponde(im)]
        imoveis_filtrados.sort(key=lambda im: self.limpar_preco(im[idx_preco]))

        resultados = []
        for imovel in imoveis_filtrados[:limite]:
            im_dict = {
                "Localização": imovel[idx_localizacao],
                "Quartos": imovel[idx_quartos],
                "Banheiros": imovel[idx_banheiros],
                "Vagas": imovel[idx_vagas],
                "Preço": f"R$ {imovel[idx_preco]}",
                "Descrição": imovel[idx_descricao],
                "Imagem": imovel[idx_imagem]
            }
            resultados.append(im_dict) 

        conn.close()
        return resultados
    
    def ids_aproximado(self, quartos_desejados=None, banheiros_desejados=None, vagas_desejadas=None, preco_desejado=None, limite=3):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM imoveis")
        imoveis = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        idx_quartos = colunas.index('quartos')
        idx_banheiros = colunas.index('banheiros')
        idx_vagas = colunas.index('vagas')
        idx_preco = colunas.index('preco')
        idx_descricao = colunas.index('descricao')
        idx_localizacao = colunas.index('localizacao') if 'localizacao' in colunas else 0
        idx_imagem = colunas.index('imagem')

        def distancia(imovel):
            try:
                quartos = int(imovel[idx_quartos])
                banheiros = int(imovel[idx_banheiros])
                vagas = int(imovel[idx_vagas])
                preco = self.limpar_preco(imovel[idx_preco])
            except:
                return float('inf')

            dist = 0
            if quartos_desejados is not None:
                dist += abs(quartos - int(quartos_desejados))
            if banheiros_desejados is not None:
                dist += abs(banheiros - int(banheiros_desejados))
            if vagas_desejadas is not None:
                dist += abs(vagas - int(vagas_desejadas))
            if preco_desejado is not None:
                dist += abs(preco - float(preco_desejado)) / 50000  # normaliza o peso do preço

            return dist

        imoveis_filtrados = sorted(imoveis, key=distancia)

        resultados = []
        for imovel in imoveis_filtrados[:limite]:
            im_dict = {
                "Localização": imovel[idx_localizacao],
                "Quartos": imovel[idx_quartos],
                "Banheiros": imovel[idx_banheiros],
                "Vagas": imovel[idx_vagas],
                "Preço": f"R$ {imovel[idx_preco]}",
                "Descrição": imovel[idx_descricao],
                "Imagem": imovel[idx_imagem]
            }
            resultados.append(im_dict) 

        conn.close()
        return resultados


