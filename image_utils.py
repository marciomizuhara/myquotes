from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import os


def generate_quote_image(quote_text, author, book_title):
    # Dimensões da imagem (formato Stories)
    width, height = 1080, 1920

    # Criar gradiente de fundo
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    for y in range(height):
        r = 240 - int((120 * y) / height)  # Gradiente de branco para cinza
        g = 240 - int((120 * y) / height)
        b = 240 - int((120 * y) / height)
        ImageDraw.Draw(img).line([(0, y), (width, y)], fill=(r, g, b), width=1)

    draw = ImageDraw.Draw(img)

    # Fontes
    font_quote = ImageFont.truetype('arial.ttf', size=80)
    font_meta = ImageFont.truetype('arial.ttf', size=50)  # Para livro e autor em itálico

    # Limite de largura para o texto (em pixels)
    max_text_width = width - 200  # Margem de 100px de cada lado

    # Quebra de linha manual para o texto da citação
    wrapped_lines = []
    for line in quote_text.split("\n"):  # Considera que o texto pode já ter quebras
        # Divide as linhas longas em partes menores que caibam na largura máxima
        current_line = ""
        for word in line.split():
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font_quote)
            if bbox[2] - bbox[0] <= max_text_width:  # Verifica largura da linha
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word
        if current_line:  # Adiciona a última linha processada
            wrapped_lines.append(current_line)

    # Junta as linhas com quebras
    wrapped_text = "\n".join(wrapped_lines)

    # Calcula a posição do texto da citação
    quote_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font_quote)
    quote_width = quote_bbox[2] - quote_bbox[0]
    quote_height = quote_bbox[3] - quote_bbox[1]
    quote_x = (width - quote_width) // 2
    quote_y = height // 3

    # Desenha a citação na imagem
    draw.multiline_text((quote_x, quote_y), wrapped_text, fill="black", font=font_quote, align="center")

    # Adicionar livro e autor em itálico
    meta_text = f"{book_title} - {author}"
    meta_bbox = draw.textbbox((0, 0), meta_text, font=font_meta)
    meta_width = meta_bbox[2] - meta_bbox[0]
    meta_height = meta_bbox[3] - meta_bbox[1]
    meta_x = (width - meta_width) // 2
    meta_y = quote_y + quote_height + 50  # Espaço abaixo da citação
    draw.text((meta_x, meta_y), meta_text, fill="gray", font=font_meta, align="center")

    # Salvar a imagem no diretório especificado
    directory = "static/quotes"
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"quote_{quote_text[:10].strip().replace(' ', '_')}.png")
    img.save(file_path)

    return file_path
