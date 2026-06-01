import os

output_file = "proyecto_para_gemini.txt"
ignore_dirs = {'node_modules', '.git', 'bin', 'obj', 'dist', 'venv', 'env', '__pycache__', '.pytest_cache', '.mypy_cache', '.vscode'}
ignore_exts = {'.exe', '.dll', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.pdf', '.mp4', '.sqlite3', '.db', '.sqlite', '.log', '.pyc', '.csv', '.docx'}

print("Recopilando archivos del proyecto...")

with open(output_file, 'w', encoding='utf-8') as out:
    out.write("=== RUTAS DEL PROYECTO ===\n")
    for root, dirs, files in os.walk('.'):
        # Modificar dirs in-place para ignorar carpetas pesadas
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            out.write(os.path.join(root, file) + '\n')

    out.write("\n=== CONTENIDO DE LOS ARCHIVOS ===\n")
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            # Ignorar variables de entorno, binarios y el propio script
            if file == ".env" or file == output_file or file == "extractor.py":
                continue
            if any(file.endswith(ext) for ext in ignore_exts):
                continue
            
            filepath = os.path.join(root, file)
            out.write(f"\n\n--------------------------------------------------\n")
            out.write(f"ARCHIVO: {filepath}\n")
            out.write(f"--------------------------------------------------\n")
            try:
                # errors='ignore' evita que caracteres raros rompan el script
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"[No se pudo leer el archivo: {e}]")

print(f"¡Listo! Se ha creado el archivo: {output_file}")