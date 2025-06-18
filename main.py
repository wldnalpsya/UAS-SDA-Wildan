from flask import Flask, render_template, request, redirect
import csv

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        jumlah = int(request.form['jumlah'])
        return render_template('form_peserta.html', jumlah=jumlah)
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    peserta_list = []
    jumlah = int(request.form['jumlah'])

    for i in range(1, jumlah + 1):
        nama = request.form.get(f'nama_{i}')
        keterangan = request.form.get(f'keteragan_{i}')
        peserta_list.append([nama, keterangan])

    with open('peserta.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Nama", "Keterangan"])
        writer.writerows(peserta_list)

    return f"<h2>{jumlah} peserta berhasil disimpan ke CSV!</h2><a href='/'>Kembali</a>"

if __name__ == '__main__':
    app.run(debug=True)
