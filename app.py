import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import openai
import os

# import configparser
# config = configparser.ConfigParser()
# config.read('config.ini')
# pythonapi_key = config.get('OpenAI', 'api_key')

openai.api_key = os.environ["api_key"]

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div(
    children=[
        html.H1("Portuguese Translate and Dictionary (pordic V.1)", style={"text-align": "center"}),
        html.Div([
            html.H3("Translate text from any language to Portuguese (Portugal version) or from Portuguese to \
                    English with the power of ChatGPT (gpt-3.5-turbo)."),
            dcc.Textarea(id="input-box", value="", rows=5, cols=50, maxLength=200),
            html.Div([
                html.Div([
                    html.Button("Translate", id="translate-button", n_clicks=0, className="btn-translate"),
                ], className="translate-button-container"),
                html.Div(id="translation-output", className="translation-box"),
            ], className="button-group"),
            html.Div([html.Br(), html.Br()]),  # Add space between the button group and the Clear button
            html.Div([
                html.Button("Clear", id="clear-button", n_clicks=0, className="btn-clear"),
            ], className="clear-button-container"),
        ], className="translation-container"),
    ],
    className="main-container",
    style={"backgroundColor": "lightgreen", "padding": "20px"}
)

@app.callback(
    Output("translation-output", "children"),
    Input("translate-button", "n_clicks"),
    State("input-box", "value")
)
def translate_text(n_clicks, input_text):
    if n_clicks > 0 and input_text:
        # response = openai.Completion.create(
        #     engine="gpt-3.5-turbo",
        #     prompt=f"Detect the language of the folowing Text and translate the Text into Portuguese from Portugal, do not use Brazilian Portuguese. If the Text \
        #          is in Portuguese, translate the text to English,only return the translation, no explnation, here is the Text: {input_text}",
        #     temperature=0,
        #     max_tokens=400,
        #     api_key=os.environ["api_key"]
        # )
        # translation = response.choices[0].text.strip()
        prompt=f"Detect the language of the folowing Text and translate the Text into Portuguese from Portugal, do not use Brazilian Portuguese, If the Text \
                  is in Portuguese, translate the text to English,only return the translation, no explnation, only return the translatiion"
        prompt_2=f"only return the translation, no explnation, only return the translatiion, here is the Text: {input_text}"
        completion = openai.ChatCompletion.create(
        model = 'gpt-3.5-turbo',
        messages = [
            {"role": "system", "content": prompt},
            {'role': 'assistant', 'content': prompt_2}
        ],
        temperature = 0  
        )

        print(completion['choices'][0]['message']['content'])
        translation = completion['choices'][0]['message']['content']
        return html.Div([
            dcc.Markdown(f"**Translation:**"),
            dcc.Markdown(f"{translation}")
            
        ])

@app.callback(
    Output("input-box", "value"),
    Input("clear-button", "n_clicks")
)
def clear_input(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        return ""

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5004)), host='0.0.0.0')


