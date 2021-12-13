# Laboratorium 07-08
# 
# Przygotowanie środowiska:
# conda install flask
# Uruchomienie serwera:
# FLASK_APP=app.py FLASK_ENV=development flask run --port 5000


from flask import Flask, request, send_from_directory
app = Flask(__name__)

@app.route('/')
def index():
    return '''
<html>
    <head>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
    </head>
    <body>
        <input type="button" value="Otwórz formularz" onclick="$('#form').load('http://127.0.0.1:5000/form.html')" />
        <div id="form"></div>
    </body>
</html>
    '''

@app.route('/form.html')
def form():
    return '''
<form action="done.html" method="post">
    <div>
        <h1>Formularz</h1>
        <p>Uzupełnij formularz następującymi wartościami.</p>
        <p><b>Odpowiedź</b>: Poprawna odpowiedź!</p>
        <p><b>Nazwa</b>: eksploracja</p>
        <p><b>Email</b>: eksploracja@eksploracja.kis.p.lodz.pl</p>
        <p><b>Hasło</b>: tajnehaslo</p>
        <hr>
        <p>
            <label for="email"><b>Email</b></label>
            <input id="email" type="text" placeholder="Podaj e-mail" name="email" required>
        </p><p>
            <label for="name"><b>Podaj nazwę</b></label>
            <input id="name" type="text" placeholder="Podaj nazwę" name="name" required>
        </p><p>
            <label for="password"><b>Password</b></label>
            <input id="password" type="password" placeholder="Podaj hasło" name="password" required>
        </p><p>
            <label for="password-repeat"><b>Powtórz hasło</b></label>
            <input id="password-repeat" type="password" placeholder="Powtórz hasło" name="password-repeat" required>
        </p><p>
            <label for="answer">Wybierz poprawną odpowiedź:</label>
            <select id="answer" name="answer">
                <option value="wrong1">Niepoprawna odpowiedź 1</option>
                <option value="wrong2">Niepoprawna odpowiedź 2</option>
                <option value="correct">Poprawna odpowiedź!</option>
                <option value="wrong3">Niepoprawna odpowiedź 3</option>
            </select>
        </p>
        <hr>
        <button type="submit">Wyślij</button>
    </div>
</form>
    '''

@app.route('/done.html', methods=['POST'])
def done():
    data = request.form
    if \
        data["answer"] == "correct" and \
        data["name"] == "eksploracja" and \
        data["email"] == "eksploracja@eksploracja.kis.p.lodz.pl" and \
        data["password"] == data["password-repeat"] == "tajnehaslo":
        return f"Poprawnie wypełniono formularz.<br />{data}"
    else:
        return f"Błędnie wypełniono formularz.<br />{data}"