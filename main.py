from flask import Flask, render_template, request, redirect
import random
import csv

# Backend

def proses_ronde(round_data, total_peserta, skor_data, ronde_ke):
    round_selanjutnya = []

    for p1, p2 in round_data:
        nama1 = p1["Nama"]
        nama2 = p2["Nama"]

        if nama1 == "BYE":
            round_selanjutnya.append(p2)
            continue
        elif nama2 == "BYE":
            round_selanjutnya.append(p1)
            continue

        skor1 = int(skor_data.get(nama1, {}).get(f"skor{ronde_ke}", 0))
        skor2 = int(skor_data.get(nama2, {}).get(f"skor{ronde_ke}", 0))

        if skor1 == 0 and skor2 == 0:
            continue

        if skor1 > skor2:
            round_selanjutnya.append(p1)
        elif skor2 > skor1:
            round_selanjutnya.append(p2)
        else:
            continue

    return round_selanjutnya

def jumlah_bracket(jml_peserta):
    if jml_peserta <= 2:
        return 2
    elif jml_peserta <= 4:
        return 4
    elif jml_peserta <= 8:
        return 8
    elif jml_peserta <= 16:
        return 16

def jumlah_seed_otomatis(n):
    if n >= 16:
        return 4
    elif n >= 12:
        return 3
    elif n >= 8:
        return 2
    elif n >= 4:
        return 1
    else:
        return 0

def buat_bracket(jumlah_peserta, daftar_seed, semua_nama):
    ukuran_bracket = jumlah_bracket(jumlah_peserta)
    jumlah_bye = ukuran_bracket - jumlah_peserta

    jumlah_seed_dibutuhkan = jumlah_seed_otomatis(jumlah_peserta)
    if len(daftar_seed) != jumlah_seed_dibutuhkan:
        raise ValueError(f"Jumlah seeded harus {jumlah_seed_dibutuhkan}, bukan {len(daftar_seed)}")

    slot_peserta = [None] * ukuran_bracket
    peserta_biasa = [nama for nama in semua_nama if nama not in daftar_seed]

    posisi_seed = []
    if len(daftar_seed) == 2:
        posisi_seed = [0, ukuran_bracket - 1]
    elif len(daftar_seed) > 0:
        jarak_seed = ukuran_bracket // len(daftar_seed)
        mulai_seed = random.randrange(jarak_seed)
        posisi_seed = [(mulai_seed + i * jarak_seed) % ukuran_bracket for i in range(len(daftar_seed))]

    for posisi, nama in zip(posisi_seed, daftar_seed):
        slot_peserta[posisi] = nama

    def lawan_dari(posisi):
        return posisi + 1 if posisi % 2 == 0 else posisi - 1

    random.shuffle(posisi_seed)
    sisa_bye = jumlah_bye

    for posisi in posisi_seed:
        lawan = lawan_dari(posisi)
        if slot_peserta[lawan] is None and sisa_bye > 0:
            slot_peserta[lawan] = "BYE"
            sisa_bye -= 1

    slot_kosong = [i for i, isi in enumerate(slot_peserta) if isi is None]
    random.shuffle(slot_kosong)

    while sisa_bye > 0 and slot_kosong:
        posisi = slot_kosong.pop()
        lawan = lawan_dari(posisi)
        if slot_peserta[lawan] != "BYE":
            slot_peserta[posisi] = "BYE"
            sisa_bye -= 1

    random.shuffle(peserta_biasa)
    for i in range(len(slot_peserta)):
        if slot_peserta[i] is None and peserta_biasa:
            slot_peserta[i] = peserta_biasa.pop()

    return [(slot_peserta[i], slot_peserta[i + 1]) for i in range(0, ukuran_bracket, 2)]

def buat_skor_csv(rincian_bracket):
    with open("skor.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = ["Nama", "skor1", "skor2", "skor3", "skor4", "skor5"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rincian_bracket:
            if row["Nama"] != "BYE":
                writer.writerow({"Nama": row["Nama"], "skor1": 0, "skor2": 0, "skor3": 0, "skor4": 0, "skor5": 0})
                
def baca_skor():
    skor_dict = {}
    try:
        with open("skor.csv", newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                skor_dict[row["Nama"]] = row
    except FileNotFoundError:
        pass
    return skor_dict

                
# Flask
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        jumlah = int(request.form['jumlah'])
        return render_template('form_peserta.html', jumlah=jumlah)
    return render_template('index.html')

@app.route("/generate", methods=["POST"])
def generate_bracket():
    semua_nama = []
    daftar_seed = []
    peserta = []

    with open("peserta.csv", newline='', encoding='utf-8') as file_csv:
        pembaca = csv.DictReader(file_csv)
        for baris in pembaca:
            peserta.append({"Nama": baris["Nama"], "Keterangan": baris["Keterangan"]})
            nama = baris["Nama"].strip()
            semua_nama.append(nama)
            if baris["Keterangan"].strip().lower() == "seeded":
                daftar_seed.append(nama)

    jumlah_peserta = len(semua_nama)
    hasil_bracket = buat_bracket(jumlah_peserta, daftar_seed, semua_nama)

    rincian_bracket = []

    for pasangan in hasil_bracket:
        for p in pasangan:
            if p == "BYE":
                rincian_bracket.append({"Nama": "BYE", "Keterangan": "BYE"})
            else:
                ket = next((x["Keterangan"] for x in peserta if x["Nama"] == p), "normal")
                rincian_bracket.append({"Nama": p, "Keterangan": ket})

    nama_bye = []
    for i in range(0, len(rincian_bracket), 2):
        p1 = rincian_bracket[i]
        p2 = rincian_bracket[i+1]
        if p1["Nama"] == "BYE":
            nama_bye.append(p2["Nama"])
        elif p2["Nama"] == "BYE":
            nama_bye.append(p1["Nama"])

    for row in rincian_bracket:
        row["r1"] = "1" if row["Nama"] in nama_bye else "0"
        row["r2"] = "0"
        row["r3"] = "0"
        row["r4"] = "0"
        row["r5"] = "0"

    with open("bracket.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = ["Nama", "Keterangan", "r1", "r2", "r3", "r4", "r5"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rincian_bracket)
        
    buat_skor_csv(rincian_bracket)

    return redirect("/bracket")


@app.route("/bracket", methods=["GET"])
def bracket():
    rincian_bracket = []
    with open("bracket.csv", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rincian_bracket.append(row)

    bracket_fix = []
    for i in range(0, len(rincian_bracket), 2):
        bracket_fix.append((rincian_bracket[i], rincian_bracket[i+1]))

    peserta_bye = [p for p in rincian_bracket if p["r2"] == "1"]
    jumlah_peserta = len(rincian_bracket)
    daftar_seed = [p["Nama"] for p in rincian_bracket if p["Keterangan"] == "seeded"]
    
    with open("bracket.csv", newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
        
    r2 = []
    r3 = []
    r4 = []
    r5 = []
    
    for row in data:
        if row["r1"] == "1":
            r2.append(row)
        if row["r2"] == "1":
            r3.append(row)
        if row["r3"] == "1":
            r4.append(row)
        if row["r4"] == "1":
            r5.append(row)
                
    ukuran_bracket = jumlah_bracket(jumlah_peserta)
    bye = r2.copy()
    win_r2 = r3.copy()
    win_r3 = r4.copy()

    if ukuran_bracket > 2:
        r2 = [(r2[i], r2[i+1]) for i in range(0, len(r2), 2) if len(r2) % 2 == 0]
    
    if ukuran_bracket > 4:
        r3 = [(r3[i], r3[i+1]) for i in range(0, len(r3), 2) if len(r3) % 2 == 0] 
    
    if ukuran_bracket > 8:
        r4 = [(r4[i], r4[i+1]) for i in range(0, len(r4), 2) if len(r4) % 2 == 0]
    
    ronde_saat_ini = 2
    if ukuran_bracket == 2:
        if len(r2) > 0:
            ronde_saat_ini = 3
    else:
        if len(r2) == len(bracket_fix) / 2:
            ronde_saat_ini = 3
    
    if len(r3) == len(bracket_fix) // 4:
        ronde_saat_ini = 4
    if len(r4) == len(bracket_fix) // 8:
        ronde_saat_ini = 5
    if len(r5) > 0:
        ronde_saat_ini = 6
        
    skor_dict = baca_skor()
                
    return render_template("bracket.html",win_r2=win_r2, win_r3=win_r3, skor_dict=skor_dict , r2=r2, r3=r3, r4=r4, r5=r5, bracket_awal=bracket_fix, peserta_bye=peserta_bye, jumlah_peserta=jumlah_peserta, daftar_seed=daftar_seed, bracket_ukuran=jumlah_bracket(jumlah_peserta), ronde_saat_ini=ronde_saat_ini, bye=bye)

@app.route("/ronde2", methods=["POST"])
def ronde2():
    with open("bracket.csv", newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
        
    pasangan = [(data[i], data[i+1]) for i in range(0, len(data), 2)]
    
    pemenang = []
    pemenang = proses_ronde(pasangan, total_peserta=len(data),skor_data=baca_skor(), ronde_ke=1)
    
    for row in data:
        for p in pemenang:
            if row["Nama"] == p["Nama"] and row["Keterangan"] == p["Keterangan"]:
                row["r1"] = "1"

    with open("bracket.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return redirect("/bracket")

@app.route("/ronde3", methods=["POST"])
def ronde3():
    with open("bracket.csv", newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
        
    pasangan = []
    for row in data:
        if row["r1"] == "1":
            pasangan.append(row)
            
    pasangan = [(pasangan[i], pasangan[i+1]) for i in range(0, len(pasangan), 2)]
                
    pemenang = []
    pemenang = proses_ronde(pasangan, total_peserta=len(data), skor_data=baca_skor(), ronde_ke=2)
    
    for row in data:
        for p in pemenang:
            if row["Nama"] == p["Nama"] and row["Keterangan"] == p["Keterangan"]:
                row["r2"] = "1"

    with open("bracket.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return redirect("/bracket")

@app.route("/ronde4", methods=["POST"])
def ronde4():
    with open("bracket.csv", newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
        
    pasangan = []
    for row in data:
        if row["r2"] == "1":
            pasangan.append(row)
            
    pasangan = [(pasangan[i], pasangan[i+1]) for i in range(0, len(pasangan), 2)]
    
    pemenang = []
    pemenang = proses_ronde(pasangan, total_peserta=len(data), skor_data=baca_skor(), ronde_ke=3)
    
    for row in data:
        for p in pemenang:
            if row["Nama"] == p["Nama"] and row["Keterangan"] == p["Keterangan"]:
                row["r3"] = "1"

    with open("bracket.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return redirect("/bracket")

@app.route("/ronde5", methods=["POST"])
def ronde5():
    with open("bracket.csv", newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
        
    pasangan = []
    for row in data:
        if row["r3"] == "1":
            pasangan.append(row)
            
    pasangan = [(pasangan[i], pasangan[i+1]) for i in range(0, len(pasangan), 2)]
               
    pemenang = []
    pemenang = proses_ronde(pasangan, total_peserta=len(data), skor_data=baca_skor(), ronde_ke=4)
    
    for row in data:
        for p in pemenang:
            if row["Nama"] == p["Nama"] and row["Keterangan"] == p["Keterangan"]:
                row["r4"] = "1"

    with open("bracket.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return redirect("/bracket")

@app.route('/submit', methods=['POST'])
def submit():
    peserta_list = []
    jumlah = int(request.form['jumlah'])

    for i in range(1, jumlah + 1):
        nama = request.form.get(f'nama_{i}')
        keterangan = request.form.get(f'keterangan_{i}')
        peserta_list.append([nama, keterangan])

    with open('peserta.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Nama", "Keterangan"])
        writer.writerows(peserta_list)
        
    semua_nama = []
    daftar_seed = []
    peserta = []

    with open("peserta.csv", newline='', encoding='utf-8') as file_csv:
        pembaca = csv.DictReader(file_csv)
        for baris in pembaca:
            peserta.append({"Nama": baris["Nama"], "Keterangan": baris["Keterangan"]})
            nama = baris["Nama"].strip()
            semua_nama.append(nama)
            if baris["Keterangan"].strip().lower() == "seeded":
                daftar_seed.append(nama)

    jumlah_peserta = len(semua_nama)
    hasil_bracket = buat_bracket(jumlah_peserta, daftar_seed, semua_nama)

    rincian_bracket = []

    for pasangan in hasil_bracket:
        for p in pasangan:
            if p == "BYE":
                rincian_bracket.append({"Nama": "BYE", "Keterangan": "BYE"})
            else:
                ket = next((x["Keterangan"] for x in peserta if x["Nama"] == p), "normal")
                rincian_bracket.append({"Nama": p, "Keterangan": ket})

    nama_bye = []
    for i in range(0, len(rincian_bracket), 2):
        p1 = rincian_bracket[i]
        p2 = rincian_bracket[i+1]
        if p1["Nama"] == "BYE":
            nama_bye.append(p2["Nama"])
        elif p2["Nama"] == "BYE":
            nama_bye.append(p1["Nama"])

    for row in rincian_bracket:
        row["r1"] = "1" if row["Nama"] in nama_bye else "0"
        row["r2"] = "0"
        row["r3"] = "0"
        row["r4"] = "0"
        row["r5"] = "0"

    with open("bracket.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = ["Nama", "Keterangan", "r1", "r2", "r3", "r4", "r5"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rincian_bracket)

    return redirect("/bracket")

if __name__ == '__main__':
    app.run(debug=True)