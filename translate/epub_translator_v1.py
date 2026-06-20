import hashlib
import html
import json
import os
import re
import shutil
import time

import ebooklib
import ftfy
from bs4 import BeautifulSoup
from ebooklib import epub
from google.cloud import translate_v2 as translate


def limpiar_texto_html(texto):
    """
    Limpia y decodifica todas las entidades HTML y caracteres especiales
    """
    if not texto:
        return texto

    return html.unescape(texto)


class TraductorConCache:
    """
    Gestor de traducciones con caché persistente
    """
    def __init__(self, archivo_cache="cache_traduccion.json", idioma_origen='en', idioma_destino='es'):
        self.archivo_cache = archivo_cache
        self.idioma_origen = idioma_origen
        self.idioma_destino = idioma_destino
        self.cache = self.cargar_cache()
        self.cliente_traduccion = translate.Client()
        self.traducciones_nuevas = 0
        
    def cargar_cache(self):
        """Carga el caché desde el archivo JSON"""
        if os.path.exists(self.archivo_cache):
            try:
                with open(self.archivo_cache, 'r', encoding='utf-8') as f:
                    print(f"Caché cargado: {self.archivo_cache}")
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar caché: {e}")
                return {}
        return {}
    
    def guardar_cache(self):
        """Guarda el caché en el archivo JSON"""
        try:
            with open(self.archivo_cache, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print(f"Caché guardado: {len(self.cache)} entradas")
        except Exception as e:
            print(f"Error al guardar caché: {e}")
    
    def generar_hash(self, texto):
        """Genera un hash único para el texto"""
        return hashlib.md5(texto.encode('utf-8')).hexdigest()
    
    def traducir_texto(self, texto):
        """
        Traduce texto usando caché o API de Google
        """
        if not texto or texto.strip() == "":
            return texto
        
        # Generar hash para buscar en caché
        hash_texto = self.generar_hash(texto)
        
        # Verificar si ya está en caché
        if hash_texto in self.cache:
            return self.cache[hash_texto]
        
        # Si no está en caché, traducir
        try:
            # Dividir textos largos (Google permite hasta 30,000 bytes)
            if len(texto.encode('utf-8')) > 25000:
                partes = self.dividir_texto_inteligente(texto, 25000)
                resultado = ""
                for parte in partes:
                    resultado += self.traducir_texto(parte)
                return resultado
            
            # Traducir usando Google Cloud Translation API
            resultado = self.cliente_traduccion.translate(
                texto,
                source_language=self.idioma_origen,
                target_language=self.idioma_destino
            )
            
            traduccion = resultado['translatedText']

            # Guardar en caché
            self.cache[hash_texto] = traduccion
            self.traducciones_nuevas += 1
            
            # Guardar caché cada 10 traducciones nuevas
            if self.traducciones_nuevas % 10 == 0:
                self.guardar_cache()
            
            # Pequeña pausa para respetar límites de tasa
            time.sleep(0.5)
            
            return traduccion
            
        except Exception as e:
            print(f"Error al traducir: {e}")
            print(f"Texto problemático: {texto}...")
            raise e

    def dividir_texto_inteligente(self, texto, max_bytes):
        """
        Divide texto en partes que no excedan max_bytes
        Intenta dividir por párrafos o frases
        """
        partes = []
        parte_actual = ""
        
        # Intentar dividir por párrafos
        parrafos = texto.split('\n')
        
        for parrafo in parrafos:
            if len((parte_actual + parrafo).encode('utf-8')) < max_bytes:
                parte_actual += parrafo + '\n'
            else:
                if parte_actual:
                    partes.append(parte_actual)
                parte_actual = parrafo + '\n'
        
        if parte_actual:
            partes.append(parte_actual)
        
        return partes

def traducir_html(contenido_html, traductor):
    """
    Traduce el contenido HTML preservando las etiquetas
    """
    soup = BeautifulSoup(contenido_html, 'html.parser')
    
    # Traducir solo el texto, preservando las etiquetas HTML
    for elemento in soup.find_all('p'):
        if elemento.parent.name not in ['script', 'style']:
            texto_original = elemento.text
            texto_original = ftfy.fix_text(re.sub(r'\s+', ' ', texto_original))

            if texto_original.strip():
                texto_traducido = traductor.traducir_texto(texto_original)
                texto_traducido = limpiar_texto_html(texto_traducido)

                elemento.clear()
                elemento.string = texto_traducido
    
    return str(soup)


def traducir_epub(ruta_entrada, ruta_salida, archivo_cache="cache_traduccion.json"):
    """
    Traduce un archivo EPUB haciendo una copia y modificando solo el texto
    Preserva completamente CSS, imágenes y estructura original
    """
    print(f"Leyendo EPUB: {ruta_entrada}")

    # Hacer una copia del archivo original primero
    print(f"Creando copia de seguridad...")
    shutil.copy2(ruta_entrada, ruta_salida)

    # Leer el libro copiado
    libro = epub.read_epub(ruta_salida)

    # Crear traductor con caché
    traductor = TraductorConCache(archivo_cache=archivo_cache)

    # Actualizar metadatos de idioma
    libro.set_language('es')

    # Traducir título si existe
    titulo_original = libro.get_metadata('DC', 'title')
    if titulo_original:
        titulo_traducido = traductor.traducir_texto(titulo_original[0][0])
        # Limpiar metadatos de título existentes
        libro.metadata[epub.NAMESPACES['DC']]['title'] = []
        libro.set_title(titulo_traducido)
        print(f"Título: {titulo_original[0][0]} → {titulo_traducido}")

    # Procesar cada item del libro
    contador = 0
    total_items = sum(1 for item in libro.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT)

    for item in libro.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            contador += 1
            print(f"\nTraduciendo capítulo {contador}/{total_items}...")

            try:
                # Obtener contenido HTML
                contenido_html = item.get_content().decode('utf-8')

                # Traducir solo el texto, preservando toda la estructura HTML
                contenido_traducido = traducir_html(contenido_html, traductor)

                # Actualizar el contenido del item existente
                item.set_content(contenido_traducido.encode('utf-8'))

                print(f"✓ Capítulo {contador} completado")

            except Exception as e:
                print(f"✗ Error en capítulo {contador}: {e}")
                # Guardar caché incluso si hay error
                traductor.guardar_cache()
                raise

    # Guardar caché final
    traductor.guardar_cache()
    print(f"\nTraducciones nuevas realizadas: {traductor.traducciones_nuevas}")
    print(f"Total en caché: {len(traductor.cache)}")

    # Guardar el EPUB modificado
    print(f"\nGuardando EPUB traducido: {ruta_salida}")
    epub.write_epub(ruta_salida, libro)
    print("¡Traducción completada exitosamente!")

# Ejemplo de uso
if __name__ == "__main__":
    # Configuración
    archivo_entrada = ...
    archivo_salida = ...
    archivo_cache = ...
    
    # Asegúrate de tener configuradas las credenciales de Google Cloud
    # export GOOGLE_APPLICATION_CREDENTIALS="..."
    
    try:
        traducir_epub(archivo_entrada, archivo_salida, archivo_cache)
    except Exception as e:
        print(f"\n✗ Error durante la traducción: {e}")
        print("El caché se ha guardado. Puedes reintentar la ejecución.")
