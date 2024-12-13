import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import ttk
import sys
import google.generativeai as genai
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "AIzaSyDzDq-zsFue-LoKT3off5kAWRvtVj4IL2M"
DATAPATH = "bgg_dataset.csv"
"# Path to your client secrets file (downloaded from Google Cloud Console)"
CLIENT_SECRETS_FILE = "client_secret_201398039171-c12k6rtalsj5t8it9rhtmb7flg5mjeg0.apps.googleusercontent.com.json"
genai.configure(api_key="AIzaSyDzDq-zsFue-LoKT3off5kAWRvtVj4IL2M")
model = genai.GenerativeModel("gemini-1.5-flash")
class BoardGameMechanicsAnalyzer:
    """Task 1: Deze klasse laat alle functies zien die we gebruiken voor de uiteindelijke GUI"""

    def __init__(self, API_KEY, DATAPATH, max_retries=3, backoff_factor=2, max_workers=5):
        self.path = DATAPATH
        self.key = API_KEY
        self.data = self.read_clean()
        if self.data is None:
            print("Er is een fout opgetreden bij het laden van de gegevens.")
            print("Controleer het pad naar het bestand.")
            sys.exit(1)
        self.max_retries = max_retries  
        self.backoff_factor = backoff_factor 
        self.max_workers = max_workers 
        

    def read_clean(self):
        """deze functie zorgt ervoor dat het csv bestand bgg_dataset.csv wordt gelezen
        en er een nieuw bestand wordt gecreeërd op de achtergrond met bepaalde variabelen"""
        try:
            data = pd.read_csv(self.path, sep=";")
            cleandata = data.dropna(subset=["Name", "Year Published", "Mechanics", "Rating Average"], how='any')
            return cleandata
        except ImportError as e:
            print(f"Fout bij het lezen van het bestand: {e}")
            return None

    def get_genai(self, game_name, year_published):
        """Task 2, 3, 4, 5: functie voor het aanroepen van gemini via een hardcoded prompt"""
        mechanics_list = \
        self.data[(self.data['Name'] == game_name) & (self.data['Year Published'] == int(year_published))][
            'Mechanics'].values
        if len(mechanics_list) == 0:
            return "Game not found in the dataset."
        prompt = f"Which of the mechanics listed in the dataset for the game {game_name} ({year_published})do really apply for the given game?({', '.join(mechanics_list)})"
        response = self.query_genai(prompt)
        return response

    def query_genai(self, prompt):
        """Task 2, 3, 4, 5: hier wordt aangegeven door welke machine de query toegewezen aan gemini moet gaan"""
        genai.api_key = self.key
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print(response)
        return response.text.strip()

    def process_genai_result(self, game_name, year_published, gemini_response):
        """Task 3: functie voor het maken van een antwoord bij het analyseren van een game"""
        # Dit wordt in de GUI laten zien
        try:
            bgg_data = self.data[
                (self.data['Name'] == game_name) & (self.data['Year Published'] == int(year_published))]
            if bgg_data.empty:
                print(f"No data found for {game_name} ({year_published}) in the DataFrame.")
                return None
            bgg_mechanics = set(bgg_data['Mechanics'].values[0].split(", "))
            gemini_mechanics = set(gemini_response.split(", "))
            common_mechanics = bgg_mechanics.intersection(gemini_mechanics)
            accuracy_ratio = len(common_mechanics) / len(bgg_mechanics)
            return accuracy_ratio
        except ImportError as e:
            print(f"Error in process_genai_result: {e}")
            return None

    def get_top_200_games(self):
        """deze functie is ervoor bedoeld om de top 200 rated games
            te verkrijgen uit de complete dataset"""
        top_200_games = self.data.sort_values(by="Rating Average", ascending=False).head(200)
        return top_200_games[["Name", "Year Published", "Mechanics", "Rating Average"]]

    def make_csv(self, filename="top_200_games.csv"):
        """deze functie maakt van de top 200 lijst een csv bestand"""
        top_200_games = self.get_top_200_games()
        top_200_games.to_csv(filename, index=False)

    def compare_game_mechanics(self, game1_name, game2_name):
        """Task 4: deze functie is bedoeld om de mechanics van twee games met elkaar te vergelijken en daarvan de nauwkeurigheid te berekenen"""
        # Dit wordt in de GUI laten zien
        game1_mechanics = set(self.data[self.data['Name'] == game1_name]['Mechanics'].values[0].split(", "))
        game2_mechanics = set(self.data[self.data['Name'] == game2_name]['Mechanics'].values[0].split(", "))
        common_mechanics = game1_mechanics.intersection(game2_mechanics)
        accuracy_ratio = len(common_mechanics) / len(game1_mechanics)
        return common_mechanics, accuracy_ratio
    
    def fetch_game_data(self, game_name, year_published):
        """
        Makes a single API call with retry logic.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.get_genai(game_name, year_published)
                return response
            except Exception as e:
                print(f"Error for {game_name} on attempt {attempt}: {e}")
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt 
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Max retries reached for {game_name}. Skipping.")
                    return None

    def process_game(self, row):
        """
        Processes a single game's data: calls the API, processes the response, and returns the result.
        """
        game_name = row['Name']
        year_published = row['Year Published']

        response = self.fetch_game_data(game_name, year_published)
        if response is None:
            return {
                'game_name': game_name,
                'year_published': year_published,
                'response': "API call failed",
                'accuracy_ratio': 0
            }

        accuracy_ratio = self.process_genai_result(game_name, year_published, response)
        return {
            'game_name': game_name,
            'year_published': year_published,
            'response': response,
            'accuracy_ratio': accuracy_ratio
        }

    def mean_accuracy(self):
        """Task 4: Deze fucntie is ervoor bedoeld, om door de top 200 games te doorlopen
        en per game de nauwkeurigheid van het spel met het antwoord van gemini te vergelijken.
        Dit is nodig om uiteindelijk de gemiddelde nauwkeurigheid te berekenen."""
        # Deze output wordt in de GUI laten zien, maar duurt ongeveer 3 minuten
        try:
            # top_200_games.csv wordt gelezen
            top_200_games = pd.read_csv("top_200_games.csv")
            total_accuracy = 0.0
            num_games = len(top_200_games)
            result_messages = []

            
            for i, row in top_200_games.iterrows():
                game_name = row['Name']
                year_published = row['Year Published']

                response = self.get_genai(game_name, row['Year Published'])
                time.sleep(3)

              
                accuracy_ratio = self.process_genai_result(game_name, row['Year Published'], response)

               
                total_accuracy += accuracy_ratio

        
                result_messages.append(
                    f"Game: {game_name} {year_published}\ngemini's reactie: {response}\nNauwkeurigheidsratio: {accuracy_ratio}\n{'=' * 50}")

            # het gemiddelde nauwkeurigheid berekenen
            if num_games > 0:
                average_accuracy = total_accuracy / num_games
                result_messages.append(f"Totaal gemiddelde nauwkeurigheidsratio voor top 200 games: {average_accuracy}")
            else:
                result_messages.append("Geen games gevonden in het bestand 'top_200_games.csv'.")

            return result_messages

        except FileNotFoundError:
            return ["Het bestand 'top_200_games.csv' kon niet worden gevonden."]
        except ImportError as e:
            return [f"Fout bij het verwerken van de nauwkeurigheid per game: {e}"]

    def get_game_names(self):
        """Dit is voor de dropdownmenu om het spel te kiezen voor de nauwkeurigheidsratio"""
        return self.data['Name'].unique()

    def get_mechanic_accuracy(self):
        "Task 5: Dit is voor de gemiddelde nauwkeurigheid berekenen"
        
        mechanic_accuracies = {}
        top_200_games = self.get_top_200_games()
        bgg_mechanics = set(self.get_top_200_games()['Mechanics'])

        for mechanic in top_200_games['Mechanics'].explode().unique():
            total_accuracy = 0.0
            num_games = 0

            for _, row in top_200_games.iterrows():
                game_name = row['Name']
                year_published = row['Year Published']
                bgg_mechanics = set(row['Mechanics'].split(", "))

                if mechanic not in bgg_mechanics:
                    continue

                response = self.get_genai(game_name, year_published)
                accuracy_ratio = self.process_genai_result(game_name, year_published, response)
                total_accuracy += accuracy_ratio
                num_games += 1
                print(response)
                time.sleep(3)
  
            if num_games > 0:
                average_accuracy = total_accuracy / num_games
                mechanic_accuracies[mechanic] = average_accuracy

        sorted_mechanics = sorted(mechanic_accuracies.items(), key=lambda x: x[1], reverse=True)
        top_200_mechanics = sorted_mechanics[:10]
        bottom_200_mechanics = sorted_mechanics[-10:]

        return top_200_mechanics, bottom_200_mechanics 

    def find_unattributed_mechanics(self):
        """Task 5: deze fucntie is bedoeld voor het vinden van mechanics die gemini niet in de output heeft weergeven"""
        # Dit wordt samen met de vorige functie laten zien
        all_mechanics = set(self.get_top_200_games()['Mechanics'].str.split(', ').explode())
        attributed_mechanics = set()

        for _, row in self.get_top_200_games().iterrows():
            game_name = row['Name']
            year_published = row['Year Published']
            response = self.get_genai(game_name, year_published)
            gemini_mechanics = set(response.split(', '))
            attributed_mechanics.update(gemini_mechanics)

        unattributed_mechanics = all_mechanics - attributed_mechanics
        return unattributed_mechanics


class GUIApp:
    """Deze klasse is voor het implementeren voor een GUI"""

    def __init__(self, master, analyzer):
        self.master = master
        self.analyzer = analyzer

        master.title("Board Game Mechanics Analyzer")
        master.geometry("700x800")

        self.label = tk.Label(master, text="Choose the first game")
        self.label.pack(pady=10)

        self.selected_game = tk.StringVar()
        self.game_menu = ttk.Combobox(master, textvariable=self.selected_game)
        self.game_menu['values'] = tuple(self.analyzer.get_game_names())
        self.game_menu.pack(pady=10)

        self.label_year1 = tk.Label(master, text="Enter the date of publication:")
        self.label_year1.pack(pady=10)

        self.entry_year1 = tk.Entry(master)
        self.entry_year1.pack(pady=10)

        self.button_analyze = tk.Button(master, text="Analyse", command=self.analyze_game)
        self.button_analyze.pack(pady=10)

        self.label_game2 = tk.Label(master, text="Choose the second game")
        self.label_game2.pack(pady=10)

        self.selected_game2 = tk.StringVar()
        self.game_menu2 = ttk.Combobox(master, textvariable=self.selected_game2)
        self.game_menu2['values'] = tuple(analyzer.get_game_names())
        self.game_menu2.pack(pady=10)

        self.label_year2 = tk.Label(master, text="Enter the date of publication:")
        self.label_year2.pack(pady=10)

        self.entry_year2 = tk.Entry(master)
        self.entry_year2.pack(pady=10)

        self.button_compare_games = tk.Button(master, text="Compare Games", command=self.compare_games)
        self.button_compare_games.pack(pady=10)

        self.button_export_csv = tk.Button(master, text="Create a list for top 200 games", command=self.export)
        self.button_export_csv.pack(pady=10)

        self.button_avg_accuracy = tk.Button(master, text="Show average accuracy",
                                             command=self.show_average_accuracy)
        self.button_avg_accuracy.pack(pady=10)

        self.button_show_accuracy = tk.Button(master, text="Show mechanism accuracy",
                                              command=self.show_mechanic_accuracy)
        self.button_show_accuracy.pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(master, width=80, height=20)
        self.result_text.pack(pady=30)

    def analyze_game(self):
        """Dit refereert naar de fucntie in de andere klasse, om toe te voegen aan een knop in de GUI"""
        game_name = self.selected_game.get()
        year_published = self.entry_year1.get()
        if game_name and year_published:
            response = self.analyzer.get_genai(game_name, year_published)
            accuracy_ratio = self.analyzer.process_genai_result(game_name, year_published, response)

            result_message = f"genai's reactie voor {game_name}({year_published}):\n{response}\n\nNauwkeurigheidsratio: {accuracy_ratio}"
            messagebox.showinfo("Resultaat", result_message)
        else:
            messagebox.showwarning("Waarschuwing", "Voer alstublieft de naam van het bordspel in en de datum.")

    def show_top_200_games(self):
        """Dit is voor de knop om de top 200 games te laten zien."""
        top_200_games = self.analyzer.get_top_200_games()
        top_200_message = "\n".join(
            [f"{i + 1}. {row['Name']} {row['Year Published']}: {row['Rating Average']}" for i, row in
             top_200_games.iterrows()])
        messagebox.showinfo("Top 200 Games", top_200_message)

    def compare_games(self):
        """Dit is voor de knop om twee spellen met elkaar te vergelijken die zijn gekozen"""
        game1_name = self.selected_game.get()
        year1_published = self.entry_year1.get()
        game2_name = self.selected_game2.get()
        year2_published = self.entry_year2.get()
        if game1_name and year1_published and game2_name and year2_published:
            common_mechanics, accuracy_ratio = self.analyzer.compare_game_mechanics(game1_name, game2_name)
            result_message = f"Gemeenschappelijke mechanica: {', '.join(common_mechanics)}\n\nNauwkeurigheidsratio: {accuracy_ratio}"
            messagebox.showinfo("Vergelijk Games", result_message)
        else:
            messagebox.showwarning("Waarschuwing", "Voer alstublieft de namen van beide bordspellen in.")

    def export(self):
        """Dit is voor de knop om de top 200 games naar een csv bestand te exporteren"""
        try:
            self.analyzer.make_csv("top_200_games.csv")
            messagebox.showinfo("Gelukt", "Het is gelukt om de lijst aan te maken")
        except ImportError as e:
            messagebox.showwarning("Fout bij het expoerteren naar CSV: {e}")
        self.analyzer.mean_accuracy()



    def show_average_accuracy(self):
        """Dit is voor de knop om de gemiddelde nauwkeurigheid te berekenen"""
        result_messages = self.analyzer.mean_accuracy()
        result_message = "\n".join(result_messages)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_message)

    def show_mechanic_accuracy(self):
        """Dit is voor de knop om de top, onderste 10 mechanismen en ongeattribueerde mechanismen te laten zien"""
        # Deze wordt laten zien in de GUI, alleen duurt even vanwege het krijgen van een antwoord van genai en de nauwkeruigheid bereken. Dus even geduld
        top_200, bottom_200 = self.analyzer.get_mechanic_accuracy()
        unattributed_mechanics = self.analyzer.find_unattributed_mechanics()

        result_message = "Top 10 Mechanismen met Hoogste Nauwkeurigheid:\n"
        for mechanic, accuracy in top_200:
            result_message += f"{mechanic}: {accuracy}\n"

        result_message += "\nBottom 10 Mechanismen met Laagste Nauwkeurigheid:\n"
        for mechanic, accuracy in bottom_200:
            result_message += f"{mechanic}: {accuracy}\n"

        result_message += "\nMechanismen nooit toegeschreven door gemini:\n"
        result_message += ", ".join(unattributed_mechanics)

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_message)

"""Hier wordt de GUI geactiveerd en de tests worden pas gedaan, nadat de GUI is afgesloten"""
# Applicatie wordt gestart
if __name__ == '__main__':
    analyzer = BoardGameMechanicsAnalyzer(API_KEY, DATAPATH)
    venster = tk.Tk()
    app = GUIApp(venster, analyzer)
    venster.mainloop()