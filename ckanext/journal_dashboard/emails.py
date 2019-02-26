html = u"""
<html>
    <head>
        <style>
            tr, td {{
                padding-left: 15px;
                text-align: center;
            }}

            .label-published{{
                background: green;
            }}

            .label-important{{
                background: #e0051e;
            }}

            .list_item{{
                font-family: monospace;
                list-style-type: none;
            }}

            a[target="_blank"]:after {{
                content: url(http://upload.wikimedia.org/wikipedia/commons/6/64/Icon_External_Link.png);
                margin: 0 0 0 5px;
            }}

            #body{{
                margin-left: 25%;
                margin-right: 25%;
            }}

            .label {{
              display: inline-block;
              padding: 2px 4px;
              font-size: 11.844px;
              font-weight: bold;
              line-height: 14px;
              color: white;
              vertical-align: baseline;
              white-space: nowrap;
              text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
              font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }}

            .label {{
              -webkit-border-radius: 3px;
              -moz-border-radius: 3px;
              border-radius: 3px;
            }}
            </style>
    </head>
    <body>
        <h1>Access Summary for {journal} </h1>
        <p>This is an email message.</p>

        {summary_table}

        <p>BODY</p>
        {main_table}
    </body>
</html>
       """

text = u"""
        Hello There,

        This is a text message.
       """
