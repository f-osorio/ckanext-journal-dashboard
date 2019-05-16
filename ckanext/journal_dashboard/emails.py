html = u"""
<html>
    <head>
        <style>
            table {{
                border: 1px solid black;
                table-layout: fixed;
                border-collapse: collapse;
                text-align:center;
                padding-right: 5px;
                padding-left: 5px;
            }}

            .heading{{
                border-bottom: 1px solid black;
            }}

            .dataset_name {{
                background: #8caef7;
            }}
        </style>
    </head>
    <body>
        <h1>Access Summary for "{journal}"</h1>

        <table style="text-align: center; width: 50%; border: 1px solid black; margin-right: 25%; margin-left: 25%;">
            <thead style="font-weight:bold;">
                <tr>
                    <td>Datasets</td>
                    <td>Resources</td>
                    <td>Total Views</td>
                    <td>Total Downloads</td>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{package_num}</td>
                    <td>{package_resources}</td>
                    <td>{package_view}</td>
                    <td>{package_download}</td>
                </tr>
            </tbody>
        </table>
        <h3>Summary of Dataset & Resources:</h3>
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
