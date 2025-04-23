def webpage(
    brightness: int,
    alarm_time: tuple[int, int],
    sunrise_led_mode: str,
    # main_led_mode: str
    ):
    """
    brightness: int, expecting 0-100
    alarm_time: tuple,
    sunrise_led_mode: str,
    main_led_mode: str
    """
    
    # convert alarm_time from tuple[int, int] to tuple[str, str]
    alarm_time_str = []
    for t in alarm_time:
        # add leading zero if required
        if t < 10:
            t = f"0{str(t)}"
        else:
            t = str(t)
        alarm_time_str.append(t)
        
    hour = alarm_time_str[0]
    minute = alarm_time_str[1]
    
    if sunrise_led_mode == "sunrise_alarm":
        sunrise_led_mode = "Alarm"
    else:
        # lowercase to Title
        sunrise_led_mode = f"{sunrise_led_mode[0].upper()}{sunrise_led_mode[1:]}"
    
    # main_led_mode = f"{main_led_mode[0].upper()}{main_led_mode[1:]}"

    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Time Input Form</title>
        <style>
        
            body {{
              background: #555;
            }}

            .content {{
              max-width: 500px;
              margin: auto;
              background: white;
              padding: 10px;
            }}
        
            .pill-button-group {{
                display: flex;
                gap: 10px;
                margin-top: 10px;
                margin-bottom: 10px;
            }}
            .pill-button {{
                padding: 10px 20px;
                border: none;
                border-radius: 20px;
                background-color: lightgray;
                cursor: pointer;
            }}
            .pill-button.selected {{
                background-color: blue;
                color: white;
            }}
        </style>
        <script>
            function selectPill(group, button) {{
                document.querySelectorAll('.' + group + ' .pill-button').forEach(btn => btn.classList.remove('selected'));
                button.classList.add('selected');
                document.getElementById(group + '-selected').value = button.textContent;
            }}
        </script>
    </head>
    <body class="content">
        <h2>Sunrise alarm clock controller</h2>
        
        <form action="/" method="POST">
            <div>
                <label for="percentage">Brightness (%):</label>
                <input type="number" id="percentage" name="percentage" min="0" max="100" step="1" value={brightness} required>
            </div>
            
            <br>

            <div>
                <label for="time">Alarm time:</label>
                <input type="time" id="time" name="time" value="{hour}:{minute}" required>
            </div>
              
            <h4>Sunrise LEDs</h4>
            <div class="pill-button-group group1">
                <button type="button" class="pill-button {'selected' if sunrise_led_mode == 'Off' else ''}" onclick="selectPill('group1', this)">Off</button>
                <button type="button" class="pill-button {'selected' if sunrise_led_mode == 'White' else ''}" onclick="selectPill('group1', this)">White</button>
                <button type="button" class="pill-button {'selected' if sunrise_led_mode == 'Rainbow' else ''}" onclick="selectPill('group1', this)">Rainbow</button>
                <button type="button" class="pill-button {'selected' if sunrise_led_mode == 'Alarm' else ''}" onclick="selectPill('group1', this)">Alarm</button>
            </div>
            <input type="hidden" id="group1-selected" name="sunrise_led" value="{sunrise_led_mode}" />
            
            <br>            
            <button type="submit">Set</button>
            <br>
        </form>
        
        <form action="/" method="POST">
            <button name="time" value="settime">Set RTC</button>
        </form>
        
    </body>
    </html>
    """

    return str(html)
