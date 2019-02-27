html = u"""
<html>
    <head>
    </head>
    <body>
        <h1>Access Summary for {journal} </h1>
        <p>This is an email message.</p>

        {summary_table}

        {main_table}
    </body>
</html>
       """

text = u"""
Dear Editor,

Below is a summary of the access to "{journal}"

--Journal Summary--
Datasets: {package_num}
Resources: {package_resources}
Total Views: {package_view}
Total Downloads: {package_download}

--Dataset Breakdown--{packages_text}

"""
