def style_sheet_template(widget_class):
    return f"""
            {widget_class.__name__}:disabled {{
                background-color: lightgray;
                color: black;
            }}
            {widget_class.__name__}:enabled {{
                background-color: white;
                color: black;
            }}
            """