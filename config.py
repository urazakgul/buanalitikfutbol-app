PLOT_STYLE = "fivethirtyeight"

event_type_translations = {
    "pass": "Pas",
    "goal": "Gol",
    "free-kick": "Serbest Vuruş",
    "clearance": "Uzaklaştırma",
    "ball-movement": "Top Taşıma",
    "corner": "Korner",
    "post": "Direk",
    "save": "Kurtarış",
    "miss": "Kaçırma"
}

event_colors = {
    "Pas": "#0074D9",
    "Gol": "#FF4136",
    "Serbest Vuruş": "#2ECC40",
    "Uzaklaştırma": "#B10DC9",
    "Top Taşıma": "#FF851B",
    "Korner": "#FFDC00",
    "Direk": "#FF69B4",
    "Kurtarış": "#7FDBFF",
    "Kaçırma": "#AAAAAA"
}

team_list = [
    "Adana Demirspor",
    "Alanyaspor",
    "Antalyaspor",
    "Beşiktaş",
    "Bodrum",
    "Çaykur Rizespor",
    "Eyüpspor",
    "Fenerbahçe",
    "Galatasaray",
    "Gaziantep",
    "Göztepe",
    "Hatayspor",
    "İstanbul Başakşehir",
    "Kasımpaşa",
    "Kayserispor",
    "Konyaspor",
    "Samsunspor",
    "Sivasspor",
    "Trabzonspor"
]

change_situations = {
    "assisted":"Asiste Edilen",
    "corner":"Korner Sonrası",
    "regular":"Akan Oyundan",
    "set-piece":"Duran Toplardan",
    "fast-break":"Hızlı Hücum Sırasında",
    "free-kick":"Serbest Vuruştan",
    "penalty":"Penaltıdan",
    "throw-in-set-piece":"Taç Atışından Sonra"
}

change_body_parts = {
    "head":"Kafa",
    "left-foot":"Sol Ayak",
    "right-foot":"Sağ Ayak",
    "other":"Diğer"
}

change_goal_locations = {
    "high-centre": "Üst-Orta",
    "high-left": "Üst-Sol",
    "high-right": "Üst-Sağ",
    "low-centre": "Alt-Orta",
    "low-left": "Alt-Sol",
    "low-right": "Alt-Sağ",
    "close-right": "Yakın-Sağ",
    "close-left": "Yakın-Sol",
    "close-high": "Yakın-Üst",
    "close-high-right": "Yakın-Üst-Sağ",
    "close-high-left": "Yakın-Üst-Sol",
    "left": "Sol",
    "right": "Sağ",
    "high": "Üst"
}

change_player_positions = {
    "F": "Forvet",
    "M": "Orta Saha",
    "D": "Defans",
    "G": "Kaleci"
}

match_performances = [
    "Topa Sahip Olma",
    "Pas Başarısı",
    "Gol Olan/Kaçırılan Büyük Fırsatlar",
    "Şut Başarısı",
    "Ceza Sahası İçi/Dışı Şut Oranı",
    "Ceza Sahasında Topla Buluşma",
    "Üçüncü Bölgeye Giriş Sayısı",
    "Üçüncü Bölge Aksiyon Başarısı",
    "Yaptığı ile Kendisine Yapılan Faul Sayısı Farkı",
    "Faul Başına Kart Sayısı",
    "Başarılı Uzun Pas Oranı",
    "Başarılı Orta Oranı"
]

match_performance_translations = {
    "Ball possession": "Topa Sahip Olma",
    "Expected goals": "Beklenen Goller",
    "Big chances": "Büyük Fırsatlar",
    "Total shots": "Toplam Şutlar",
    "Goalkeeper saves": "Kaleci Kurtarışları",
    "Corner kicks": "Köşe Vuruşları",
    "Fouls": "Fauller",
    "Passes": "Paslar",
    "Tackles": "Müdahaleler",
    "Free kicks": "Serbest Vuruşlar",
    "Yellow cards": "Sarı Kartlar",
    "Shots on target": "İsabetli Şutlar",
    "Hit woodwork": "Direğe Çarpan Şutlar",
    "Shots off target": "İsabetsiz Şutlar",
    "Blocked shots": "Bloke Edilen Şutlar",
    "Shots inside box": "Ceza Sahası İçinden Şutlar",
    "Shots outside box": "Ceza Sahası Dışından Şutlar",
    "Big chances scored": "Gol Olan Büyük Fırsatlar",
    "Big chances missed": "Kaçırılan Büyük Fırsatlar",
    "Through balls": "Ara Paslar",
    "Touches in penalty area": "Ceza Sahasında Topla Buluşma",
    "Fouled in final third": "Üçüncü Bölgede Faul Yapılan",
    "Offsides": "Ofsaytlar",
    "Accurate passes": "İsabetli Paslar",
    "Throw-ins": "Taç Atışları",
    "Final third entries": "Üçüncü Bölgeye Girişler",
    "Final third phase": "Üçüncü Bölge Aşaması",
    "Long balls": "Uzun Paslar",
    "Crosses": "Ortalar",
    "Duels": "İkili Mücadeleler",
    "Dispossessed": "Top Kayıpları",
    "Ground duels": "Yer Mücadeleleri",
    "Aerial duels": "Hava Topu Mücadeleleri",
    "Dribbles": "Çalımlar",
    "Tackles won": "Kazanılan Müdahaleler",
    "Total tackles": "Toplam Müdahaleler",
    "Interceptions": "Top Kesmeler",
    "Recoveries": "Top Kazanımları",
    "Clearances": "Uzaklaştırmalar",
    "Total saves": "Toplam Kurtarışlar",
    "Goals prevented": "Önlenen Goller",
    "Goal kicks": "Kale Vuruşları",
    "High claims": "Yüksek Topları Alma",
    "Big saves": "Büyük Kurtarışlar",
    "Red cards": "Kırmızı Kartlar",
    "Errors lead to a goal": "Gole Neden Olan Hatalar",
    "Errors lead to a shot": "Şuta Neden Olan Hatalar",
    "Punches": "Yumruklamalar",
    "Penalty saves": "Penaltı Kurtarışları"
}

match_stats_group_name = [
    "Genel Görünüm",
    "Şutlar",
    "Hücum",
    "Paslar",
    "İkili Mücadeleler",
    "Savunma",
    "Kalecilik"
]

match_stats_group_name_translations = {
    "Match overview": "Genel Görünüm",
    "Shots": "Şutlar",
    "Attack": "Hücum",
    "Passes": "Paslar",
    "Duels": "İkili Mücadeleler",
    "Defending": "Savunma",
    "Goalkeeping": "Kalecilik"
}