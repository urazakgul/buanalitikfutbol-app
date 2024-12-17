from config import match_performance_translations
from code.utils.plotters import plot_boxplot, plot_stacked_bar_chart, plot_stacked_horizontal_bar, plot_horizontal_bar
from code.utils.helpers import load_filtered_json_files
import os
import pandas as pd
import streamlit as st

def clean_percent_columns(dataframe, columns_to_check, target_columns):
    for index, row in dataframe.iterrows():
        if any(keyword in row["name"] for keyword in columns_to_check):
            for col in target_columns:
                dataframe.at[index, col] = row[col].replace("%", "").strip()
    return dataframe

def clean_parenthesis_columns(dataframe, columns_to_check, target_columns):
    for index, row in dataframe.iterrows():
        if any(keyword in row["name"] for keyword in columns_to_check):
            for col in target_columns:
                if "(" in row[col]:
                    dataframe.at[index, col] = row[col].split("(")[0].strip()
    return dataframe

def create_performance_plot(master_df, result_all_stats_df, subcategory, league_display, season_display, last_round):
    if subcategory == "Topa Sahip Olma":
        possession_data = result_all_stats_df[result_all_stats_df["stat_name"] == "Topa Sahip Olma"]

        median_possession_by_team = possession_data.groupby("team_name")["stat_value"].median().reset_index()
        median_possession_by_team = median_possession_by_team.sort_values("stat_value", ascending=False)

        sorted_team_names = median_possession_by_team["team_name"]

        plot_boxplot(
            data=possession_data,
            x="stat_value",
            y="team_name",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Topa Sahip Olma Oranı",
            xlabel="Topa Sahip Olma Oranı (%) (Medyan)",
            ylabel="",
            ordered_labels=sorted_team_names,
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png"
        )
    elif subcategory == "Pas Başarısı":
        passing_data = result_all_stats_df[result_all_stats_df["stat_name"].isin(["Paslar", "İsabetli Paslar"])]

        team_passing_stats = passing_data.pivot_table(
            index="team_name",
            columns="stat_name",
            values="stat_value",
            aggfunc="sum",
            fill_value=0
        )

        team_passing_stats["Toplam Pas"] = team_passing_stats["Paslar"]
        team_passing_stats["İsabetsiz Paslar"] = team_passing_stats["Toplam Pas"] - team_passing_stats["İsabetli Paslar"]

        plot_stacked_bar_chart(
            data=team_passing_stats,
            stat_columns=["İsabetli Paslar", "İsabetsiz Paslar"],
            total_column="Toplam Pas",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Pas Başarısı",
            xlabel="Pas Sayısı",
            ylabel="",
            colors={"İsabetli Paslar": "#4169E1", "İsabetsiz Paslar": "#CD5C5C"},
            sort_by="Toplam Pas",
            ascending=True,
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png"
        )
    elif subcategory == "Gol Olan/Kaçırılan Büyük Fırsatlar":
        big_chances_data = result_all_stats_df[
            result_all_stats_df["stat_name"].isin(["Gol Olan Büyük Fırsatlar", "Kaçırılan Büyük Fırsatlar"])
        ]

        team_big_chances_stats = big_chances_data.pivot_table(
            index="team_name",
            columns="stat_name",
            values="stat_value",
            aggfunc="sum"
        ).fillna(0)

        team_big_chances_stats["Toplam Büyük Fırsat"] = team_big_chances_stats.sum(axis=1)

        team_big_chances_stats = team_big_chances_stats.sort_values("Toplam Büyük Fırsat")

        plot_stacked_horizontal_bar(
            data=team_big_chances_stats,
            stat_columns=["Gol Olan Büyük Fırsatlar", "Kaçırılan Büyük Fırsatlar"],
            total_column="Toplam Büyük Fırsat",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Büyük Fırsatları Değerlendirme Oranı",
            xlabel="Büyük Fırsat Sayısı",
            ylabel="",
            colors={
                "Gol Olan Büyük Fırsatlar": "#4169E1",
                "Kaçırılan Büyük Fırsatlar": "#CD5C5C"
            },
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png"
        )
    elif subcategory == "Şut Başarısı":
        shooting_data = result_all_stats_df[
            result_all_stats_df["stat_name"].isin(
                ["İsabetli Şutlar", "İsabetsiz Şutlar", "Bloke Edilen Şutlar", "Direğe Çarpan Şutlar"]
            )
        ]

        team_shooting_stats = shooting_data.pivot_table(
            index="team_name",
            columns="stat_name",
            values="stat_value",
            aggfunc="sum",
            fill_value=0
        )

        team_shooting_stats["Toplam Şut"] = team_shooting_stats.sum(axis=1)

        shooting_categories = ["İsabetli Şutlar", "İsabetsiz Şutlar", "Bloke Edilen Şutlar", "Direğe Çarpan Şutlar"]

        for category in shooting_categories:
            team_shooting_stats[f"{category} (%)"] = (team_shooting_stats[category] / team_shooting_stats["Toplam Şut"]) * 100

        team_shooting_stats = team_shooting_stats.sort_values("Toplam Şut")

        plot_stacked_horizontal_bar(
            data=team_shooting_stats,
            stat_columns=shooting_categories,
            total_column="Toplam Şut",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Şut Başarısı",
            xlabel="Şut Sayısı",
            ylabel="",
            colors={
                "İsabetli Şutlar": "#4169E1",
                "İsabetsiz Şutlar": "#CD5C5C",
                "Bloke Edilen Şutlar": "#FFA07A",
                "Direğe Çarpan Şutlar": "#FFD700"
            },
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png"
        )
    elif subcategory == "Ceza Sahası İçi/Dışı Şut Oranı":
        penalty_area_shooting_data = result_all_stats_df[
            result_all_stats_df["stat_name"].isin(["Ceza Sahası İçinden Şutlar", "Ceza Sahası Dışından Şutlar"])
        ]

        team_penalty_area_stats = penalty_area_shooting_data.pivot_table(
            index="team_name",
            columns="stat_name",
            values="stat_value",
            aggfunc="sum",
            fill_value=0
        )

        team_penalty_area_stats["Toplam Şut"] = team_penalty_area_stats.sum(axis=1)

        shooting_categories = ["Ceza Sahası İçinden Şutlar", "Ceza Sahası Dışından Şutlar"]

        for category in shooting_categories:
            team_penalty_area_stats[f"{category} (%)"] = (team_penalty_area_stats[category] / team_penalty_area_stats["Toplam Şut"]) * 100

        team_penalty_area_stats = team_penalty_area_stats.sort_values("Toplam Şut")

        plot_stacked_horizontal_bar(
            data=team_penalty_area_stats,
            stat_columns=shooting_categories,
            total_column="Toplam Şut",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Ceza Sahasına Göre Şut Tercih Oranı",
            xlabel="Şut Sayısı",
            ylabel="",
            colors={
                "Ceza Sahası İçinden Şutlar": "#4169E1",
                "Ceza Sahası Dışından Şutlar": "#CD5C5C"
            },
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png"
        )
    elif subcategory == "Ceza Sahasında Topla Buluşma":
        penalty_area_touch_data = result_all_stats_df[
            result_all_stats_df["stat_name"] == "Ceza Sahasında Topla Buluşma"
        ].groupby("team_name", as_index=False)["stat_value"].sum()

        plot_horizontal_bar(
            data=penalty_area_touch_data,
            x="stat_value",
            y="team_name",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Ceza Sahasında Topla Buluşma Sayıları",
            xlabel="Ceza Sahasında Topla Buluşma Sayısı",
            ylabel="",
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            sort_by="stat_value",
            ascending=True,
            calculate_percentages=False,
            cmap_name="coolwarm_r",
            is_int=True
        )
    elif subcategory == "Üçüncü Bölgeye Giriş Sayısı":
        final_third_entry_data = result_all_stats_df[
            result_all_stats_df["stat_name"] == "Üçüncü Bölgeye Girişler"
        ].groupby("team_name", as_index=False)["stat_value"].sum()

        plot_horizontal_bar(
            data=final_third_entry_data,
            x="stat_value",
            y="team_name",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Üçüncü Bölgeye Giriş Sayısı",
            xlabel="Üçüncü Bölgeye Giriş Sayısı",
            ylabel="",
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            sort_by="stat_value",
            ascending=True,
            calculate_percentages=False,
            cmap_name="coolwarm_r",
            is_int=True
        )
    elif subcategory == "Üçüncü Bölge Aksiyon Başarısı":
        final_third_action_data = result_all_stats_df[
            result_all_stats_df["stat_name"] == "Üçüncü Bölge Aşaması"
        ]

        final_third_action_data[["Başarılı Aksiyon", "Toplam Aksiyon"]] = (
            final_third_action_data["stat_value"]
            .str.split("/", expand=True)
            .astype(int)
        )

        final_third_action_data["Başarısız Aksiyon"] = (
            final_third_action_data["Toplam Aksiyon"] - final_third_action_data["Başarılı Aksiyon"]
        )

        team_final_third_actions = final_third_action_data.groupby("team_name", as_index=True).sum()

        plot_stacked_horizontal_bar(
            data=team_final_third_actions,
            stat_columns=["Başarılı Aksiyon", "Başarısız Aksiyon"],
            total_column="Toplam Aksiyon",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Üçüncü Bölge Aksiyon Oranı",
            xlabel="Üçüncü Bölge Aksiyon Sayısı",
            ylabel="",
            colors={
                "Başarılı Aksiyon": "#4169E1",
                "Başarısız Aksiyon": "#CD5C5C"
            },
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            sort_by="Toplam Aksiyon",
            ascending=True
        )
    elif subcategory == "Yaptığı ile Kendisine Yapılan Faul Sayısı Farkı":
        foul_data = master_df[master_df["name"] == "Fauller"]

        fouls_home = foul_data.groupby("home_team").agg(
            Yaptigi=("home_team_stats", "sum"),
            Yapilan=("away_team_stats", "sum")
        ).reset_index().rename(columns={"home_team": "team"})

        fouls_away = foul_data.groupby("away_team").agg(
            Yaptigi=("away_team_stats", "sum"),
            Yapilan=("home_team_stats", "sum")
        ).reset_index().rename(columns={"away_team": "team"})

        total_fouls_summary = (
            pd.concat([fouls_home, fouls_away], axis=0)
            .groupby("team", as_index=False)
            .sum()
        )

        total_fouls_summary["Faul Farkı"] = (
            total_fouls_summary["Yaptigi"] - total_fouls_summary["Yapilan"]
        )
        total_fouls_summary = total_fouls_summary.sort_values("Faul Farkı", ascending=True)

        plot_horizontal_bar(
            data=total_fouls_summary,
            x="Faul Farkı",
            y="team",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Yaptığı ile Kendisine Yapılan Faul Sayısı Farkı",
            xlabel="Faul Sayısı Farkı",
            ylabel="",
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            calculate_percentages=False,
            sort_by="Faul Farkı",
            ascending=True,
            cmap_name="coolwarm",
            is_int=True
        )
    elif subcategory == "Faul Başına Kart Sayısı":
        fouls_data = result_all_stats_df[
            result_all_stats_df["stat_name"] == "Fauller"
        ].groupby("team_name", as_index=False)["stat_value"].sum().rename(columns={"stat_value": "Faul Sayısı"})

        yellow_cards_data = result_all_stats_df[
            result_all_stats_df["stat_name"] == "Sarı Kartlar"
        ].groupby("team_name", as_index=False)["stat_value"].sum().rename(columns={"stat_value": "Sarı Kart Sayısı"})

        red_cards_data = result_all_stats_df[
            result_all_stats_df["stat_name"] == "Kırmızı Kartlar"
        ].groupby("team_name", as_index=False)["stat_value"].sum().rename(columns={"stat_value": "Kırmızı Kart Sayısı"})

        cards_data = pd.merge(
            yellow_cards_data, red_cards_data,
            on="team_name", how="outer"
        ).fillna(0)

        cards_data["Toplam Kart Sayısı"] = cards_data["Sarı Kart Sayısı"] + cards_data["Kırmızı Kart Sayısı"]

        merged_data = pd.merge(
            fouls_data, cards_data[["team_name", "Toplam Kart Sayısı"]],
            on="team_name"
        )

        merged_data["Faul Başına Kart Sayısı"] = merged_data["Toplam Kart Sayısı"] / merged_data["Faul Sayısı"]

        merged_data = merged_data.sort_values("Faul Başına Kart Sayısı", ascending=True)

        plot_horizontal_bar(
            data=merged_data,
            x="Faul Başına Kart Sayısı",
            y="team_name",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Yaptığı Faul Başına Kart (Sarı ve Kırmızı) Sayısı",
            xlabel="Faul Başına Kart (Sarı ve Kırmızı) Sayısı",
            ylabel="",
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            calculate_percentages=False,
            sort_by="Faul Başına Kart Sayısı",
            ascending=True,
            cmap_name="coolwarm",
            is_int=False
        )
    elif subcategory == "Başarılı Uzun Pas Oranı":
        long_pass_data = result_all_stats_df[result_all_stats_df["stat_name"] == "Uzun Paslar"]

        long_pass_data[["Başarılı Uzun Pas", "Toplam Uzun Pas"]] = (
            long_pass_data["stat_value"]
            .str.split("/", expand=True)
            .astype(int)
        )

        long_pass_data["Başarısız Uzun Pas"] = (
            long_pass_data["Toplam Uzun Pas"] - long_pass_data["Başarılı Uzun Pas"]
        )

        grouped_long_pass_data = long_pass_data.groupby("team_name", as_index=True).sum()

        plot_stacked_horizontal_bar(
            data=grouped_long_pass_data,
            stat_columns=["Başarılı Uzun Pas", "Başarısız Uzun Pas"],
            total_column="Toplam Uzun Pas",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Başarılı ve Başarısız Uzun Pas Oranı",
            xlabel="Uzun Pas Sayısı",
            ylabel="",
            colors={
                "Başarılı Uzun Pas": "#4169E1",
                "Başarısız Uzun Pas": "#CD5C5C"
            },
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            sort_by="Toplam Uzun Pas",
            ascending=True
        )
    elif subcategory == "Başarılı Orta Oranı":
        crossing_data = result_all_stats_df[result_all_stats_df["stat_name"] == "Ortalar"]

        crossing_data[["Başarılı Orta", "Toplam Orta"]] = (
            crossing_data["stat_value"]
            .str.split("/", expand=True)
            .astype(int)
        )

        crossing_data["Başarısız Orta"] = (
            crossing_data["Toplam Orta"] - crossing_data["Başarılı Orta"]
        )

        grouped_crossing_data = crossing_data.groupby("team_name", as_index=True).sum()

        plot_stacked_horizontal_bar(
            data=grouped_crossing_data,
            stat_columns=["Başarılı Orta", "Başarısız Orta"],
            total_column="Toplam Orta",
            title=f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada Takımların Başarılı ve Başarısız Orta Oranı",
            xlabel="Orta Sayısı",
            ylabel="",
            colors={
                "Başarılı Orta": "#4169E1",
                "Başarısız Orta": "#CD5C5C"
            },
            filename=f"{league_display}_{season_display}_{last_round}_{subcategory}.png",
            sort_by="Toplam Orta",
            ascending=True
        )

