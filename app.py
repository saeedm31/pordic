import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import openai

import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()

openai.api_key = config.get("OpenAI", "api_key")


# Read the config.ini file
config.read("config.ini")


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dictionary"),
    dcc.Textarea(id="input-box", value="", rows=10, cols=50, maxLength=200),
    html.Button("Translate it", id="translate-button", n_clicks=0),
    html.H2("Here are the translation:"),
    html.Div(id="translation-output"),
    html.Button("Clear", id="clear-button"),
])

@app.callback(
    Output("translation-output", "children"),
    Input("translate-button", "n_clicks"),
    State("input-box", "value")
)
def dic_response(n_clicks, input_text):
    if n_clicks > 0 and input_text:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Translate this in Portuguese from Portugal, DO NOT USE Portuguese from Brazil, only use Portuguese from Portugal: {input_text}",
            temperature=0,
            max_tokens=100
        )
        translation = response.choices[0].text.strip()
        return translation

@app.callback(
    Output("input-box", "value"),
    Input("clear-button", "n_clicks")
)
def clear_input(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        return ""

if __name__ == "__main__":
    app.run_server(debug=True)
