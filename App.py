import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import requests
from html.parser import HTMLParser
import json
from urllib.parse import quote


class WikiHTMLParser(HTMLParser):
    """Parser to extract readable text from Wikipedia HTML content."""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.current_tag = None
        self.skip_tags = {'sup', 'span', 'table', 'style', 'script'}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if (self.current_tag not in self.skip_tags and 
            data.strip() and 
            not data.startswith('[') and 
            not data.startswith('/')):
            self.text.append(data.strip())

    def get_text(self):
        return '\n'.join(line for line in self.text if line)


class WikiAPIAgent:
    """Handles all Wikipedia API interactions."""
    
    LANGUAGES = {
        "English": "en",
        "Українська": "uk"
    }
    
    @staticmethod
    def get_summary(topic, language="en"):
        try:
            url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('extract', 'No summary available.')
        except requests.RequestException as e:
            return f"Error fetching summary: {str(e)}"

    @staticmethod
    def get_full_article(topic, language="en"):
        try:
            url = f"https://{language}.wikipedia.org/w/api.php"
            params = {
                'action': 'parse',
                'page': topic,
                'format': 'json',
                'prop': 'text',
                'formatversion': '2'
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                return f"Error: {data['error']['info']}"
            
            html_content = data['parse']['text']
            parser = WikiHTMLParser()
            parser.feed(html_content)
            return parser.get_text()
        except requests.RequestException as e:
            return f"Error fetching article: {str(e)}"
        except (KeyError, json.JSONDecodeError) as e:
            return f"Error parsing response: {str(e)}"


class WikiSearchApp:
    """Main application class for the Wikipedia Search tool."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Wikipedia Search | Пошук у Вікіпедії")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Set custom fonts
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=10, family="Segoe UI")
        self.heading_font = font.Font(family="Segoe UI", size=16, weight="bold")
        
        self.setup_ui()

    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.configure('TButton', padding=8, font=('Segoe UI', 10))
        style.configure('TEntry', padding=8, font=('Segoe UI', 10))
        style.configure('TCheckbutton', padding=5, font=('Segoe UI', 10))
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TCombobox', padding=5, font=('Segoe UI', 10))
        
        # Create and configure main frame with padding
        main_frame = ttk.Frame(self.root, padding="20", style='TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title Label
        title_label = tk.Label(
            main_frame,
            text="Wikipedia Search | Пошук у Вікіпедії",
            font=self.heading_font,
            background='#f0f0f0',
            foreground='#2c3e50'
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Search frame
        search_frame = ttk.Frame(main_frame, style='TFrame')
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        search_frame.columnconfigure(1, weight=1)

        # Language selector
        lang_label = tk.Label(
            search_frame,
            text="Language | Мова:",
            font=('Segoe UI', 10),
            background='#f0f0f0',
            foreground='#34495e'
        )
        lang_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))

        self.language_var = tk.StringVar(value="English")
        language_cb = ttk.Combobox(
            search_frame,
            textvariable=self.language_var,
            values=list(WikiAPIAgent.LANGUAGES.keys()),
            state='readonly',
            width=15
        )
        language_cb.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        # Search label
        search_label = tk.Label(
            search_frame,
            text="Search term | Пошуковий запит:",
            font=('Segoe UI', 10),
            background='#f0f0f0',
            foreground='#34495e'
        )
        search_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 5))

        # Search entry with custom style
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Segoe UI', 11)
        )
        search_entry.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

        # Control frame for checkbox and button
        control_frame = ttk.Frame(main_frame, style='TFrame')
        control_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        
        # Full article checkbox with custom style
        self.full_article_var = tk.BooleanVar(value=False)
        full_article_cb = ttk.Checkbutton(
            control_frame,
            text="Show Full Article | Показати повну статтю",
            variable=self.full_article_var,
            style='TCheckbutton'
        )
        full_article_cb.pack(side=tk.LEFT, padx=5)

        # Search button with custom style
        search_button = ttk.Button(
            control_frame,
            text="Search | Пошук",
            command=self.perform_search,
            style='TButton'
        )
        search_button.pack(side=tk.LEFT, padx=5)

        # Result frame
        result_frame = ttk.Frame(main_frame, style='TFrame')
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)

        # Results label
        results_label = tk.Label(
            result_frame,
            text="Results | Результати:",
            font=('Segoe UI', 10),
            background='#f0f0f0',
            foreground='#34495e'
        )
        results_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Result area with custom styling
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            background='white',
            foreground='#2c3e50',
            padx=10,
            pady=10,
            height=25
        )
        self.result_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        self.status_var = tk.StringVar(value="Ready | Готово")
        status_bar = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9),
            background='#f0f0f0',
            foreground='#7f8c8d'
        )
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Bind Enter key to search
        search_entry.bind('<Return>', lambda e: self.perform_search())
        
        # Give focus to search entry
        search_entry.focus()

    def display_result(self, text):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)

    def perform_search(self):
        topic = self.search_var.get().strip()
        if not topic:
            messagebox.showwarning(
                "Input Required | Потрібне введення",
                "Please enter a search term.\nБудь ласка, введіть пошуковий запит."
            )
            return
        
        # Update status
        self.status_var.set("Searching... | Пошук...")
        self.root.update_idletasks()
        
        try:
            language_code = WikiAPIAgent.LANGUAGES[self.language_var.get()]
            if self.full_article_var.get():
                result = WikiAPIAgent.get_full_article(topic, language_code)
                self.status_var.set("Full article retrieved | Отримано повну статтю")
            else:
                result = WikiAPIAgent.get_summary(topic, language_code)
                self.status_var.set("Summary retrieved | Отримано короткий зміст")
        except Exception as e:
            self.status_var.set("Error occurred | Виникла помилка")
            result = f"Error | Помилка: {str(e)}"
        
        self.display_result(result)


if __name__ == "__main__":
    root = tk.Tk()
    app = WikiSearchApp(root)
    root.mainloop()