def main(subcategory, league, season, league_display, season_display):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        match_stats_data = load_filtered_json_files(directories, "match_stats", league, season)
        matches_data = load_filtered_json_files(directories, "matches", league, season)

        matches_data = matches_data[["game_id","home_team","away_team"]]

        match_stats_data = match_stats_data[match_stats_data["period"] == "ALL"]
        match_stats_data = match_stats_data.rename(columns={
            "home_team":"home_team_stats",
            "away_team":"away_team_stats"
        })

        percent_keywords = ["Ball possession", "Tackles won", "Duels"]
        parenthesis_keywords = ["Final third phase", "Long balls", "Crosses", "Ground duels", "Aerial duels", "Dribbles"]
        target_columns = ["home_team_stats", "away_team_stats"]

        match_stats_data = clean_percent_columns(match_stats_data, percent_keywords, target_columns)
        match_stats_data = clean_parenthesis_columns(match_stats_data, parenthesis_keywords, target_columns)

        match_stats_data.loc[~match_stats_data["home_team_stats"].str.contains("/", na=False), "home_team_stats"] = \
            pd.to_numeric(match_stats_data["home_team_stats"], errors="coerce")

        match_stats_data.loc[~match_stats_data["away_team_stats"].str.contains("/", na=False), "away_team_stats"] = \
            pd.to_numeric(match_stats_data["away_team_stats"], errors="coerce")

        master_df = match_stats_data.merge(
            matches_data,
            on="game_id"
        )

        master_df["name"] = master_df["name"].replace(match_performance_translations)

        all_stats_df_list = []

        for stat in master_df["name"].unique():
            stat_df = master_df[master_df["name"] == stat]
            temp_df = pd.DataFrame({
                "team_name": pd.concat([stat_df["home_team"], stat_df["away_team"]]),
                "stat_name": [stat] * len(stat_df) * 2,
                "stat_value": pd.concat([stat_df["home_team_stats"], stat_df["away_team_stats"]])
            })
            all_stats_df_list.append(temp_df)

        result_all_stats_df = pd.concat(all_stats_df_list, ignore_index=True)
        result_all_stats_df = result_all_stats_df.reset_index(drop=True)

        last_round = master_df["round"].max()

        create_performance_plot(master_df, result_all_stats_df, subcategory, league_display, season_display, last_round)

    except Exception as e:
        st.error(f"Uygun veri bulunamadı. {e}")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/buanalitikfutbol-app/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )