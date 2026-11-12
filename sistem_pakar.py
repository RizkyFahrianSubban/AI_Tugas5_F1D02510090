"""Sistem pakar sederhana dengan Forward Chaining.

Cara pakai:
    python sistem_pakar.py                      # mode interaktif (tanya y/t)
    python sistem_pakar.py --ya "fakta1;fakta2" # mode uji (tanpa tanya)
"""
import argparse
import json
import sys


def muat_kb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fakta_dasar(kb):
    """Fakta yang tidak pernah menjadi hasil aturan -> ditanyakan ke user."""
    hasil = {r["maka"] for r in kb["aturan"]}
    dasar = []
    for r in kb["aturan"]:
        for p in r["jika"]:
            if p not in hasil and p not in dasar:
                dasar.append(p)
    return dasar


def terpenuhi(aturan, memori):
    ada = [p in memori for p in aturan["jika"]]
    return all(ada) if aturan["mode"] == "dan" else any(ada)


def forward_chaining(kb, fakta_awal):
    memori = set(fakta_awal)
    asal = {}   # fakta turunan -> aturan penghasilnya
    log = []
    siklus = 0
    while True:
        cocok = [r for r in kb["aturan"]
                 if r["maka"] not in memori and terpenuhi(r, memori)]
        if not cocok:
            break
        r = cocok[0]
        siklus += 1
        memori.add(r["maka"])
        asal[r["maka"]] = r
        log.append((siklus, r))
    return memori, asal, log


def kesimpulan_akhir(kb, asal):
    """Fakta turunan yang tidak dipakai sebagai syarat aturan lain."""
    premis = {p for r in kb["aturan"] for p in r["jika"]}
    return [f for f in asal if f not in premis]


def cetak_alasan(fakta, asal, memori, tingkat=1):
    r = asal[fakta]
    if r["mode"] == "atau":
        syarat = [p for p in r["jika"] if p in memori]
    else:
        syarat = r["jika"]
    print("  " * tingkat + f"{fakta}  <- {r['id']} ({', '.join(syarat)}) "
          f"[{', '.join(r['sumber'])}]")
    for p in syarat:
        if p in asal:
            cetak_alasan(p, asal, memori, tingkat + 1)


def tanya(kb):
    print("Jawab y/t.")
    ya = []
    for i, f in enumerate(fakta_dasar(kb), 1):
        jawab = ""
        while jawab not in ("y", "t"):
            jawab = input(f"{i}. Apakah {f}? (y/t) > ").strip().lower()
        if jawab == "y":
            ya.append(f)
    return ya


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default="kb_lele.json")
    ap.add_argument("--ya", help="fakta yang dijawab ya, dipisah titik koma (mode uji)")
    args = ap.parse_args()

    kb = muat_kb(args.kb)
    print(kb["judul"])

    if args.ya is not None:
        awal = [x.strip() for x in args.ya.split(";") if x.strip()]
        valid = set(fakta_dasar(kb))
        salah = [x for x in awal if x not in valid]
        if salah:
            sys.exit(f"Fakta tidak dikenal: {salah}\nFakta yang valid: {sorted(valid)}")
    else:
        awal = tanya(kb)

    print("\nFakta awal:", ", ".join(awal) if awal else "(tidak ada)")
    print()
    memori, asal, log = forward_chaining(kb, awal)
    for siklus, r in log:
        print(f"Siklus {siklus}: {r['id']} -> {r['maka']}")
    print(f"Siklus {len(log) + 1}: tidak ada aturan baru, berhenti")

    akhir = kesimpulan_akhir(kb, asal)
    print()
    if akhir:
        print("Kesimpulan:", "; ".join(akhir))
        print("Alasan:")
        for k in akhir:
            cetak_alasan(k, asal, memori)
    else:
        print("Kesimpulan: tidak ada kesimpulan akhir dari fakta yang diberikan")
        if asal:
            print("Fakta turunan sementara:", ", ".join(asal))

    print("\nCatatan:", kb["batas"])
    print("\nSumber:")
    dipakai = sorted({s for r in log for s in r[1]["sumber"]})
    for s in dipakai:
        print(f"  {s}: {kb['sumber'][s]}")


if __name__ == "__main__":
    main()
