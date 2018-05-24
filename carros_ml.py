#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 23 06:03:29 2018

@author: itsbarreto


Navega na pagina do Mercado Livre e captura as imagens dos anuncio para uma determinada marca de carros.

"""

from bs4 import BeautifulSoup
import requests
import re
import os
import pandas as pd
import time
import math

IMAGE_PATH = '../../Imagens/carros_gm/'
CSV_DADOS = '../../csv/valid_dados_anuncios_multi.csv'
MARCAS_A_PESQUISAR = ['Fiat','Volksvagem','Ford']
qtd_tentativas = 0
sopa = lambda url: BeautifulSoup(requests.get(url).text, "html5lib")
re_nao_alfa_num = re.compile('[\W]')


def escreve_img(r,i):
    with open(i, 'wb') as f:
        for chunk in r.iter_content():
            f.write(chunk)


def pega_img(img,id_anuncio):
    global qtd_tentativas
    if 'youtube' not in img:
        r = None
        path_nm_img = lambda id_a, i : IMAGE_PATH + id_a+'/'+str(len(os.listdir(IMAGE_PATH + id_a)) + 1)+'.' + i.split('.')[-1]
        try:
            r = requests.get(img, stream=True)
            qtd_tentativas = 0
        except requests.exceptions.ConnectionError:
            if qtd_tentativas < 10:
                time.sleep(qtd_tentativas+0.5)
                qtd_tentativas += 1
                pega_img(img,id_anuncio)
                return None
            else:
                raise
        if r.status_code == 200:
            i = path_nm_img(id_anuncio,img)
            escreve_img(r,i)
            del r
            return i
        else:
            del r
            img = img[:-5] + 'O.'+img[-3:]
            r = requests.get(img, stream=True)
            i = path_nm_img(id_anuncio,img)
            if r.status_code == 200:
                escreve_img(r,i)
                del r
                return i
    return None


def captura_anuncio_pg(li):
    url_a = li.find('a',{'class' : 'item__info-link'})['href']
    ano = 9999
    preco = 999999
    try:
        ano = int(li.find('a',{'class' : 'item__info-link'}).find('div', {'class': 'item__attrs'}).text.split('|')[0].strip())
        preco = int(li.find('a',{'class' : 'item__info-link'}).find('span', {'class': 'price__fraction'}).text.replace('.','').strip())
    except Exception as e:
        print(str(e).encode('utf-8'))
        ano = 9999
        preco = 999999
        pass
    if ano < 9999 or ano > 2016:
        id_anuncio = url_a.split('/')[-1].split('-')[1]
        if not os.path.exists(IMAGE_PATH + id_anuncio):
            s_a = None
            qt = 0
            while not s_a:
                try:
                    s_a = sopa(url_a)
                except requests.exceptions.ConnectionError:
                    if qt<10:
                        qt += 1
                        time.sleep(qt)
                        s_a = sopa(url_a)
                    else:
                        return 0
                    pass
            os.makedirs(IMAGE_PATH+id_anuncio)
            imagens = [pega_img(i['src'][:-5] + 'F.'+i['src'][-3:],id_anuncio) for i in s_a.find(id='gallery_dflt').findAll('img',{'width' : '70', 'height' : '70'})]
            dados_anuncio = {
                'marca' : re_nao_alfa_num.sub(' ', s_a.find('ul',{'class' : 'vip-navigation-breadcrumb-list'}).findAll('li')[-2].text).strip(),
                'preco' :  preco,
                'modelo' : re_nao_alfa_num.sub(' ',s_a.find('ul',{'class' : 'vip-navigation-breadcrumb-list'}).findAll('li')[-1].text).strip(),
                'ano' : s_a.find(id='short-desc').find('article').findAll('dd')[0].text,
                'id_anuncio' : id_anuncio,
                'dcr' : "-".join(url_a.split('/')[-1].split('-')[2:-1])
            }
            try:
                da = pd.read_csv(CSV_DADOS).append(pd.DataFrame([dados_anuncio]), ignore_index=True)
                #print('%i anuncios pesquisados.' %len(da.index))
                da.to_csv(CSV_DADOS,index=False)
            except Exception as e:
                print(e)
                pd.DataFrame([dados_anuncio]).to_csv(CSV_DADOS,index=False)
                pass
            return len([i for i in imagens if i])
        else:
            return len(os.listdir(IMAGE_PATH+id_anuncio)) if ano > 2000 else 0


def get_anuncios_pg(pg):
    sopa_pg = None
    qt = 0
    while not sopa_pg:
        try:
            sopa_pg = sopa(url)
        except requests.exceptions.ConnectionError:
            if qt<10:
                qt += 1
                time.sleep(qt)
                sopa_pg = sopa(url)
            else:
                return 0
            pass
    try:
        print('%i imagens na pagina.                ' %sum(list(map(captura_anuncio_pg,sopa_pg.findAll('li',{'class' : 'results-item'})))))
    except Exception as e:
        print(e)
        pass
    try:
        return sopa_pg.find('div',{'class' : 'pagination__container'}).find('li',{'class' : 'pagination__next'}).find('a')['href']
    except:
        return None

if __name__ == "__main__":
    localtime = time.asctime( time.localtime(time.time()) )
    print('Inicio do processamento ', localtime)
    marcas = [m.lower() for m in MARCAS_A_PESQUISAR]
    for m in marcas:
        q_s = 50
        qtd_espacos_r = math.floor((q_s - 2 - len(m))/2)
        qtd_espacos_l = math.ceil((q_s - 2 - len(m))/2)
        print('\n\n')
        print('=' * q_s)
        print('|' +(' ' * qtd_espacos_l) + m + (' ' * qtd_espacos_r) +  '|')
        print('=' * q_s)
        print('\n\n')
        url = 'https://carros.mercadolivre.com.br/' + m
        i = 0
        while url:
            print(str(i) + '.' + url)
            try:
                url = get_anuncios_pg(url)
                i+=1            
            except Exception:
                url = None
                pass
