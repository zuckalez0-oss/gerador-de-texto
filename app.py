from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui' # Necessário para usar flash messages

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('texts.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar o banco de dados
def init_db():
    conn = get_db_connection()
    # Adicionamos uma coluna para 'variables' caso você queira armazenar variáveis padrão para um texto
    # Por enquanto, vamos manter simples e focar na entrada de variáveis no momento da geração
    conn.execute('''
        CREATE TABLE IF NOT EXISTS texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    texts = conn.execute('SELECT * FROM texts').fetchall()
    conn.close()
    return render_template('index.html', texts=texts)

@app.route('/add', methods=('GET', 'POST'))
def add_text():
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        if not name or not content:
            flash('O nome e o conteúdo são obrigatórios!')
            return redirect(url_for('add_text'))
        conn = get_db_connection()
        conn.execute('INSERT INTO texts (name, content) VALUES (?, ?)', (name, content))
        conn.commit()
        conn.close()
        flash('Texto adicionado com sucesso!')
        return redirect(url_for('index'))
    return render_template('add_text.html')

# Nova rota para edição
@app.route('/edit/<int:text_id>', methods=('GET', 'POST'))
def edit_text(text_id):
    conn = get_db_connection()
    text = conn.execute('SELECT * FROM texts WHERE id = ?', (text_id,)).fetchone()

    if text is None:
        flash('Texto não encontrado para edição.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        if not name or not content:
            flash('O nome e o conteúdo são obrigatórios!')
        else:
            conn.execute('UPDATE texts SET name = ?, content = ? WHERE id = ?', (name, content, text_id))
            conn.commit()
            flash('Texto atualizado com sucesso!')
            conn.close()
            return redirect(url_for('index'))
    
    conn.close()
    return render_template('edit_text.html', text=text)

# Nova rota para exclusão
@app.route('/delete/<int:text_id>', methods=('POST',))
def delete_text(text_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM texts WHERE id = ?', (text_id,))
    conn.commit()
    conn.close()
    flash('Texto excluído com sucesso!')
    return redirect(url_for('index'))

@app.route('/generate/<int:text_id>', methods=('GET', 'POST'))
def generate_text(text_id):
    conn = get_db_connection()
    text = conn.execute('SELECT * FROM texts WHERE id = ?', (text_id,)).fetchone()
    conn.close()

    if text is None:
        flash('Texto não encontrado.')
        return redirect(url_for('index'))

    generated_content = text['content']

    # 1. Saudação Dinâmica
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Bom dia"
    elif 12 <= current_hour < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"
    
    generated_content = generated_content.replace('{saudacao}', greeting)

    # 2. Lógica para variáveis customizáveis
    # Se o método for POST, o usuário enviou as variáveis
    if request.method == 'POST':
        # Itera sobre os dados do formulário para encontrar as variáveis customizadas
        for key, value in request.form.items():
            if key.startswith('var_'): # Assumimos que as variáveis customizadas começarão com 'var_'
                placeholder = '{' + key[4:] + '}' # Ex: 'var_nome' -> '{nome}'
                generated_content = generated_content.replace(placeholder, value)
        
        # O campo 'content' do formulário pode ser usado para o texto base, mas já temos de 'text'
        # Isso é mais para garantir que as variáveis sejam aplicadas no texto original do DB
        
        return render_template('generated_text.html', generated_content=generated_content, text_name=text['name'])
    
    # Se o método for GET (primeira vez que acessa a página de geração)
    # Precisamos identificar os placeholders no conteúdo do texto para criar o formulário dinamicamente
    import re
    placeholders = re.findall(r'\{([a-zA-Z0-9_]+)\}', text['content'])
    
    # Remove 'saudacao' da lista de placeholders que o usuário precisa preencher
    if 'saudacao' in placeholders:
        placeholders.remove('saudacao')

    # Remove duplicatas, mantendo a ordem (Python 3.7+ para set)
    placeholders = list(dict.fromkeys(placeholders))
    
    return render_template('generate_form.html', text=text, placeholders=placeholders)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
