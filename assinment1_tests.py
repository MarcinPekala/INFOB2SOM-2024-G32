import unittest
from unittest.mock import patch
import tkinter as tk
from tkinter import messagebox
import time
import assignment1 as a1

API_KEY = "AIzaSyBeFDa_BHcPKi8sebnjMkq5WHRenKEIRIs"
DATAPATH = "bgg_dataset.csv"


class TestBoardGameMechanicsAnalyzer(unittest.TestCase):
    """Deze klasse is gemaakt voor het testen van de functies"""

    def setUp(self):
        self.analyzer = a1.BoardGameMechanicsAnalyzer(API_KEY, DATAPATH)

    def test_get_genai_successful(self):
        """Hier wordt getest of gemini een antwoord geeft"""
        response = self.analyzer.get_genai("Gloomhaven", 2017)
        self.assertIsInstance(response, str)

    @patch('genai.Completion.create')
    def test_query_genai_mocked(self, mock_genai):
        """Hier wordt gekeken naar of genai het mock antwoordt geeft"""
        mock_genai.return_value.text = "Mocked response"
        response = self.analyzer.query_genai("Test prompt")
        self.assertEqual(response, "Mocked response")


class TestGUIApp(unittest.TestCase):
    """Deze initialiseert de omgeving om de GUI te testen"""

    def setUp(self):
        self.analyzer = a1.BoardGameMechanicsAnalyzer(API_KEY, DATAPATH)
        self.master = tk.Tk()

    def tearDown(self):
        """Na elke test wordt er opgeruimd"""
        self.master.destroy()

    def test_analyze_game_successful(self):
        """Er wordt gekeken naar of analyze_game succesvol wordt uigevoerd"""
        app = a1.GUIApp(self.master, self.analyzer)
        app.selected_game.set("Gloomhaven")
        app.entry_year1.insert(0, "2017")
        with patch.object(messagebox, 'showinfo') as mock_info:
            app.analyze_game()
            mock_info.assert_called_once()

    def test_compare_games_successful(self):
        """Er wordt gekeken naar of compare_games succesvol wordt uigevoerd"""
        app = a1.GUIApp(self.master, self.analyzer)
        app.selected_game.set("Gloomhaven")
        app.entry_year1.insert(0, "2017")
        app.selected_game2.set("Pandemic Legacy: Season 1")
        app.entry_year2.insert(0, "2015")
        with patch.object(messagebox, 'showinfo') as mock_info:
            app.compare_games()
            mock_info.assert_called_once()


# Nadat de applicatie wordt afgesloten, worden de test gestart
if __name__ == '_main_':
    unittest.main()
time.sleep(2)
