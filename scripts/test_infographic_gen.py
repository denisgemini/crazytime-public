from PIL import Image, ImageDraw, ImageFont
import os

def create_infographic():
    # Cargar fondo
    img = Image.open('fondo_monitores.png').convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Fuentes
    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 35)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
    except:
        font_header = font_main = font_small = ImageFont.load_default()

    # 1. HEADER (Top Banner)
    draw.text((512, 110), "RESUMEN DIARIO - S4 D2", fill=(200, 255, 255, 255), font=font_header, anchor="mm")
    
    # 2. CRAZY TIME (Monitor Izquierda - con inclinación)
    # Creamos una capa aparte para rotar el texto y que encaje en la perspectiva
    ct_layer = Image.new('RGBA', (400, 200), (0, 0, 0, 0))
    ct_draw = ImageDraw.Draw(ct_layer)
    ct_draw.text((10, 10), "CRAZY TIME", fill=(0, 255, 255, 255), font=font_main)
    ct_draw.text((10, 60), "DIST: 195", fill=(255, 255, 255, 255), font=font_small)
    ct_draw.text((10, 100), "ROI: +12%", fill=(0, 255, 100, 255), font=font_small)
    ct_draw.text((10, 140), "HITS: 4", fill=(255, 255, 255, 255), font=font_small)
    
    # Rotar un poco para la perspectiva (aprox 5 grados)
    ct_rotated = ct_layer.rotate(4, expand=True, resample=Image.BICUBIC)
    overlay.paste(ct_rotated, (100, 280), ct_rotated)

    # 3. PACHINKO (Monitor Derecha Vertical)
    draw.text((710, 310), "PACHINKO", fill=(255, 200, 0, 255), font=font_main)
    draw.text((710, 360), "DIST: 42", fill=(255, 255, 255, 255), font=font_small)
    draw.text((710, 400), "ROI: -5%", fill=(255, 100, 100, 255), font=font_small)
    draw.text((710, 440), "HITS: 1", fill=(255, 255, 255, 255), font=font_small)

    # 4. NUMERO 10 (Marco Dorado Inferior Izq)
    draw.text((135, 650), "NUMERO 10", fill=(255, 255, 255, 255), font=font_main)
    draw.text((135, 700), "APARICIONES: 18", fill=(200, 200, 200, 255), font=font_small)
    draw.text((135, 740), "DIST. ACT: 12", fill=(255, 200, 0, 255), font=font_small)

    # 5. SECUENCIAS (Marco Dorado Inferior Der)
    draw.text((580, 690), "SECUENCIAS", fill=(255, 255, 255, 255), font=font_main)
    draw.text((580, 740), "2 -> 5: 3 HITS", fill=(200, 255, 200, 255), font=font_small)
    draw.text((580, 780), "5 -> 2: 0 HITS", fill=(255, 200, 200, 255), font=font_small)

    # Combinar y guardar
    out = Image.alpha_composite(img, overlay)
    out.save('test_dashboard_stats.png')
    print("Dashboard generado: test_dashboard_stats.png")

if __name__ == "__main__":
    create_infographic()
