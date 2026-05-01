# baselines.py - Baseline (Normal Profil) Hesaplama
# Her kullanıcı için bi "normal davranış" profili oluşturuyorz
# Sonra yeni gelen olayları (eventleri) bu profille karşılaştırcaz.
#
# Z-skoru hesaplaması da var. (istatistik dersinden hatırladığım kadarıyla: z = (x - mean) / std)
# umarım doğru çalışıyordur...

import math
from models import Event, Baseline
import config


def calculate_user_baseline(username, events):
    """
    Tek bir kullanıcının profilini oluşturur.
    Toplam işlem sayısı, dosya okuma/yazma vb. bulur.
    """

    baseline = Baseline(username=username)

    # eğer adamın hiç eventi yoksa patlamasın diye direk dönüyoruz
    if not events:
        # print("event yok:", username) # TODO: burayı sonra sil
        return baseline

    baseline.total_events = len(events)

    # Dosya işlemlerini say
    okuma_sayisi = 0
    yazma_sayisi = 0
    silme_sayisi = 0

    for e in events:
        if e.action == "READ":
            okuma_sayisi += 1
        elif e.action == "WRITE":
            yazma_sayisi += 1
        elif e.action == "DELETE":
            silme_sayisi += 1

    baseline.file_reads = okuma_sayisi
    baseline.file_writes = yazma_sayisi
    baseline.file_deletes = silme_sayisi
    
    # toplam dosya operasyonu
    baseline.total_file_ops = okuma_sayisi + yazma_sayisi + silme_sayisi

    # Hangi saatlerde aktif onu bul (gececi mi gündüzcü mü anlamak için)
    saat_dagilimi = {}
    farkli_gunler = set() # aynı günü 2 kere saymasın diye set kullandım

    for event in events:
        saat = event.timestamp.hour
        gun = event.timestamp.date()

        # o saatteki işlemi 1 artır
        if saat in saat_dagilimi:
            saat_dagilimi[saat] += 1
        else:
            saat_dagilimi[saat] = 1

        farkli_gunler.add(gun)

        # mesai dışı mı kontrol et
        if saat < config.WORK_HOURS_START or saat >= config.WORK_HOURS_END:
            baseline.off_hours_count += 1

        # gece yarısı mı? (kim gece 3'te sisteme girer ki?)
        if saat >= config.NIGHT_HOURS_START and saat < config.NIGHT_HOURS_END:
            baseline.deep_night_count += 1

    baseline.active_hours = saat_dagilimi
    baseline.active_days = len(farkli_gunler)

    # mesai dışı çalışma oranını bul (0'a bölünme hatası almamak için if koydum)
    if baseline.total_events > 0:
        baseline.off_hours_ratio = baseline.off_hours_count / baseline.total_events

    # günlük ortalama olay sayısı
    if baseline.active_days > 0:
        baseline.events_per_day = baseline.total_events / baseline.active_days

    # saatlik ortalama ve standart sapma hesabı (baya karışık buralar)
    saat_degerleri = list(saat_dagilimi.values())
    if len(saat_degerleri) > 0:
        # ortalama bul
        toplam = 0
        for val in saat_degerleri:
            toplam += val
        ortalama = toplam / len(saat_degerleri)
        baseline.events_per_hour_avg = ortalama

        # standart sapma (std) bul
        # n-1'e bölmek gerekiyormuş örneklem olduğu için (hocanın notlarında öyle yazıyordu)
        if len(saat_degerleri) > 1:
            fark_kare_toplam = 0
            for val in saat_degerleri:
                fark = val - ortalama
                fark_kare_toplam += (fark * fark)
            
            varyans = fark_kare_toplam / (len(saat_degerleri) - 1)
            baseline.events_per_hour_std = math.sqrt(varyans)

    return baseline


def calculate_group_zscores(baselines):
    """
    Gruptaki diğer kişilere göre Z-Skoru hesaplar.
    Z skoru = (kişinin değeri - grubun ortalaması) / grubun standart sapması
    """

    # Eğer sadece 1 kişi varsa karşılaştıramayız
    if len(baselines) < 2:
        return baselines

    # herkesin verilerini bir listede toplayalım
    hacimler = []
    dosya_islemleri = []
    silmeler = []

    for b in baselines:
        hacimler.append(b.total_events)
        dosya_islemleri.append(b.total_file_ops)
        silmeler.append(b.file_deletes)

    # 1. Toplam hacim (volume) için ortalama ve sapma
    vol_toplam = sum(hacimler)
    vol_ort = vol_toplam / len(hacimler)

    vol_fark = 0
    for v in hacimler:
        vol_fark += (v - vol_ort) ** 2
    vol_std = math.sqrt(vol_fark / (len(hacimler) - 1))

    # 2. Dosya işlemleri için ortalama ve sapma
    fops_toplam = sum(dosya_islemleri)
    fops_ort = fops_toplam / len(dosya_islemleri)

    fops_fark = 0
    for v in dosya_islemleri:
        fops_fark += (v - fops_ort) ** 2
    fops_std = math.sqrt(fops_fark / (len(dosya_islemleri) - 1))

    # 3. Silme işlemleri için ortalama ve sapma (bunu sabotaj tespiti için eklemiştim)
    del_toplam = sum(silmeler)
    del_ort = del_toplam / len(silmeler)

    del_fark = 0
    for v in silmeler:
        del_fark += (v - del_ort) ** 2
    del_std = math.sqrt(del_fark / (len(silmeler) - 1))

    # Herkese z-skorlarını atayalım
    for baseline in baselines:
        # std 0 olursa (herkes aynı şeyi yapmışsa) divide by zero hatası verir, o yüzden kontrol koydum
        if vol_std > 0:
            baseline.volume_zscore = (baseline.total_events - vol_ort) / vol_std
        
        if fops_std > 0:
            baseline.file_ops_zscore = (baseline.total_file_ops - fops_ort) / fops_std

        if del_std > 0:
            baseline.delete_zscore = (baseline.file_deletes - del_ort) / del_std

    return baselines


def calculate_all_baselines(user_events_dict):
    """
    Bütün kullanıcılar için baseline hesaplayan ana fonksiyon.
    Run dosyasından bu çağırılıyor.
    """
    baselines = []
    
    # dictionary'de dönüyoruz (items kullanmak lazım unutma!)
    for username, events in user_events_dict.items():
        user_baseline = calculate_user_baseline(username, events)
        baselines.append(user_baseline)
        
    # en son herkesin birbiriyle kıyaslamasını yapıyoruz
    baselines = calculate_group_zscores(baselines)
    
    return baselines


def baseline_summary(baseline):
    """
    Ekrana basmak için string döndürür.
    Terminalde falan log basarken kullanıyorum bunu.
    """
    # virgülden sonra 2 basamak göstermek için .2f kullandım (stack overflow'dan buldum)
    return f"  User: {baseline.username} | Total Events: {baseline.total_events} | File Ops: {baseline.total_file_ops} | Z-Score (Vol): {baseline.volume_zscore:.2f}"
